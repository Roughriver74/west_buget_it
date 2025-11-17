# Business Operation Mapping (Маппинг хозяйственных операций)

## Обзор

**Business Operation Mapping** - гибкая система маппинга хозяйственных операций из 1С (`ХозяйственнаяОперация`) на категории бюджета IT Budget Manager.

**Преимущества гибкого подхода:**
- ✅ Настройка маппинга для каждого отдела отдельно
- ✅ Изменение маппинга без изменения кода (через БД)
- ✅ Приоритезация при множественных соответствиях
- ✅ Высокая точность автоматической категоризации (confidence 0.98)
- ✅ Простая настройка через SQL или UI (в будущем)

## Архитектура

### 1. Модель данных (BusinessOperationMapping)

**Таблица**: `business_operation_mappings`

```sql
CREATE TABLE business_operation_mappings (
    id SERIAL PRIMARY KEY,

    -- Хозяйственная операция из 1С
    business_operation VARCHAR(100) NOT NULL,

    -- Связь с категорией бюджета
    category_id INTEGER NOT NULL REFERENCES budget_categories(id),

    -- Приоритет (чем выше - тем важнее)
    priority INTEGER DEFAULT 10,

    -- Уверенность маппинга (0.0-1.0)
    confidence NUMERIC(5,4) DEFAULT 0.98,

    -- Комментарий
    notes TEXT,

    -- Multi-tenancy
    department_id INTEGER NOT NULL REFERENCES departments(id),

    -- System fields
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),

    -- Unique constraint: одна операция -> одна категория в рамках отдела
    CONSTRAINT ix_business_operation_mapping_unique
        UNIQUE (business_operation, department_id, category_id)
);

CREATE INDEX ON business_operation_mappings(business_operation);
CREATE INDEX ON business_operation_mappings(category_id);
CREATE INDEX ON business_operation_mappings(department_id);
CREATE INDEX ON business_operation_mappings(is_active);
```

### 2. Сервис маппинга (BusinessOperationMapper)

**Файл**: `backend/app/services/business_operation_mapper.py`

**Основные методы:**

```python
class BusinessOperationMapper:
    def get_category_by_business_operation(
        self,
        business_operation: str,
        department_id: int
    ) -> Optional[int]:
        """
        Получить ID категории по хозяйственной операции

        Returns:
            category_id или None если не найдено
        """

    def get_confidence_for_mapping(
        self,
        business_operation: str,
        department_id: int
    ) -> float:
        """
        Получить уровень уверенности для маппинга

        Returns:
            Confidence (0.0-1.0, или 0.0 если маппинг не найден)
        """

    def get_all_mappings(self, department_id: int) -> List[Dict]:
        """
        Получить все активные маппинги для отдела
        """
```

**Кэширование**: Сервис использует внутренний кэш для оптимизации запросов к БД.

### 3. Интеграция с классификатором

**Файл**: `backend/app/services/transaction_classifier.py`

**Приоритет маппинга**: `ХозяйственнаяОперация` имеет **наивысший приоритет** (проверяется первым) перед всеми остальными методами классификации:

```python
def classify(
    self,
    payment_purpose: str,
    # ... other params
    business_operation: Optional[str] = None
) -> Tuple[Optional[int], float, str]:

    # 0. HIGHEST PRIORITY: Check business_operation first
    if business_operation:
        category_id = self.business_operation_mapper.get_category_by_business_operation(
            business_operation,
            department_id
        )
        if category_id:
            confidence = self.business_operation_mapper.get_confidence_for_mapping(business_operation)
            return category_id, confidence, f"Маппинг по ХозяйственнаяОперация: '{business_operation}'"

    # 1. Historical data (прошлые назначения)
    # 2. Keyword matching (по назначению платежа)
    # 3. Counterparty matching (по ИНН)
    # ...
```

## Базовые маппинги (примеры)

### Поступления (CREDIT)

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ПоступлениеОплатыОтКлиента`               | Выручка от клиентов           | 100      | 0.98       |
| `ПоступлениеОплатыПоПлатежнойКарте`        | Выручка от клиентов           | 100      | 0.98       |
| `ПоступлениеОтПодотчетногоЛица`            | Возврат подотчетных средств   | 95       | 0.95       |
| `ВозвратОтПоставщика`                      | Возврат от поставщика         | 90       | 0.95       |
| `ПолучениеКредитаЗайма`                    | Получение кредита             | 90       | 0.98       |

### Списания (DEBIT)

#### Зарплата

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ВыплатаЗарплатыНаЛицевыеСчета`            | Зарплата                      | 100      | 0.98       |
| `ВыплатаЗарплатыПоЗарплатномуПроекту`      | Зарплата                      | 100      | 0.98       |
| `ВыплатаЗарплаты`                          | Зарплата                      | 100      | 0.98       |
| `ВыплатаПособий`                           | Пособия и компенсации         | 95       | 0.95       |

