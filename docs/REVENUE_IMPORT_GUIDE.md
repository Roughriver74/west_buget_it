# Revenue Import Guide

## Обзор

Revenue модуль полностью поддерживает Universal Import System для импорта данных из Excel.

## Поддерживаемые сущности

- ✅ **revenue_plan_details** - Детальное планирование доходов (12 месяцев)
- ℹ️ revenue_streams - Используйте UI для создания (поддержка иерархии)
- ℹ️ revenue_categories - Используйте UI для создания (поддержка иерархии)

## Быстрый старт

### 1. Скачайте шаблон

```bash
# Получите токен авторизации
TOKEN="your_jwt_token_here"

# Скачайте шаблон для revenue_plan_details
curl -X GET "http://localhost:8000/api/v1/import/template/revenue_plan_details?language=ru" \
  -H "Authorization: Bearer $TOKEN" \
  -o revenue_plan_details_template.xlsx
```

### 2. Заполните шаблон

Шаблон содержит следующие колонки:
- **ID версии плана** (version_id) - обязательно
- **Поток доходов** (revenue_stream_name) - опционально
- **Категория доходов** (revenue_category_name) - опционально
- **Январь - Декабрь** (month_01 - month_12) - 12 месячных колонок

**Требования:**
- Хотя бы один из: revenue_stream_name или revenue_category_name должен быть указан
- Месячные значения >= 0
- Сумма по всем месяцам рассчитывается автоматически

### 3. Предпросмотр файла

```bash
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=revenue_plan_details" \
  -F "file=@revenue_data.xlsx"
```

**Ответ:**
```json
{
  "success": true,
  "entity_type": "revenue_plan_details",
  "file_info": {
    "total_rows": 50,
    "total_columns": 15
  },
  "columns": [...],
  "suggested_mapping": {
    "version_id": "ID версии",
    "revenue_stream_name": "Поток доходов",
    "month_01": "Январь",
    ...
  }
}
```

### 4. Валидация данных

```bash
# Создайте маппинг колонок
MAPPING='{
  "ID версии": "version_id",
  "Поток доходов": "revenue_stream_name",
  "Январь": "month_01",
  "Февраль": "month_02",
  "Март": "month_03",
  "Апрель": "month_04",
  "Май": "month_05",
  "Июнь": "month_06",
  "Июль": "month_07",
  "Август": "month_08",
  "Сентябрь": "month_09",
  "Октябрь": "month_10",
  "Ноябрь": "month_11",
  "Декабрь": "month_12"
}'

curl -X POST "http://localhost:8000/api/v1/import/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=revenue_plan_details" \
  -F "column_mapping=$MAPPING" \
  -F "file=@revenue_data.xlsx"
```

**Ответ:**
```json
{
  "success": true,
  "is_valid": true,
  "total_rows": 50,
  "validation_summary": {
    "errors": 0,
    "warnings": 2,
    "valid_rows": 50
  },
  "validation_messages": [...]
}
```

### 5. Выполнить импорт

```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=revenue_plan_details" \
  -F "column_mapping=$MAPPING" \
  -F "file=@revenue_data.xlsx" \
  -F "skip_errors=false"
```

**Ответ:**
```json
{
  "success": true,
  "statistics": {
    "total_processed": 50,
    "created": 45,
    "updated": 5,
    "skipped": 0,
    "errors": 0
  }
}
```

## Python скрипт для импорта

```python
#!/usr/bin/env python3
"""
Revenue Import Script
Imports revenue plan details from Excel using Universal Import System
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"  # Change this
PASSWORD = "admin"  # Change this

def get_token(username: str, password: str) -> str:
    """Get JWT token"""
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def import_revenue_details(
    token: str,
    excel_file: str,
    version_id: int
):
    """Import revenue plan details from Excel"""

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Preview
    print("Step 1: Previewing file...")
    with open(excel_file, "rb") as f:
        response = requests.post(
            f"{API_URL}/import/preview",
            headers=headers,
            data={"entity_type": "revenue_plan_details"},
            files={"file": f}
        )

    if not response.ok:
        print(f"Preview failed: {response.text}")
        return False

    preview = response.json()
    print(f"✓ File has {preview['file_info']['total_rows']} rows, {preview['file_info']['total_columns']} columns")

    # Use suggested mapping
    suggested = preview["suggested_mapping"]
    print(f"✓ Auto-detected {len(suggested)} field mappings")

    # Step 2: Validate
    print("\nStep 2: Validating data...")
    column_mapping = {v: k for k, v in suggested.items() if v}

    with open(excel_file, "rb") as f:
        response = requests.post(
            f"{API_URL}/import/validate",
            headers=headers,
            data={
                "entity_type": "revenue_plan_details",
                "column_mapping": json.dumps(column_mapping)
            },
            files={"file": f}
        )

    if not response.ok:
        print(f"Validation failed: {response.text}")
        return False

    validation = response.json()
    summary = validation["validation_summary"]
    print(f"✓ Validation complete:")
    print(f"  - Valid rows: {summary['valid_rows']}")
    print(f"  - Errors: {summary['errors']}")
    print(f"  - Warnings: {summary['warnings']}")

    if summary['errors'] > 0:
        print("\nErrors found:")
        for msg in validation['validation_messages'][:10]:
            if msg['severity'] == 'error':
                print(f"  Row {msg['row']}: {msg['message']}")

        answer = input("\nContinue with valid rows only? (y/n): ")
        if answer.lower() != 'y':
            return False

    # Step 3: Execute import
    print("\nStep 3: Executing import...")
    with open(excel_file, "rb") as f:
        response = requests.post(
            f"{API_URL}/import/execute",
            headers=headers,
            data={
                "entity_type": "revenue_plan_details",
                "column_mapping": json.dumps(column_mapping),
                "skip_errors": "true" if summary['errors'] > 0 else "false"
            },
            files={"file": f}
        )

    if not response.ok:
        print(f"Import failed: {response.text}")
        return False

    result = response.json()
    stats = result["statistics"]
    print(f"\n✓ Import complete!")
    print(f"  - Created: {stats['created']}")
    print(f"  - Updated: {stats['updated']}")
    print(f"  - Skipped: {stats['skipped']}")
    print(f"  - Errors: {stats['errors']}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python import_revenue.py <excel_file> <version_id>")
        sys.exit(1)

    excel_file = sys.argv[1]
    version_id = int(sys.argv[2])

    if not Path(excel_file).exists():
        print(f"Error: File '{excel_file}' not found")
        sys.exit(1)

    print("Revenue Plan Details Import")
    print(f"File: {excel_file}")
    print(f"Version ID: {version_id}")
    print()

    # Get token
    print("Authenticating...")
    token = get_token(USERNAME, PASSWORD)
    print("✓ Authenticated")
    print()

    # Import
    success = import_revenue_details(token, excel_file, version_id)

    sys.exit(0 if success else 1)
```

