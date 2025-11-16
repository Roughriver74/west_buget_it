#!/bin/bash

# Script to check for duplicates in credit portfolio tables on production server
# Usage: ./scripts/check_duplicates_prod.sh

set -e

echo "=================================================="
echo "Проверка дубликатов в кредитном портфолио"
echo "=================================================="
echo ""

# Find PostgreSQL container
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i postgres | head -1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ PostgreSQL контейнер не найден!"
    exit 1
fi

echo "✅ PostgreSQL контейнер: $POSTGRES_CONTAINER"
echo ""

# Database credentials (adjust if needed)
DB_USER="budget_user"
DB_NAME="it_budget_db"

echo "=================================================="
echo "1. Проверка таблиц кредитного портфолио"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND (table_name LIKE 'fin_%' OR table_name IN ('receipts', 'expenses', 'expense_details'))
ORDER BY table_name;
"

echo ""
echo "=================================================="
echo "2. Проверка дубликатов в fin_receipts"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    department_id,
    COUNT(*) as total_records,
    COUNT(DISTINCT operation_id) as unique_operations,
    COUNT(*) - COUNT(DISTINCT operation_id) as duplicates,
    CASE
        WHEN COUNT(*) - COUNT(DISTINCT operation_id) > 0 THEN '❌ ЕСТЬ ДУБЛИ'
        ELSE '✅ Нет дублей'
    END as status
FROM fin_receipts
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "=================================================="
echo "3. Проверка дубликатов в fin_expenses"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    department_id,
    COUNT(*) as total_records,
    COUNT(DISTINCT operation_id) as unique_operations,
    COUNT(*) - COUNT(DISTINCT operation_id) as duplicates,
    CASE
        WHEN COUNT(*) - COUNT(DISTINCT operation_id) > 0 THEN '❌ ЕСТЬ ДУБЛИ'
        ELSE '✅ Нет дублей'
    END as status
FROM fin_expenses
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "=================================================="
echo "4. Проверка дубликатов в fin_expense_details"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    department_id,
    COUNT(*) as total_records,
    COUNT(DISTINCT expense_operation_id) as unique_operations,
    CASE
        WHEN COUNT(*) - COUNT(DISTINCT expense_operation_id) > 0 THEN '⚠️ ВОЗМОЖНЫ ДУБЛИ (несколько деталей на операцию)'
        ELSE '✅ OK'
    END as status
FROM fin_expense_details
GROUP BY department_id
ORDER BY department_id;
"

echo ""
echo "=================================================="
echo "5. Примеры дубликатов в fin_receipts (если есть)"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    operation_id,
    department_id,
    COUNT(*) as count,
    STRING_AGG(id::text, ', ') as record_ids
FROM fin_receipts
GROUP BY operation_id, department_id
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;
"

echo ""
echo "=================================================="
echo "6. Примеры дубликатов в fin_expenses (если есть)"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    operation_id,
    department_id,
    COUNT(*) as count,
    STRING_AGG(id::text, ', ') as record_ids
FROM fin_expenses
GROUP BY operation_id, department_id
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;
"

echo ""
echo "=================================================="
echo "7. Суммы для department_id=8"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
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

echo ""
echo "=================================================="
echo "8. Проверка UNIQUE индексов"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('fin_receipts', 'fin_expenses', 'fin_expense_details')
  AND indexdef LIKE '%UNIQUE%'
ORDER BY tablename, indexname;
"

echo ""
echo "=================================================="
echo "9. История импортов (последние 10)"
echo "=================================================="
echo ""

docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT
    import_date,
    table_name,
    department_id,
    rows_inserted,
    rows_updated,
    rows_failed,
    status,
    source_file
FROM fin_import_logs
ORDER BY import_date DESC
LIMIT 10;
"

echo ""
echo "=================================================="
echo "✅ Проверка завершена!"
echo "=================================================="
echo ""
echo "Если найдены дубликаты, выполните очистку:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python scripts/clean_credit_data.py --department-id 8 --dry-run"
echo ""
