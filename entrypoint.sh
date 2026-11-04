#!/bin/sh
# Runs as root, prepares the data dir, then drops to `appuser` for everything else.
set -e

mkdir -p /app/data
chown -R appuser:appuser /app/data

# Wait until the postgres / redis containers (if enabled in COMPOSE_PROFILES) accept connections.
gosu appuser python - <<'EOF'
import os, socket, sys, time

profiles = os.environ.get("COMPOSE_PROFILES", "")
targets = [(host, port) for name, host, port in [("postgres", "db", 5432), ("redis", "redis", 6379)] if name in profiles]

for host, port in targets:
    for _ in range(60):
        try:
            socket.create_connection((host, port), timeout=2).close()
            print(f"{host}:{port} is up")
            break
        except OSError:
            print(f"Waiting for {host}:{port}...")
            time.sleep(1)
    else:
        sys.exit(f"Could not reach {host}:{port}")
EOF

echo "Applying database migrations..."
gosu appuser python manage.py migrate --noinput

# Creates the admin user on first start when DJANGO_SUPERUSER_* is set in .env.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@localhost}"
    if output=$(gosu appuser python manage.py createsuperuser --noinput 2>&1); then
        echo "Superuser '$DJANGO_SUPERUSER_USERNAME' created."
    elif echo "$output" | grep -q "already taken"; then
        echo "Superuser '$DJANGO_SUPERUSER_USERNAME' already exists."
    else
        echo "Could not create superuser: $output"
    fi
fi

echo "Starting: $*"
exec gosu appuser "$@"
