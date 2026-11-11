from django import forms
from datetime import date
from .models import CampanaMensual, RegistroMensual
from .validaciones import errores_mensuales


class RegistroMensualForm(forms.ModelForm):
    class Meta:
        model = RegistroMensual
        fields = [
            "fecha", "alumnos_inicio", "consultas", "clases_prueba",
            "inversion_publicidad", "cuota_mensual", "promocion",
            "alumnos_nuevos", "bajas",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "field-input"}, format="%Y-%m-%d"),
            "alumnos_inicio": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "consultas": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "clases_prueba": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "inversion_publicidad": forms.NumberInput(attrs={"class": "field-input", "min": 0, "step": "0.01"}),
            "cuota_mensual": forms.NumberInput(attrs={"class": "field-input", "min": 0, "step": "0.01"}),
            "promocion": forms.CheckboxInput(attrs={"class": "field-checkbox"}),
            "alumnos_nuevos": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "bajas": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
        }
        labels = {
            "fecha": "Mes del registro", "alumnos_inicio": "Socios al inicio",
            "consultas": "Consultas recibidas", "clases_prueba": "Clases de prueba",
            "inversion_publicidad": "Inversión publicitaria · ARS",
            "cuota_mensual": "Cuota mensual · ARS", "promocion": "Hubo promoción",
            "alumnos_nuevos": "Altas del mes", "bajas": "Bajas del mes",
        }

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if not date(1900, 1, 1) <= fecha <= date(2100, 12, 1):
            raise forms.ValidationError("Usá un período entre 1900 y 2100.")
        if fecha.day != 1:
            raise forms.ValidationError("Usá el primer día del mes para identificar el período.")
        return fecha

    def clean(self):
        data = super().clean()
        for field, error in errores_mensuales(data).items():
            self.add_error(field, error)
        return data


class CampanaMensualForm(forms.ModelForm):
    class Meta:
        model = CampanaMensual
        fields = ["periodo", "nombre", "canal", "inversion", "alcance", "clics", "contactos", "pruebas", "altas"]
        widgets = {
            "periodo": forms.DateInput(attrs={"type": "date", "class": "field-input"}, format="%Y-%m-%d"),
            "nombre": forms.TextInput(attrs={"class": "field-input", "maxlength": 120, "placeholder": "Ej. Semana de prueba gratis"}),
            "canal": forms.Select(attrs={"class": "field-input"}),
            "inversion": forms.NumberInput(attrs={"class": "field-input", "min": 0, "step": "0.01"}),
            "alcance": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "clics": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "contactos": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "pruebas": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
            "altas": forms.NumberInput(attrs={"class": "field-input", "min": 0}),
        }
        labels = {
            "periodo": "Mes", "nombre": "Nombre de campaña", "canal": "Canal",
            "inversion": "Inversión · ARS", "alcance": "Alcance", "clics": "Clics",
            "contactos": "Contactos", "pruebas": "Clases de prueba", "altas": "Altas atribuidas",
        }

    def clean_periodo(self):
        periodo = self.cleaned_data["periodo"]
        if not date(1900, 1, 1) <= periodo <= date(2100, 12, 1):
            raise forms.ValidationError("Usá un período entre 1900 y 2100.")
        if periodo.day != 1:
            raise forms.ValidationError("Seleccioná el primer día del mes.")
        return periodo

    def clean(self):
        data = super().clean()
        for field in ("pruebas", "altas"):
            if data.get(field) is not None and data.get("contactos") is not None and data[field] > data["contactos"]:
                self.add_error(field, "Este valor no puede superar los contactos de la campaña.")
        return data


class ImportarCSVForm(forms.Form):
    archivo = forms.FileField(label="Archivo CSV", widget=forms.ClearableFileInput(attrs={"accept": ".csv", "class": "field-input"}))
    modo = forms.ChoiceField(label="Cómo cargar los meses", choices=[("actualizar", "Agregar nuevos y actualizar coincidencias"), ("nuevos", "Agregar solo meses nuevos")], widget=forms.Select(attrs={"class": "field-input"}))

    def clean_archivo(self):
        file = self.cleaned_data["archivo"]
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Elegí un archivo .csv.")
        if file.size > 2 * 1024 * 1024:
            raise forms.ValidationError("El archivo supera el límite de 2 MB.")
        return file


class FiltroRegistrosForm(forms.Form):
    desde = forms.DateField(required=False, label="Desde", input_formats=["%Y-%m", "%Y-%m-%d"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "field-input"}))
    hasta = forms.DateField(required=False, label="Hasta", input_formats=["%Y-%m", "%Y-%m-%d"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "field-input"}))
    promocion = forms.ChoiceField(required=False, label="Promoción", choices=[("", "Todas"), ("si", "Con promoción"), ("no", "Sin promoción")], widget=forms.Select(attrs={"class": "field-input"}))
    buscar = forms.CharField(required=False, max_length=80, label="Buscar mes o año", widget=forms.TextInput(attrs={"class": "field-input", "placeholder": "Ej. octubre o 2025"}))

    def clean(self):
        data = super().clean()
        if data.get("desde") and data.get("hasta") and data["desde"] > data["hasta"]:
            raise forms.ValidationError("El mes inicial debe ser anterior o igual al final.")
        return data


class SimulacionForm(forms.Form):
    alumnos_inicio = forms.IntegerField(label="Socios al inicio", min_value=0, max_value=2_147_483_647)
    consultas = forms.IntegerField(label="Consultas", min_value=0, max_value=2_147_483_647)
    clases_prueba = forms.IntegerField(label="Clases de prueba", min_value=0, max_value=2_147_483_647)
    inversion_publicidad = forms.FloatField(label="Inversión publicitaria", min_value=0, max_value=999_999_999_999)
    cuota_mensual = forms.FloatField(label="Cuota mensual", min_value=0, max_value=999_999_999_999)
    mes_objetivo = forms.IntegerField(label="Mes a proyectar", min_value=1, max_value=12)
    promocion = forms.BooleanField(required=False)

    def clean(self):
        data = super().clean()
        for field, error in errores_mensuales(data).items():
            self.add_error(field, error)
        return data
