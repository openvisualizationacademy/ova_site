from .base import *
import os


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-@$7dr8z96_o%u067c#(nt$k7b60v+_%306qb2azc+145!0n19^"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += [
    'debug_toolbar',
]

INTERNAL_IPS = ["127.0.0.1"]

try:
    from .local import *
except ImportError:
    pass
