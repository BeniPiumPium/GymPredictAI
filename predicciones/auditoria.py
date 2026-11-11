from django.shortcuts import render
from django.views.decorators.http import require_GET
from .modelo_ia import _historial, CAMPOS
from .models import RegistroMensual
from .csv_service import leer_csv
from django.conf import settings

@require_GET
def auditoria(request):
    analysis = _historial()
    evaluation = analysis[2] if analysis else None
    matches = 0
    try:
        sample = {row['fecha']: row for row in leer_csv((settings.BASE_DIR / 'datos_gimnasio.csv').read_bytes())}
        for row in RegistroMensual.objects.values(*CAMPOS):
            row['fecha'] = row['fecha'].isoformat()
            matches += row == sample.get(row['fecha'])
    except (OSError, ValueError): pass
    return render(request,'predicciones/auditoria.html',{'evaluacion':evaluation,'coincidencias':matches,'cantidad':RegistroMensual.objects.count()})
