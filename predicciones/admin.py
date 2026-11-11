from django.contrib import admin
from .models import CampanaMensual, RegistroMensual


@admin.register(RegistroMensual)
class RegistroMensualAdmin(admin.ModelAdmin):
    list_display = ("fecha", "alumnos_inicio", "alumnos_nuevos", "bajas", "consultas", "clases_prueba")
    list_filter = ("promocion", "fecha")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)


@admin.register(CampanaMensual)
class CampanaMensualAdmin(admin.ModelAdmin):
    list_display = ("nombre", "periodo", "canal", "inversion", "alcance", "altas")
    list_filter = ("canal", "periodo")
    date_hierarchy = "periodo"
