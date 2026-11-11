from io import StringIO
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from dotenv import dotenv_values

from deploy.preparar_pythonanywhere import preparar
from .models import RegistroMensual


LOGIN_MIDDLEWARE = "django.contrib.auth.middleware.LoginRequiredMiddleware"
protected_middleware = [item for item in settings.MIDDLEWARE if item != LOGIN_MIDDLEWARE]
protected_middleware.insert(protected_middleware.index("django.contrib.auth.middleware.AuthenticationMiddleware") + 1, LOGIN_MIDDLEWARE)


@override_settings(MIDDLEWARE=protected_middleware, SECURE_SSL_REDIRECT=False)
class AccesoOnlineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("owner_test", password="solo-para-pruebas-2719")
        call_command("importar_datos", stdout=StringIO())

    def test_anonimo_no_ve_ni_modifica_los_datos(self):
        for path in ["/", "/registros/nuevo/", "/registros/exportar/", "/registros/importar/", "/registros/plantilla/", "/marketing/exportar/", "/marketing/campanas/nueva/"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/cuenta/entrar/"))
        registro = RegistroMensual.objects.first()
        response = self.client.post(f"/registros/{registro.pk}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RegistroMensual.objects.count(), 36)

    def test_usuario_autenticado_ve_el_panel_y_el_csv(self):
        self.client.force_login(self.owner)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Centro de crecimiento")
        cuota = RegistroMensual.objects.order_by("-fecha").first().cuota_mensual
        self.assertContains(response, f'name="cuota_mensual" value="{cuota}"')
        self.assertEqual(self.client.get("/registros/exportar/").status_code, 200)

    def test_login_y_cierre_respetan_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get("/cuenta/entrar/").status_code, 200)
        values = {"username": self.owner.username, "password": "solo-para-pruebas-2719"}
        self.assertEqual(client.post("/cuenta/entrar/", values).status_code, 403)
        values["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
        self.assertEqual(client.post("/cuenta/entrar/", values).status_code, 302)
        self.assertEqual(client.post("/cuenta/salir/").status_code, 403)
        self.assertEqual(client.post("/cuenta/salir/", {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}).status_code, 302)
        self.assertEqual(client.get("/").status_code, 302)


class PreparacionHostingTests(SimpleTestCase):
    def test_repetir_instalacion_conserva_registros_y_clave(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "proyecto"
            root.mkdir()
            with sqlite3.connect(root / "db.sqlite3") as source:
                source.execute("CREATE TABLE predicciones_registromensual (id INTEGER PRIMARY KEY)")
                source.execute("INSERT INTO predicciones_registromensual VALUES (1)")
            database, created = preparar(root, Path(temporary) / "datos", "ejemplo.pythonanywhere.com")
            self.assertTrue(created)
            first_config = dotenv_values(root / ".env")
            with sqlite3.connect(database) as connection:
                connection.execute("INSERT INTO predicciones_registromensual VALUES (2)")
            same_database, created = preparar(root, Path(temporary) / "datos", "ejemplo.pythonanywhere.com")
            self.assertFalse(created)
            self.assertEqual(database, same_database)
            self.assertEqual(first_config["DJANGO_SECRET_KEY"], dotenv_values(root / ".env")["DJANGO_SECRET_KEY"])
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM predicciones_registromensual").fetchone()[0], 2)
