import csv
from datetime import date
import hashlib
from io import StringIO
import uuid
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, SimpleTestCase

from .csv_service import COLUMNAS, ErrorCSV, aplicar_csv, estado_actual, leer_csv
from .forms import CampanaMensualForm, RegistroMensualForm, SimulacionForm
from .models import CampanaMensual, ImportacionCSV, RegistroMensual
from .modelo_ia import _entrenamiento, _evaluar, _preparar, predecir_proximo_mes, simular_prediccion
from .calidad import revisar_historial


def row(period='2025-01-01', **changes):
    data = {'fecha': period, 'alumnos_inicio': 100, 'consultas': 30, 'clases_prueba': 12, 'inversion_publicidad': 3000, 'cuota_mensual': 10000, 'promocion': 0, 'alumnos_nuevos': 6, 'bajas': 3}
    data.update(changes)
    return data


def csv_bytes(rows, delimiter=','):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNAS, delimiter=delimiter)
    writer.writeheader()
    writer.writerows(rows)
    return ('\ufeff' + output.getvalue()).encode()


class ValidacionDatosTests(TestCase):
    def test_bom_espacios_punto_y_coma_y_decimales(self):
        content = csv_bytes([row(inversion_publicidad='1200,50')], ';') + b'\n;;;;;;;;\n'
        self.assertEqual(leer_csv(content)[0]['inversion_publicidad'], 1200.5)

    def test_csv_rechaza_duplicados_no_finitos_booleanos_y_fechas(self):
        for rows in [[row(), row()], [row(inversion_publicidad='NaN')], [row(cuota_mensual='Infinity')], [row(promocion='quizas')], [row('2025-01-02')], [row('0001-01-01')], [row(bajas=999)], [row(alumnos_nuevos='2.5')]]:
            with self.subTest(rows=rows), self.assertRaises(ErrorCSV): leer_csv(csv_bytes(rows))

    def test_formularios_rechazan_valores_invalidos_en_servidor(self):
        for change in [{'inversion_publicidad': -1}, {'inversion_publicidad': '1e100'}, {'cuota_mensual': 'nan'}, {'bajas': 120}, {'clases_prueba': 31}]:
            self.assertFalse(RegistroMensualForm(row(**change)).is_valid())
        self.assertFalse(CampanaMensualForm({'periodo': '2025-01-01', 'nombre': 'Prueba', 'canal': 'Instagram', 'inversion': '-1', 'alcance': '', 'clics': '5', 'contactos': '', 'pruebas': '5', 'altas': '2'}).is_valid())
        self.assertFalse(SimulacionForm(dict(row(), mes_objetivo=1, inversion_publicidad='nan')).is_valid())


class ConSesionTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.client.force_login(get_user_model().objects.create_user(username='equipo_prueba'))

