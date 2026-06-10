from .base import *
import os

# Test settings: run against a local SQLite database for speed.
# The app's normal settings build DATABASES from DATABASE_URL/DB_ENGINE, which
# point at a remote Azure Postgres — far too slow for the test suite (every query
# is a network round-trip). Override that here.

DEBUG = False
SECRET_KEY = "django-insecure-test-key"
ALLOWED_HOSTS = ["*"]

# base.py splits an empty env var into [""]; drop empties so CSRF validation is sane.
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]

# Local SQLite file — overrides the remote-Postgres config from base/env.
# --reuse-db (pytest.ini) keeps this file between runs so migrations run only once.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),
    }
}

# Fast hashing — the auth_client fixture creates a user with a real password.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
