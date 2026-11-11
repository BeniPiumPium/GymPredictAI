import csv
import hashlib
from collections import defaultdict
from datetime import date
import time
import unicodedata
from urllib.parse import urlencode
import uuid

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .analisis import calcular_indicadores
from .calidad import revisar_historial, siguiente_mes
from .csv_service import COLUMNAS, ErrorCSV, aplicar_csv, estado_actual, leer_csv, resumir
from .forms import CampanaMensualForm, FiltroRegistrosForm, ImportarCSVForm, RegistroMensualForm, SimulacionForm
from .models import CampanaMensual, ImportacionCSV, RegistroMensual
from .modelo_ia import predecir_proximo_mes, simular_prediccion

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def _normalizar(text):
    return ''.join(char for char in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(char))


def _filtrar(request):
    form = FiltroRegistrosForm(request.GET)
    if not form.is_valid(): return [], form
    values = form.cleaned_data
    records = RegistroMensual.objects.order_by('-fecha')
    if values['desde']: records = records.filter(fecha__gte=values['desde'].replace(day=1))
    if values['hasta']: records = records.filter(fecha__lte=values['hasta'].replace(day=1))
    if values['promocion']: records = records.filter(promocion=values['promocion'] == 'si')
    records = list(records)
    if values['buscar']:
        query = _normalizar(values['buscar'].strip())
        records = [record for record in records if query in _normalizar(f'{MESES[record.fecha.month-1]} {record.fecha.year} {record.fecha:%Y-%m} {record.fecha:%m/%Y}')]
    return records, form


@require_http_methods(['GET', 'POST'])
def dashboard(request):
    records = list(RegistroMensual.objects.order_by('fecha'))
    campaigns = list(CampanaMensual.objects.order_by('-periodo', '-creada'))
    latest = records[-1] if records else None
    indicators = calcular_indicadores()
    forecast = predecir_proximo_mes()
    filtered, filter_form = _filtrar(request)
    page = Paginator(filtered, 12).get_page(request.GET.get('page'))
    query = urlencode({key: request.GET[key] for key in filter_form.fields if request.GET.get(key)})
    def page_url(number): return '?' + (query + '&' if query else '') + f'page={number}#registros'
    totals = {key: sum(getattr(record, key) for record in records) for key in ['alumnos_nuevos', 'consultas', 'clases_prueba', 'bajas', 'inversion_publicidad']}
    active = indicators['alumnos_activos'] if indicators else 0
    last_year = records[-12:]
    charts = {
        'labels': [f'{MESES[r.fecha.month-1][:3]} {r.fecha:%y}' for r in last_year],
        'altas': [r.alumnos_nuevos for r in last_year], 'bajas': [r.bajas for r in last_year],
        'socios': [max(0, r.alumnos_inicio+r.alumnos_nuevos-r.bajas) for r in last_year],
        'inversion': [r.inversion_publicidad for r in last_year],
    }
    months = defaultdict(list)
    for record in records: months[record.fecha.month].append(record.alumnos_nuevos)
    seasonality = [{'mes': MESES[i-1], 'promedio': round(sum(months[i])/len(months[i]), 1) if months[i] else 0, 'registros': len(months[i])} for i in range(1, 13)]
    campaign_totals = {key: sum(getattr(c, key) for c in campaigns) for key in ['inversion', 'alcance', 'clics', 'contactos', 'pruebas', 'altas']}
    campaign_totals['costo_alta'] = campaign_totals['inversion']/campaign_totals['altas'] if campaign_totals['altas'] else None
    by_channel = {}
    for campaign in campaigns:
        entry = by_channel.setdefault(campaign.canal, {'canal': campaign.canal, 'inversion': 0, 'altas': 0, 'contactos': 0})
        for key in ['inversion', 'altas', 'contactos']: entry[key] += getattr(campaign, key)
    for entry in by_channel.values(): entry['costo_alta'] = entry['inversion']/entry['altas'] if entry['altas'] else None
    result, simulation_error = None, None
    simulation = {
        'alumnos_inicio': active, 'consultas': latest.consultas if latest else 80,
        'clases_prueba': latest.clases_prueba if latest else 25,
        'inversion_publicidad': latest.inversion_publicidad if latest else 0,
        'cuota_mensual': latest.cuota_mensual if latest else 0,
        'promocion': latest.promocion if latest else False,
        'mes_objetivo': latest.fecha.month % 12 + 1 if latest else 1,
    }
    if request.method == 'POST':
        if request.POST.get('accion') != 'simular': return HttpResponse('Acción inválida.', status=400)
        form = SimulacionForm(request.POST)
        simulation = request.POST
        if form.is_valid():
            result = simular_prediccion(form.cleaned_data)
            if result is None: simulation_error = 'Necesitás al menos 12 meses para simular.'
        else:
            simulation_error = ' '.join(f'{form.fields[key].label or key}: {error}' for key, errors in form.errors.items() for error in errors)
    context = {
        'registros': page.object_list, 'pagina': page, 'filtro_form': filter_form, 'filter_query': query,
        'prev_url': page_url(page.previous_page_number()) if page.has_previous() else '',
        'next_url': page_url(page.next_page_number()) if page.has_next() else '',
        'campanas': campaigns, 'canales': sorted(by_channel.values(), key=lambda item: item['inversion'], reverse=True),
        'total_meses': len(records), 'total_filtrados': len(filtered), 'total_alumnos_nuevos': totals['alumnos_nuevos'],
        'total_consultas': totals['consultas'], 'total_pruebas': totals['clases_prueba'], 'total_bajas': totals['bajas'],
        'total_inversion': totals['inversion_publicidad'], 'promedio_alumnos_nuevos': round(totals['alumnos_nuevos']/len(records), 1) if records else 0,
        'socios_activos': active, 'ingreso_estimado': active*latest.cuota_mensual if latest else 0,
        'ultimo': latest, 'prediccion': forecast, 'indicadores': indicators, 'datos_grafico': charts,
        'estacionalidad': seasonality, 'campaign_totals': campaign_totals, 'calidad': revisar_historial(records),
        'resultado_simulacion': result, 'error_simulacion': simulation_error, 'sim_form': simulation,
        'meses': list(enumerate(MESES, 1)),
        'initial_view': 'prediccion' if request.method == 'POST' else 'registros' if request.GET else 'inicio',
        'formulario_campana': CampanaMensualForm(initial={'periodo': siguiente_mes(latest.fecha) if latest else timezone.localdate().replace(day=1)}),
    }
    return render(request, 'predicciones/dashboard.html', context)


