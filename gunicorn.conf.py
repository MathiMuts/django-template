# gunicorn.conf.py — picked up automatically by gunicorn (production server).

import os

bind = "0.0.0.0:8000"
wsgi_app = "project.wsgi:application"
worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS") or 3)
threads = 2
timeout = 60
accesslog = "-"
errorlog = "-"
loglevel = (os.environ.get("LOG_LEVEL") or "info").lower()
