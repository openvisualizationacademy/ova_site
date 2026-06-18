#!/bin/bash
# Copies the production database into this slot's database.
# Run on demand from inside the blue slot container:
#   az webapp ssh --name ova --slot blue
#   bash /home/site/wwwroot/copy_db.sh
#
# Prerequisites (one-time setup on the blue slot):
#   - DATABASE_URL  → points at ova_blue (already set for normal operation)
#   - PROD_DATABASE_URL → set as a slot-specific app setting with the prod connection string
set -e

if [ -z "$PROD_DATABASE_URL" ]; then
    echo "ERROR: PROD_DATABASE_URL is not set on this slot." >&2
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set on this slot." >&2
    exit 1
fi

PG_VERSION=17
if ! command -v pg_dump &>/dev/null || [ "$(pg_dump --version | grep -oP '\d+' | head -1)" -lt "$PG_VERSION" ]; then
    echo "Installing postgresql-client-${PG_VERSION}..."
    apt-get install -y -qq curl gnupg lsb-release
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] \
        https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list
    apt-get update -qq
    apt-get install -y -qq "postgresql-client-${PG_VERSION}"
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
