"""Arranque local: instala y ejecuta siempre dentro del mismo entorno virtual."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
from urllib.error import URLError
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent
MODULES = {'Django': 'django', 'numpy': 'numpy', 'pandas': 'pandas', 'scikit-learn': 'sklearn', 'python-dotenv': 'dotenv'}


class ErrorInicio(RuntimeError):
    pass


def ejecutar(arguments, **kwargs):
    result = subprocess.run([str(value) for value in arguments], cwd=ROOT, **kwargs)
    if result.returncode:
        raise ErrorInicio('El comando no pudo completarse. Revisá el mensaje anterior; la base no se reinicia ni se reemplaza.')
    return result


def ruta_python(folder):
    return folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def version_python(executable):
    try:
        result = subprocess.run([str(executable), '-c', 'import sys,json; print(json.dumps(list(sys.version_info[:3])))'], capture_output=True, text=True, timeout=15)
        if result.returncode == 0: return tuple(json.loads(result.stdout))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def entorno():
    if sys.version_info < (3, 12):
        raise ErrorInicio('Usá Python 3.12, 3.13 o 3.14 de 64 bits para iniciar este proyecto.')
    folder = ROOT / '.venv'
    executable = ruta_python(folder)
    existing = version_python(executable) if executable.exists() else None
    if existing and existing >= (3, 12): return executable
    if folder.exists():
        backup = folder.with_name('.venv_anterior_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        folder.rename(backup)
        print(f'El entorno anterior no funciona aquí. Se conservó en {backup.name}.')
    print('1/4 · Creando un entorno propio para GymPredictAI…', flush=True)
    venv.EnvBuilder(with_pip=True).create(folder)
    return executable


def comprobar_librerias(executable):
    code = 'import importlib,json; from importlib.metadata import version\n'
    code += 'names=' + repr(MODULES) + '\n'
    code += 'for name,module in names.items(): importlib.import_module(module)\n'
    code += 'print(json.dumps({name:version(name) for name in names}))'
    try:
        result = subprocess.run([str(executable), '-c', code], capture_output=True, text=True, timeout=60)
        return json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def instalar(executable):
    requirements = ROOT / 'requirements.txt'
    wanted = {}
    for line in requirements.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '==' in line:
            name, version = line.split('==', 1)
            wanted[name] = version
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    receipt = executable.parent.parent / '.gym_instalacion.json'
    try: previous = json.loads(receipt.read_text())
    except (OSError, ValueError): previous = {}
    installed = comprobar_librerias(executable)
    matches = installed is not None and all(installed.get(name) == version for name, version in wanted.items())
    if previous.get('requirements') != digest or not matches:
        print('2/4 · Instalando las bibliotecas del proyecto. La primera vez necesita Internet…', flush=True)
        command = [executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--only-binary=:all:', '--no-cache-dir', '-r', requirements]
        if previous.get('requirements') == digest and installed is None:
            command.append('--force-reinstall')
        try:
            ejecutar(command)
            ejecutar([executable, '-m', 'pip', 'check'])
        except ErrorInicio:
            raise ErrorInicio('No se terminaron de instalar las dependencias. Revisá la conexión. Si pip indica que no hay una versión compatible, usá Python 3.12–3.14 de 64 bits y volvé a ejecutar este archivo.') from None
        installed = comprobar_librerias(executable)
        if installed is None: raise ErrorInicio('Las bibliotecas se descargaron, pero no se pueden cargar. Ejecutá python iniciar.py --diagnostico y compartí la salida.')
        receipt.write_text(json.dumps({'requirements': digest, 'versions': installed}), encoding='utf-8')
    else:
        print('2/4 · Bibliotecas comprobadas; no hace falta reinstalarlas.', flush=True)


def entorno_local():
    values = os.environ.copy()
    # La configuración del hosting queda separada de la utilizada en esta PC.
    values['DJANGO_ENV_FILE'] = str(ROOT / '.env.local')
    values['DJANGO_DEBUG'] = 'true'
    values['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1,[::1]'
    values['PYTHONUTF8'] = '1'
    return values


def puerto_disponible(preferred):
    if not 1024 <= preferred <= 65535:
        raise ErrorInicio('Elegí un puerto entre 1024 y 65535.')
    for port in range(preferred, min(preferred + 10, 65536)):
        with socket.socket() as listener:
            try:
                listener.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise ErrorInicio('Los puertos están ocupados. Cerrá el servidor anterior o usá --puerto 8100.')


def abrir_cuando_responda(url):
    for _ in range(60):
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (URLError, OSError):
            time.sleep(.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-preparar', action='store_true')
    parser.add_argument('--no-navegador', action='store_true')
    parser.add_argument('--diagnostico', action='store_true')
    parser.add_argument('--puerto', type=int, default=8000)
    options = parser.parse_args()
    if options.diagnostico:
        executable = ruta_python(ROOT / '.venv')
        if not executable.exists(): executable = Path(sys.executable)
        print('Python:', executable)
        print('Versión:', version_python(executable))
        print('Bibliotecas:', comprobar_librerias(executable) or 'Faltan bibliotecas o alguna no pudo cargarse.')
        print('Para instalar y reparar: python iniciar.py')
        return 0
    try:
        executable = entorno()
        instalar(executable)
        env = entorno_local()
        print('3/4 · Aplicando migraciones y comprobando el proyecto…', flush=True)
        ejecutar([executable, ROOT / 'manage.py', 'migrate', '--noinput'], env=env)
        ejecutar([executable, ROOT / 'manage.py', 'check'], env=env)
        if options.solo_preparar:
            print('Preparación correcta. Para abrir la página: python iniciar.py')
            return 0
        # El primer propietario se crea en la consola, sin contraseñas predeterminadas.
        check = ejecutar([executable, ROOT / 'manage.py', 'shell', '-c', 'from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(is_superuser=True,is_active=True).exists())'], env=env, capture_output=True, text=True)
        if check.stdout.strip().splitlines()[-1] == 'False':
            print('Primera apertura: creá tu usuario administrador. La contraseña no se muestra al escribir.')
            ejecutar([executable, ROOT / 'manage.py', 'createsuperuser'], env=env)
        port = puerto_disponible(options.puerto)
        url = f'http://127.0.0.1:{port}/'
        print(f'4/4 · Página local: {url}\nDejá esta ventana abierta. Para detener: Ctrl+C.', flush=True)
        if not options.no_navegador:
            threading.Thread(target=abrir_cuando_responda, args=(url,), daemon=True).start()
        ejecutar([executable, ROOT / 'manage.py', 'runserver', f'127.0.0.1:{port}'], env=env)
        return 0
    except KeyboardInterrupt:
        print('\nServidor detenido.')
        return 0
    except (ErrorInicio, OSError) as error:
        print(f'\nNo se pudo iniciar: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
