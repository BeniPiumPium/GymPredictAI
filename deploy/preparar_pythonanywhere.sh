#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$HOME/.virtualenvs/gympredictai"
cd "$project_dir"

if ! command -v python3.12 >/dev/null; then
  echo "Necesitás Python 3.12. Revisá Account > System image en PythonAnywhere."
  exit 1
fi
if [ ! -x "$venv_dir/bin/python" ]; then
  python3.12 -m venv "$venv_dir"
fi
"$venv_dir/bin/python" -m pip install --no-cache-dir -r requirements.txt
"$venv_dir/bin/python" deploy/preparar_pythonanywhere.py
"$venv_dir/bin/python" manage.py migrate --noinput
"$venv_dir/bin/python" manage.py collectstatic --noinput
"$venv_dir/bin/python" manage.py check

echo "Preparación terminada. Creá tu usuario con:"
echo "$venv_dir/bin/python $project_dir/manage.py createsuperuser"
echo "En Web > Virtualenv usá: $venv_dir"
echo "En Web > Static files, /static/ debe apuntar a: $project_dir/staticfiles"
echo "El archivo deploy/pythonanywhere_wsgi.py contiene el código para pegar en Web > WSGI."
