# 1C Catalog Synchronization

Автоматическая синхронизация справочников из 1С через OData API.

## Обзор

Модуль позволяет синхронизировать справочники из 1С:
1. **Catalog_Организации** → `organizations` (наши организации)
2. **Catalog_СтатьиДвиженияДенежныхСредств** → `budget_categories` (категории расходов)

## Архитектура

```
1C OData API
    ↓
OData1CClient
    ├─ get_organizations()
    └─ get_cash_flow_categories()
    ↓
Sync Services
    ├─ OrganizationSync
    └─ BudgetCategorySync
    ↓
Database
    ├─ organizations (shared)
    └─ budget_categories (per department)
```

## Модели данных

### Organizations (Организации)

**1C → Database маппинг:**

| 1C Field                    | Database Field  | Описание                     |
|-----------------------------|-----------------|------------------------------|
| `Ref_Key`                   | `external_id_1c` | GUID организации (unique)    |
| `Description`               | `name`          | Наименование                 |
| `НаименованиеПолное`        | `full_name`     | Полное наименование          |
| `НаименованиеСокращенное`   | `short_name`    | Краткое наименование         |
| `ИНН`                       | `inn`           | ИНН                          |
| `КПП`                       | `kpp`           | КПП                          |
| `ОГРН`                      | `ogrn`          | ОГРН                         |
| `Префикс`                   | `prefix`        | Префикс (ВА, Вест и т.д.)    |
| `КодПоОКПО`                 | `okpo`          | Код по ОКПО                  |
| `Статус`                    | `status_1c`     | Статус ("Действует", и т.д.) |
| `DeletionMark`              | `is_active`     | Признак удаления (инверсия)  |

**Особенности:**
- Organizations are **shared** across all departments
- `external_id_1c` is **globally unique**
- `department_id` is nullable (tracking purpose)

### BudgetCategories (Категории бюджета)

**1C → Database маппинг:**

| 1C Field                        | Database Field    | Описание                         |
|---------------------------------|-------------------|----------------------------------|
| `Ref_Key`                       | `external_id_1c`  | GUID категории                   |
| `Code`                          | `code_1c`         | Код из 1С (01-000021)            |
| `Description`                   | `name`            | Наименование категории           |
| `IsFolder`                      | `is_folder`       | Папка (группа) или элемент       |
| `Parent_Key`                    | `parent_id`       | ID родительской категории        |
| `РеквизитДопУпорядочивания`     | `order_index`     | Индекс сортировки                |
| `DeletionMark`                  | `is_active`       | Признак удаления (инверсия)      |

**Иерархия:**
- **Folders** (`IsFolder=true`) — группы/отделы (например: "Операционная деятельность")
- **Items** (`IsFolder=false`) — конкретные статьи расходов (например: "Аренда офиса")
- `Parent_Key` связывает элементы с папками

**Особенности:**
- Categories are **per department** (multi-tenancy)
- `external_id_1c` + `department_id` = unique constraint
- Hierarchy через `parent_id` (после синхронизации)

## API Endpoints

Base path: `/api/v1/sync/1c`

### 1. Синхронизировать все справочники

```bash
POST /api/v1/sync/1c/catalogs
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "department_id": 1,
  "sync_organizations": true,
  "sync_categories": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Catalog synchronization completed",
  "organizations_result": {
    "total_fetched": 50,
    "total_processed": 48,
    "total_created": 30,
    "total_updated": 18,
    "total_skipped": 2,
    "errors": [],
    "success": true
  },
  "categories_result": {
    "total_fetched": 120,
    "total_processed": 115,
    "total_created": 80,
    "total_updated": 35,
    "total_skipped": 5,
    "errors": [],
    "success": true
  },
  "department": {
    "id": 1,
    "code": "IT",
    "name": "IT Department"
  }
}
```

### 2. Синхронизировать только организации

```bash
POST /api/v1/sync/1c/organizations?department_id=1
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Organizations synchronization completed",
  "statistics": {
    "total_fetched": 50,
    "total_processed": 48,
    "total_created": 30,
    "total_updated": 18,
    "total_skipped": 2,
    "errors": [],
    "success": true
  }
}
```

### 3. Синхронизировать только категории бюджета

```bash
POST /api/v1/sync/1c/budget-categories?department_id=1
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Budget categories synchronization completed",
  "statistics": {
    "total_fetched": 120,
    "total_processed": 115,
    "total_created": 80,
    "total_updated": 35,
    "total_skipped": 5,
    "errors": [],
    "success": true
  },
  "department": {
    "id": 1,
    "code": "IT",
    "name": "IT Department"
  }
}
```

### 4. Проверить статус синхронизации

```bash
GET /api/v1/sync/1c/status
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "connection_ok": true,
  "statistics": {
    "organizations_synced": 48,
    "budget_categories_synced": 115
  },
  "odata_url": "http://10.10.100.77/trade/odata/standard.odata"
}
```

## Права доступа

**Требуемая роль:** `ADMIN` или `MANAGER`

## Скрипты

### 1. Анализ структуры справочников

```bash
cd backend
python scripts/check_1c_catalogs.py
```

Выводит:
- Структуру полей Catalog_Организации
- Структуру полей Catalog_СтатьиДвиженияДенежныхСредств
- Примеры данных
- Иерархию (папки/элементы)

### 2. Синхронизация справочников

```bash
cd backend
python scripts/sync_1c_catalogs.py
```

Интерактивный скрипт:
1. Выбор отдела
2. Выбор что синхронизировать (организации/категории/всё)
3. Запуск синхронизации
4. Вывод статистики

## Workflow синхронизации

### Organizations Sync

