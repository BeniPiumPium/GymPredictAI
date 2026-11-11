"""Copiar este contenido en el archivo WSGI que muestra la pestaña Web."""
import os
from pathlib import Path
import sys

project_dir = Path.home() / "GymPredictAI"
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

os.environ["DJANGO_DEBUG"] = "false"
os.environ["DJANGO_REQUIRE_LOGIN"] = "true"
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