def _registro_form(request, record=None):
    latest = RegistroMensual.objects.order_by('-fecha').first()
    initial = {'fecha': siguiente_mes(latest.fecha) if latest else timezone.localdate().replace(day=1)}
    form = RegistroMensualForm(request.POST if request.method == 'POST' else None, instance=record, initial=initial if record is None else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'El registro quedó guardado. Los indicadores se actualizaron.')
        return redirect(reverse('dashboard') + '#registros')
    return render(request, 'predicciones/registrar_mes.html', {'formulario': form, 'modo': 'editar' if record else 'nuevo'})


@require_http_methods(['GET', 'POST'])
def registrar_mes(request): return _registro_form(request)


@require_http_methods(['GET', 'POST'])
def editar_mes(request, registro_id): return _registro_form(request, get_object_or_404(RegistroMensual, pk=registro_id))


@require_POST
def eliminar_mes(request, registro_id):
    get_object_or_404(RegistroMensual, pk=registro_id).delete()
    messages.success(request, 'Se eliminó el registro mensual.')
    return redirect(reverse('dashboard') + '#registros')


def _campana_form(request, campaign=None):
    form = CampanaMensualForm(request.POST if request.method == 'POST' else None, instance=campaign)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Campaña guardada. Los totales por canal se actualizaron.')
        return redirect(reverse('dashboard') + '#marketing')
    return render(request, 'predicciones/campana_form.html', {'formulario': form, 'modo': 'editar' if campaign else 'nuevo'})


@require_http_methods(['GET', 'POST'])
def registrar_campana(request): return _campana_form(request)


@require_http_methods(['GET', 'POST'])
def editar_campana(request, campana_id): return _campana_form(request, get_object_or_404(CampanaMensual, pk=campana_id))


