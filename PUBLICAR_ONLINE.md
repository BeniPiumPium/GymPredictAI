# Publicar GymPredictAI en PythonAnywhere

Este procedimiento publica el proyecto Django con una dirección HTTPS. Tu computadora puede estar apagada: el servidor ejecuta la página y guarda los datos.

## 1. Crear la cuenta y subir el ZIP

1. Entrá a https://www.pythonanywhere.com/ y creá una cuenta **Beginner** para una primera prueba. La dirección disponible depende de tu nombre de usuario.
2. En **Files**, subí `GymPredictAI_Usuarios_Redes.zip` a tu carpeta principal `/home/TU_USUARIO/`.
3. En **Consoles → Bash**, ejecutá:

```bash
unzip GymPredictAI_Usuarios_Redes.zip
cd GymPredictAI
bash deploy/preparar_pythonanywhere.sh
```

El instalador crea un entorno de Python 3.12, instala las dependencias, genera la clave privada del sitio, prepara los estilos y guarda una copia de la base fuera de la carpeta del código. Cuando te pregunte el dominio, ingresá el que tendrá tu Web app, por ejemplo `tuusuario.pythonanywhere.com`.

Estos comandos son para la consola de **PythonAnywhere**, no para PowerShell en tu PC. En la primera instalación la carpeta `GymPredictAI` no debe existir. Si ya la tenés, hacé una copia antes de extraer el ZIP.

## 2. Crear tu usuario de acceso

En la misma consola, ejecutá:

```bash
~/.virtualenvs/gympredictai/bin/python manage.py createsuperuser
```

Elegí un nombre de usuario y una contraseña propios. La contraseña no muestra letras mientras la escribís: es normal. No hay una cuenta ni una contraseña predeterminadas.

## 3. Conectar la Web app

En **Web → Add a new web app**:

1. Confirmá el dominio y elegí **Manual configuration → Python 3.12**.
2. En **Virtualenv**, escribí `/home/TU_USUARIO/.virtualenvs/gympredictai`.
3. En **Source code** y **Working directory**, escribí `/home/TU_USUARIO/GymPredictAI`.
4. Abrí el archivo **WSGI configuration file** que aparece en esa pantalla. Reemplazá su contenido por el de `GymPredictAI/deploy/pythonanywhere_wsgi.py`.
5. En **Static files**, agregá:

| Campo | Valor |
| --- | --- |
| URL | `/static/` |
| Directory | `/home/TU_USUARIO/GymPredictAI/staticfiles` |

WSGI es la conexión entre el servidor de PythonAnywhere y tu aplicación Django. Static files le indica dónde encontrar los estilos y JavaScript.

## 4. Publicar

Activá **Force HTTPS** en la pestaña Web y presioná **Reload**. Abrí la dirección HTTPS de tu Web app e ingresá con el usuario del paso 2.

El servidor pide iniciar sesión antes de mostrar el panel, exportar datos o permitir cambios. Los usuarios creados para este proyecto comparten los datos de un mismo gimnasio; esta versión no separa varios negocios.

## Dónde quedan los datos

- Base inicial del paquete: `GymPredictAI/db.sqlite3`, con los 36 meses del CSV.
- Base utilizada online: `/home/TU_USUARIO/.local/share/gympredictai/db.sqlite3`.
- Configuración privada: `GymPredictAI/.env`, creada únicamente en tu servidor.

El instalador conserva la base online si se vuelve a ejecutar. No ejecutes `importar_datos` en cada actualización: ese comando vuelve a colocar los valores originales del CSV en los meses coincidentes.

Para guardar una copia de la base online, desde la carpeta `GymPredictAI`:

```bash
~/.virtualenvs/gympredictai/bin/python manage.py respaldar_base
```

El comando informa el archivo de copia para que puedas descargarlo desde **Files**.

## Si algo falla

- **No aparece Python 3.12:** revisá **Account → System image**; esa versión está disponible en la imagen `innit`.
- **La página no tiene estilos:** revisá la entrada `/static/` y volvé a presionar Reload.
- **Error al cargar la página:** abrí **Web → Error log** y compartí el mensaje de error. No compartas el contenido de `.env`.
- **Olvidaste la contraseña:** ejecutá `~/.virtualenvs/gympredictai/bin/python manage.py changepassword TU_USUARIO_DEL_PANEL`.

## Alcance de esta primera publicación

La cuenta gratuita tiene recursos y conexiones salientes limitados. SQLite sirve para esta prueba pequeña; el proveedor desaconseja usarla como base de producción. Para vender el servicio a varios gimnasios habrá que preparar una base administrada y separación de datos por negocio. Los pagos de Mercado Pago siguen pendientes de integración.

Documentación consultada el 28 de octubre de 2026:

- https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
- https://help.pythonanywhere.com/pages/DjangoStaticFiles/
- https://help.pythonanywhere.com/pages/PythonVersions/
- https://help.pythonanywhere.com/pages/KindsOfDatabases/
- https://www.pythonanywhere.com/pricing/

## Actualizar una instalación existente

1. Detené o poné en mantenimiento la aplicación y ejecutá `manage.py respaldar_base` con su entorno virtual. Descargá la copia.
2. Conservá el archivo `.env` de tu servidor y la base persistente en `/home/TU_USUARIO/.local/share/gympredictai/`.
3. Actualizá el código desde el ZIP. No reemplaces la base persistente con la base de ejemplo del paquete.
4. Dentro de la carpeta del proyecto, ejecutá:

```bash
~/.virtualenvs/gympredictai/bin/python -m pip install -r requirements.txt
~/.virtualenvs/gympredictai/bin/python manage.py migrate --noinput
~/.virtualenvs/gympredictai/bin/python manage.py collectstatic --noinput
~/.virtualenvs/gympredictai/bin/python manage.py check
```

5. Presioná **Reload** en la pestaña Web y comprobá el inicio de sesión y tus registros.

No ejecutes `iniciar.py` ni `runserver` como servidor público; el hosting utiliza WSGI. Las migraciones de esta entrega agregan el historial de importaciones y conservan los registros existentes.
