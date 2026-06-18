#!/bin/bash
set -e

python3 manage.py collectstatic --no-input --settings=ova.settings.production
exec daphne -b 0.0.0.0 -p 8000 ova.asgi:application