@require_POST
def eliminar_campana(request, campana_id):
    get_object_or_404(CampanaMensual, pk=campana_id).delete()
    messages.success(request, 'Se eliminó la campaña.')
    return redirect(reverse('dashboard') + '#marketing')


def _csv_response(filename, headers):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(headers)
    return response, writer


@require_GET
def exportar_datos(request):
    records, form = _filtrar(request)
    if not form.is_valid(): return HttpResponse('Filtros inválidos. Revisá el período elegido.', status=400)
    response, writer = _csv_response('gympredictai-registros.csv', COLUMNAS)
    for record in reversed(records):
        writer.writerow([record.fecha.isoformat(), record.alumnos_inicio, record.consultas, record.clases_prueba, record.inversion_publicidad, record.cuota_mensual, int(record.promocion), record.alumnos_nuevos, record.bajas])
    return response


@require_GET
def plantilla_csv(request): return _csv_response('gympredictai-plantilla.csv', COLUMNAS)[0]


def _excel_text(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value


@require_GET
def exportar_campanas(request):
    response, writer = _csv_response('gympredictai-campanas.csv', ['periodo', 'nombre', 'canal', 'inversion', 'alcance', 'clics', 'contactos', 'pruebas', 'altas'])
    for c in CampanaMensual.objects.order_by('periodo', 'id'):
        writer.writerow([c.periodo.isoformat(), _excel_text(c.nombre), c.canal, c.inversion, c.alcance, c.clics, c.contactos, c.pruebas, c.altas])
    return response


@require_http_methods(['GET', 'POST'])
def importar_csv(request):
    form = ImportarCSVForm()
    import_errors = []
    pending = request.session.get('csv_pending')
    status = 200
    if request.method == 'POST':
        action = request.POST.get('accion')
        if action == 'previsualizar':
            request.session.pop('csv_pending', None)
            pending = None
            form = ImportarCSVForm(request.POST, request.FILES)
            if form.is_valid():
                content = form.cleaned_data['archivo'].read()
                try:
                    rows = leer_csv(content)
                    baseline = estado_actual(rows)
                    pending = {'rows': rows, 'baseline': baseline, 'mode': form.cleaned_data['modo'], 'token': str(uuid.uuid4()), 'filename': form.cleaned_data['archivo'].name[:120], 'fingerprint': hashlib.sha256(content).hexdigest(), 'timestamp': time.time(), 'totals': resumir(rows, form.cleaned_data['modo'], baseline)}
                    request.session['csv_pending'] = pending
                except ErrorCSV as error:
                    form.add_error('archivo', error.errors)
        elif action == 'confirmar':
            token = request.POST.get('token')
            if token and token == request.session.get('csv_last_token'):
                messages.info(request, 'Esa importación ya se había aplicado.')
                return redirect(reverse('dashboard') + '#registros')
            if not pending or token != pending['token'] or time.time()-pending['timestamp'] > 1800:
                import_errors.append('La vista previa venció o no corresponde a esta sesión. Cargá el archivo de nuevo.')
                status = 400
                pending = None
                request.session.pop('csv_pending', None)
            else:
                try:
                    batch = aplicar_csv(pending['rows'], pending['mode'], pending['baseline'], pending['token'], pending['filename'], pending['fingerprint'], request.user if request.user.is_authenticated else None)
                    request.session.pop('csv_pending', None)
                    request.session['csv_last_token'] = token
                    messages.success(request, f'CSV importado: {batch.creados} nuevos, {batch.actualizados} actualizados y {batch.omitidos} sin cambios.')
                    return redirect(reverse('dashboard') + '#registros')
                except ErrorCSV as error:
                    import_errors.extend(error.errors)
                    request.session.pop('csv_pending', None)
                    pending, status = None, 409
                except (OperationalError, IntegrityError):
                    import_errors.append('No se guardó la importación porque la base cambió o está ocupada. Volvé a previsualizar el archivo.')
                    request.session.pop('csv_pending', None)
                    pending, status = None, 409
        else:
            return HttpResponse('Acción inválida.', status=400)
    return render(request, 'predicciones/importar_csv.html', {'formulario': form, 'pendiente': pending, 'errores_importacion': import_errors, 'muestra': pending['rows'][:10] if pending else [], 'lotes': ImportacionCSV.objects.select_related('usuario')[:10]}, status=status)