#### Налоги

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ПеречислениеВБюджет`                      | Налоги и сборы                | 100      | 0.98       |
| `ПеречислениеНДС`                          | НДС                           | 100      | 0.99       |
| `ПеречислениеНДФЛ`                         | НДФЛ                          | 100      | 0.99       |
| `ПеречислениеСтраховыхВзносов`             | Страховые взносы              | 100      | 0.98       |

#### Закупки

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ОплатаПоставщику`                         | Закупки у поставщиков         | 90       | 0.95       |
| `ПредоплатаПоставщику`                     | Предоплата поставщикам        | 90       | 0.95       |
| `ОплатаТоваровУслуг`                       | Закупки у поставщиков         | 85       | 0.90       |

#### Подотчет

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ВыдачаПодотчетномуЛицу`                   | Выдача подотчетных средств    | 95       | 0.95       |
| `ВыдачаДенежныхСредствВПодотчет`           | Выдача подотчетных средств    | 95       | 0.95       |

#### Кредиты

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ВозвратКредитаЗайма`                      | Возврат кредита               | 95       | 0.98       |
| `УплатаПроцентовПоКредиту`                 | Проценты по кредитам          | 95       | 0.98       |

#### Внутренние переводы

| ХозяйственнаяОперация                                | Категория                  | Priority | Confidence |
|-----------------------------------------------------|----------------------------|----------|------------|
| `ОплатаДенежныхСредствВДругуюОрганизацию`           | Внутренние переводы        | 90       | 0.95       |
| `ПеречислениеВДругуюОрганизацию`                    | Внутренние переводы        | 90       | 0.95       |

#### Комиссии банка

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `КомиссияБанка`                            | Комиссии банка                | 100      | 0.98       |
| `ОплатаБанковскихУслуг`                    | Комиссии банка                | 95       | 0.95       |

#### Прочее

| ХозяйственнаяОперация                      | Категория                     | Priority | Confidence |
|--------------------------------------------|-------------------------------|----------|------------|
| `ПрочееСписание`                           | Прочие расходы                | 50       | 0.70       |
| `ПрочаяОперация`                           | Прочие расходы                | 50       | 0.70       |

## Заполнение начальных маппингов

**Скрипт**: `backend/scripts/seed_business_operation_mappings.py`

### Для конкретного отдела:

```bash
cd backend
python scripts/seed_business_operation_mappings.py --department-id 1
```

### Для всех отделов:

```bash
cd backend
python scripts/seed_business_operation_mappings.py --all-departments
```

### С указанием пользователя (для created_by):

```bash
cd backend
python scripts/seed_business_operation_mappings.py --all-departments --user-id 1
```

**Результат скрипта:**
- ✅ Created: количество созданных маппингов
- ⏭️ Skipped: количество пропущенных (уже существуют)
- ❌ Not found: количество не найденных (категория отсутствует в БД)

**Важно**: Скрипт пытается найти категорию по списку возможных названий (например, для "Зарплата" ищет "Зарплата", "Оплата труда", "ФОТ"). Если категория не найдена, маппинг не создаётся.

## Настройка маппингов через SQL

### Просмотр существующих маппингов

```sql
-- Все маппинги для отдела
SELECT
    m.id,
    m.business_operation,
    c.name AS category_name,
    m.priority,
    m.confidence,
    m.notes
FROM business_operation_mappings m
JOIN budget_categories c ON m.category_id = c.id
WHERE m.department_id = 1
  AND m.is_active = TRUE
ORDER BY m.priority DESC, m.business_operation;
```

### Добавление нового маппинга

```sql
-- Найти ID категории
SELECT id, name FROM budget_categories
WHERE name ILIKE '%Зарплата%'
  AND department_id = 1
  AND is_active = TRUE;

-- Создать маппинг
INSERT INTO business_operation_mappings (
    business_operation,
    category_id,
    priority,
    confidence,
    notes,
    department_id,
    created_by
) VALUES (
    'ВыплатаЗарплаты',
    51,  -- ID категории "Зарплата"
    100,
    0.98,
    'Выплата зарплаты сотрудникам',
    1,   -- department_id
    1    -- user_id (optional)
);
```

