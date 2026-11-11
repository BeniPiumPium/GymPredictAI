"""Crea la configuración online y una base persistente sin pisar datos existentes."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3

from dotenv import dotenv_values


def preparar(project_dir, data_dir, domain):
    domain = domain.strip().lower()
    label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    if len(domain) > 253 or not re.fullmatch(rf"{label}(?:\.{label})+", domain):
        raise ValueError("Ingresá solamente el dominio, sin https:// ni barras.")

    env_path = project_dir / ".env"
    if env_path.exists():
        config = dotenv_values(env_path)
        if config.get("DJANGO_DEBUG", "true").lower() not in {"false", "0", "no"}:
            raise ValueError("Ya existe un .env de desarrollo. Guardalo con otro nombre antes de preparar el servidor.")
        if config.get("DJANGO_ALLOWED_HOSTS") != domain:
            raise ValueError("El .env existente usa otro dominio. Revisá DJANGO_ALLOWED_HOSTS antes de continuar.")
        if not config.get("DJANGO_SECRET_KEY"):
            raise ValueError("El .env existente no tiene DJANGO_SECRET_KEY.")
        database = Path(config.get("DJANGO_DB_PATH", str(project_dir / "db.sqlite3")))
        if not database.is_absolute() or not database.is_file():
            raise ValueError("Revisá DJANGO_DB_PATH: la base configurada no existe o no tiene una ruta absoluta.")
        return database, False

    data_dir = data_dir.expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    database = data_dir / "db.sqlite3"
    if not database.exists():
        source = project_dir / "db.sqlite3"
        if not source.is_file():
            raise ValueError("Falta db.sqlite3 en el proyecto. Usá el ZIP completo con la base del CSV.")
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as source_conn:
            with sqlite3.connect(database) as destination:
                source_conn.backup(destination)
        database.chmod(0o600)
    with sqlite3.connect(database) as connection:
        connection.execute("SELECT COUNT(*) FROM predicciones_registromensual").fetchone()

    values = {
        "DJANGO_DEBUG": "false",
        "DJANGO_REQUIRE_LOGIN": "true",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
        "DJANGO_ALLOWED_HOSTS": domain,
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://" + domain,
        "DJANGO_DB_PATH": str(database),
    }
    descriptor = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write("# Configuración privada generada en el servidor. No compartir.\n")
        for key, value in values.items():
            file.write(f"{key}={json.dumps(value)}\n")
    return database, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dominio", help="Ejemplo: tuusuario.pythonanywhere.com")
    args = parser.parse_args()
    project_dir = Path(__file__).resolve().parent.parent
    suggested = getpass.getuser() + ".pythonanywhere.com"
    domain = args.dominio or input(f"Dominio de tu Web app [{suggested}]: ").strip() or suggested
    try:
        database, created = preparar(project_dir, Path.home() / ".local/share/gympredictai", domain)
    except (ValueError, sqlite3.Error, OSError) as error:
        raise SystemExit(f"No se pudo preparar el servidor: {error}") from error
    print("Configuración creada." if created else "Se conserva la configuración existente.")
    print(f"Base persistente: {database}")
    print("La clave secreta se guardó en .env; no hace falta copiarla ni compartirla.")


if __name__ == "__main__":
    main()
