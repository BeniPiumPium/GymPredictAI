
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd

# Generador aleatorio reproducible:
# siempre obtendremos el mismo conjunto de datos.
rng = np.random.default_rng(42)

# Generamos 36 meses consecutivos.
fechas = pd.date_range(
    start="2023-01-01",
    periods=36,
    freq="MS"
)

registros = []
alumnos_activos = 300

for fecha in fechas:
    mes = fecha.month

    # Simulamos una mayor demanda en enero y febrero,
    # y un repunte moderado en agosto.
    estacionalidad = {
        1: 1.35,
        2: 1.20,
        3: 1.05,
        4: 0.95,
        5: 0.90,
        6: 0.90,
        7: 0.95,
        8: 1.10,
        9: 1.00,
        10: 0.95,
        11: 1.00,
        12: 0.85,
    }[mes]

    alumnos_inicio = alumnos_activos

    # Inversión mensual ficticia en publicidad.
    inversion_publicidad = round(
        rng.uniform(40000, 120000), 2
    )

    # Consultas: dependen parcialmente de la publicidad
    # y de la estacionalidad.
    consultas = max(
        5,
        int(
            (25 + inversion_publicidad / 3000)
            * estacionalidad
            + rng.normal(0, 5)
        )
    )

    # Personas que realizan una clase de prueba.
    clases_prueba = min(
        consultas,
        max(0, int(consultas * rng.uniform(0.35, 0.65)))
    )

    # Alumnos nuevos: dependen de las consultas,
    # las clases de prueba y el comportamiento estacional.
    conversion = rng.uniform(0.25, 0.45)

    alumnos_nuevos = max(
        0,
        int(
            clases_prueba * conversion
            + rng.normal(2, 2)
        )
    )

    # Bajas mensuales aproximadas.
    bajas = max(
        0,
        int(alumnos_inicio * rng.uniform(0.02, 0.05))
    )

    # Precio mensual ficticio.
    cuota = round(
        15000 * (1.03 ** ((fecha.year - 2023) * 12 + mes - 1)),
        2
    )

    # Indicador de si hubo una promoción ese mes.
    promocion = int(rng.random() < 0.40)

    registros.append({
        "fecha": fecha.strftime("%Y-%m-%d"),
        "alumnos_inicio": alumnos_inicio,
        "consultas": consultas,
        "clases_prueba": clases_prueba,
        "inversion_publicidad": inversion_publicidad,
        "cuota_mensual": cuota,
        "promocion": promocion,
        "alumnos_nuevos": alumnos_nuevos,
        "bajas": bajas,
    })

    # Actualizamos los alumnos para el mes siguiente.
    alumnos_activos = max(
        0,
        alumnos_inicio + alumnos_nuevos - bajas
    )

# Convertimos los registros en una tabla.
df = pd.DataFrame(registros)

# Exportamos el historial a CSV.
df.to_csv(
    "datos_gimnasio.csv",
    index=False,
    encoding="utf-8"
)

print("Datos simulados generados correctamente.")
print(f"Cantidad de meses: {len(df)}")
print("\nPrimeros registros:")
print(df.head().to_string(index=False))

print("\nArchivo creado: datos_gimnasio.csv")
