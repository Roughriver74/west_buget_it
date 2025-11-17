# Автоматический импорт маппингов бизнес-операций

## Проблема

При загрузке банковских транзакций из 1С на **продакшен сервере не работает автоматическая категоризация**, хотя на локальной системе работает нормально.

**Причина**: На продакшен сервере отсутствуют маппинги между хозяйственными операциями 1С и категориями бюджета (таблица `business_operation_mappings`).

## Решение

Создан скрипт `backend/scripts/import_default_business_operation_mappings.py`, который автоматически создает стандартные маппинги для типовых операций 1С.

## Что импортирует скрипт

Скрипт создает маппинги для **15 стандартных бизнес-операций 1С**:

### 1. Зарплата и ФОТ (приоритет 100, уверенность 98%)
- `ВыплатаЗарплаты` → ФОТ / Зарплата
- `ВыплатаЗарплатыНаЛицевыеСчета` → ФОТ / Зарплата
- `ВыплатаЗарплатыПоЗарплатномуПроекту` → ФОТ / Зарплата

### 2. Налоги и взносы (приоритет 100, уверенность 98-99%)
- `ПеречислениеНДФЛ` → НДФЛ / Налоги
- `ПеречислениеНДС` → Налог НДС / Налоги
- `ПеречислениеСтраховыхВзносов` → Страховые взносы / Налоги
- `ПеречислениеВБюджет` → Налоги

### 3. Банковские услуги (приоритет 95-100, уверенность 95-98%)
- `КомиссияБанка` → Услуги банка / Банковские услуги
- `ОплатаБанковскихУслуг` → Услуги банка / Банковские услуги

### 4. Поставщики и клиенты (приоритет 100)
- `ОплатаПоставщику` → Поставщики (расход) / Закупки у поставщиков (уверенность 69%)
- `ПоступлениеОплатыОтКлиента` → Покупатели (приход) / Реализация продукции (98%)
- `ПоступлениеОплатыПоПлатежнойКарте` → Покупатели (приход) / Реализация продукции (98%)

### 5. Подотчет (приоритет 95, уверенность 95%)
- `ВыдачаДенежныхСредствВПодотчет` → Подотчет / Хозяйственные расходы
- `ВыдачаПодотчетномуЛицу` → Подотчет / Хозяйственные расходы
- `ПоступлениеОтПодотчетногоЛица` → Подотчет / Хозяйственные расходы

## Как работает скрипт

1. **Поиск категорий**: Для каждой операции ищет соответствующую категорию в базе по названию
2. **Создание маппинга**: Создает связь операция → категория с указанным приоритетом и уверенностью
3. **Пропуск дубликатов**: Не создает маппинги, которые уже существуют
4. **Обновление**: Обновляет приоритет/уверенность, если маппинг уже есть
5. **Мульти-департамент**: Создает маппинги для каждого активного отдела

## Использование

### На продакшен сервере (Docker)

```bash
# 1. SSH на сервер
ssh root@31.129.107.178

# 2. Запустить скрипт внутри контейнера backend
cd /opt/budget-app
docker compose -f docker-compose.prod.yml exec -T backend python scripts/import_default_business_operation_mappings.py

# Или для конкретного отдела
docker compose -f docker-compose.prod.yml exec -T backend python scripts/import_default_business_operation_mappings.py --department-id 8
```

### Локально (venv)

```bash
cd backend
source venv/bin/activate  # macOS/Linux

# Импорт для всех отделов
python scripts/import_default_business_operation_mappings.py

# Только для конкретного отдела
python scripts/import_default_business_operation_mappings.py --department-id 1
```

## Пример вывода

```
============================================================
Import Default Business Operation Mappings
============================================================
Processing 2 department(s)
Default mappings: 15 operations

Processing department: IT Отдел WEST (ID: 8)
  ✓ Found category 'ФОТ' for operation 'ВыплатаЗарплаты'
  + Created mapping: ВыплатаЗарплаты → ФОТ
  ✓ Found category 'НДФЛ' for operation 'ПеречислениеНДФЛ'
  + Created mapping: ПеречислениеНДФЛ → НДФЛ
  ...

Processing department: Финансы (ID: 1)
  ✓ Found category 'Зарплата' for operation 'ВыплатаЗарплаты'
  + Created mapping: ВыплатаЗарплаты → Зарплата
  ...

============================================================
SUMMARY
============================================================
✓ Created:  18
↻ Updated:  0
= Skipped:  3
✗ Errors:   0

✅ Import completed successfully!
```

