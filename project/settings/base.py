# project/settings/base.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# INFO: Application definition

ROOT_URLCONF = 'project.urls'

WSGI_APPLICATION = 'project.wsgi.application'


# INFO: Internationalization

LANGUAGE_CODE = 'nl'

TIME_ZONE = 'Europe/Brussels'
TIME_FORMAT = 'H:i'

USE_I18N = True

USE_TZ = True