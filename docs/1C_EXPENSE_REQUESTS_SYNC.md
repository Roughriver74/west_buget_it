# 1C Expense Requests Synchronization

## Overview

Интеграция для синхронизации заявок на расходование денежных средств из 1С через OData API.

**Документ 1С**: `Document_ЗаявкаНаРасходованиеДенежныхСредств`

## Features

- ✅ Синхронизация заявок на расход из 1С через OData
- ✅ Автоматическое создание/обновление организаций и контрагентов
- ✅ Предотвращение дубликатов через `external_id_1c`
- ✅ Маппинг статусов документов 1С -> IT Budget Manager
- ✅ Поддержка пагинации для больших объемов данных
- ✅ Batch processing с коммитами после каждого батча

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         1C System                           │
│  Document_ЗаявкаНаРасходованиеДенежныхСредств              │
└────────────────────────┬────────────────────────────────────┘
                         │ OData API
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OData1CClient (odata_1c_client.py)             │
│  - get_expense_requests()                                   │
│  - get_organization_by_key()                                │
│  - get_counterparty_by_key()                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Expense1CSync (expense_1c_sync.py)                │
│  - sync_expenses()                                          │
│  - _map_1c_to_expense()                                     │
│  - _get_or_create_organization()                            │
│  - _get_or_create_contractor()                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Tables                          │
│  - expenses (с полем external_id_1c)                        │
│  - organizations                                            │
│  - contractors                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Mapping

### 1C Document Fields → IT Budget Manager Expense

| 1C Field                     | Expense Field      | Type     | Notes                                    |
|------------------------------|-------------------|----------|------------------------------------------|
| `Ref_Key`                    | `external_id_1c`  | String   | Уникальный GUID документа                |
| `Number`                     | `number`          | String   | Номер документа (например: "ВЛ0В-000203")|
| `Date`                       | `request_date`    | DateTime | Дата документа                           |
| `ДатаПлатежа`                | `payment_date`    | DateTime | Дата платежа (если указана)              |
| `СуммаДокумента`             | `amount`          | Decimal  | Сумма документа                          |
| `Организация_Key`            | `organization_id` | FK       | GUID организации (создается автоматически)|
| `Контрагент_Key`             | `contractor_id`   | FK       | GUID контрагента (создается автоматически)|
| `НазначениеПлатежа`          | `comment`         | Text     | Полное назначение платежа                |
| `Комментарий`                | `comment`         | Text     | Резервный (если нет НазначениеПлатежа)   |
| `Posted`                     | `status`          | Enum     | См. маппинг статусов ниже                |
| `Статус`                     | `status`, `is_paid`, `is_closed` | Multiple | См. маппинг статусов ниже |

### Status Mapping

| 1C Status      | 1C Posted | IT Budget Status | is_paid | is_closed |
|----------------|-----------|------------------|---------|-----------|
| `вс_Оплачена`  | Any       | `PAID`           | `true`  | `true`    |
| Any            | `true`    | `PENDING`        | `false` | `false`   |
| Any            | `false`   | `DRAFT`          | `false` | `false`   |

### Organization/Contractor Creation

При первой синхронизации заявки, если организация или контрагент не найдены в БД по `external_id_1c`, они создаются автоматически:

**Organization**:
- `НаименованиеСокращенное` → `short_name`
- `Наименование` → `full_name` (fallback: `short_name`)
- `ИНН` → `inn`
- `КПП` → `kpp`
- `Ref_Key` → `external_id_1c`

**Contractor**:
- `Наименование` → `name`
- `ИНН` → `inn`
- `КПП` → `kpp`
- `Ref_Key` → `external_id_1c`

## API Endpoints

### POST /api/v1/expenses/sync/1c

Запустить синхронизацию заявок из 1С.

**Permissions**: `ADMIN`, `MANAGER` only

**Request Body**:
```json
{
  "date_from": "2025-11-01T00:00:00",
  "date_to": "2025-11-30T23:59:59",
  "department_id": 1,
  "only_posted": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Sync completed",
  "statistics": {
    "total_fetched": 150,
    "total_processed": 148,
    "total_created": 120,
    "total_updated": 28,
    "total_skipped": 0,
    "errors": [],
    "success": true
  },
  "department": {
    "id": 1,
    "name": "IT Department"
  }
}
```

## Usage Examples

### 1. Test Connection and Data Structure

Используйте тестовый скрипт для проверки подключения и структуры данных:

```bash
cd backend
python scripts/test_1c_expense_sync.py
```

Скрипт выполнит:
1. Проверку подключения к 1С OData
2. Получение 5 образцов документов
3. Вывод структуры полей
4. Валидацию маппинга
5. Тест получения данных организаций/контрагентов

### 2. Sync via API (cURL)

```bash
# Get JWT token first
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')

# Sync expenses for November 2025
curl -X POST "http://localhost:8000/api/v1/expenses/sync/1c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-11-01T00:00:00",
    "date_to": "2025-11-30T23:59:59",
    "department_id": 1,
    "only_posted": true
  }'
```

