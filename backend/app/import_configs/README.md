# Import Configurations

Эта директория содержит JSON конфигурации для системы Unified Import API.

## Структура конфигурации

Каждый файл описывает одну сущность (entity) и содержит:

```json
{
  "entity": "entity_name",           // Имя сущности в системе
  "display_name": {                  // Отображаемое имя
    "ru": "Русское название",
    "en": "English name"
  },
  "description": {                   // Описание
    "ru": "Описание на русском",
    "en": "Description in English"
  },
  "fields": [                        // Поля для импорта
    {
      "name": "field_name",          // Имя поля в БД
      "display_name": {
        "ru": "Название поля",
        "en": "Field Name"
      },
      "type": "string|integer|decimal|date|boolean|enum",
      "required": true|false,
      "aliases": ["alias1", "alias2"], // Альтернативные названия колонок
      "lookup_entity": "entity_name",  // Для связанных сущностей
      "lookup_field": "field_name",
      "auto_create": true|false        // Создавать ли связанные сущности
    }
  ],
  "validation_rules": {              // Правила валидации
    "unique_fields": ["field1", "field2"]
  },
  "import_options": {                // Опции импорта
    "allow_update": true|false,      // Разрешить обновление существующих записей
    "update_key": "field_name" | ["field1", "field2"], // Ключ для поиска существующих записей
    "batch_size": 100,               // Размер батча
    "auto_create_related": true|false, // Автоматически создавать связанные сущности
    "calculated_fields": {           // Вычисляемые поля
      "field_name": "expression"
    }
  }
}
```

## Доступные конфигурации

### Справочники (References)
- **budget_categories.json** - Категории бюджета (OPEX/CAPEX)
- **contractors.json** - Контрагенты и поставщики
- **organizations.json** - Внутренние организации
- **employees.json** - Сотрудники
- **revenue_streams.json** - Потоки доходов
- **revenue_categories.json** - Категории доходов

### Транзакционные данные
- **expenses.json** - Расходы и заявки на оплату
- **payroll_plans.json** - План ФОТ (фонд оплаты труда)
- **budget_plans.json** - План бюджета по месяцам
- **budget_plan_details.json** - Детальный план бюджета с версиями
- **revenue_plan_details.json** - Детальный план доходов

## Типы данных

| Тип | Описание | Пример |
|-----|----------|--------|
| `string` | Текстовая строка | "Иванов Иван" |
| `integer` | Целое число | 2025 |
| `decimal` | Десятичное число | 150000.50 |
| `date` | Дата | "2025-01-15" |
| `boolean` | Логическое значение | true/false |
| `enum` | Перечисление | "CAPEX", "OPEX" |

## Примеры использования

### Получить список доступных сущностей

```bash
curl -X GET "http://localhost:8000/api/v1/import/entities" \
  -H "Authorization: Bearer $TOKEN"
```

### Скачать шаблон для сущности

```bash
curl -X GET "http://localhost:8000/api/v1/import/template/employees?language=ru" \
  -H "Authorization: Bearer $TOKEN" \
  -o employees_template.xlsx
```

### Импортировать данные

```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}'
```

## Добавление новой конфигурации

1. Создайте JSON файл с именем сущности (например, `new_entity.json`)
2. Заполните структуру согласно описанию выше
3. Добавьте маппинг модели в `UnifiedImportService.ENTITY_MODELS`
4. Перезапустите сервер

## Валидация конфигураций

Конфигурации автоматически валидируются при загрузке. Проверьте логи сервера на наличие ошибок:

```bash
tail -f backend.log | grep "import_config"
```

## Документация

Полная документация по системе импорта:
- **Подробное руководство:** `docs/API_DATA_IMPORT.md`
- **Быстрый старт (RU):** `docs/DATA_IMPORT_QUICKSTART_RU.md`
- **Swagger UI:** http://localhost:8000/docs

## Поддержка

По вопросам обращайтесь:
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@example.com
