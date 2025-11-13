#!/bin/bash
set -e

echo "==================================="
echo "Database Migration Script"
echo "From: 93.189.228.52 (old Coolify server)"
echo "To: 31.129.107.178 (new production server)"
echo "==================================="

# Configuration
OLD_SERVER="93.189.228.52"
NEW_SERVER="31.129.107.178"
BACKUP_FILE="budget_db_backup_$(date +%Y%m%d_%H%M%S).sql"
REMOTE_BACKUP_PATH="/tmp/$BACKUP_FILE"

echo ""
echo "Step 1: Creating backup on old server..."
ssh root@$OLD_SERVER "docker exec db-io00swck8gss4kosckwwwo88-140950610773 pg_dump -U budget_user -d it_budget_db -F c -f /tmp/$BACKUP_FILE && echo 'Backup created successfully'"

echo ""
echo "Step 2: Copying backup from old server to local..."
scp root@$OLD_SERVER:/tmp/$BACKUP_FILE ./$BACKUP_FILE

echo ""
echo "Step 3: Copying backup to new server..."
scp ./$BACKUP_FILE root@$NEW_SERVER:/tmp/$BACKUP_FILE

echo ""
echo "Step 4: Starting PostgreSQL on new server..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml up -d db"

echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo ""
echo "Step 5: Restoring database on new server..."
ssh root@$NEW_SERVER "docker exec -i budget_db_prod pg_restore -U budget_user -d it_budget_db -c -F c /tmp/$BACKUP_FILE || echo 'Some errors are expected if database is empty'"

echo ""
echo "Step 6: Verifying database..."
ssh root@$NEW_SERVER "docker exec budget_db_prod psql -U budget_user -d it_budget_db -c 'SELECT COUNT(*) FROM departments;' -c 'SELECT COUNT(*) FROM users;' -c 'SELECT COUNT(*) FROM employees;'"

echo ""
echo "Step 7: Cleaning up..."
rm -f ./$BACKUP_FILE
ssh root@$OLD_SERVER "rm -f /tmp/$BACKUP_FILE"
ssh root@$NEW_SERVER "rm -f /tmp/$BACKUP_FILE"

echo ""
echo "==================================="
echo "Migration completed successfully!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Verify data on new server"
echo "2. Setup GitHub Secrets"
echo "3. Trigger CI/CD deployment"
