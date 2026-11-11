from datetime import date
from django.utils import timezone


def siguiente_mes(value):
    return date(value.year + value.month // 12, value.month % 12 + 1, 1)


def revisar_historial(records):
    missing, discontinuities = [], []
    for previous, current in zip(records, records[1:]):
        expected = siguiente_mes(previous.fecha)
        while expected < current.fecha:
            missing.append(expected.strftime('%m/%Y'))
            expected = siguiente_mes(expected)
        if current.fecha == siguiente_mes(previous.fecha):
            close = previous.alumnos_inicio + previous.alumnos_nuevos - previous.bajas
            if current.alumnos_inicio != close:
                discontinuities.append(current.fecha.strftime('%m/%Y'))
    latest = records[-1].fecha if records else None
    today = timezone.localdate()
    age = max(0, (today.year-latest.year)*12+today.month-latest.month) if latest else 0
    return {'faltantes': missing, 'saltos': discontinuities, 'atraso': age, 'ultimo': latest}
