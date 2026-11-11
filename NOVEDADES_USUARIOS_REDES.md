# Actualización: usuarios, modelo y redes — 8 de noviembre de 2026

## Inicio y usuarios

Extraé el ZIP en una carpeta nueva. Conservá tu carpeta anterior. Si tenés datos propios, copiá tu `db.sqlite3` anterior en la nueva carpeta con el servidor detenido, antes de iniciar. Las migraciones conservan usuarios y registros.

Hacé doble clic en **INICIAR_WINDOWS.cmd**. Si no existe un administrador activo, la consola te pedirá crearlo. La contraseña no muestra caracteres mientras la escribís. Luego ingresá en la página con esa cuenta.

El login es obligatorio también en la computadora local. El menú **Mi gimnasio** permite cerrar sesión. **Mi gimnasio → Administrar usuarios** permite al administrador crear cuentas; Django guarda las contraseñas mediante hash, no como texto legible. Cada cuenta del equipo accede al mismo gimnasio. No hay registro público de usuarios ni separación entre distintos negocios.

Alternativa manual después de preparar el entorno:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

`--solo-preparar` instala y migra sin pedir un administrador; se pide en el inicio normal. En hosting usá el procedimiento de PUBLICAR_ONLINE.md.

## Random Forest

Abrí **Predicciones → Comprobar modelo**. Hay una tabla con valores registrados, estimaciones del bosque y referencia estacional. Con seis meses evaluables, los tres primeros eligen el método y los tres últimos lo validan, sin cambiar la elección. El bosque se reentrena con los datos previos a cada pronóstico; no utiliza entradas reales del mes que anticipa.

En la base ficticia incluida (36 meses):

- Selección, julio–septiembre de 2025: MAE del bosque **1,92 altas**; referencia **2,72**.
- Validación posterior, octubre–diciembre de 2025: MAE del método elegido **4,16 altas**.
- Se mantiene Random Forest. El panel principal muestra el error de validación cuando existe; con menos datos identifica el error como exploratorio.

MAE significa error absoluto medio: cuánto difiere, en promedio, la estimación del valor registrado. **4,16 no es una garantía ni un porcentaje de exactitud.** Los registros de ejemplo son ficticios: el modelo funciona técnicamente, pero estos resultados no validan precisión comercial. Tres meses de prueba son pocos; hacen falta datos reales y seguimiento de futuras predicciones.

## Redes sociales

Se agregó **Redes conectadas** con consultas de solo lectura a Meta, intervalos de fechas, guardado en SQLite, consulta de informes anteriores y tratamiento de errores. Leé **CONECTAR_REDES.md** para el alcance de cada métrica y la configuración.

La conexión real queda pendiente de tus credenciales y permisos. Las pruebas usaron respuestas simuladas del proveedor; no se importaron estadísticas reales. Los datos sociales no se mezclan con el CSV ficticio ni se convierten en altas del gimnasio automáticamente.

## Pruebas

34 pruebas Django aprobadas: incluyen acceso anónimo bloqueado, login/logout, hash de contraseña, creación restringida de usuarios, reconsulta sin duplicar informes, conservación de informes ante errores, fechas, paginación, métricas ausentes, bosque real con objetivo conocido y separación temporal. Se conservaron las pruebas previas de CSV, campañas y hosting.

Se ejecutaron en Linux con Python 3.12. La prueba real con Meta y la ejecución nativa en Windows siguen pendientes. No se publicó el sitio online durante esta entrega. Mercado Pago sigue sin conectar.
