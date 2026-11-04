# project/settings.py
#
# All configuration lives in `.env` (copy `.env.example` to get started).
# This file only translates those values into Django settings, so you should
# rarely need to edit it — except for LOCAL_APPS below.

import os
import secrets
import shutil
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Your own Django apps go here.
LOCAL_APPS = [
    "example_app",
]


# --- INFO: .env helpers -------------------------------------------------------

def env(name, default=""):
    value = os.environ.get(name, "").strip()
    return value if value else default


def env_bool(name, default=False):
    value = env(name).lower()
    if not value:
        return default
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ImproperlyConfigured(f"{name}={value!r} is not a boolean, use True or False.")


def env_int(name, default):
    value = env(name)
    try:
        return int(value) if value else default
    except ValueError:
        raise ImproperlyConfigured(f"{name}={value!r} is not a number.")


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


def env_choice(name, default, choices):
    value = env(name, default).lower()
    if value not in choices:
        raise ImproperlyConfigured(f"{name}={value!r} must be one of: {', '.join(choices)}.")
    return value


# --- INFO: Core ---------------------------------------------------------------

PROJECT_NAME = env("PROJECT_NAME", "django-app")
DEBUG = env_bool("DJANGO_DEBUG", False)

# Everything that must survive a container rebuild (SQLite db, uploads, secret key).
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Uses DJANGO_SECRET_KEY if set, otherwise generates one once and keeps it in data/.
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    key_file = DATA_DIR / ".secret_key"
    if not key_file.exists():
        key_file.write_text(secrets.token_urlsafe(50))
    SECRET_KEY = key_file.read_text().strip()

ROOT_URLCONF = "project.urls"
WSGI_APPLICATION = "project.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ADMIN_URL = env("ADMIN_URL", "admin/").strip("/") + "/"


# --- INFO: Apps & middleware --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "tailwind",
    "theme",
    *LOCAL_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("django_browser_reload")
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = shutil.which("npm") or "npm"  # finds npm.cmd on Windows too


# --- INFO: Hosts & security ---------------------------------------------------

DOMAINS = env_list("DOMAIN")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", *DOMAINS]
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in DOMAINS]

# SSL_TLS=True means: a reverse proxy in front of this app terminates HTTPS
# and sets the X-Forwarded-Proto header.
if env_bool("SSL_TLS", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGOUT_URL = "logout"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# --- INFO: Database & cache ---------------------------------------------------
# COMPOSE_PROFILES decides: `postgres` -> the postgres container, otherwise SQLite;
#                           `redis`    -> the redis container, otherwise a RAM cache.

COMPOSE_PROFILES = env_list("COMPOSE_PROFILES")
for profile in COMPOSE_PROFILES:
    if profile not in ("postgres", "redis"):
        raise ImproperlyConfigured(f"COMPOSE_PROFILES: unknown {profile!r}, use postgres and/or redis.")
USE_POSTGRES = "postgres" in COMPOSE_PROFILES
USE_REDIS = "redis" in COMPOSE_PROFILES

if USE_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": PROJECT_NAME,
            "USER": PROJECT_NAME,
            "HOST": "db",  # no password: the container is only reachable from `web`
            "PORT": "5432",
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DATA_DIR / "db.sqlite3",
            "OPTIONS": {
                # WAL + IMMEDIATE: several gunicorn workers can write without "database is locked".
                "transaction_mode": "IMMEDIATE",
                "timeout": 20,
                "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
            },
        }
    }

if USE_REDIS:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": "redis://redis:6379/0"}}
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
else:
    # Per gunicorn worker, not shared — fine for small sites.
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CACHES["default"]["KEY_PREFIX"] = PROJECT_NAME


# --- INFO: Static & media files -----------------------------------------------
# Static files are served by WhiteNoise, uploads by Django, so no nginx is needed.
# theme/static (the compiled tailwind css) is found automatically because `theme` is an app.

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [path for path in [BASE_DIR / "static"] if path.exists()]

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}


# --- INFO: Email --------------------------------------------------------------
# Mails are sent over SMTP as soon as a password is set, otherwise printed to the console.

EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_USE_TLS = not EMAIL_USE_SSL
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = SERVER_EMAIL = EMAIL_HOST_USER or "webmaster@localhost"

EMAIL_BACKEND = {
    "console": "django.core.mail.backends.console.EmailBackend",
    "smtp": "django.core.mail.backends.smtp.EmailBackend",
    "none": "django.core.mail.backends.dummy.EmailBackend",
}[env_choice("EMAIL_BACKEND", "smtp" if EMAIL_HOST_PASSWORD else "console", ["console", "smtp", "none"])]

# Who gets an email when a 500 error happens in production.
ADMINS = [(email, email) for email in env_list("ADMIN_EMAILS")]


# --- INFO: Internationalization -----------------------------------------------

LANGUAGE_CODE = env("LANGUAGE_CODE", "nl")
TIME_ZONE = env("TIME_ZONE", "Europe/Brussels")
TIME_FORMAT = "H:i"
USE_I18N = True
USE_TZ = True


# --- INFO: Logging ------------------------------------------------------------

LOG_LEVEL = env("LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console", "mail_admins"], "level": LOG_LEVEL, "propagate": False},
    },
}
