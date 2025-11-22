#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U ${POSTGRES_USER:-budget_user} > /dev/null 2>&1; do
  sleep 1
done
echo "Database is ready!"

echo "Running database migrations..."
alembic upgrade head

# Start background scheduler as separate process
echo "Starting background scheduler..."
python run_scheduler.py > /proc/1/fd/1 2>&1 &
SCHEDULER_PID=$!
echo "Background scheduler started (PID: $SCHEDULER_PID)"

# Trap SIGTERM and SIGINT to gracefully stop scheduler
trap "echo 'Stopping scheduler...'; kill -TERM $SCHEDULER_PID 2>/dev/null || true; wait $SCHEDULER_PID 2>/dev/null || true" SIGTERM SIGINT

echo "Starting application..."
exec "$@"