## Проверка результатов

### Проверить количество маппингов

```bash
# На продакшен сервере
ssh root@31.129.107.178 "docker compose -f /opt/budget-app/docker-compose.prod.yml exec -T db psql -U budget_user -d it_budget_db -c \"SELECT COUNT(*) FROM business_operation_mappings WHERE is_active = true\""

# Локально
docker exec it_budget_db psql -U budget_user -d it_budget_db -c "SELECT COUNT(*) FROM business_operation_mappings WHERE is_active = true"
```

### Посмотреть все маппинги

```sql
SELECT
  bom.business_operation,
  bc.name as category_name,
  bom.priority,
  bom.confidence,
  d.name as department
FROM business_operation_mappings bom
JOIN budget_categories bc ON bom.category_id = bc.id
JOIN departments d ON bom.department_id = d.id
WHERE bom.is_active = true
ORDER BY bom.priority DESC, bom.business_operation;
```

## После импорта

После успешного импорта маппингов:

1. **Автоматическая категоризация заработает** при следующей загрузке транзакций из 1С
2. Транзакции с `ВидОперации` из списка выше будут автоматически получать категорию
3. Уверенность AI будет соответствовать настроенной в маппингах
4. Статус транзакции: `CATEGORIZED` (если уверенность > 90%) или `NEEDS_REVIEW` (если < 90%)

## Добавление новых маппингов

### Через веб-интерфейс (рекомендуется)

1. Открыть страницу `/business-operation-mappings`
2. Нажать "Создать маппинг"
3. Заполнить форму:
   - **Операция**: Название операции из 1С (например: `ОплатаАренды`)
   - **Категория**: Выбрать из списка
   - **Приоритет**: 0-100 (100 = максимальный)
   - **Уверенность**: 0-100% (например: 95)
   - **Примечания**: Описание
4. Сохранить

### Через SQL (для массовых операций)

```sql
INSERT INTO business_operation_mappings
  (business_operation, category_id, department_id, priority, confidence, is_active, created_at)
VALUES
  ('НоваяОперация',
   (SELECT id FROM budget_categories WHERE name = 'Название категории' AND department_id = 8 LIMIT 1),
   8,
   90,
   0.85,
   true,
   NOW()
  );
```

## Troubleshooting

### Скрипт не находит категории

**Проблема**: `⚠ No matching category found for 'ВыплатаЗарплаты'`

**Решение**:
1. Проверить, что категория существует в БД для этого отдела
2. Создать категорию вручную через веб-интерфейс
3. Или изменить список `category_names` в скрипте под ваши названия категорий

### Маппинги не применяются к транзакциям

**Возможные причины**:
1. Маппинг неактивен (`is_active = false`)
2. Название операции в 1С отличается (проверить поле `ВидОперации` в транзакции)
3. Категория неактивна
4. Несоответствие `department_id`

**Проверка**:
```sql
-- Посмотреть реальные операции из транзакций
SELECT DISTINCT operation_type
FROM bank_transactions
WHERE operation_type IS NOT NULL
LIMIT 20;

-- Сравнить с маппингами
SELECT business_operation
FROM business_operation_mappings
WHERE is_active = true;
```

## Связанные документы

- [Business Operation Mapping UI Guide](BUSINESS_OPERATION_MAPPING_UI.md)
- [Business Operation Mapping Technical Docs](BUSINESS_OPERATION_MAPPING.md)
- [Bank Transactions Import Guide](BANK_TRANSACTIONS_IMPORT_GUIDE.md)
- [1C Integration Overview](1C_INTEGRATION.md)

## Changelog

### 2025-11-17
- ✅ Создан скрипт автоматического импорта дефолтных маппингов
- ✅ Добавлены 15 стандартных операций 1С
- ✅ Поддержка мульти-департамента
- ✅ Логирование прогресса и ошибок
