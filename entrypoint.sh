#!/bin/sh

set -e

echo "Entrypoint script started as user: $(whoami)"

echo "Creating environment file for cron jobs..."

if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_ENV" != "development" ]; then
    echo "Collecting static files for production..."
    python manage.py collectstatic --noinput --clear

    echo "Building css..."
    python manage.py tailwind build
fi
 
echo "Starting application server..."
exec "$@"
```
