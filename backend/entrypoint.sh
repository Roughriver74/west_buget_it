#!/bin/bash
set -e

echo "======================================"
echo "IT Budget Manager - Backend Starting"
echo "======================================"

# Wait for database to be ready
echo "Waiting for database to be ready..."
max_attempts=30
attempt=0

while ! python -c "
import psycopg2
import os
import sys
try:
    # Parse DATABASE_URL or use individual vars
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Extract connection params from URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if match:
            user, password, host, port, database = match.groups()
        else:
            print('Invalid DATABASE_URL format')
            sys.exit(1)
    else:
        user = os.environ.get('DB_USER', 'budget_user')
        password = os.environ.get('DB_PASSWORD', 'budget_pass')
        host = os.environ.get('DB_HOST', 'db')
        port = os.environ.get('DB_PORT', '5432')
        database = os.environ.get('DB_NAME', 'it_budget_db')

    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=5
    )
    conn.close()
    print('Database is ready!')
    sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ Database is not available after $max_attempts attempts"
        exit 1
    fi
    echo "Database not ready yet (attempt $attempt/$max_attempts)..."
    sleep 2
done

echo "✅ Database is ready!"

# Run database migrations
echo ""
echo "Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Optional: Create admin user if it doesn't exist
echo ""
echo "Checking for admin user..."
if [ -f "create_admin.py" ]; then
    python create_admin.py || echo "⚠️  Admin user creation skipped (may already exist)"
else
    echo "⚠️  create_admin.py not found, skipping admin creation"
fi

echo ""
echo "======================================"
echo "Starting Cron service for FTP import"
echo "======================================"
echo ""

# Create log directory for cron
mkdir -p /app/logs

# Start cron service
service cron start
if [ $? -eq 0 ]; then
    echo "✅ Cron service started successfully"
    echo "   FTP import will run every 2 hours"
    echo "   Logs: /app/logs/cron_ftp_import.log"
else
    echo "⚠️  Cron service failed to start, but continuing..."
fi

echo ""
echo "======================================"
echo "Starting Gunicorn application server"
echo "======================================"
echo ""

# Start the application with Gunicorn
# Note: Always bind to 8000 inside container, external port mapping is handled by Docker
# Memory optimization: reduced workers and automatic worker restart to prevent memory leaks
exec gunicorn app.main:app \
    --workers "${GUNICORN_WORKERS:-2}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:8000" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --keep-alive "${GUNICORN_KEEPALIVE:-5}" \
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-50}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}"
