from .base import *
import os


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if not DEBUG:
    raise RuntimeError("dev.py should never be used with DEBUG=False")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-dev-key-do-not-use-in-production"
)

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Filter out empty strings from CSRF_TRUSTED_ORIGINS (base.py splits "", producing [""])
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if DEBUG:
    INSTALLED_APPS += [
        "debug_toolbar",
        "django_extensions",
    ]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# This is for debug toolbar - no need to use in prod
INTERNAL_IPS = ["127.0.0.1"]

# STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default to sqlite3 for local dev / CI when DATABASE_URL is not set
if not DATABASES["default"].get("ENGINE"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }

try:
    from .local import *
except ImportError:
    pass
