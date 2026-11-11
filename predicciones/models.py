from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class RegistroMensual(models.Model):
    fecha = models.DateField(unique=True)
    alumnos_inicio = models.PositiveIntegerField(default=0)
    consultas = models.PositiveIntegerField(default=0)
    clases_prueba = models.PositiveIntegerField(default=0)
    inversion_publicidad = models.FloatField(default=0, validators=[MinValueValidator(0)])
    cuota_mensual = models.FloatField(default=0, validators=[MinValueValidator(0)])
    promocion = models.BooleanField(default=False)
    alumnos_nuevos = models.PositiveIntegerField(default=0)
    bajas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["fecha"]
        verbose_name = "Registro mensual"
        verbose_name_plural = "Registros mensuales"

    def __str__(self):
        return f"{self.fecha:%m/%Y} - {self.alumnos_nuevos} altas"


class CampanaMensual(models.Model):
    CANALES = [
        ("Instagram", "Instagram"),
        ("Facebook", "Facebook"),
        ("TikTok", "TikTok"),
        ("Google", "Google"),
        ("WhatsApp", "WhatsApp"),
        ("Referidos", "Referidos"),
        ("Otro", "Otro"),
    ]

    periodo = models.DateField()
    nombre = models.CharField(max_length=120)
    canal = models.CharField(max_length=24, choices=CANALES, default="Instagram")
    inversion = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    alcance = models.PositiveIntegerField(default=0)
    clics = models.PositiveIntegerField(default=0)
    contactos = models.PositiveIntegerField(default=0)
    pruebas = models.PositiveIntegerField(default=0)
    altas = models.PositiveIntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-periodo", "-creada"]
        verbose_name = "Campaña mensual"
        verbose_name_plural = "Campañas mensuales"

    def __str__(self):
        return f"{self.nombre} · {self.periodo:%m/%Y}"


class ImportacionCSV(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    archivo = models.CharField(max_length=120)
    huella = models.CharField(max_length=64)
    modo = models.CharField(max_length=12, default="actualizar")
    creada = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    omitidos = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-creada"]
        verbose_name = "Importación CSV"
        verbose_name_plural = "Importaciones CSV"


class InformeSocial(models.Model):
    fuente = models.CharField(max_length=24)
    cuenta = models.CharField(max_length=100)
    desde = models.DateField()
    hasta = models.DateField()
    filas = models.JSONField(default=list)
    consultado = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['fuente','cuenta','desde','hasta'], name='informe_social_periodo')]
        ordering = ['-consultado']