## Использование скрипта

```bash
# Сохраните скрипт как import_revenue.py
chmod +x import_revenue.py

# Запустите импорт
python import_revenue.py revenue_data.xlsx 1

# Где:
#   - revenue_data.xlsx - путь к Excel файлу
#   - 1 - ID версии плана доходов
```

## Особенности импорта Revenue

### Автоматический расчет total

Поле `total` рассчитывается автоматически как сумма всех 12 месяцев. Не указывайте его в Excel файле.

### Обновление существующих записей

Импорт поддерживает обновление по ключу `[version_id, revenue_stream_name, revenue_category_name]`.

Если запись с таким ключом уже существует, она будет обновлена новыми значениями.

### Валидация

**Проверки при импорте:**
- ✅ Version ID существует и в статусе DRAFT
- ✅ Revenue stream/category существуют (если указаны)
- ✅ Хотя бы один из stream/category указан
- ✅ Месячные значения >= 0
- ✅ Department ID совпадает

### Batch обработка

Импорт обрабатывает данные пакетами по 50 записей для оптимальной производительности.

## Применение коэффициентов сезонности

После импорта можно применить коэффициенты сезонности для автораспределения годового бюджета:

```python
import requests

token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

# Применить коэффициенты сезонности
response = requests.post(
    f"{API_URL}/revenue/plan-details/apply-seasonality",
    headers=headers,
    json={
        "detail_id": 123,                      # ID детали плана
        "seasonality_coefficient_id": 1,        # ID коэффициента сезонности
        "annual_target": 1200000                # Годовая цель (руб)
    }
)

result = response.json()
print(f"Applied seasonality to detail {result['id']}")
print(f"Total: {result['total']}")
```

**Алгоритм:**
- Формула: `month_value = annual_target * (coefficient / 12)`
- Пример: Годовая цель 1,200,000 руб, коэффициент января = 1.2
- Результат: Январь = 1,200,000 * (1.2 / 12) = 120,000 руб

## Troubleshooting

### Ошибка: "Version not found"

Убедитесь, что version_id существует и принадлежит вашему департаменту.

```bash
# Проверить существующие версии
curl -X GET "http://localhost:8000/api/v1/revenue/plans/1/versions" \
  -H "Authorization: Bearer $TOKEN"
```

### Ошибка: "Cannot edit version in APPROVED status"

Импорт возможен только для версий в статусе DRAFT. Создайте новую версию для редактирования.

### Ошибка: "Revenue stream not found"

Сначала создайте потоки доходов через UI или API:

```bash
curl -X POST "http://localhost:8000/api/v1/revenue/streams/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "СПБ и ЛО", "stream_type": "REGIONAL"}'
```

## Дополнительная информация

- Полная документация Universal Import System: [UNIVERSAL_IMPORT_SYSTEM.md](UNIVERSAL_IMPORT_SYSTEM.md)
- Конфигурация импорта: `backend/app/import_configs/revenue_plan_details.json`
- API документация: `http://localhost:8000/docs#/Universal%20Import`

## Примеры Excel файлов

Примеры шаблонов доступны через API:

```bash
# RU шаблон
curl -O "http://localhost:8000/api/v1/import/template/revenue_plan_details?language=ru" \
  -H "Authorization: Bearer $TOKEN"

# EN шаблон
curl -O "http://localhost:8000/api/v1/import/template/revenue_plan_details?language=en" \
  -H "Authorization: Bearer $TOKEN"
```