### 3. Sync via Python Script

```python
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.odata_1c_client import OData1CClient
from app.services.expense_1c_sync import Expense1CSync

# Initialize
db = next(get_db())
odata_client = OData1CClient(
    base_url='http://10.10.100.77/trade/odata/standard.odata',
    username='odata.user',
    password='ak228Hu2hbs28'
)

# Create sync service
sync_service = Expense1CSync(
    db=db,
    odata_client=odata_client,
    department_id=1
)

# Run sync
result = sync_service.sync_expenses(
    date_from=date(2025, 11, 1),
    date_to=date(2025, 11, 30),
    batch_size=100,
    only_posted=True
)

print(result.to_dict())
```

## Configuration

### Environment Variables

Add to `backend/.env`:

```bash
# 1C OData Configuration
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28
```

## Database Schema

### Expense Table Changes

Migration: `2025_11_16_1531-158ce187a936_add_external_id_1c_to_expenses_for_1c_.py`

```sql
-- Add external_id_1c field
ALTER TABLE expenses
ADD COLUMN external_id_1c VARCHAR(100);

-- Create index for faster lookups
CREATE INDEX ix_expenses_external_id_1c ON expenses(external_id_1c);
```

### Organizations & Contractors

Для работы синхронизации необходимо, чтобы таблицы `organizations` и `contractors` имели поле `external_id_1c`:

```sql
-- Organizations
ALTER TABLE organizations
ADD COLUMN external_id_1c VARCHAR(100);

CREATE INDEX ix_organizations_external_id_1c ON organizations(external_id_1c);

-- Contractors
ALTER TABLE contractors
ADD COLUMN external_id_1c VARCHAR(100);

CREATE INDEX ix_contractors_external_id_1c ON contractors(external_id_1c);
```

## Performance Considerations

### Batch Processing

Синхронизация работает батчами по 100 документов (настраивается):
- Каждый батч коммитится отдельно
- Снижает нагрузку на память
- Позволяет восстановиться после ошибки

### Pagination

1С OData имеет лимит на количество возвращаемых записей (max 1000):
- Используется пагинация с параметром `$skip`
- Автоматическое продолжение до конца данных

### Duplicate Prevention

```python
# Проверка по external_id_1c перед созданием
existing = db.query(Expense).filter(
    Expense.external_id_1c == ref_key,
    Expense.department_id == department_id
).first()
```

## Error Handling

### Common Errors

**1. Connection Error**
```
Failed to connect to 1C OData service
```
**Solution**: Проверьте URL, credentials, network access

**2. Missing Required Fields**
```
Missing or invalid Ref_Key
```
**Solution**: Документ в 1С имеет некорректную структуру

**3. Organization/Contractor Not Found**
```
Organization {guid} not found in 1C
```
**Solution**: GUID существует в документе, но не найден в справочнике 1С

### Logging

```python
import logging

# Enable debug logging for sync
logging.getLogger("app.services.expense_1c_sync").setLevel(logging.DEBUG)
logging.getLogger("app.services.odata_1c_client").setLevel(logging.DEBUG)
```

## Monitoring

### Sync Statistics

Каждая синхронизация возвращает статистику:
- `total_fetched`: Получено из 1С
- `total_processed`: Обработано
- `total_created`: Создано новых
- `total_updated`: Обновлено существующих
- `total_skipped`: Пропущено (без изменений)
- `errors`: Список ошибок

### Audit Log

Все операции создания/обновления логируются через стандартный audit log системы.

## Troubleshooting

### Debug Sync Process

1. **Test Connection**
   ```bash
   python scripts/test_1c_expense_sync.py
   ```

2. **Check OData Response**
   ```bash
   curl -u odata.user:ak228Hu2hbs28 \
     "http://10.10.100.77/trade/odata/standard.odata/Document_ЗаявкаНаРасходованиеДенежныхСредств?\$top=1&\$format=json"
   ```

3. **Verify Database**
   ```sql
   -- Check synced expenses
   SELECT id, number, external_id_1c, status, created_at
   FROM expenses
   WHERE external_id_1c IS NOT NULL
   ORDER BY created_at DESC;

   -- Check auto-created organizations
   SELECT id, short_name, inn, external_id_1c
   FROM organizations
   WHERE external_id_1c IS NOT NULL;
   ```

## Future Enhancements

- [ ] Scheduled sync (daily/hourly via cron)
- [ ] Webhook notifications from 1C on document changes
- [ ] Bi-directional sync (update status in 1C when paid in IT Budget Manager)
- [ ] Sync expense details (табличная часть РасшифровкаПлатежа)
- [ ] Auto-categorization based on 1C expense item (СтатьяРасходов)
- [ ] Link with bank transactions for auto-matching

## Related Documentation

- [1C OData Integration](./1C_ODATA_INTEGRATION.md)
- [Bank Transactions Sync](./BANK_TRANSACTIONS_IMPORT_GUIDE.md)
- [Expense Management](../README.md#expense-management)