class ImportacionWebTests(ConSesionTests):
    def setUp(self):
        super().setUp()
        RegistroMensual.objects.create(**row())

    def preview(self, rows, mode='actualizar'):
        return self.client.post('/registros/importar/', {'accion': 'previsualizar', 'modo': mode, 'archivo': SimpleUploadedFile('datos.csv', csv_bytes(rows), 'text/csv')})

    def confirm(self, token=None):
        return self.client.post('/registros/importar/', {'accion': 'confirmar', 'token': token or self.client.session['csv_pending']['token']})

    def test_preview_confirmacion_y_reintento(self):
        response = self.preview([row(alumnos_nuevos=8), row('2025-02-01')])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmar importación')
        self.assertEqual(RegistroMensual.objects.count(), 1)
        self.assertEqual(RegistroMensual.objects.first().alumnos_nuevos, 6)
        token = self.client.session['csv_pending']['token']
        self.assertEqual(self.confirm().status_code, 302)
        self.assertEqual(RegistroMensual.objects.count(), 2)
        self.assertEqual(ImportacionCSV.objects.count(), 1)
        batch = ImportacionCSV.objects.get()
        self.assertEqual((batch.creados, batch.actualizados), (1, 1))
        self.assertEqual(self.confirm(token).status_code, 302)
        self.assertEqual(ImportacionCSV.objects.count(), 1)

    def test_archivo_invalido_no_modifica_nada(self):
        response = self.preview([row(alumnos_nuevos=9), row('2025-02-01', bajas=1000)])
        self.assertContains(response, 'Fila 3')
        self.assertEqual(RegistroMensual.objects.first().alumnos_nuevos, 6)
        self.assertNotIn('csv_pending', self.client.session)
        self.assertFalse(ImportacionCSV.objects.exists())

    def test_solo_nuevos_conserva_lo_existente(self):
        self.preview([row(alumnos_nuevos=9), row('2025-02-01')], mode='nuevos')
        self.confirm()
        self.assertEqual(RegistroMensual.objects.get(fecha='2025-01-01').alumnos_nuevos, 6)
        self.assertEqual(ImportacionCSV.objects.get().omitidos, 1)

    def test_edicion_concurrente_exige_otra_vista_previa(self):
        self.preview([row(alumnos_nuevos=9), row('2025-02-01')])
        RegistroMensual.objects.filter(fecha='2025-01-01').update(alumnos_nuevos=10)
        response = self.confirm()
        self.assertEqual(response.status_code, 409)
        self.assertContains(response, 'historial cambió', status_code=409)
        self.assertEqual(RegistroMensual.objects.count(), 1)
        self.assertFalse(ImportacionCSV.objects.exists())

    def test_sin_token_no_importa(self):
        response = self.confirm('token-invalido')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RegistroMensual.objects.count(), 1)

    def test_error_de_base_revierte_el_lote_completo(self):
        rows = leer_csv(csv_bytes([row(alumnos_nuevos=9), row('2025-02-01')]))
        baseline = estado_actual(rows)
        original = RegistroMensual.objects.update_or_create
        calls = 0
        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2: raise IntegrityError('fallo simulado de prueba')
            return original(*args, **kwargs)
        with patch('predicciones.csv_service.RegistroMensual.objects.update_or_create', side_effect=fail_second):
            with self.assertRaises(IntegrityError): aplicar_csv(rows, 'actualizar', baseline, uuid.uuid4(), 'test.csv', 'a'*64)
        self.assertEqual(RegistroMensual.objects.get().alumnos_nuevos, 6)
        self.assertFalse(ImportacionCSV.objects.exists())

    def test_cli_verificar_no_modifica_registros(self):
        before = list(RegistroMensual.objects.values())
        call_command('importar_datos', verificar=True, stdout=StringIO())
        self.assertEqual(before, list(RegistroMensual.objects.values()))
        self.assertFalse(ImportacionCSV.objects.exists())


