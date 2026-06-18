#!/bin/bash
# Copies the production database into this slot's database.
# Run on demand from inside the blue slot container:
#   az webapp ssh --name ova --slot blue
#   bash /home/site/wwwroot/copy_db.sh
#
# Prerequisites (one-time setup on the blue slot):
#   - DATABASE_URL      → points at ova_blue (already set for normal operation)
#   - PROD_DATABASE_URL → slot-specific app setting with the prod connection string
set -e

if [ -z "$PROD_DATABASE_URL" ]; then
    echo "ERROR: PROD_DATABASE_URL is not set on this slot." >&2
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set on this slot." >&2
    exit 1
fi

if ! command -v pg_dump &>/dev/null; then
    echo "Installing postgresql-client..."
    apt-get update -qq && apt-get install -y -qq postgresql-client
fi

echo "Dumping production database..."
pg_dump \
    --format=custom \
    "$PROD_DATABASE_URL" \
    -f /tmp/prod_dump.dump

echo "Restoring to staging database..."
pg_restore \
    --clean --if-exists \
    --dbname="$DATABASE_URL" \
    /tmp/prod_dump.dump

rm -f /tmp/prod_dump.dump
echo "Done. Run 'python3 manage.py migrate' if you have pending migrations."
