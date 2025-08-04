#!/bin/sh

set -e

echo "Entrypoint script started as user: $(whoami)"

echo "Setting mask..."
umask 0002

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Building css..."
python manage.py tailwind install
python manage.py tailwind build

echo "Collecting static files for production..."
python manage.py collectstatic --noinput --clear

echo "Starting application server..."
exec "$@"