class HistorialYCampanasTests(ConSesionTests):
    @classmethod
    def setUpTestData(cls):
        call_command('importar_datos', stdout=StringIO())

    def test_filtros_exportacion_y_paginacion(self):
        values = {'desde': '2025-02', 'hasta': '2025-02'}
        response = self.client.get('/', values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_filtrados'], 1)
        export = self.client.get('/registros/exportar/', values)
        rows = list(csv.DictReader(StringIO(export.content.decode('utf-8-sig'))))
        self.assertEqual([record['fecha'] for record in rows], ['2025-02-01'])
        second = self.client.get('/', {'page': 2})
        self.assertEqual(len(second.context['registros']), 12)
        self.assertEqual(second.context['pagina'].number, 2)
        searched = self.client.get('/', {'buscar': 'febrero'})
        self.assertEqual(searched.context['total_filtrados'], 3)

    def test_rango_invalido_no_exporta_todo(self):
        values = {'desde': '2025-12', 'hasta': '2025-01'}
        self.assertEqual(self.client.get('/registros/exportar/', values).status_code, 400)
        self.assertContains(self.client.get('/', values), 'mes inicial')

    def test_campana_edita_persiste_y_exporta_texto_seguro(self):
        values = {'periodo': '2025-01-01', 'nombre': '=SUM(1+1)', 'canal': 'Instagram', 'inversion': '1000.50', 'alcance': '100', 'clics': '120', 'contactos': '10', 'pruebas': '5', 'altas': '2'}
        self.assertEqual(self.client.post('/marketing/campanas/nueva/', values).status_code, 302)
        campaign = CampanaMensual.objects.get()
        values['inversion'] = '1500.50'
        self.assertEqual(self.client.post(f'/marketing/campanas/{campaign.pk}/editar/', values).status_code, 302)
        campaign.refresh_from_db()
        self.assertEqual(float(campaign.inversion), 1500.5)
        self.assertEqual(CampanaMensual.objects.count(), 1)
        self.assertIn("'=SUM", self.client.get('/marketing/exportar/').content.decode())
        values['inversion'] = '-1'
        error = self.client.post(f'/marketing/campanas/{campaign.pk}/editar/', values)
        self.assertEqual(error.status_code, 200)
        self.assertContains(error, '=SUM(1+1)')
        campaign.refresh_from_db()
        self.assertEqual(float(campaign.inversion), 1500.5)

    def test_simulador_rechaza_nan_sin_error_500(self):
        response = self.client.post('/', dict(row(), accion='simular', mes_objetivo=1, inversion_publicidad='NaN'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['resultado_simulacion'])
        self.assertTrue(response.context['error_simulacion'])


class PrediccionesTests(TestCase):
    def setUp(self): _entrenamiento.cache_clear()

    def test_backtest_no_usa_consultas_reales_del_mes_a_predecir(self):
        rows = [row(f'{2024+i//12}-{i%12+1:02}-01', clases_prueba=10+i%5, alumnos_nuevos=4+i%6) for i in range(13)]
        original = _evaluar(_preparar(rows))
        rows[-1].update(consultas=100000, clases_prueba=90000, inversion_publicidad=99999999, alumnos_inicio=100000)
        changed = _evaluar(_preparar(rows))
        self.assertEqual(original, changed)
        self.assertEqual(original['periodos'], 1)

    def test_doce_meses_no_muestran_error_cero_inventado(self):
        for i in range(12): RegistroMensual.objects.create(**row(f'2025-{i+1:02}-01'))
        result = predecir_proximo_mes()
        self.assertIsNone(result['error_medio'])
        self.assertEqual(result['periodos_evaluados'], 0)

    def test_simulacion_usa_los_datos_del_escenario(self):
        rows = [row(f'2025-{i+1:02}-01') for i in range(12)]
        df = _preparar(rows)
        class PredictByQueries:
            def predict(self, values): return [float(values.iloc[0]['consultas']) / 10]
        with patch('predicciones.modelo_ia._historial', return_value=(df, PredictByQueries(), {'modelo': 50, 'referencia': 1})):
            result = simular_prediccion(dict(row(), alumnos_inicio=100, consultas=90, mes_objetivo=1))
        self.assertEqual(result['altas'], 9)
        self.assertEqual(result['base_altas'], 3)
        self.assertEqual(RegistroMensual.objects.count(), 0)

    def test_cache_cambia_cuando_se_edita_un_mes(self):
        for i in range(12): RegistroMensual.objects.create(**row(f'2025-{i+1:02}-01'))
        predecir_proximo_mes(); predecir_proximo_mes()
        self.assertEqual(_entrenamiento.cache_info().misses, 1)
        RegistroMensual.objects.filter(fecha='2025-12-01').update(alumnos_nuevos=8)
        predecir_proximo_mes()
        self.assertEqual(_entrenamiento.cache_info().misses, 2)

    def test_calidad_detecta_huecos_y_saldos(self):
        first = RegistroMensual.objects.create(**row('2025-01-01'))
        third = RegistroMensual.objects.create(**row('2025-03-01'))
        fourth = RegistroMensual.objects.create(**row('2025-04-01', alumnos_inicio=999))
        quality = revisar_historial(list(RegistroMensual.objects.order_by('fecha')))
        self.assertEqual(quality['faltantes'], ['02/2025'])
        self.assertEqual(quality['saltos'], ['04/2025'])
