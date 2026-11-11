from django.urls import path
from . import views
from .redes import redes
from .auditoria import auditoria

urlpatterns = [
    path("modelo/comprobar/", auditoria, name="auditoria"),
    path("redes/", redes, name="redes"),
    path("", views.dashboard, name="dashboard"),
    path("registros/nuevo/", views.registrar_mes, name="registrar_mes"),
    path("registros/<int:registro_id>/editar/", views.editar_mes, name="editar_mes"),
    path("registros/<int:registro_id>/eliminar/", views.eliminar_mes, name="eliminar_mes"),
    path("registros/exportar/", views.exportar_datos, name="exportar_datos"),
    path("registros/importar/", views.importar_csv, name="importar_csv"),
    path("registros/plantilla/", views.plantilla_csv, name="plantilla_csv"),
    path("marketing/exportar/", views.exportar_campanas, name="exportar_campanas"),
    path("marketing/campanas/nueva/", views.registrar_campana, name="registrar_campana"),
    path("marketing/campanas/<int:campana_id>/editar/", views.editar_campana, name="editar_campana"),
    path("marketing/campanas/<int:campana_id>/eliminar/", views.eliminar_campana, name="eliminar_campana"),
]
