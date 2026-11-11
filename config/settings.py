"""Configuración de GymPredictAI para desarrollo local y despliegue."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(Path(os.environ.get("DJANGO_ENV_FILE", str(BASE_DIR / ".env"))), override=False)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in {"1", "true", "yes", "sí", "si"}
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-gym-predict-ai-local-only-key-change-before-hosting"
    else:
        raise RuntimeError("Configurá DJANGO_SECRET_KEY antes de iniciar en producción.")
if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-")):
    raise RuntimeError("La clave de producción debe ser propia, aleatoria y tener al menos 50 caracteres.")

ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",") if host.strip()]
REQUIRE_LOGIN = True
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if value.strip()]

# PythonAnywhere termina HTTPS delante de Django y conserva el esquema WSGI.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "predicciones",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if REQUIRE_LOGIN:
    index = MIDDLEWARE.index("django.contrib.auth.middleware.AuthenticationMiddleware") + 1
    MIDDLEWARE.insert(index, "django.contrib.auth.middleware.LoginRequiredMiddleware")
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "predicciones.context_processors.entorno",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": Path(os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3"))), "OPTIONS": {"timeout": 20}}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
