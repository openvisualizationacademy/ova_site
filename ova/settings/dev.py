from .base import *
import os


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if not DEBUG:
    raise RuntimeError("dev.py should never be used with DEBUG=False")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', "django-insecure-@$7dr8z96_o%u067c#(nt$k7b60v+_%306qb2azc+145!0n19^")

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS",["*"]).split(",")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += [
    'debug_toolbar',
]

# This is for debug toolbar - no need to use in prod
INTERNAL_IPS = ["127.0.0.1"]

STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

try:
    from .local import *
except ImportError:
    pass
