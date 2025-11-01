# Universal Import System

## Обзор

Универсальная система импорта данных с поддержкой:
- ✅ **Динамический парсинг** - автоопределение типов данных
- ✅ **Гибкий маппинг колонок** - пользователь сам выбирает соответствие
- ✅ **Предварительный просмотр** - валидация перед импортом
- ✅ **Множество форматов** - поддержка дат, чисел, булевых значений
- ✅ **Шаблоны Excel** - красиво оформленные с примерами
- ✅ **Мультиязычность** - русский и английский интерфейсы
- ✅ **Автосоздание связей** - автоматическое создание контрагентов, категорий
- ✅ **Детальная валидация** - ошибки и предупреждения с номерами строк

## Архитектура

### Компоненты

1. **DynamicImportService** (`app/services/dynamic_import_service.py`)
   - Чтение Excel файлов
   - Автоопределение типов данных
   - Гибкий маппинг колонок
   - Валидация данных

2. **ImportConfigManager** (`app/services/import_config_manager.py`)
   - Загрузка конфигураций из JSON
   - Управление правилами валидации
   - Метаданные для каждой сущности

3. **UnifiedImportService** (`app/services/unified_import_service.py`)
   - Координация всех компонентов
   - Бизнес-логика импорта
   - Взаимодействие с базой данных

4. **TemplateGenerator** (`app/services/template_generator.py`)
   - Генерация Excel шаблонов
   - Форматирование и стилизация
   - Примеры и инструкции

5. **API Endpoints** (`app/api/v1/unified_import.py`)
   - RESTful интерфейс
   - Загрузка файлов
   - Скачивание шаблонов

### Конфигурации

Конфигурации хранятся в `/backend/app/import_configs/*.json`:

- `categories.json` - Бюджетные категории
- `contractors.json` - Контрагенты
- `employees.json` - Сотрудники
- `payroll_plans.json` - Планы по зарплате
- `expenses.json` - Расходы

## API Endpoints

### 1. Получить доступные сущности

```http
GET /api/v1/import/entities
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "success": true,
  "entities": [
    {
      "entity": "budget_categories",
      "display_name": "Бюджетные категории",
      "description": "Импорт категорий расходов (OPEX/CAPEX)",
      "fields_count": 4,
      "required_fields": ["name", "type"],
      "allows_update": true,
      "auto_create_related": false
    }
  ]
}
```

### 2. Предварительный просмотр

```http
POST /api/v1/import/preview
Authorization: Bearer <token>
Content-Type: multipart/form-data

entity_type: employees
file: <Excel file>
sheet_name: Данные (optional)
header_row: 0 (optional)
```

**Ответ:**
```json
{
  "success": true,
  "entity_type": "employees",
  "entity_display_name": "Сотрудники",
  "file_info": {
    "sheet_names": ["Данные", "Инструкция"],
    "selected_sheet": "Данные",
    "total_rows": 150,
    "total_columns": 6
  },
  "columns": [
    {
      "index": 0,
      "name": "ФИО",
      "detected_type": "string",
      "sample_values": ["Иванов Иван", "Петрова Мария"],
      "null_count": 0,
      "unique_count": 150,
      "total_count": 150,
      "completeness": 100
    }
  ],
  "preview_rows": [
    {
      "_row_number": 1,
      "ФИО": "Иванов Иван Иванович",
      "Должность": "Системный администратор",
      "Оклад": 80000
    }
  ],
  "suggested_mapping": {
    "full_name": "ФИО",
    "position": "Должность",
    "base_salary": "Оклад"
  },
  "required_fields": ["full_name", "position", "base_salary"],
  "config_fields": [...]
}
```

### 3. Валидация данных

```http
POST /api/v1/import/validate
Authorization: Bearer <token>
Content-Type: multipart/form-data

entity_type: employees
file: <Excel file>
column_mapping: {"ФИО": "full_name", "Должность": "position"}
sheet_name: Данные (optional)
header_row: 0 (optional)
```

