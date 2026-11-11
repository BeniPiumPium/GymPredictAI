from .models import RegistroMensual


def calcular_indicadores():
    registros = list(RegistroMensual.objects.order_by("fecha"))
    if not registros:
        return None

    total_nuevos = sum(r.alumnos_nuevos for r in registros)
    total_bajas = sum(r.bajas for r in registros)
    total_consultas = sum(r.consultas for r in registros)
    total_pruebas = sum(r.clases_prueba for r in registros)
    total_inicio = sum(r.alumnos_inicio for r in registros)
    ultimo = registros[-1]
    alumnos_activos = max(0, ultimo.alumnos_inicio + ultimo.alumnos_nuevos - ultimo.bajas)
    conversion = total_nuevos / total_consultas * 100 if total_consultas else 0
    conversion_prueba = total_nuevos / total_pruebas * 100 if total_pruebas else 0
    tasa_bajas = total_bajas / total_inicio * 100 if total_inicio else 0

    return {
        "crecimiento_neto": total_nuevos - total_bajas,
        "conversion": round(conversion, 1),
        "conversion_prueba": round(conversion_prueba, 1),
        "total_bajas": total_bajas,
        "tasa_bajas": round(tasa_bajas, 2),
        "alumnos_activos": alumnos_activos,
        "promedio_altas": round(total_nuevos / len(registros), 1),
        "meses": len(registros),
    }
