# Быстрый старт: Импорт данных в IT Budget Manager

Краткое руководство по загрузке данных в систему.

## 📋 Два способа импорта

### 🗂️ 1. Excel файлы (Unified Import API)

**Для кого:** Ручная загрузка данных через веб-интерфейс или cURL

**Шаги:**

```bash
# Шаг 1: Получить список доступных сущностей
curl -X GET "http://localhost:8000/api/v1/import/entities" \
  -H "Authorization: Bearer $TOKEN"

# Шаг 2: Скачать шаблон Excel
curl -X GET "http://localhost:8000/api/v1/import/template/employees?language=ru" \
  -H "Authorization: Bearer $TOKEN" \
  -o шаблон_сотрудники.xlsx

# Шаг 3: Заполнить шаблон в Excel и загрузить
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@сотрудники.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}'
```

### 🔌 2. JSON/CSV через API токены (External API)

**Для кого:** Автоматизация, интеграции с внешними системами

**Шаги:**

```bash
# Шаг 1: Создать API токен в веб-интерфейсе (раздел "API Tokens")

# Шаг 2: Импортировать данные в формате JSON
curl -X POST "http://localhost:8000/api/v1/external/import/expenses" \
  -H "Authorization: Bearer <api_token>" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "amount": 50000.00,
      "category_id": 1,
      "contractor_id": 5,
      "organization_id": 2,
      "description": "Оплата услуг",
      "request_date": "2025-01-15",
      "status": "DRAFT"
    }
  ]'
```

## 📦 Поддерживаемые сущности

### Справочники
- ✅ **budget_categories** - Категории бюджета (OPEX/CAPEX)
- ✅ **contractors** - Контрагенты и поставщики
- ✅ **organizations** - Внутренние организации
- ✅ **employees** - Сотрудники
- ✅ **revenue_streams** - Потоки доходов
- ✅ **revenue_categories** - Категории доходов

### Транзакционные данные
- ✅ **expenses** - Расходы и заявки на оплату
- ✅ **budget_plans** - План бюджета
- ✅ **budget_plan_details** - Детальный план бюджета
- ✅ **payroll_plans** - План ФОТ
- ✅ **revenue_actuals** - Фактические доходы
- ✅ **revenue_plan_details** - Детальный план доходов

## 🎯 Примеры для каждой сущности

### Категории бюджета

**Excel (через Unified Import):**
```bash
curl -X GET "http://localhost:8000/api/v1/import/template/budget_categories" \
  -H "Authorization: Bearer $TOKEN" \
  -o категории.xlsx
```

**JSON (через External API):**
```bash
curl -X POST "http://localhost:8000/api/v1/external/import/budget-categories" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "Оборудование",
      "category_type": "CAPEX",
      "description": "Закупка оборудования"
    },
    {
      "name": "Лицензии",
      "category_type": "OPEX",
      "description": "ПО и лицензии"
    }
  ]'
```

### Контрагенты

```bash
curl -X POST "http://localhost:8000/api/v1/external/import/contractors" \
  -H "Authorization: Bearer $API_TOKEN" \
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

### Сотрудники

**Формат Excel:**
| ФИО | Должность | Оклад | Дата приема | Email |
|-----|-----------|-------|-------------|-------|
| Иванов Иван Иванович | Разработчик | 150000 | 2024-01-15 | ivanov@company.ru |
| Петрова Мария | Аналитик | 120000 | 2024-02-01 | petrova@company.ru |

```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@сотрудники.xlsx" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary","Дата приема":"hire_date","Email":"email"}'
```

### Расходы

```bash
curl -X POST "http://localhost:8000/api/v1/external/import/expenses" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "amount": 50000.00,
      "category_id": 1,
      "contractor_id": 5,
      "organization_id": 2,
      "description": "Microsoft 365 подписка",
      "request_date": "2025-01-15",
      "status": "PENDING"
    }
  ]'
```

### План ФОТ

**Формат Excel:**
| Год | Месяц | Сотрудник | Оклад | Тип премии | Премия | Соц. отчисления |
|-----|-------|-----------|-------|------------|--------|-----------------|
| 2025 | 1 | Иванов Иван | 150000 | FIXED | 30000 | 54000 |
| 2025 | 1 | Петрова Мария | 120000 | PERFORMANCE_BASED | 24000 | 43200 |

```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=payroll_plans" \
  -F "file=@фот_план.xlsx" \
  -F 'column_mapping={"Год":"year","Месяц":"month","Сотрудник":"employee_name","Оклад":"base_salary","Тип премии":"bonus_type","Премия":"bonus_amount","Соц. отчисления":"social_contributions"}'
```

### План бюджета

**Формат Excel:**
| Год | Месяц | Категория | Плановая сумма | CAPEX | OPEX |
|-----|-------|-----------|----------------|-------|------|
| 2025 | 1 | Оборудование | 500000 | 500000 | 0 |
| 2025 | 1 | Лицензии | 100000 | 0 | 100000 |

```bash
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=budget_plans" \
  -F "file=@бюджет_план.xlsx" \
  -F 'column_mapping={"Год":"year","Месяц":"month","Категория":"category_name","Плановая сумма":"planned_amount","CAPEX":"capex_planned","OPEX":"opex_planned"}'
```

## 🔍 Проверка и валидация

### Предпросмотр перед импортом

```bash
# Сначала посмотреть, что в файле
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@сотрудники.xlsx"

# Затем проверить валидность
curl -X POST "http://localhost:8000/api/v1/import/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@сотрудники.xlsx" \
  -F 'column_mapping={...}'

# И только потом импортировать
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@сотрудники.xlsx" \
  -F 'column_mapping={...}'
```

## 📤 Экспорт данных

```bash
# Экспорт в JSON
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025" \
  -H "Authorization: Bearer $API_TOKEN"

# Экспорт в CSV
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025&format=csv" \
  -H "Authorization: Bearer $API_TOKEN" \
  -o расходы_2025.csv
```

## 🔐 Аутентификация

### JWT Token (для Unified Import)

```bash
# Получить токен
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Использовать токен
TOKEN="ваш_jwt_token"
curl -H "Authorization: Bearer $TOKEN" ...
```

### API Token (для External API)

1. Войдите в веб-интерфейс
2. Перейдите в **"API Tokens"**
3. Создайте токен с нужными правами:
   - **READ** - для экспорта
   - **WRITE** - для импорта

```bash
API_TOKEN="ваш_api_token"
curl -H "Authorization: Bearer $API_TOKEN" ...
```

## ⚠️ Важные моменты

### Multi-tenancy
- Все данные автоматически привязываются к вашему департаменту
- `department_id` определяется из токена
- Вы видите только данные своего департамента

### Обновление vs Создание
- **Unified Import:** Настраивается в конфигурации (`allow_update`, `update_key`)
- **External API:** Автоматически обновляет по уникальному ключу (INN, name, и т.д.)

### Пропуск ошибок
```bash
# Пропустить строки с ошибками
curl ... -F "skip_errors=true"

# Только валидация, без сохранения
curl ... -F "dry_run=true"
```

## 🆘 Помощь

### Swagger документация
http://localhost:8000/docs

### Полная документация
См. файл `docs/API_DATA_IMPORT.md`

### Примеры скриптов
См. директорию `scripts/`

### Техподдержка
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@example.com

---

**Версия:** 1.0
**Дата:** 2025-01-04