```
1. ПОДКЛЮЧЕНИЕ К 1С
   ↓
   OData1CClient.get_organizations(batch_size)

2. ОБРАБОТКА БАТЧА
   ↓
   Для каждой организации:
   ├─ Пропустить DeletionMark=true
   ├─ Проверить external_id_1c → existing?
   │  ├─ Да → Update
   │  └─ Нет → Create
   └─ Commit batch

3. ПАГИНАЦИЯ
   ↓
   skip += batch_size
   Повторить пока len(results) == batch_size

4. РЕЗУЛЬТАТ
   ↓
   CatalogSyncResult
```

### BudgetCategories Sync

```
1. ПОДКЛЮЧЕНИЕ К 1С
   ↓
   OData1CClient.get_cash_flow_categories(batch_size)

2. FIRST PASS: Создать/обновить категории
   ↓
   Для каждой категории:
   ├─ Пропустить DeletionMark=true
   ├─ Проверить external_id_1c + department_id → existing?
   │  ├─ Да → Update
   │  └─ Нет → Create
   ├─ Сохранить Ref_Key → DB ID mapping
   └─ Commit batch

3. SECOND PASS: Обновить parent_id
   ↓
   Для каждой категории:
   ├─ Получить Parent_Key из 1С
   ├─ Найти parent_db_id через mapping
   └─ Установить parent_id

4. РЕЗУЛЬТАТ
   ↓
   CatalogSyncResult
```

## Performance

**Batch Processing:**
- Default batch size: 100 записей
- Коммит после каждого батча
- Pagination через `$skip`

**Indexes:**
```sql
-- Organizations
CREATE UNIQUE INDEX ON organizations(external_id_1c);
CREATE INDEX ON organizations(inn);
CREATE INDEX ON organizations(is_active);

-- BudgetCategories
CREATE INDEX ON budget_categories(external_id_1c);
CREATE UNIQUE INDEX ON budget_categories(external_id_1c, department_id);
CREATE INDEX ON budget_categories(parent_id);
CREATE INDEX ON budget_categories(is_folder);
CREATE INDEX ON budget_categories(department_id, is_active);
```

## Duplicate Prevention

**Organizations:**
- `external_id_1c` уникален глобально
- Если организация существует → UPDATE
- Используется для всех отделов (shared)

**BudgetCategories:**
- `external_id_1c` + `department_id` = unique constraint
- Каждый отдел имеет свою копию категорий из 1С
- Parent relationships восстанавливаются после синхронизации

## Environment Variables

```bash
# .env файл
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28
```

## Database Migration

```bash
# Migration file
backend/alembic/versions/2025_11_17_1200-abc123def456_add_1c_catalog_sync_fields.py

# Apply migration
cd backend
alembic upgrade head
```

## Примеры использования

### 1. Первичная синхронизация

```bash
# Запустить скрипт
cd backend
python scripts/sync_1c_catalogs.py

# Выбрать:
# 1. Отдел: IT Department
# 2. Что синхронизировать: Всё (3)
```

### 2. Синхронизация через API

```bash
# Get JWT token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# Sync all catalogs
curl -X POST "http://localhost:8000/api/v1/sync/1c/catalogs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": 1,
    "sync_organizations": true,
    "sync_categories": true
  }'
```

### 3. Проверка синхронизированных данных

```sql
-- Проверить организации
SELECT
  id,
  name,
  inn,
  kpp,
  external_id_1c,
  is_active
FROM organizations
WHERE external_id_1c IS NOT NULL
ORDER BY created_at DESC;

-- Проверить категории
SELECT
  id,
  name,
  code_1c,
  is_folder,
  parent_id,
  external_id_1c,
  department_id
FROM budget_categories
WHERE external_id_1c IS NOT NULL
ORDER BY department_id, order_index;

-- Проверить иерархию категорий
WITH RECURSIVE category_tree AS (
  -- Root categories (folders)
  SELECT
    id,
    name,
    code_1c,
    is_folder,
    parent_id,
    1 AS level,
    CAST(name AS TEXT) AS path
  FROM budget_categories
  WHERE parent_id IS NULL AND department_id = 1

  UNION ALL

  -- Child categories
  SELECT
    c.id,
    c.name,
    c.code_1c,
    c.is_folder,
    c.parent_id,
    ct.level + 1,
    ct.path || ' > ' || c.name
  FROM budget_categories c
  INNER JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT
  level,
  REPEAT('  ', level - 1) || name AS name,
  code_1c,
  CASE WHEN is_folder THEN '📁' ELSE '📄' END AS type
FROM category_tree
ORDER BY path;
```

## Troubleshooting

**Connection Error:**
```
Failed to connect to 1C OData service
```
→ Проверьте URL, credentials, сетевой доступ

**Duplicate Key Error:**
```
duplicate key value violates unique constraint
```
→ Категория уже существует для этого отдела, будет обновлена

**Parent Not Found:**
```
Failed to update parent for category
```
→ Родительская категория не была синхронизирована, будет создана в следующем проходе

## Future Enhancements

- [ ] Scheduled sync (ежедневная через cron)
- [ ] Incremental sync (только изменения с последней синхронизации)
- [ ] Webhook от 1С при изменении справочников
- [ ] Auto-mapping категорий 1С → expense types (OPEX/CAPEX)
- [ ] Sync history tracking (когда, кем, сколько записей)

## Ссылки

- [1C OData Integration](1C_ODATA_INTEGRATION.md)
- [Bank Transactions](BANK_TRANSACTIONS_IMPORT_GUIDE.md)
- [Expense Requests Sync](1C_EXPENSE_REQUESTS_SYNC.md)
