#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from importlib.util import find_spec
    required = {'django': 'Django', 'numpy': 'numpy', 'pandas': 'pandas', 'sklearn': 'scikit-learn', 'dotenv': 'python-dotenv'}
    missing = [package for module, package in required.items() if find_spec(module) is None]
    if missing:
        print('Faltan bibliotecas en este Python: ' + ', '.join(missing), file=sys.stderr)
        print('Solución automática: ejecutá INICIAR_WINDOWS.cmd o python iniciar.py.', file=sys.stderr)
        print('Instalación manual: python -m pip install -r requirements.txt', file=sys.stderr)
        raise SystemExit(1)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
