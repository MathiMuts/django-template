# django-template
A template for websites using Django + Tailwind, dockerised. No nginx needed: static files are served by WhiteNoise.

## Setup
This repository contains multiple branches. To use a certain branch as the starting point:
>```
>git checkout tailwind
>git branch -D main
>git branch -m main
>git push -f origin main
>git push origin --delete tailwind
>```

Then:
1. `cp .env.example .env`
2. Fill in `.env`. **This is the only config file.** Django and docker compose both read it.
3. Add your apps to `LOCAL_APPS` in `project/settings.py` and to `project/urls.py`.

## Configuration (`.env`)
Everything is documented in `.env.example`; names, db credentials, allowed hosts etc. are derived from it.

| Setting | Meaning |
|---|---|
| `PROJECT_NAME` | container/db/volume names (lowercase) |
| `DJANGO_DEBUG` | `True` in development, `False` in production |
| `DOMAIN` | your domain(s), sets allowed hosts + CSRF origins |
| `SSL_TLS` | `True` when an HTTPS reverse proxy is in front |
| `APP_PORT`, `APP_BIND_ADDRESS` | where the app is published on the host |
| `COMPOSE_PROFILES` | empty = SQLite + RAM cache · `postgres` · `redis` · `postgres,redis` |
| `DJANGO_SUPERUSER_*` | auto-create an admin user on container start |
| `EMAIL_HOST_*` | mails are sent once a password is set, otherwise printed in the logs |

The secret key is generated on first start and stored in `./data/.secret_key` (or set `DJANGO_SECRET_KEY`).
All persistent data (SQLite db, uploads, secret key) lives in `./data`. Back up that folder (plus the postgres volume, if used).

## Development
Activate the `venv`, `pip install -r requirements.txt`, then start the tailwind watcher:
>```
>python manage.py tailwind install
>python manage.py tailwind start
>```

And the webserver, either locally:
>```
>python manage.py migrate
>python manage.py runserver
>```
or in docker (`docker-compose.override.yml` is applied automatically: runserver, live code, DEBUG on):
>```
>docker compose up -d --build
>```

[http://localhost:8000/](http://localhost:8000/) (port = `APP_PORT`).

## Production
In `.env`: `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, your domain in `DJANGO_ALLOWED_HOSTS`, and `SSL_TLS=True` if served over HTTPS.

>```
>docker compose -f docker-compose.yml up -d --build --remove-orphans
>```

The image builds the tailwind css and collects static files at build time, so the running container has no node. On start it waits for postgres/redis (if used), runs migrations and starts gunicorn on `APP_PORT`.

For HTTPS, put any reverse proxy (Caddy, Traefik, the host's nginx, Cloudflare Tunnel, ...) in front and set `APP_BIND_ADDRESS=127.0.0.1` so the app is only reachable through it.

See `.github/workflows/` for an auto-deploy example.
