from math import isfinite


def errores_mensuales(data):
    errors = {}
    for field in ("alumnos_inicio", "consultas", "clases_prueba", "inversion_publicidad", "cuota_mensual", "alumnos_nuevos", "bajas"):
        value = data.get(field)
        maximum = 999_999_999_999.99 if field in ("inversion_publicidad", "cuota_mensual") else 2_147_483_647
        if value is not None and (not isfinite(float(value)) or value < 0 or value > maximum):
            errors[field] = f"Ingresá un número válido entre 0 y {maximum}."
    if data.get("consultas") is not None and data.get("clases_prueba") is not None:
        if data["clases_prueba"] > data["consultas"]:
            errors["clases_prueba"] = "Las pruebas no pueden superar las consultas."
    if all(data.get(key) is not None for key in ("bajas", "alumnos_inicio", "alumnos_nuevos")):
        if data["bajas"] > data["alumnos_inicio"] + data["alumnos_nuevos"]:
            errors["bajas"] = "Las bajas superan los socios disponibles en ese mes."
    return errors
