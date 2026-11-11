from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("predicciones", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="CampanaMensual",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("periodo", models.DateField()),
                ("nombre", models.CharField(max_length=120)),
                ("canal", models.CharField(choices=[("Instagram", "Instagram"), ("Facebook", "Facebook"), ("TikTok", "TikTok"), ("Google", "Google"), ("WhatsApp", "WhatsApp"), ("Referidos", "Referidos"), ("Otro", "Otro")], default="Instagram", max_length=24)),
                ("inversion", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("alcance", models.PositiveIntegerField(default=0)),
                ("clics", models.PositiveIntegerField(default=0)),
                ("contactos", models.PositiveIntegerField(default=0)),
                ("pruebas", models.PositiveIntegerField(default=0)),
                ("altas", models.PositiveIntegerField(default=0)),
                ("creada", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Campaña mensual", "verbose_name_plural": "Campañas mensuales", "ordering": ["-periodo", "-creada"]},
        ),
    ]
