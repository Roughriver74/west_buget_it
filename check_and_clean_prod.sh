#!/bin/bash

# Script to check and clean credit portfolio data on production server
# Usage: ./check_and_clean_prod.sh

SERVER="root@31.129.107.178"
PROJECT_PATH="/root/west_buget_it"  # Adjust if needed

echo "=================================================="
echo "🔍 Подключение к продакшн серверу..."
echo "=================================================="
echo ""

# Check connection
ssh -o ConnectTimeout=5 $SERVER "echo '✅ Соединение установлено'" || {
    echo "❌ Не удалось подключиться к серверу $SERVER"
    echo "Проверьте SSH ключи и доступ к серверу"
    exit 1
}

echo ""
echo "=================================================="
echo "📥 Обновление кода из GitHub..."
echo "=================================================="
echo ""

ssh $SERVER << 'ENDSSH'
# Find project directory
if [ -d "/root/west_buget_it" ]; then
    PROJECT_DIR="/root/west_buget_it"
elif [ -d "/app/west_buget_it" ]; then
    PROJECT_DIR="/app/west_buget_it"
else
    PROJECT_DIR=$(find /root /app -name "west_buget_it" -type d 2>/dev/null | head -1)
fi

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Проект не найден!"
    exit 1
fi

echo "✅ Проект найден: $PROJECT_DIR"
cd $PROJECT_DIR

# Pull latest code
git pull origin main

ENDSSH

echo ""
echo "=================================================="
echo "🔍 Проверка дубликатов на продакшн сервере..."
echo "=================================================="
echo ""

ssh $SERVER << 'ENDSSH'
# Find project directory
if [ -d "/root/west_buget_it" ]; then
    PROJECT_DIR="/root/west_buget_it"
elif [ -d "/app/west_buget_it" ]; then
    PROJECT_DIR="/app/west_buget_it"
else
    PROJECT_DIR=$(find /root /app -name "west_buget_it" -type d 2>/dev/null | head -1)
fi

cd $PROJECT_DIR/backend

# Find PostgreSQL container
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E '(postgres|db)' | head -1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ PostgreSQL контейнер не найден!"
    exit 1
fi

echo "PostgreSQL контейнер: $POSTGRES_CONTAINER"
echo ""

# Check duplicates in fin_receipts
echo "📊 Проверка fin_receipts..."
docker exec $POSTGRES_CONTAINER psql -U budget_user -d it_budget_db -c "
SELECT
    department_id,
    COUNT(*) as total,
    COUNT(DISTINCT operation_id) as unique_ops,
    COUNT(*) - COUNT(DISTINCT operation_id) as duplicates
FROM fin_receipts
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "📊 Проверка fin_expenses..."
docker exec $POSTGRES_CONTAINER psql -U budget_user -d it_budget_db -c "
SELECT
    department_id,
    COUNT(*) as total,
    COUNT(DISTINCT operation_id) as unique_ops,
    COUNT(*) - COUNT(DISTINCT operation_id) as duplicates
FROM fin_expenses
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "📊 Проверка fin_expense_details..."
docker exec $POSTGRES_CONTAINER psql -U budget_user -d it_budget_db -c "
SELECT
    department_id,
    COUNT(*) as total,
    COUNT(DISTINCT expense_operation_id) as unique_ops
FROM fin_expense_details
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "💰 Суммы для department 8:"
docker exec $POSTGRES_CONTAINER psql -U budget_user -d it_budget_db -c "
WITH receipt_totals AS (
  SELECT SUM(amount) as total FROM fin_receipts WHERE department_id = 8 AND is_active = true
),
expense_totals AS (
  SELECT SUM(amount) as total FROM fin_expenses WHERE department_id = 8 AND is_active = true
),
detail_totals AS (
  SELECT
    SUM(CASE WHEN payment_type = 'Погашение долга' THEN payment_amount ELSE 0 END) as principal,
    SUM(CASE WHEN payment_type = 'Уплата процентов' THEN payment_amount ELSE 0 END) as interest
  FROM fin_expense_details WHERE department_id = 8
)
SELECT
  (SELECT total FROM receipt_totals) as total_receipts,
  (SELECT total FROM expense_totals) as total_expenses,
  (SELECT principal FROM detail_totals) as principal_paid,
  (SELECT interest FROM detail_totals) as interest_paid,
  (SELECT total FROM receipt_totals) - (SELECT principal FROM detail_totals) as debt_balance;
"

ENDSSH

echo ""
echo "=================================================="
echo "Хотите очистить данные department 8? (yes/no)"
echo "=================================================="
read -p "Введите yes для подтверждения: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Отменено."
    exit 0
fi

echo ""
echo "=================================================="
echo "🗑️  Очистка данных на продакшн сервере..."
echo "=================================================="
echo ""

ssh $SERVER << 'ENDSSH'
# Find project directory
if [ -d "/root/west_buget_it" ]; then
    PROJECT_DIR="/root/west_buget_it"
elif [ -d "/app/west_buget_it" ]; then
    PROJECT_DIR="/app/west_buget_it"
else
    PROJECT_DIR=$(find /root /app -name "west_buget_it" -type d 2>/dev/null | head -1)
fi

cd $PROJECT_DIR/backend

# Find PostgreSQL container
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E '(postgres|db)' | head -1)

echo "Удаление данных из department 8..."

# Delete in correct order (child to parent)
docker exec $POSTGRES_CONTAINER psql -U budget_user -d it_budget_db << 'EOSQL'
BEGIN;

DELETE FROM fin_expense_details WHERE department_id = 8;
DELETE FROM fin_expenses WHERE department_id = 8;
DELETE FROM fin_receipts WHERE department_id = 8;
DELETE FROM fin_contracts WHERE department_id = 8;
DELETE FROM fin_bank_accounts WHERE department_id = 8;
DELETE FROM fin_organizations WHERE department_id = 8;
DELETE FROM fin_import_logs WHERE department_id = 8;

COMMIT;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW mv_contract_totals;

SELECT 'Данные успешно удалены!' as status;
EOSQL

echo ""
echo "✅ Данные department 8 очищены!"

ENDSSH

echo ""
echo "=================================================="
echo "🔄 Очистка Redis кэша..."
echo "=================================================="
echo ""

ssh $SERVER << 'ENDSSH'
# Find Redis container
REDIS_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i redis | head -1)

if [ -n "$REDIS_CONTAINER" ]; then
    echo "Redis контейнер: $REDIS_CONTAINER"
    docker exec $REDIS_CONTAINER redis-cli KEYS "credit_portfolio:*" | xargs -I {} docker exec $REDIS_CONTAINER redis-cli DEL {}
    echo "✅ Кэш очищен"
else
    echo "⚠️  Redis контейнер не найден (это нормально если не используется)"
fi
ENDSSH

echo ""
echo "=================================================="
echo "✅ Готово!"
echo "=================================================="
echo ""
echo "Данные будут автоматически импортированы при следующем запуске импорта (08:00 MSK)"
echo "Или запустите импорт вручную через API"
echo ""
