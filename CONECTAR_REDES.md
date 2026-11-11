# Conectar Facebook e Instagram

## Qué está implementado

La sección **Redes conectadas** consulta directamente la API de Meta desde el servidor. El administrador elige una fuente y fechas, y presiona **Consultar estadísticas**. El informe se guarda en SQLite y los usuarios del gimnasio pueden verlo después. Consultar otra vez el mismo período y cuenta actualiza ese informe, sin duplicarlo. Un error conserva el informe anterior y su fecha de consulta.

- **Campañas pagas de Meta:** gasto y moneda, impresiones, alcance, clics, CTR y CPC por campaña, para el intervalo solicitado. Las acciones atribuidas por Meta se conservan en el informe técnico guardado, pero no se convierten automáticamente en socios.
- **Instagram:** publicaciones creadas en las fechas elegidas, likes, comentarios y alcance acumulado disponible.
- **Facebook:** publicaciones de la página creadas en esas fechas, reacciones, comentarios y compartidos disponibles. Esta entrega no consulta alcance orgánico de Facebook.

Las publicaciones muestran contadores acumulados hasta la consulta; no representan necesariamente interacciones ocurridas dentro del intervalo. Los datos ausentes aparecen como —. No se suman alcances únicos entre campañas. El período publicitario utiliza el calendario de la cuenta publicitaria; la selección de publicaciones utiliza America/Argentina/Buenos_Aires.

No se incluyen historias que hayan vencido, mensajes privados, publicaciones de cuentas personales de Instagram, TikTok, Google Ads ni LinkedIn. No se publica contenido ni se cambia el presupuesto publicitario. Tampoco se incorporan automáticamente estas métricas al modelo predictivo: antes hace falta vincularlas con altas reales por mes y revisar atribución.

## Antes de conectar

Necesitás administrar los activos de Meta o contar con acceso concedido por su propietario. Esta implementación usa Graph API con Facebook Login para Instagram: cuenta profesional vinculada a una página, no el flujo separado de Instagram Login.

1. Creá/configurá una aplicación en Meta for Developers para los productos que vas a consultar.
2. Obtené los identificadores numéricos de cuenta publicitaria, cuenta profesional de Instagram y página de Facebook.
3. Generá los tokens correspondientes con acceso de lectura a esos activos. Para anuncios necesitás `ads_read`. Para Instagram, revisá `instagram_basic`, `instagram_manage_insights` y los permisos de página correspondientes. Para lectura de publicaciones de página, revisá `pages_read_engagement`. La aprobación y nivel de acceso requeridos dependen del uso y los activos; Meta puede exigir revisión de la aplicación para clientes externos.
4. Seleccioná una versión vigente de Graph API en tu aplicación y comprobá los permisos con los ejemplos oficiales de Meta.

No uses la contraseña de Facebook como token. No pegues tokens en el chat, en el código, en Git ni en capturas. El token es una credencial que autoriza consultas; debe guardarse en el servidor. Revocalo desde Meta cuando retires la conexión.

## Configuración de esta entrega

En tu PC, creá `.env.local` al lado de `manage.py` y usá `python iniciar.py`. En hosting, agregá estas variables al `.env` que ya existe, conservando su clave privada y configuración:

```dotenv
# Reemplazá VERSION por una versión vigente de tu app (formato vN.0).
META_API_VERSION=VERSION
META_AD_ID=ID_NUMERICO_SIN_ACT_
META_AD_TOKEN=TOKEN_CON_ADS_READ
META_IG_ID=ID_NUMERICO_INSTAGRAM_PROFESIONAL
META_IG_TOKEN=TOKEN_CON_PERMISOS_DE_INSTAGRAM
META_PAGE_ID=ID_NUMERICO_PAGINA
META_PAGE_TOKEN=TOKEN_DE_PAGINA
```

Podés configurar solo las fuentes que uses. Estos valores son marcadores, no credenciales funcionales. No compartas el archivo configurado. Reiniciá el servidor después de modificarlo. Si ejecutás `manage.py` directamente, carga `.env` por defecto; el iniciador selecciona `.env.local`.

Entrá como administrador, abrí **Redes conectadas**, elegí la fuente y un intervalo de hasta 91 días que termine como máximo ayer. El estado “configuración cargada” no verifica los permisos; solo una consulta exitosa confirma acceso. Compará el primer informe con Meta Business Suite/Ads Manager usando la misma cuenta, fechas y zona horaria.

La conexión es una configuración de servidor para un gimnasio. No hay todavía un botón OAuth de autoservicio para conectar múltiples negocios. Los tokens se renuevan manualmente cuando vencen. No hay actualización programada: cada consulta la inicia el administrador.

## Límites y errores

- Hasta 2000 elementos paginados y 100 publicaciones a consultar por informe. La lista de Instagram puede recorrer publicaciones anteriores al período, por lo que cuentas muy grandes necesitan ampliar el conector antes de usarlo.
- Tiempo máximo aproximado de consulta: 50 segundos, con límite individual de 20 segundos. El hosting puede imponer un límite inferior; elegí períodos pequeños en ese caso.
- Si hay límites de Meta, un token inválido, métricas no disponibles para un contenido o una respuesta incompleta, se muestra un error y no se guarda un informe parcial.
- No se siguen URLs de paginación arbitrarias: se reutiliza el endpoint autorizado y su cursor.
- Algunas cifras de Meta pueden ser estimaciones y actualizarse después. La fecha de consulta queda visible.

## Verificación pendiente

Se probó el procesamiento con respuestas simuladas y pruebas automatizadas. No se recibieron tokens ni acceso a una cuenta real en esta entrega, por lo que la autorización, compatibilidad final de campos y exactitud frente a Business Suite **deben validarse al conectar tus activos**.

Referencias oficiales:

- https://www.postman.com/meta/facebook-marketing-api/collection/0zr4mes/facebook-marketing-api-mapi
- https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- https://developers.facebook.com/docs/marketing-api/insights/
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/insights/
- https://github.com/meta/facebook-python-business-sdk
