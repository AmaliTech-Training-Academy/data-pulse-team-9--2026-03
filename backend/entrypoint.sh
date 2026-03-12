#!/bin/sh
set -e

if [ "$1" = 'celery' ] || [ "$1" = 'python' ]; then
    echo "==> Starting $1 command..."
    exec "$@"
fi

echo "==> Running migrations..."
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput

echo "==> Seeding default users..."
python manage.py seed_users || true

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
exec gunicorn datapulse.wsgi:application -c gunicorn.conf.py
