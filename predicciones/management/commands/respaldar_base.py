"""Copia consistente de SQLite, incluso cuando el servidor está activo."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Guarda una copia de la base SQLite en una carpeta de respaldos."

    def handle(self, *args, **options):
        source = Path(settings.DATABASES["default"]["NAME"]).resolve()
        folder = source.parent / "respaldos"
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = "gympredictai-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".sqlite3"
        target = folder / name
        try:
            with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as origin:
                with sqlite3.connect(target) as destination:
                    origin.backup(destination)
            target.chmod(0o600)
        except (sqlite3.Error, OSError) as error:
            raise CommandError(f"No se pudo crear la copia: {error}") from error
        self.stdout.write(self.style.SUCCESS(f"Copia creada: {target}"))
