# Abrir GymPredictAI en tu computadora

## Windows: inicio recomendado

1. Extraé **GymPredictAI_Usuarios_Redes.zip** en una carpeta nueva.
2. Abrí la carpeta **GymPredictAI**, donde están `manage.py` e `INICIAR_WINDOWS.cmd`.
3. Hacé doble clic en **INICIAR_WINDOWS.cmd**.
4. Si no hay un administrador, la consola te pide crear tu usuario y contraseña. Esperá a que termine. La primera vez necesita Internet para descargar las bibliotecas.
5. Se abre la página en el navegador. Ingresá con tu usuario y contraseña. Dejá la ventana de comandos abierta mientras la usás. Para detenerla, presioná **Ctrl+C**.

Necesitás Python de 64 bits, versión 3.12, 3.13 o 3.14. El iniciador crea `.venv`, instala todas las dependencias (incluido pandas), prepara las tablas y ejecuta el servidor con ese mismo Python. No tenés que activar el entorno con PowerShell.

También podés abrir la terminal de Visual Studio Code dentro de esa carpeta y ejecutar:

```powershell
.\INICIAR_WINDOWS.cmd
```

O, si `python` ya funciona en tu terminal:

```powershell
python iniciar.py
```

La dirección habitual es http://127.0.0.1:8000/. Si el puerto está ocupado, el iniciador prueba los siguientes y te muestra la dirección elegida.

## Si ya cargaste datos en la versión anterior

Conservá la carpeta anterior. Antes de iniciar esta versión por primera vez, copiá **tu `db.sqlite3` anterior** dentro de la nueva carpeta `GymPredictAI`, reemplazando únicamente la base de ejemplo incluida. Hacé la copia con el servidor anterior detenido.

El inicio aplica las migraciones necesarias y conserva los registros. No vuelve a cargar el CSV automáticamente. No copies la carpeta `.venv` de la versión anterior.

Si usabas una base en otra ubicación mediante `DJANGO_DB_PATH`, conservá esa configuración en `.env.local`. Para una instalación online, seguí la sección de actualización de `PUBLICAR_ONLINE.md`.

## Qué pasó con los errores que aparecían

- El comando correcto es `python`, no `phyton`.
- `manage.py` es un archivo que ejecuta Python; no hace falta lanzarlo como un comando independiente.
- `No module named 'pandas'` significa que falta una biblioteca en el Python que inició Django. El nuevo iniciador instala y usa todas las dependencias en el mismo entorno.

Para abrirlo con comandos después de la primera preparación:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Si necesitás ver qué Python y bibliotecas está usando:

```powershell
python iniciar.py --diagnostico
```

Si una instalación falla, guardá el mensaje completo de la consola. No borres la base de datos para resolver un error de dependencias.

## Usar las funciones nuevas

- **Registros → Importar CSV:** elegí un archivo, revisá los conteos y confirmá. Podés actualizar meses coincidentes o agregar solamente meses nuevos.
- **Registros:** filtrá por período, promoción o nombre del mes/año. La exportación de esa sección respeta los filtros, incluyendo todas sus páginas.
- **Marketing:** creá y editá campañas; exportá sus resultados. Los totales se agrupan por canal.
- **Predicciones:** probá escenarios y revisá el error histórico. Los avisos señalan datos viejos, meses faltantes o saldos inconsistentes.

El paquete trae los mismos 36 meses de ejemplo, de enero de 2023 a diciembre de 2025. Son datos simulados. Reemplazalos o actualizalos con registros reales para analizar tu gimnasio.

Este iniciador abre la página en tu computadora. Para publicarla en Internet, consultá **PUBLICAR_ONLINE.md**.
