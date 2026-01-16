#!/bin/bash
set -e

echo "Entrypoint: executando migrações..."
cd /app/Escola
python manage.py migrate --noinput

if [ "${COLLECT_STATIC:-0}" = "1" ]; then
  echo "Entrypoint: coletando static files..."
  python manage.py collectstatic --noinput
fi

echo "Entrypoint: iniciando comando: $@"
exec "$@"