**Ответ:**
```json
{
  "success": true,
  "is_valid": false,
  "total_rows": 150,
  "validation_summary": {
    "errors": 5,
    "warnings": 12,
    "valid_rows": 145
  },
  "validation_messages": [
    {
      "row": 45,
      "column": "base_salary",
      "severity": "error",
      "message": "Field 'base_salary' is required",
      "value": null
    },
    {
      "row": 78,
      "column": "full_name",
      "severity": "warning",
      "message": "Employee 'Сидоров С.С.' not found in your department",
      "value": "Сидоров С.С."
    }
  ],
  "preview_data": [...]
}
```

### 4. Выполнить импорт

```http
POST /api/v1/import/execute
Authorization: Bearer <token>
Content-Type: multipart/form-data

entity_type: employees
file: <Excel file>
column_mapping: {"ФИО": "full_name", "Должность": "position"}
sheet_name: Данные (optional)
header_row: 0 (optional)
skip_errors: false (optional)
dry_run: false (optional)
```

**Параметры:**
- `skip_errors`: Пропустить строки с ошибками и импортировать только валидные
- `dry_run`: Только валидация, без сохранения в БД

**Ответ:**
```json
{
  "success": true,
  "statistics": {
    "total_processed": 150,
    "created": 120,
    "updated": 25,
    "skipped": 5,
    "errors": 5
  },
  "errors": [
    {
      "row": 45,
      "error": "Employee with this name already exists"
    }
  ]
}
```

### 5. Скачать шаблон

```http
GET /api/v1/import/template/{entity_type}?language=ru&include_examples=true&include_instructions=true
Authorization: Bearer <token>
```

**Параметры:**
- `entity_type`: Тип сущности (employees, contractors, etc.)
- `language`: Язык (ru/en)
- `include_examples`: Включить примеры (true/false)
- `include_instructions`: Включить лист с инструкциями (true/false)

**Ответ:** Excel файл

## Типы данных

### Автоопределяемые типы

- `STRING` - Текст
- `INTEGER` - Целое число
- `DECIMAL` - Десятичное число
- `BOOLEAN` - Да/Нет
- `DATE` - Дата
- `DATETIME` - Дата и время
- `ENUM` - Выбор из списка

### Форматы дат

Поддерживаются форматы:
- `31.12.2024` (DD.MM.YYYY)
- `31/12/2024` (DD/MM/YYYY)
- `2024-12-31` (YYYY-MM-DD)
- `31-12-2024` (DD-MM-YYYY)
- `31 Dec 2024`
- `31 December 2024`

### Булевые значения

Распознаются значения:
- **True**: да, yes, true, 1, y, т, истина, +, активен, active, enabled
- **False**: нет, no, false, 0, n, ф, ложь, -, неактивен, inactive, disabled

## Примеры использования

### Python (httpx)

```python
import httpx
import json

# Авторизация
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

# 1. Получить доступные сущности
response = httpx.get(
    "http://localhost:8000/api/v1/import/entities",
    headers=headers
)
entities = response.json()

# 2. Предпросмотр файла
with open("employees.xlsx", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/import/preview",
        headers=headers,
        data={"entity_type": "employees"},
        files={"file": f}
    )
preview = response.json()

# 3. Валидация
column_mapping = {
    "ФИО": "full_name",
    "Должность": "position",
    "Оклад": "base_salary"
}

with open("employees.xlsx", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/import/validate",
        headers=headers,
        data={
            "entity_type": "employees",
            "column_mapping": json.dumps(column_mapping)
        },
        files={"file": f}
    )
validation = response.json()

# 4. Импорт
if validation["is_valid"]:
    with open("employees.xlsx", "rb") as f:
        response = httpx.post(
            "http://localhost:8000/api/v1/import/execute",
            headers=headers,
            data={
                "entity_type": "employees",
                "column_mapping": json.dumps(column_mapping),
                "skip_errors": "false",
                "dry_run": "false"
            },
            files={"file": f}
        )
    result = response.json()
    print(f"Created: {result['statistics']['created']}")
    print(f"Updated: {result['statistics']['updated']}")

# 5. Скачать шаблон
response = httpx.get(
    "http://localhost:8000/api/v1/import/template/employees",
    headers=headers,
    params={"language": "ru", "include_examples": "true"}
)
with open("template_employees.xlsx", "wb") as f:
    f.write(response.content)
```

### cURL

