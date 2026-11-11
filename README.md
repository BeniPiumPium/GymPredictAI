# Última entrega

Leé **NOVEDADES_USUARIOS_REDES.md**: el login ahora es obligatorio, el administrador crea usuarios, hay validación posterior del modelo y un conector Meta configurable. Para cuentas reales seguí **CONECTAR_REDES.md**.

# GymPredictAI

Gestión y proyección mensual para gimnasios con **Python, Django, HTML, CSS y JavaScript**. Los datos se guardan en SQLite. Se conserva el diseño oscuro con acentos rojos y amarillos.

## Inicio rápido

Extraé el ZIP y hacé doble clic en **INICIAR_WINDOWS.cmd** dentro de `GymPredictAI`. También podés ejecutar:

```powershell
python iniciar.py
```

El iniciador crea un entorno propio, instala las dependencias, aplica las migraciones y abre la página local. Requiere Python 3.12–3.14 de 64 bits e Internet en la primera preparación. Para conservar datos de una versión anterior, leé **LEEME_PRIMERO.md** antes de iniciar.

Opciones útiles:

```powershell
python iniciar.py --solo-preparar
python iniciar.py --diagnostico
python iniciar.py --no-navegador --puerto 8100
```

En macOS/Linux, usá `python3 iniciar.py` y los ejecutables de `.venv/bin/` para las tareas siguientes. El iniciador local utiliza `.env.local` y limita el servidor a tu computadora. El hosting sigue usando `.env`.

## Funciones

- Panel con métricas y gráficos de la base de datos.
- Alta, edición y eliminación de registros mensuales con validación en el servidor.
- Historial con filtros por mes/año, período y promoción, paginación y exportación de la selección completa.
- Importación CSV con vista previa, validación integral, confirmación, protección frente a reintentos y cambios ocurridos después de la vista previa. Si una fila falla, no se guarda ninguna.
- Modo de importación que actualiza coincidencias y otro que solo agrega meses nuevos. Los meses ausentes del CSV se conservan. Historial de las últimas diez importaciones.
- Plantilla CSV descargable; admite UTF-8/BOM, coma, punto y coma o tabulación, encabezados con espacios y líneas vacías. Máximo 2 MB y 1200 filas de datos. Usá fechas `AAAA-MM` o `AAAA-MM-01` y números sin separadores de miles. La coma decimal se admite con punto y coma como separador de columnas.
- Campañas con alta, edición, eliminación, exportación y totales por canal. El costo por alta aparece sin valor cuando no hay altas atribuidas.
- Avisos de meses faltantes, antigüedad del historial y diferencias entre el cierre de un mes y el inicio del siguiente.
- Pronóstico del mes posterior al último registro, con comparación de Random Forest contra una referencia reciente y estacional.
- Simulador que utiliza los valores enviados, compara contra un escenario base y avisa cuando hay valores fuera del rango observado.
- Secciones de retención, ingresos estimados y asistente guiado del producto.
- Inicio de sesión obligatorio en producción y protección CSRF de las operaciones.

## Datos y entrenamiento

La base incluida contiene **36 meses simulados: enero de 2023 a diciembre de 2025**. El CSV incluye socios iniciales, consultas, pruebas, inversión, cuota, promoción, altas y bajas. Las campañas tienen una tabla separada: sus clics y alcance sirven para el análisis de marketing y **todavía no se usan como variables del modelo mensual**.

Se requieren al menos 12 registros para entrenar. La evaluación pronostica hasta seis meses finales (con seis, tres seleccionan el método y tres lo validan), entrenando cada vez solo con meses anteriores. Para las entradas futuras utiliza las mismas suposiciones que la página: valores del último mes, socios estimados al cierre y mes del calendario. Omite una evaluación cuando falta el mes inmediatamente anterior. Con exactamente 12 meses todavía no hay períodos reservados para medir el error.

Se compara el error absoluto medio (MAE, expresado en altas) y se usa el método con menor error histórico para la proyección automática. La selección y la validación se separan cuando hay seis meses evaluables; ninguna garantiza precisión futura. La estacionalidad se aprende del historial, sin imponer que ciertos meses deban crecer.

El simulador usa Random Forest aunque la referencia resulte mejor para la proyección automática. Puede dar el mismo resultado ante cambios pequeños; no es una calculadora causal de inversión. El MAE mostrado corresponde a los pronósticos históricos, no a una probabilidad o intervalo de confianza del escenario. El entrenamiento se reutiliza mientras el contenido de la base no cambie.

Evaluar la base actual desde Windows:

```powershell
.\.venv\Scripts\python.exe entrenar_modelo.py
```

## Importación y copias desde la terminal

Primero verificá un archivo sin modificar la base:

```powershell
.\.venv\Scripts\python.exe manage.py importar_datos datos_gimnasio.csv --verificar
```

Agregar únicamente meses inexistentes:

```powershell
.\.venv\Scripts\python.exe manage.py importar_datos datos_gimnasio.csv --solo-nuevos
```

Actualizar coincidencias y agregar nuevos:

```powershell
.\.venv\Scripts\python.exe manage.py importar_datos datos_gimnasio.csv
```

No ejecutes este último comando en cada inicio: vuelve a colocar los valores del archivo en los meses coincidentes. El iniciador nuevo no lo ejecuta.

Crear una copia consistente de SQLite:

```powershell
.\.venv\Scripts\python.exe manage.py respaldar_base
```

## Comprobaciones

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test predicciones
```

Los casos cubren validaciones, importación atómica y reintentos, filtros/exportación, edición de campañas, evaluación temporal, actualización del modelo, acceso y conservación de datos en el instalador de hosting. Consultá **CAMBIOS_Y_PRUEBAS.md** para el alcance de la verificación realizada.

## Publicación y alcance

**PUBLICAR_ONLINE.md** contiene los pasos de despliegue con PythonAnywhere, configuración WSGI, HTTPS y usuario propio. La base online se conserva fuera de la carpeta del código. No se incluye ninguna clave de producción ni cuenta predeterminada.

Esta versión maneja un gimnasio compartido por sus usuarios. Los planes y Mercado Pago siguen demostrativos: no hay cobros reales. El asistente es una ayuda local mediante reglas; no tiene un servicio externo de lenguaje conectado. Los ingresos se estiman con socios por cuota y no equivalen a ganancia neta.
