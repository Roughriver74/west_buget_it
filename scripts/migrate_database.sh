#!/bin/bash
set -e

# Database Migration Script
# Migrates database from old Docker server to new production server

echo "==========================================="
echo "Database Migration: Docker → Production"
echo "==========================================="
echo ""
echo "From: 93.189.228.52 (Docker)"
echo "To: 31.129.107.178 (Production)"
echo ""

# Configuration
OLD_SERVER="93.189.228.52"
NEW_SERVER="31.129.107.178"

# Old database (Docker)
OLD_CONTAINER="postgres-sskow88ckgsk4ossc8s8440k-093812936523"
OLD_DB_NAME="west_fin_dwh"
OLD_DB_USER="west_user"
OLD_DB_PASSWORD="west_secure_password_2025"

# New database (Production)
NEW_CONTAINER="budget_db_prod"
NEW_DB_NAME="it_budget_db"
NEW_DB_USER="budget_user"
NEW_DB_PASSWORD="budget_pass"

BACKUP_FILE="budget_db_backup_$(date +%Y%m%d_%H%M%S).sql"
TEMP_DIR="/tmp/db_migration"

# Create temp directory
mkdir -p "$TEMP_DIR"

echo "Step 1: Creating backup on old server..."
echo "  Database: $OLD_DB_NAME"
echo "  Container: $OLD_CONTAINER"
echo ""

ssh root@$OLD_SERVER "docker exec $OLD_CONTAINER pg_dump -U $OLD_DB_USER -d $OLD_DB_NAME --clean --if-exists" > "$TEMP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$TEMP_DIR/$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created successfully (Size: $BACKUP_SIZE)"
else
    echo "❌ Failed to create backup"
    exit 1
fi

echo ""
echo "Step 2: Verifying backup..."
if [ -s "$TEMP_DIR/$BACKUP_FILE" ]; then
    LINE_COUNT=$(wc -l < "$TEMP_DIR/$BACKUP_FILE")
    echo "✅ Backup file is valid ($LINE_COUNT lines)"
else
    echo "❌ Backup file is empty"
    exit 1
fi

echo ""
echo "Step 3: Creating safety backup of current database on new server..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U $NEW_DB_USER -d $NEW_DB_NAME --clean --if-exists" > "$TEMP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || echo "⚠️  No existing data to backup (database might be empty)"

echo ""
echo "Step 4: Stopping backend on new server..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml stop backend"
echo "✅ Backend stopped"

echo ""
echo "Step 5: Importing data into new database..."
echo "  Database: $NEW_DB_NAME"
echo "  Container: $NEW_CONTAINER"
echo ""

# Import via stdin
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db psql -U $NEW_DB_USER -d $NEW_DB_NAME" < "$TEMP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Data imported successfully"
else
    echo "❌ Failed to import data"
    echo "Restoring from safety backup..."
    if [ -f "$TEMP_DIR/safety_backup_*.sql" ]; then
        ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db psql -U $NEW_DB_USER -d $NEW_DB_NAME" < "$TEMP_DIR/safety_backup_"*.sql
    fi
    exit 1
fi

echo ""
echo "Step 6: Running database migrations..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head" 2>/dev/null || echo "⚠️  Migrations may have already been applied"

echo ""
echo "Step 7: Starting backend on new server..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml start backend"

echo ""
echo "Step 8: Waiting for backend to be ready..."
sleep 5

for i in {1..30}; do
    if ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health 2>/dev/null"; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "Step 9: Verifying data migration..."

# Count tables
OLD_TABLES=$(ssh root@$OLD_SERVER "docker exec $OLD_CONTAINER psql -U $OLD_DB_USER -d $OLD_DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';\"" | tr -d ' ')
NEW_TABLES=$(ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db psql -U $NEW_DB_USER -d $NEW_DB_NAME -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';\"" | tr -d ' ')

echo "  Old database tables: $OLD_TABLES"
echo "  New database tables: $NEW_TABLES"

if [ "$OLD_TABLES" -le "$NEW_TABLES" ]; then
    echo "✅ Table count verification passed"
else
    echo "⚠️  Warning: New database has fewer tables"
fi

# Sample data verification
echo ""
echo "Checking sample data..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db psql -U $NEW_DB_USER -d $NEW_DB_NAME -c 'SELECT COUNT(*) FROM departments;' -c 'SELECT COUNT(*) FROM users;' -c 'SELECT COUNT(*) FROM employees;' 2>/dev/null" || echo "Some tables may not exist yet"

echo ""
echo "==========================================="
echo "✅ Database migration completed!"
echo "==========================================="
echo ""
echo "📁 Backup files saved in: $TEMP_DIR"
echo ""
echo "🔍 Next steps:"
echo "1. Test application: https://budget-west.shknv.ru/login"
echo "2. Verify all data is present"
echo "3. Check application logs for errors"
echo ""
echo "📦 Backup files:"
echo "  - Migration backup: $TEMP_DIR/$BACKUP_FILE"
echo "  - Safety backup: $TEMP_DIR/safety_backup_*.sql"
echo ""
echo "🗑️  To cleanup backups after verification:"
echo "   rm -rf $TEMP_DIR"
echo ""
