"""La página y la terminal comparten validación e importación transaccional."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.db import transaction

from .models import ImportacionCSV, RegistroMensual
from .validaciones import errores_mensuales

COLUMNAS = ["fecha", "alumnos_inicio", "consultas", "clases_prueba", "inversion_publicidad", "cuota_mensual", "promocion", "alumnos_nuevos", "bajas"]
ENTEROS = ["alumnos_inicio", "consultas", "clases_prueba", "alumnos_nuevos", "bajas"]
MAX_BYTES = 2 * 1024 * 1024
MAX_FILAS = 1200


class ErrorCSV(ValueError):
    def __init__(self, errors):
        self.errors = errors if isinstance(errors, list) else [errors]
        super().__init__(" · ".join(self.errors))


def _numero(value, integer=False):
    try:
        number = Decimal(value.strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError("número vacío o inválido") from None
    maximum = 2_147_483_647 if integer else Decimal("999999999999.99")
    if not number.is_finite() or number < 0 or number > maximum:
        raise ValueError("usá un número finito, no negativo y dentro del límite permitido")
    if integer and number != number.to_integral_value():
        raise ValueError("la cantidad debe ser un número entero")
    return int(number) if integer else float(number)


def leer_csv(content):
    if len(content) > MAX_BYTES:
        raise ErrorCSV("El archivo supera 2 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ErrorCSV("Guardá el archivo como CSV UTF-8 antes de importarlo.") from None
    if not text.strip():
        raise ErrorCSV("El archivo está vacío.")
    header = text.splitlines()[0]
    delimiter = max([",", ";", "\t"], key=header.count)
    reader = csv.DictReader(StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        columns = [(name or "").strip().lower() for name in (reader.fieldnames or [])]
        if len(columns) != len(set(columns)):
            raise ErrorCSV("Hay encabezados repetidos en el CSV.")
        missing = set(COLUMNAS) - set(columns)
        if missing:
            raise ErrorCSV("Faltan columnas: " + ", ".join(sorted(missing)))
        reader.fieldnames = columns
        rows, errors, seen = [], [], set()
        for raw in reader:
            line = reader.line_num
            if None in raw:
                errors.append(f"Fila {line}: hay más valores que encabezados.")
                if len(errors) >= 20: break
                continue
            if not any(value and value.strip() for value in raw.values()):
                continue
            try:
                if len(rows) >= MAX_FILAS:
                    raise ValueError(f"el máximo permitido es {MAX_FILAS} meses")
                value = (raw.get("fecha") or "").strip()
                period = date.fromisoformat(value + "-01" if len(value) == 7 else value)
                if not 1900 <= period.year <= 2100:
                    raise ValueError("usá un período entre 1900 y 2100")
                if period.day != 1:
                    raise ValueError("la fecha debe ser el primer día del mes")
                if period in seen:
                    raise ValueError("el mes está repetido dentro del archivo")
                seen.add(period)
                row = {"fecha": period.isoformat()}
                for key in ENTEROS:
                    try: row[key] = _numero(raw[key], integer=True)
                    except ValueError as error: raise ValueError(f"{key}: {error}") from error
                for key in ("inversion_publicidad", "cuota_mensual"):
                    try: row[key] = _numero(raw[key])
                    except ValueError as error: raise ValueError(f"{key}: {error}") from error
                boolean = (raw.get("promocion") or "").strip().lower()
                if boolean not in {"1", "0", "true", "false", "sí", "si", "no", "yes", "on", "off"}:
                    raise ValueError("promocion: usá 1/0 o sí/no")
                row["promocion"] = boolean in {"1", "true", "sí", "si", "yes", "on"}
                validation = errores_mensuales(row)
                if validation: raise ValueError("; ".join(validation.values()))
                rows.append(row)
            except (ValueError, TypeError, KeyError) as error:
                errors.append(f"Fila {line}: {error}")
                if len(errors) >= 20: break
    except csv.Error as error:
        raise ErrorCSV(f"No se pudo leer el CSV: {error}") from error
    if errors:
        raise ErrorCSV(errors)
    if not rows:
        raise ErrorCSV("El CSV no contiene registros de datos.")
    return sorted(rows, key=lambda row: row["fecha"])


def _serializar(record):
    result = {column: getattr(record, column) for column in COLUMNAS}
    result["fecha"] = record.fecha.isoformat()
    return result


def estado_actual(rows, lock=False):
    records = RegistroMensual.objects.filter(fecha__in=[row["fecha"] for row in rows])
    if lock: records = records.select_for_update()
    existing = {record.fecha.isoformat(): _serializar(record) for record in records}
    return {row["fecha"]: existing.get(row["fecha"]) for row in rows}


def resumir(rows, mode, state):
    totals = {"creados": 0, "actualizados": 0, "omitidos": 0}
    for row in rows:
        previous = state[row["fecha"]]
        key = "creados" if previous is None else "omitidos" if mode == "nuevos" or previous == row else "actualizados"
        totals[key] += 1
    return totals


def aplicar_csv(rows, mode, baseline, token, filename, fingerprint, user=None):
    if mode not in {"nuevos", "actualizar"}:
        raise ErrorCSV("Modo de importación inválido.")
    with transaction.atomic():
        batch, created = ImportacionCSV.objects.get_or_create(token=token, defaults={"archivo": filename[:120], "huella": fingerprint, "modo": mode, "usuario": user})
        if not created:
            return batch
        current = estado_actual(rows, lock=True)
        if current != baseline:
            raise ErrorCSV("El historial cambió después de la vista previa. Volvé a cargar el CSV para revisar los cambios.")
        totals = resumir(rows, mode, current)
        for row in rows:
            previous = current[row["fecha"]]
            if previous is not None and (mode == "nuevos" or row == previous):
                continue
            RegistroMensual.objects.update_or_create(fecha=row["fecha"], defaults={key: value for key, value in row.items() if key != "fecha"})
        for key, value in totals.items(): setattr(batch, key, value)
        batch.save(update_fields=list(totals))
    return batch