### Изменение маппинга

```sql
-- Изменить категорию
UPDATE business_operation_mappings
SET
    category_id = 52,
    notes = 'Обновлённая категория',
    updated_at = NOW()
WHERE business_operation = 'ВыплатаЗарплаты'
  AND department_id = 1;

-- Изменить приоритет
UPDATE business_operation_mappings
SET
    priority = 95,
    updated_at = NOW()
WHERE business_operation = 'ВыплатаПособий'
  AND department_id = 1;
```

### Отключение маппинга

```sql
-- Временно отключить
UPDATE business_operation_mappings
SET is_active = FALSE
WHERE business_operation = 'ПрочаяОперация'
  AND department_id = 1;

-- Включить обратно
UPDATE business_operation_mappings
SET is_active = TRUE
WHERE id = 123;
```

### Удаление маппинга

```sql
-- Удалить конкретный маппинг
DELETE FROM business_operation_mappings
WHERE id = 123;

-- Удалить все маппинги для операции
DELETE FROM business_operation_mappings
WHERE business_operation = 'ПрочаяОперация'
  AND department_id = 1;
```

## Использование в коде

### Получение категории по хозяйственной операции

```python
from app.services.business_operation_mapper import BusinessOperationMapper

mapper = BusinessOperationMapper(db)

# Получить ID категории
category_id = mapper.get_category_by_business_operation(
    business_operation='ВыплатаЗарплаты',
    department_id=1
)

if category_id:
    print(f"Found category: {category_id}")
else:
    print("No mapping found")
```

### Получение уверенности маппинга

```python
confidence = mapper.get_confidence_for_mapping(
    business_operation='ВыплатаЗарплаты',
    department_id=1
)

print(f"Confidence: {confidence}")  # 0.98
```

### Получение всех маппингов для отдела

```python
mappings = mapper.get_all_mappings(department_id=1)

for m in mappings:
    print(f"{m['business_operation']} → {m['category_name']} (priority: {m['priority']}, confidence: {m['confidence']})")
```

### Очистка кэша

```python
# Если изменили маппинги через SQL, нужно очистить кэш
mapper.clear_cache()
```

## Workflow синхронизации с 1С

```
1. ИМПОРТ ИЗ 1С
   ↓
   OData API → BankTransaction1CImporter
   ↓
   Парсинг поля "ХозяйственнаяОперация"
   ↓
   Сохранение в bank_transactions.business_operation

2. АВТОМАТИЧЕСКАЯ КАТЕГОРИЗАЦИЯ
   ↓
   TransactionClassifier.classify()
   ↓
   0️⃣ HIGHEST PRIORITY: Проверка business_operation
   ↓
   BusinessOperationMapper.get_category_by_business_operation()
   ↓
   Найден маппинг?
   │
   ├─ ДА → Назначить category_id, confidence=0.98
   │        Статус: CATEGORIZED (если confidence > 0.9)
   │
   └─ НЕТ → Продолжить другие методы классификации
            1️⃣ Historical data
            2️⃣ Keyword matching
            3️⃣ Counterparty matching

3. РЕЗУЛЬТАТ
   ↓
   Транзакция автоматически категоризирована с высокой уверенностью
```

## Тестирование

### 1. Проверка маппингов в БД

```sql
-- Количество маппингов по отделам
SELECT
    d.name AS department,
    COUNT(*) AS mappings_count
FROM business_operation_mappings m
JOIN departments d ON m.department_id = d.id
WHERE m.is_active = TRUE
GROUP BY d.id, d.name
ORDER BY d.name;

-- Проверка конкретного маппинга
SELECT
    m.business_operation,
    c.name AS category_name,
    m.priority,
    m.confidence
FROM business_operation_mappings m
JOIN budget_categories c ON m.category_id = c.id
WHERE m.business_operation = 'ВыплатаЗарплаты'
  AND m.department_id = 1;
```

### 2. Тест синхронизации с 1С

```bash
# Запустить синхронизацию банковских транзакций
curl -X POST "http://localhost:8000/api/v1/bank-transactions/sync/1c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-11-01",
    "date_to": "2025-11-30",
    "department_id": 1,
    "auto_classify": true
  }'
```

