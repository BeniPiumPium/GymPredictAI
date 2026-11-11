> Informe histórico de la entrega anterior. Para los cambios y resultados actuales, leé NOVEDADES_USUARIOS_REDES.md.

# Entrega de correcciones y mejoras — 2 de noviembre de 2026

## Qué se corrigió

- Se agregó un iniciador que instala las dependencias completas en un entorno propio y usa ese mismo Python para arrancar. Resuelve la causa del error `No module named pandas` sin depender del pip global del equipo.
- `manage.py` informa con claridad cuando faltan dependencias y muestra cómo prepararlas.
- Los formularios rechazan números negativos, no finitos, desproporcionados y relaciones imposibles entre cantidades. Los errores se muestran conservando los valores ingresados.
- Las campañas ahora permiten editar; los totales se agrupan por canal y no muestran un costo por alta de cero cuando no hay altas.
- El simulador utiliza las entradas del usuario aunque la referencia reciente resulte mejor para la proyección automática.
- La evaluación del pronóstico ya no utiliza consultas, pruebas ni inversión reales del mes que intenta anticipar. Se muestran el MAE y el número de períodos evaluados, sin presentar el error como un intervalo de confianza.
- El evaluador de terminal usa la base actual y el mismo procedimiento que el panel.
- Se corrigieron etiquetas del gráfico financiero y el enlace para editar el último período desde Retención. Se mantuvo el menú desplegable funcional del gimnasio.

## Funciones nuevas entregadas

1. Importación CSV desde la página, con plantilla, vista previa, confirmación y selección entre actualizar coincidencias o solo agregar nuevos.
2. Validación completa del archivo antes de guardar, transacción de todo el lote, detección de cambios posteriores a la vista previa y reintentos sin duplicación.
3. Historial de importaciones con archivo, fecha, usuario cuando hay sesión y cantidades afectadas.
4. Filtros de registros por período, promoción y mes/año; paginación y exportación de la selección completa.
5. Edición y exportación de campañas, con protección de los textos exportados frente a fórmulas de Excel.
6. Avisos de meses faltantes, datos antiguos y diferencias entre saldos consecutivos.
7. Comparación del escenario con una referencia y aviso de valores fuera del rango histórico.
8. Reutilización del entrenamiento mientras no cambien los datos, para evitar repetirlo en cada visita.

## Verificaciones realizadas

| Comprobación | Resultado |
| --- | --- |
| Pruebas Django de validación, importaciones, filtros, campañas, predicción, acceso y hosting | 23 aprobadas |
| Migraciones pendientes de generar | Ninguna |
| `manage.py check` con las dependencias instaladas | Sin problemas |
| Comprobación de sintaxis JavaScript con `node --check` | Correcta |
| Preparación desde cero en una carpeta con espacios, con `iniciar.py` y Python 3.12 sobre Linux | Instalación, migraciones y comprobaciones correctas |
| Segunda preparación | Reutiliza el entorno; no reinstala paquetes ni reinicia datos |
| Inicio real mediante `iniciar.py --no-navegador` | Resumen e importación responden HTTP 200 |
| Conservación de datos durante la preparación y el arranque | Los 36 meses se conservaron |
| Descarga de dependencias binarias para Windows x64 / Python 3.14 | Correcta para todas las dependencias fijadas y sus dependencias transitivas |
| Aviso al ejecutar con un Python sin las dependencias del proyecto | Mensaje de solución claro, sin el traceback original |
| Integridad de SQLite | Correcta |

La ejecución se probó en Linux, no en un Windows nativo. La descarga de paquetes para Windows confirma disponibilidad de distribuciones compatibles, pero no sustituye una ejecución en ese sistema. La revisión visual en navegador quedó bloqueada por la revisión automática de acceso al servidor local; no se presenta como realizada. Las rutas y plantillas se verificaron mediante Django y peticiones locales.

## Lectura del modelo de ejemplo

Sobre los 36 meses simulados, evaluando cronológicamente los últimos seis, el MAE obtenido fue 3,04 altas para Random Forest y 3,72 para la referencia reciente y estacional. Se seleccionó Random Forest. El próximo período respecto de ese archivo es enero de 2026: el panel avisa que el historial necesita actualizarse. Estas cifras describen el archivo de ejemplo y no certifican precisión para un gimnasio real.

## Alcance conservado

- Python/Django, HTML, CSS, JavaScript y SQLite; mismo estilo visual de base.
- Base incluida: 36 registros mensuales del archivo recibido, sin cuentas predeterminadas ni credenciales de producción.
- La guía de hosting y sus scripts se conservan y se agregan instrucciones de actualización. No se publicó un sitio online durante esta entrega.
- Los datos de campañas se analizan por separado y no se incorporan todavía al modelo mensual.
- Mercado Pago sigue sin cobros reales. El asistente sigue siendo ayuda mediante reglas locales. El producto maneja un gimnasio; la separación de múltiples negocios no está implementada.
