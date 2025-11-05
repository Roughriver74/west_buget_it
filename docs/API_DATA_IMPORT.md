# API для импорта данных

Полное руководство по загрузке данных в систему IT Budget Manager через API.

## Содержание

- [Обзор](#обзор)
- [Методы импорта](#методы-импорта)
  - [1. Unified Import API (Excel)](#1-unified-import-api-excel)
  - [2. External API (JSON/CSV с токенами)](#2-external-api-jsoncsv-с-токенами)
- [Поддерживаемые сущности](#поддерживаемые-сущности)
- [Примеры использования](#примеры-использования)
- [Обработка ошибок](#обработка-ошибок)

---

## Обзор

Система предоставляет **два способа** импорта данных:

| Метод | Формат | Аутентификация | Использование |
|-------|--------|----------------|---------------|
| **Unified Import** | Excel (.xlsx, .xls) | JWT Token (пользователь) | Веб-интерфейс, ручная загрузка |
| **External API** | JSON, CSV | API Token | Автоматизация, интеграции |

---

## Методы импорта

### 1. Unified Import API (Excel)

**Базовый URL:** `http://localhost:8000/api/v1/import`

**Аутентификация:** JWT Token в заголовке `Authorization: Bearer <token>`

#### Workflow импорта

```
1. GET /entities          → Получить список доступных сущностей
2. GET /template/{entity} → Скачать шаблон Excel
3. POST /preview          → Предпросмотр файла
4. POST /validate         → Валидация данных
5. POST /execute          → Импорт в базу данных
```

#### 1.1. Получить список сущностей

**Endpoint:** `GET /api/v1/import/entities`

**Response:**
```json
{
  "success": true,
  "entities": [
    {
      "entity": "budget_categories",
      "display_name": "Категории бюджета",
      "description": "Справочник категорий расходов бюджета (OPEX/CAPEX)",
      "fields_count": 4,
      "required_fields": ["name", "category_type"],
      "allows_update": true,
      "auto_create_related": false
    },
    ...
  ]
}
```

#### 1.2. Скачать шаблон

**Endpoint:** `GET /api/v1/import/template/{entity_type}`

**Parameters:**
- `entity_type` (path) - тип сущности (например, `employees`)
- `language` (query) - язык шаблона: `ru` (по умолчанию) или `en`
- `include_examples` (query) - включить примеры данных (по умолчанию: `true`)
- `include_instructions` (query) - включить лист с инструкциями (по умолчанию: `true`)

**Пример:**
```bash
curl -X GET "http://localhost:8000/api/v1/import/template/employees?language=ru" \
  -H "Authorization: Bearer $TOKEN" \
  -o employees_template.xlsx
```

**Response:** Excel файл с форматированным шаблоном

#### 1.3. Предпросмотр файла

**Endpoint:** `POST /api/v1/import/preview`

**Form Data:**
- `entity_type` - тип сущности
- `file` - Excel файл
- `sheet_name` (optional) - название или индекс листа
- `header_row` (optional) - номер строки с заголовками (по умолчанию: 0)

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx"
```

**Response:**
```json
{
  "success": true,
  "entity_type": "employees",
  "entity_display_name": "Сотрудники",
  "file_info": {
    "sheet_names": ["Sheet1"],
    "selected_sheet": "Sheet1",
    "total_rows": 50,
    "total_columns": 7
  },
  "columns": [
    {
      "name": "ФИО",
      "detected_type": "string",
      "sample_values": ["Иванов Иван Иванович", "Петров Петр Петрович"]
    },
    ...
  ],
  "suggested_mapping": {
    "ФИО": "full_name",
    "Должность": "position",
    "Оклад": "base_salary"
  },
  "required_fields": ["full_name", "position", "base_salary"],
  "preview_rows": [...]
}
```

#### 1.4. Валидация данных

**Endpoint:** `POST /api/v1/import/validate`

**Form Data:**
- `entity_type` - тип сущности
- `file` - Excel файл
- `column_mapping` - JSON маппинг колонок (формат: `{"Excel Column": "field_name"}`)
- `sheet_name` (optional)
- `header_row` (optional)

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/v1/import/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}'
```

**Response:**
```json
{
  "success": true,
  "is_valid": true,
  "total_rows": 50,
  "validation_summary": {
    "errors": 2,
    "warnings": 5,
    "valid_rows": 48
  },
  "validation_messages": [
    {
      "row": 15,
      "column": "base_salary",
      "severity": "error",
      "message": "Значение должно быть больше 0",
      "value": -1000
    },
    {
      "row": 23,
      "column": "email",
      "severity": "warning",
      "message": "Некорректный формат email",
      "value": "invalid-email"
    }
  ],
  "preview_data": [...]
}
```

#### 1.5. Выполнить импорт

**Endpoint:** `POST /api/v1/import/execute`

**Form Data:**
- `entity_type` - тип сущности
- `file` - Excel файл
- `column_mapping` - JSON маппинг колонок
- `sheet_name` (optional)
- `header_row` (optional)
- `skip_errors` (optional) - пропустить строки с ошибками (по умолчанию: `false`)
- `dry_run` (optional) - только валидация, не сохранять (по умолчанию: `false`)

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}' \
  -F "skip_errors=true"
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_processed": 50,
    "created": 45,
    "updated": 3,
    "skipped": 2,
    "errors": 2
  },
  "errors": [
    {
      "row": 15,
      "error": "base_salary: значение должно быть больше 0"
    }
  ]
}
```

---

### 2. External API (JSON/CSV с токенами)

**Базовый URL:** `http://localhost:8000/api/v1/external`

**Аутентификация:** API Token в заголовке `Authorization: Bearer <api_token>`

#### Создание API токена

1. Войдите в веб-интерфейс
2. Перейдите в раздел **"API Tokens"**
3. Создайте новый токен с нужными правами:
   - **READ** - чтение и экспорт данных
   - **WRITE** - импорт и изменение данных

#### 2.1. Экспорт данных

**Доступные endpoints:**

```bash
GET /api/v1/external/export/expenses
GET /api/v1/external/export/revenue-actuals
GET /api/v1/external/export/budget-plans
GET /api/v1/external/export/employees
```

**Parameters:**
- `year` (optional) - фильтр по году
- `month` (optional) - фильтр по месяцу
- `format` (optional) - формат: `json` (по умолчанию) или `csv`

**Пример (JSON):**
```bash
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025&month=1" \
  -H "Authorization: Bearer <api_token>"
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "amount": 50000.00,
      "category_id": 1,
      "contractor_id": 5,
      "organization_id": 2,
      "description": "Закупка оборудования",
      "request_date": "2025-01-15",
      "payment_date": "2025-01-20",
      "status": "PAID",
      "department_id": 1
    },
    ...
  ],
  "count": 15
}
```

**Пример (CSV):**
```bash
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?format=csv" \
  -H "Authorization: Bearer <api_token>" \
  -o expenses.csv
```

#### 2.2. Импорт данных

**Доступные endpoints:**

```bash
POST /api/v1/external/import/expenses
POST /api/v1/external/import/revenue-actuals
POST /api/v1/external/import/contractors
POST /api/v1/external/import/organizations
POST /api/v1/external/import/budget-categories
POST /api/v1/external/import/payroll-plans
```

**Формат запроса:** JSON массив объектов

**Пример (импорт расходов):**
```bash
curl -X POST "http://localhost:8000/api/v1/external/import/expenses" \
  -H "Authorization: Bearer <api_token>" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "amount": 10000.00,
      "category_id": 1,
      "contractor_id": 5,
      "organization_id": 2,
      "description": "Оплата услуг",
      "request_date": "2025-01-15",
      "status": "DRAFT"
    },
    {
      "amount": 25000.00,
      "category_id": 2,
      "contractor_id": 3,
      "organization_id": 2,
      "description": "Закупка материалов",
      "request_date": "2025-01-16",
      "status": "APPROVED"
    }
  ]'
```

**Response:**
```json
{
  "success": true,
  "created_count": 2,
  "updated_count": 0,
  "error_count": 0,
  "errors": []
}
```

**Пример (импорт контрагентов):**
```bash
curl -X POST "http://localhost:8000/api/v1/external/import/contractors" \
  -H "Authorization: Bearer <api_token>" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "ООО Поставщик",
      "inn": "1234567890",
      "contact_person": "Иванов И.И.",
      "email": "contact@supplier.ru",
      "phone": "+7 (495) 123-45-67"
    }
  ]'
```

#### 2.3. Справочные данные

Получение ID для связанных сущностей:

```bash
# Категории бюджета
GET /api/v1/external/reference/categories

# Контрагенты
GET /api/v1/external/reference/contractors

# Организации
GET /api/v1/external/reference/organizations

# Потоки доходов
GET /api/v1/external/reference/revenue-streams

# Категории доходов
GET /api/v1/external/reference/revenue-categories
```

**Пример:**
```bash
curl -X GET "http://localhost:8000/api/v1/external/reference/categories" \
  -H "Authorization: Bearer <api_token>"
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Оборудование",
      "category_type": "CAPEX",
      "department_id": 1
    },
    {
      "id": 2,
      "name": "Лицензии",
      "category_type": "OPEX",
      "department_id": 1
    }
  ]
}
```

---

## Поддерживаемые сущности

### Справочники (References)

| Сущность | Unified Import | External API | Описание |
|----------|----------------|--------------|----------|
| `budget_categories` | ✅ | ✅ | Категории бюджета (OPEX/CAPEX) |
| `contractors` | ✅ | ✅ | Контрагенты и поставщики |
| `organizations` | ✅ | ✅ | Внутренние организации |
| `employees` | ✅ | ✅ (export) | Сотрудники |
| `revenue_streams` | ✅ | ✅ (reference) | Потоки доходов |
| `revenue_categories` | ✅ | ✅ (reference) | Категории доходов |

### Транзакционные данные

| Сущность | Unified Import | External API | Описание |
|----------|----------------|--------------|----------|
| `expenses` | ✅ | ✅ | Расходы и заявки на оплату |
| `budget_plans` | ✅ | ✅ (export) | План бюджета |
| `budget_plan_details` | ✅ | ❌ | Детальный план бюджета с версиями |
| `payroll_plans` | ✅ | ✅ | План ФОТ |
| `revenue_actuals` | ❌ | ✅ | Фактические доходы |
| `revenue_plan_details` | ✅ | ❌ | Детальный план доходов |

---

## Примеры использования

### Сценарий 1: Импорт сотрудников через Excel

```bash
# 1. Скачать шаблон
curl -X GET "http://localhost:8000/api/v1/import/template/employees" \
  -H "Authorization: Bearer $TOKEN" \
  -o employees_template.xlsx

# 2. Заполнить шаблон в Excel
# ФИО                      | Должность      | Оклад    | Дата приема
# Иванов Иван Иванович     | Разработчик    | 150000   | 2024-01-15
# Петрова Мария Сергеевна  | Аналитик       | 120000   | 2024-02-01

# 3. Предпросмотр
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx"

# 4. Валидация
curl -X POST "http://localhost:8000/api/v1/import/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary","Дата приема":"hire_date"}'

# 5. Импорт
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary","Дата приема":"hire_date"}'
```

### Сценарий 2: Автоматическая загрузка расходов из внешней системы

```bash
#!/bin/bash
API_TOKEN="your_api_token_here"
API_URL="http://localhost:8000/api/v1/external"

# 1. Получить справочные данные
CATEGORIES=$(curl -s -X GET "$API_URL/reference/categories" \
  -H "Authorization: Bearer $API_TOKEN")

# 2. Найти ID нужной категории
CATEGORY_ID=$(echo $CATEGORIES | jq -r '.data[] | select(.name=="Лицензии") | .id')

# 3. Импортировать расходы
curl -X POST "$API_URL/import/expenses" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[
    {
      \"amount\": 50000.00,
      \"category_id\": $CATEGORY_ID,
      \"contractor_id\": 1,
      \"organization_id\": 1,
      \"description\": \"Microsoft 365 подписка\",
      \"request_date\": \"$(date +%Y-%m-%d)\",
      \"status\": \"PENDING\"
    }
  ]"
```

### Сценарий 3: Массовый импорт категорий бюджета

```bash
# Подготовить данные в JSON
cat > budget_categories.json <<EOF
[
  {"name": "Оборудование", "category_type": "CAPEX", "description": "Закупка оборудования"},
  {"name": "Лицензии", "category_type": "OPEX", "description": "ПО и лицензии"},
  {"name": "Обучение", "category_type": "OPEX", "description": "Обучение сотрудников"},
  {"name": "Серверы", "category_type": "CAPEX", "description": "Серверное оборудование"}
]
EOF

# Импортировать
curl -X POST "http://localhost:8000/api/v1/external/import/budget-categories" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @budget_categories.json
```

### Сценарий 4: Экспорт и резервное копирование

```bash
#!/bin/bash
# Скрипт для ежедневного экспорта данных

API_TOKEN="your_api_token_here"
BACKUP_DIR="./backups/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

# Экспорт всех сущностей
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?format=csv" \
  -H "Authorization: Bearer $API_TOKEN" \
  -o "$BACKUP_DIR/expenses.csv"

curl -X GET "http://localhost:8000/api/v1/external/export/budget-plans" \
  -H "Authorization: Bearer $API_TOKEN" \
  -o "$BACKUP_DIR/budget_plans.json"

curl -X GET "http://localhost:8000/api/v1/external/export/employees" \
  -H "Authorization: Bearer $API_TOKEN" \
  -o "$BACKUP_DIR/employees.json"

echo "Backup completed: $BACKUP_DIR"
```

---

## Обработка ошибок

### Коды ошибок

| Код | Описание | Решение |
|-----|----------|---------|
| 400 | Неверный формат данных | Проверьте формат JSON/Excel и mapping |
| 401 | Не авторизован | Проверьте токен аутентификации |
| 403 | Нет доступа | Проверьте права токена (READ/WRITE) |
| 404 | Сущность не найдена | Проверьте `entity_type` |
| 422 | Ошибка валидации | Проверьте данные на соответствие схеме |
| 500 | Внутренняя ошибка сервера | Обратитесь к администратору |

### Типичные ошибки

#### 1. Validation errors

```json
{
  "success": false,
  "error": "Validation failed",
  "validation_result": {
    "is_valid": false,
    "validation_messages": [
      {
        "row": 5,
        "column": "amount",
        "severity": "error",
        "message": "Значение должно быть больше 0"
      }
    ]
  }
}
```

**Решение:** Исправьте данные в указанных строках

#### 2. Missing required fields

```json
{
  "success": false,
  "error": "Missing required fields: ['name', 'category_type']"
}
```

**Решение:** Добавьте обязательные поля в column_mapping

#### 3. Duplicate keys

```json
{
  "success": true,
  "created_count": 8,
  "updated_count": 2,
  "error_count": 1,
  "errors": [
    {
      "index": 5,
      "error": "Duplicate entry for INN: 1234567890",
      "data": {...}
    }
  ]
}
```

**Решение:** При `allow_update=true` дубликаты обновляются, иначе - пропускаются

### Best Practices

1. **Всегда используйте preview и validate** перед execute
2. **Используйте skip_errors=true** для пропуска проблемных строк
3. **Проверяйте validation_messages** для понимания проблем
4. **Используйте dry_run=true** для тестирования без изменений
5. **Загружайте данные батчами** (по 100-1000 записей)
6. **Сохраняйте column_mapping** для повторного использования

---

## Swagger Documentation

Полная интерактивная документация доступна по адресу:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Техническая поддержка

По вопросам работы API обращайтесь:
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@example.com

**Версия документа:** 1.0
**Дата обновления:** 2025-01-04