### 3. Проверка результатов категоризации

```sql
-- Транзакции с автоматической категоризацией по business_operation
SELECT
    bt.transaction_date,
    bt.business_operation,
    bt.amount,
    bc.name AS category_name,
    bt.category_confidence,
    bt.status
FROM bank_transactions bt
LEFT JOIN budget_categories bc ON bt.category_id = bc.id
WHERE bt.business_operation IS NOT NULL
  AND bt.category_id IS NOT NULL
  AND bt.category_confidence > 0.95
ORDER BY bt.transaction_date DESC
LIMIT 20;

-- Статистика категоризации
SELECT
    business_operation,
    COUNT(*) AS total_count,
    COUNT(CASE WHEN category_id IS NOT NULL THEN 1 END) AS categorized_count,
    AVG(category_confidence) AS avg_confidence
FROM bank_transactions
WHERE business_operation IS NOT NULL
  AND department_id = 1
GROUP BY business_operation
ORDER BY total_count DESC;
```

## Future Enhancements

### 1. UI для управления маппингами

Планируется создать административный интерфейс для управления маппингами:

- ✅ Просмотр всех маппингов
- ✅ Добавление новых маппингов
- ✅ Редактирование существующих
- ✅ Отключение/включение маппингов
- ✅ Массовые операции

### 2. API endpoints

```python
# GET /api/v1/business-operation-mappings
# Получить все маппинги для отдела

# POST /api/v1/business-operation-mappings
# Создать новый маппинг

# PUT /api/v1/business-operation-mappings/{id}
# Обновить маппинг

# DELETE /api/v1/business-operation-mappings/{id}
# Удалить маппинг
```

### 3. Импорт/экспорт маппингов

Возможность экспортировать и импортировать маппинги между отделами:

```bash
# Export
python scripts/export_mappings.py --department-id 1 --output mappings.json

# Import
python scripts/import_mappings.py --department-id 2 --input mappings.json
```

### 4. Аналитика маппингов

Отчёты о эффективности маппингов:
- Какие операции чаще всего встречаются
- Какие операции не имеют маппинга
- Статистика уверенности категоризации

## Troubleshooting

### Проблема: Маппинг не работает

**Причины:**
1. Категория не существует в БД
2. Маппинг отключен (is_active = FALSE)
3. Неправильный department_id
4. Кэш не обновлён после изменения в БД

**Решение:**
```sql
-- Проверить существование маппинга
SELECT * FROM business_operation_mappings
WHERE business_operation = 'ВыплатаЗарплаты'
  AND department_id = 1;

-- Проверить категорию
SELECT * FROM budget_categories
WHERE id = 51 AND department_id = 1;

-- Очистить кэш (через код)
mapper.clear_cache()
```

### Проблема: Категория не найдена при заполнении

**Причины:**
1. Категория с таким названием отсутствует в БД
2. Категория неактивна (is_active = FALSE)
3. Категория принадлежит другому отделу

**Решение:**
```sql
-- Проверить доступные категории
SELECT id, name, type
FROM budget_categories
WHERE department_id = 1
  AND is_active = TRUE
ORDER BY name;

-- Создать отсутствующую категорию
INSERT INTO budget_categories (name, type, department_id)
VALUES ('Зарплата', 'OPEX', 1);
```

### Проблема: Несколько маппингов для одной операции

**Причины:**
- Разные категории для разных приоритетов

**Решение:**
```sql
-- Найти дубликаты
SELECT
    business_operation,
    department_id,
    COUNT(*) AS count
FROM business_operation_mappings
WHERE is_active = TRUE
GROUP BY business_operation, department_id
HAVING COUNT(*) > 1;

-- Система выберет маппинг с наивысшим приоритетом
-- Или оставить только один:
UPDATE business_operation_mappings
SET is_active = FALSE
WHERE id = 123;  -- ID маппинга с меньшим приоритетом
```

## Заключение

Система маппинга хозяйственных операций обеспечивает:

- ✅ **Высокую точность** автоматической категоризации (98%)
- ✅ **Гибкость** настройки для каждого отдела
- ✅ **Простоту** управления через SQL
- ✅ **Масштабируемость** для новых операций
- ✅ **Производительность** благодаря кэшированию

Эта система значительно сокращает ручную работу при обработке банковских транзакций и повышает качество финансовой отчётности.
