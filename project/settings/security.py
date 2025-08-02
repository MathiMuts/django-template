# project/settings/security.py

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_09r+q3ewsrv5expk^88_vgw()=#w+ejtc#kmzlvwo4ygtuk%='

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
