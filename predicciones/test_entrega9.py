from datetime import date
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from io import StringIO
from .models import InformeSocial
from .redes_api import Meta, ErrorRedes, consultar
from .modelo_ia import _historial, _entrenamiento, _modelo, _preparar, VARIABLES
from .test_funcionalidad import row

class CuentasTests(TestCase):
    def test_login_logout_y_contrasena_protegida(self):
        u=get_user_model().objects.create_user('beni',password='ClaveDePrueba!92736')
        self.assertNotEqual(u.password,'ClaveDePrueba!92736')
        self.assertTrue(u.check_password('ClaveDePrueba!92736'))
        for path in ['/','/redes/','/modelo/comprobar/','/registros/exportar/']:
            self.assertEqual(self.client.get(path).status_code,302)
        self.assertFalse(self.client.login(username='beni',password='incorrecta'))
        self.assertTrue(self.client.login(username='beni',password='ClaveDePrueba!92736'))
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/cuenta/salir/').status_code,405)
        self.assertEqual(self.client.post('/cuenta/salir/').status_code,302)
        self.assertEqual(self.client.get('/').status_code,302)
    def test_solo_propietario_crea_cuentas(self):
        owner=get_user_model().objects.create_superuser('owner',password='UnaClaveCompleja!53689')
        self.client.force_login(owner)
        response=self.client.post('/cuenta/usuarios/',{'username':'nuevo','password1':'OtraClaveCompleja!9217','password2':'OtraClaveCompleja!9217'})
        self.assertEqual(response.status_code,302)
        nuevo=get_user_model().objects.get(username='nuevo')
        self.assertFalse(nuevo.is_staff)
        self.assertTrue(nuevo.check_password('OtraClaveCompleja!9217'))
        self.client.force_login(nuevo)
        self.assertEqual(self.client.get('/cuenta/usuarios/').status_code,302)
        self.assertEqual(self.client.post('/redes/',{}).status_code,403)

class RedesTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser('owner'))
        self.values={'fuente':'anuncios','desde':'2025-01-01','hasta':'2025-01-31'}
    @patch('predicciones.redes.consultar',return_value=('123',[{'id':'1','nombre':'Real desde API','gasto':'10','moneda':'ARS'}]))
    def test_guardado_reconsulta_sin_duplicados_y_vista(self,fetch):
        for _ in range(2): self.assertEqual(self.client.post('/redes/',self.values).status_code,302)
        self.assertEqual(InformeSocial.objects.count(),1)
        report=InformeSocial.objects.get()
        self.assertEqual(report.desde,date(2025,1,1))
        self.assertContains(self.client.get('/redes/',{'informe':report.pk}),'Real desde API')
    def test_error_conserva_informe_y_fecha(self):
        report=InformeSocial.objects.create(fuente='anuncios',cuenta='123',desde='2025-01-01',hasta='2025-01-31',filas=[{'id':'anterior'}])
        old=report.consultado
        with patch('predicciones.redes.consultar',side_effect=ErrorRedes('Token vencido')):
            self.assertContains(self.client.post('/redes/',self.values),'Token vencido')
        report.refresh_from_db()
        self.assertEqual(report.consultado,old)
        self.assertEqual(report.filas,[{'id':'anterior'}])
    @patch('predicciones.redes.consultar')
    def test_periodo_invalido_no_consulta(self,fetch):
        self.client.post('/redes/',dict(self.values,hasta='2024-01-01'))
        fetch.assert_not_called()

class TransporteTests(SimpleTestCase):
    def test_paginacion_no_sigue_urls_del_proveedor(self):
        api=Meta('secreto','v26.0')
        with patch.object(api,'get',side_effect=[{'data':[{'id':'1'}],'paging':{'next':'https://otro-sitio.invalid/','cursors':{'after':'cursor'}}},{'data':[{'id':'2'}]}]) as get:
            self.assertEqual(len(api.listar('act_123/insights',{})),2)
            self.assertEqual(get.call_args.args[0],'act_123/insights')
            self.assertEqual(get.call_args.args[1]['after'],'cursor')
    def test_ciclo_no_devuelve_informe_parcial(self):
        api=Meta('secreto','v26.0')
        with patch.object(api,'get',return_value={'data':[{}],'paging':{'next':'url','cursors':{'after':'igual'}}}):
            with self.assertRaises(ErrorRedes): api.listar('123/media',{})
    @patch('predicciones.redes_api.configuracion',return_value=('123','secreto','v26.0'))
    def test_anuncios_envia_periodo_y_conserva_moneda(self,config):
        with patch.object(Meta,'listar',return_value=[{'campaign_id':'1','spend':'4.21','account_currency':'USD'}]) as listing:
            account,rows=consultar('anuncios',date(2025,1,1),date(2025,1,31))
            self.assertEqual(rows[0]['moneda'],'USD')
            self.assertIn('2025-01-31',listing.call_args.args[1]['time_range'])
    @patch('predicciones.redes_api.configuracion',return_value=('123','secreto','v26.0'))
    def test_publicaciones_filtra_fecha_y_ausencia_no_es_cero(self,config):
        data=[{'id':'1','timestamp':'2025-01-02T12:00:00Z','like_count':0},{'id':'2','timestamp':'2024-12-01T12:00:00Z'}]
        with patch.object(Meta,'listar',return_value=data),patch.object(Meta,'get',return_value={'data':[{'name':'reach','values':[{'value':12}]}]}):
            _,rows=consultar('instagram',date(2025,1,1),date(2025,1,31))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['alcance'],12)
        self.assertEqual(rows[0]['likes'],0)
        self.assertIsNone(rows[0]['comentarios'])

class ModeloRealTests(TestCase):
    def test_bosque_real_aprende_objetivo_constante(self):
        df=_preparar([row(f'2025-{i+1:02}-01',alumnos_nuevos=7) for i in range(12)])
        model=_modelo().fit(df[VARIABLES],df['alumnos_nuevos'])
        predictions=model.predict(df[VARIABLES])
        self.assertTrue(all(x==7 for x in predictions))
    def test_separacion_seleccion_validacion_y_auditoria(self):
        call_command('importar_datos',stdout=StringIO())
        _entrenamiento.cache_clear()
        _,model,e=_historial()
        self.assertEqual(e['periodos'],3)
        self.assertEqual(len(e['validacion']),3)
        self.assertEqual(len(e['comparacion']),6)
        self.assertIsNotNone(e['mae_validacion'])
        self.assertTrue(all(x['modelo']>=0 for x in e['comparacion']))
        self.client.force_login(get_user_model().objects.create_user('auditor'))
        self.assertContains(self.client.get('/modelo/comprobar/'),'36 coinciden')