```bash
# Предпросмотр
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx"

# Скачать шаблон
curl -X GET "http://localhost:8000/api/v1/import/template/employees?language=ru" \
  -H "Authorization: Bearer $TOKEN" \
  -o template.xlsx
```

## Добавление новой сущности

### 1. Создать конфигурацию

Создайте файл `backend/app/import_configs/new_entity.json`:

```json
{
  "entity": "new_entities",
  "display_name": {
    "ru": "Новые сущности",
    "en": "New Entities"
  },
  "description": {
    "ru": "Описание импорта",
    "en": "Import description"
  },
  "fields": [
    {
      "name": "name",
      "display_name": {"ru": "Название", "en": "Name"},
      "type": "string",
      "required": true,
      "min_length": 2,
      "max_length": 255,
      "aliases": ["название", "name", "наименование"]
    },
    {
      "name": "amount",
      "display_name": {"ru": "Сумма", "en": "Amount"},
      "type": "decimal",
      "required": true,
      "min": 0,
      "aliases": ["сумма", "amount"]
    }
  ],
  "validation_rules": {
    "cross_field": [],
    "business_rules": []
  },
  "import_options": {
    "allow_update": true,
    "update_key": "name",
    "auto_create_related": false,
    "skip_duplicates": false,
    "batch_size": 100
  }
}
```

### 2. Добавить модель в UnifiedImportService

В `unified_import_service.py` добавьте:

```python
ENTITY_MODELS = {
    ...
    "new_entities": NewEntity,
}
```

### 3. (Опционально) Добавить примеры в TemplateGenerator

В `template_generator.py` добавьте примеры в `_get_example_rows`.

### 4. Готово!

Система автоматически подхватит новую конфигурацию.

## Особенности

### Multi-Tenancy

- Все импорты автоматически привязываются к `department_id` текущего пользователя
- USER видит только свой департамент
- MANAGER/ADMIN могут импортировать для любого департамента

### Автосоздание связанных сущностей

Для полей с `"auto_create": true` система автоматически создаст связанные записи:

```json
{
  "name": "contractor_name",
  "lookup_entity": "contractors",
  "lookup_field": "name",
  "auto_create": true
}
```

### Обновление существующих записей

Если `"allow_update": true`, система найдет существующие записи по `update_key` и обновит их.

### Валидация

- **Обязательные поля** - проверка на null
- **Типы данных** - автоматическое преобразование
- **Диапазоны** - min/max для чисел
- **Длина** - min_length/max_length для строк
- **Регулярные выражения** - pattern для сложных форматов
- **Enum** - проверка на список допустимых значений
- **Бизнес-правила** - кастомная логика (уникальность, связи)

## Производительность

- **Batch processing** - импорт пакетами (по умолчанию 100 записей)
- **Предпросмотр** - ограничен 100 строками для быстрого анализа
- **Streaming** - для больших файлов используется потоковое чтение
- **Индексы** - все lookup-поля должны иметь индексы в БД

## Безопасность

- ✅ JWT аутентификация обязательна
- ✅ Multi-tenancy изоляция
- ✅ Валидация типов файлов (только .xlsx, .xls)
- ✅ Лимит размера файла (10MB)
- ✅ SQL injection защита (SQLAlchemy ORM)
- ✅ Rate limiting применяется

## Troubleshooting

### Файл не загружается

Проверьте:
- Формат файла (.xlsx или .xls)
- Размер файла (< 10MB)
- Валидный JWT token

### Неправильное определение типа

Используйте маппинг вручную через `column_mapping`.

### Ошибки валидации

Проверьте:
- Формат данных (даты, числа)
- Обязательные поля заполнены
- Связанные сущности существуют

### Дубликаты при импорте

Установите `"allow_update": true` и укажите `"update_key"` в конфигурации.

## Будущие улучшения

- [ ] Frontend UI для визуального маппинга
- [ ] Прогресс-бар для больших импортов
- [ ] Экспорт валидационных ошибок в Excel
- [ ] Поддержка CSV формата
- [ ] Scheduled imports (cron)
- [ ] Import templates with formulas
- [ ] Rollback mechanism для импортов
- [ ] Audit trail для всех импортов
