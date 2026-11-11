import hashlib
from pathlib import Path
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from predicciones.csv_service import ErrorCSV, aplicar_csv, estado_actual, leer_csv, resumir


class Command(BaseCommand):
    help = 'Valida e importa el CSV completo sin cambios parciales ni meses duplicados.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', nargs='?', default='datos_gimnasio.csv')
        parser.add_argument('--solo-nuevos', action='store_true', help='Conserva los meses que ya existen.')
        parser.add_argument('--verificar', action='store_true', help='Valida y muestra el resumen sin guardar.')

    def handle(self, *args, **options):
        path = Path(options['archivo'])
        if not path.is_absolute(): path = settings.BASE_DIR / path
        try:
            content = path.read_bytes()
            rows = leer_csv(content)
            mode = 'nuevos' if options['solo_nuevos'] else 'actualizar'
            baseline = estado_actual(rows)
            totals = resumir(rows, mode, baseline)
            if not options['verificar']:
                aplicar_csv(rows, mode, baseline, uuid.uuid4(), path.name, hashlib.sha256(content).hexdigest())
        except (ErrorCSV, OSError) as error:
            raise CommandError(str(error)) from error
        prefix = 'Vista previa' if options['verificar'] else 'Importación completada'
        self.stdout.write(self.style.SUCCESS(f"{prefix}: {len(rows)} meses; {totals['creados']} nuevos, {totals['actualizados']} actualizados y {totals['omitidos']} sin cambios."))
