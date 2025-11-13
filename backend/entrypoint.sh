#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U ${POSTGRES_USER:-budget_user} > /dev/null 2>&1; do
  sleep 1
done
echo "Database is ready!"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
