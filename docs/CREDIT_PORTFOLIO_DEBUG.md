# Диагностика проблем с кредитным портфолио

## Проблема: Неправильные суммы на дашборде

### Симптомы
- "Остаток задолженности" показывает огромное число типа `-15413831348`
- "Погашено тела" показывает неправильную сумму (19.9 млрд вместо 4.3 млрд)
- Числа выглядят как конкатенация строк

### Возможные причины и решения

## 1. Старая версия фронтенда на сервере

### Проверка
```bash
ssh root@31.129.107.178
cd /путь/к/проекту/frontend/src/legacy/pages
grep "Number(r.amount" CreditDashboard.tsx
```

Если `Number()` отсутствует - нужен деплой новой версии.

### Исправление
Выполните деплой через Coolify или вручную:
```bash
git pull origin main
cd frontend
npm run build
```

## 2. Проблема с кэшем Redis

### Очистка кэша
```bash
ssh root@31.129.107.178
# Подключиться к Redis контейнеру
docker exec -it <redis_container> redis-cli

# Очистить весь кэш кредитного портфолио
KEYS credit_portfolio:*
DEL credit_portfolio:*

# Или очистить весь кэш
FLUSHDB
```

## 3. Дубли данных в базе

### Проверка дублей
```bash
ssh root@31.129.107.178
cd /путь/к/проекту/backend

# Активировать venv
source venv/bin/activate

# Проверить дубли
python -c "
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check receipts
result = db.execute(text('''
    SELECT
        COUNT(*) as total,
        COUNT(DISTINCT operation_id) as unique_ops,
        COUNT(*) - COUNT(DISTINCT operation_id) as duplicates
    FROM fin_receipts
    WHERE department_id = 8
''')).fetchone()

print(f'Receipts: total={result[0]}, unique={result[1]}, duplicates={result[2]}')

# Check expenses
result = db.execute(text('''
    SELECT
        COUNT(*) as total,
        COUNT(DISTINCT operation_id) as unique_ops,
        COUNT(*) - COUNT(DISTINCT operation_id) as duplicates
    FROM fin_expenses
    WHERE department_id = 8
''')).fetchone()

print(f'Expenses: total={result[0]}, unique={result[1]}, duplicates={result[2]}')
"
```

Если есть дубли (duplicates > 0), выполните очистку:

```bash
# DRY RUN сначала
python scripts/clean_credit_data.py --department-id 8 --dry-run

# Реальная очистка
python scripts/clean_credit_data.py --department-id 8
```

После очистки данные импортируются заново через FTP (по расписанию в 08:00 MSK).

## 4. Проверка корректности данных в БД

### SQL запрос
```bash
docker exec <postgres_container> psql -U budget_user -d it_budget_db -c "
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
```

**Ожидаемые значения (корректные):**
- total_receipts: ~4.5 млрд
- principal_paid: ~4.3 млрд
- interest_paid: ~185 млн
- debt_balance: ~104 млн

## 5. Проверка API ответов

### Тест summary endpoint
```bash
# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"admin"}' | jq -r '.access_token')

# Проверить summary
curl -s http://localhost:8000/api/v1/credit-portfolio/summary?department_id=8 \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

Ответ должен содержать числа, а не строки:
```json
{
  "total_receipts": 4455387241.61,
  "total_expenses": 4415997870.92,
  "net_balance": 39389370.69,
  "active_contracts_count": 52,
  "total_principal": 4350755636.02,
  "total_interest": 185326194.47
}
```

## 6. Проверка логов импорта

```bash
docker exec <postgres_container> psql -U budget_user -d it_budget_db -c "
SELECT
  table_name,
  COUNT(*) as imports,
  SUM(rows_inserted) as total_inserted,
  SUM(rows_failed) as total_failed,
  MAX(import_date) as last_import,
  MAX(status) as last_status
FROM fin_import_logs
WHERE department_id = 8
GROUP BY table_name
ORDER BY last_import DESC;
"
```

Проверьте:
- Есть ли ошибки (rows_failed > 0)?
- Когда был последний импорт?
- Все ли таблицы импортировались?

## Пошаговый план исправления

### Шаг 1: Обновить код на сервере
```bash
ssh root@31.129.107.178
cd /путь/к/проекту
git pull origin main
```

### Шаг 2: Пересобрать фронтенд
```bash
cd frontend
npm install
npm run build
```

### Шаг 3: Перезапустить backend (если нужно)
```bash
cd ../backend
docker-compose restart backend
# или через Coolify
```

### Шаг 4: Очистить Redis кэш
```bash
docker exec -it <redis_container> redis-cli
FLUSHDB
exit
```

### Шаг 5: Очистить данные department 8
```bash
cd backend
source venv/bin/activate
python scripts/clean_credit_data.py --department-id 8 --dry-run
# Если OK, то без --dry-run
python scripts/clean_credit_data.py --department-id 8
```

### Шаг 6: Запустить импорт вручную (опционально)
```bash
curl -X POST http://your-domain/api/v1/credit-portfolio/import/trigger \
  -H "Authorization: Bearer $TOKEN"
```

Или подождать автоматического импорта в 08:00 MSK.

### Шаг 7: Проверить результат
Открыть страницу "Аналитика кредитов и платежей" и проверить суммы.

## Профилактика

### 1. Настроить мониторинг
- Добавить алерт если остаток задолженности отрицательный
- Проверять суммы после каждого импорта

### 2. Регулярная проверка дублей
Запускать скрипт проверки 1 раз в месяц:
```bash
python scripts/check_duplicates.py --department-id 8
```

### 3. Логировать API ответы
Добавить логирование больших чисел (> 10 млрд) - возможный признак проблемы.

## Контакты

Если проблема не решилась:
1. Проверьте логи бэкенда: `docker logs <backend_container>`
2. Проверьте логи фронтенда в браузере (Console)
3. Создайте issue в репозитории
