# Invoice to 1C Integration - Testing Guide

## Быстрый старт

### 1. Проверка подключения к 1С

```bash
cd backend
python scripts/test_invoice_to_1c.py --test-connection
```

**Что проверяется:**
- ✅ Доступность OData API 1C
- ✅ Корректность credentials
- ✅ Сетевой доступ

**Ожидаемый результат:**
```
✅ 1C connection successful
```

---

### 2. Проверка синхронизации категорий

```bash
python scripts/test_invoice_to_1c.py --department-id 1
```

**Что проверяется:**
- ✅ Наличие категорий с `external_id_1c`
- ✅ Корректность маппинга с 1С

**Если ошибка:**
```
❌ No synced categories found!
Run: POST /api/v1/sync-1c/categories/sync to sync categories
```

**Решение:**
```bash
curl -X POST "http://localhost:8000/api/v1/sync-1c/categories/sync" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. Тест поиска контрагента по ИНН

```bash
# Тестовый поиск контрагента и организации
python scripts/test_invoice_to_1c.py --test-inn "7734640247/7727563778"
```

**Формат:** `supplier_inn/buyer_inn`

**Что проверяется:**
- ✅ Поиск контрагента (поставщика) в Catalog_Контрагенты
- ✅ Поиск организации (покупателя) в Catalog_Организации
- ✅ Корректность OData $filter

**Ожидаемый результат:**
```
✅ Contractor found:
  Ref_Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Description: ООО ТРАСТ ТЕЛЕКОМ
  ИНН: 7734640247

✅ Organization found:
  Ref_Key: e5f6g7h8-i9j0-k1l2-m3n4-o5p6q7r8s9t0
  Description: ООО ВЕСТ ГРУПП
  ИНН: 7727563778
```

**Если контрагент не найден:**
```
⚠️ Contractor with INN 7734640247 not found in 1C
```
→ Создайте контрагента в 1С вручную перед отправкой счета

---

### 4. Валидация конкретного счета

```bash
python scripts/test_invoice_to_1c.py --invoice-id 1 --validate-only
```

**Что проверяется:**
- ✅ Обязательные поля invoice заполнены
- ✅ Контрагент найден в 1С по supplier_inn
- ✅ Организация найдена в 1С по buyer.inn
- ✅ Категория (category_id) выбрана и синхронизирована

**Ожидаемый результат (успех):**
```
Invoice: СФ-2025-001
Date: 2025-10-31
Amount: 2000.00
Supplier: ООО ТРАСТ ТЕЛЕКОМ
Supplier INN: 7734640247
Category ID: 15

VALIDATION RESULT:
==================
✅ Validation PASSED

✅ Counterparty: ООО ТРАСТ ТЕЛЕКОМ
   GUID: a1b2c3d4-...

✅ Organization: ООО ВЕСТ ГРУПП
   GUID: e5f6g7h8-...

✅ Cash Flow Category: Услуги связи
   GUID: i9j0k1l2-...
```

**Возможные ошибки:**

#### Ошибка 1: Категория не выбрана
```
❌ Errors:
  ❌ Статья ДДС не выбрана. Выберите категорию бюджета перед отправкой в 1С.
```

**Решение:**
```bash
# 1. Получить список категорий
curl "http://localhost:8000/api/v1/invoice-processing/cash-flow-categories" \
  -H "Authorization: Bearer $TOKEN"

# 2. Установить категорию
curl -X PUT "http://localhost:8000/api/v1/invoice-processing/1/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category_id": 15}'
```

#### Ошибка 2: Контрагент не найден
```
❌ Errors:
  ❌ Контрагент с ИНН 7734640247 не найден в 1С. Создайте контрагента 'ООО ТРАСТ ТЕЛЕКОМ' в 1С перед отправкой.
```

**Решение:**
1. Открыть 1С
2. Справочники → Контрагенты → Создать
3. Заполнить: Наименование, ИНН, КПП
4. Сохранить
5. Повторить валидацию

#### Ошибка 3: Категория не синхронизирована
```
❌ Errors:
  ❌ Категория 'Услуги связи' не синхронизирована с 1С. external_id_1c не заполнен.
```

**Решение:**
```bash
POST /api/v1/sync-1c/categories/sync
```

#### Ошибка 4: ИНН покупателя не найден
```
❌ Errors:
  ❌ ИНН покупателя (buyer.inn) не найден в parsed_data. Возможно, AI не распознал данные покупателя.
```

**Решение:**
1. Проверить invoice в UI
2. Вручную добавить `parsed_data.buyer.inn` через API
3. Или обновить поле напрямую в БД

---

### 5. Создание заявки в 1С (реальный тест)

```bash
# С загрузкой файла
python scripts/test_invoice_to_1c.py --invoice-id 1

# Без загрузки файла
python scripts/test_invoice_to_1c.py --invoice-id 1 --no-attachment
```

**Что происходит:**
1. Валидация invoice
2. Формирование JSON для 1С
3. POST к `Document_ЗаявкаНаРасходованиеДенежныхСредств`
4. Загрузка PDF файла (если указано)
5. Обновление `invoice.external_id_1c`

**Ожидаемый результат (успех):**
```
Creating expense request in 1C...

✅ EXPENSE REQUEST CREATED!
==========================================
Ref_Key (GUID): a1810a57-b6eb-11f0-ad7f-74563c634acb
Invoice #1 updated with external_id_1c
File uploaded: invoice_001.pdf

✅ ALL TESTS PASSED!
```

**Возможные ошибки:**

#### Ошибка 1: Счет уже отправлен
```
⚠️ Invoice already has external_id_1c: a1810a57-b6eb-11f0-ad7f-74563c634acb
Skipping creation to avoid duplicate
```
→ Нормальное поведение, дубликаты не создаются

#### Ошибка 2: Валидация не прошла
```
❌ Validation failed: Invoice validation failed: Контрагент не найден...
```
→ Исправить ошибки валидации (см. выше)

#### Ошибка 3: OData ошибка от 1С
```
❌ Creation error: OData request failed with status 400
Response: {"error": {"message": "Неверный формат даты"}}
```
→ Проверить формат данных, отладка в `invoice_to_1c_converter.py`

#### Ошибка 4: Файл слишком большой
```
⚠️ Failed to upload attachment: File size exceeds 6MB limit (non-critical)
```
→ Файл не загружен, но заявка создана (можно прикрепить вручную в 1С)

---

## Полный workflow тестирования

```bash
# 1. Проверка окружения
python scripts/test_invoice_to_1c.py --test-connection

# 2. Проверка синхронизации
python scripts/test_invoice_to_1c.py --department-id 1

# 3. Тест поиска по ИНН (опционально)
python scripts/test_invoice_to_1c.py --test-inn "7734640247/7727563778"

# 4. Валидация счета
python scripts/test_invoice_to_1c.py --invoice-id 1 --validate-only

# 5. Создание заявки
python scripts/test_invoice_to_1c.py --invoice-id 1
```

---

## Отладка через логи

### Включить DEBUG logging

Добавить в `backend/scripts/test_invoice_to_1c.py`:

```python
# Детальные логи OData клиента
logging.getLogger("app.services.odata_1c_client").setLevel(logging.DEBUG)

# Детальные логи конвертера
logging.getLogger("app.services.invoice_to_1c_converter").setLevel(logging.DEBUG)
```

### Проверка созданной заявки в 1С

```bash
# Открыть 1С → Документы → Заявки на расходование денежных средств
# Найти по номеру или дате
# Проверить:
# - Контрагент заполнен
# - Сумма корректна
# - Статья ДДС выбрана
# - Назначение платежа заполнено
# - Файл прикреплен (если был загружен)
```

---

## Частые проблемы и решения

### Problem 1: Connection timeout

**Симптомы:**
```
❌ Connection error: HTTPConnectionPool timeout
```

**Решение:**
- Проверить сетевой доступ к 1С серверу
- Проверить firewall
- Проверить что 1С OData публикация работает

### Problem 2: Unauthorized (401)

**Симптомы:**
```
❌ OData request failed with status 401
```

**Решение:**
- Проверить `ODATA_1C_USERNAME` и `ODATA_1C_PASSWORD` в `.env`
- Проверить права пользователя в 1С

### Problem 3: Invalid GUID format

**Симптомы:**
```
❌ Creation error: Invalid GUID format
```

**Решение:**
- Проверить что `RUB_CURRENCY_GUID` корректен для вашей базы 1С
- Проверить формат external_id_1c в категориях

### Problem 4: Missing required field

**Симптомы:**
```
❌ OData error: Required field 'ХозяйственнаяОперация' is missing
```

**Решение:**
- Проверить структуру документа в `invoice_to_1c_converter.py`
- Возможно, ваша конфигурация 1С требует дополнительные поля

---

## Проверка результата

### 1. Проверить invoice в БД

```sql
SELECT
  id,
  invoice_number,
  invoice_date,
  total_amount,
  category_id,
  external_id_1c,
  created_in_1c_at
FROM processed_invoices
WHERE id = 1;
```

**Ожидаемо:**
- `external_id_1c` заполнен (GUID)
- `created_in_1c_at` установлен

### 2. Проверить заявку в 1С

Открыть 1С:
1. Документы → Заявки на расходование денежных средств
2. Найти по GUID (`external_id_1c`)
3. Проверить все поля

### 3. Проверить синхронизацию обратно

После следующей синхронизации (`Expense1CSync`):
```sql
SELECT *
FROM expenses
WHERE external_id_1c = 'a1810a57-b6eb-11f0-ad7f-74563c634acb';
```

Заявка должна подцепиться как `Expense` в локальную БД.

---

## Дополнительные проверки

### Проверка доступных категорий через API

```bash
curl "http://localhost:8000/api/v1/invoice-processing/cash-flow-categories" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### AI-предложение категории

```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/1/suggest-category" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Установка категории

```bash
curl -X PUT "http://localhost:8000/api/v1/invoice-processing/1/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category_id": 15}'
```

### Валидация через API

```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/1/validate-for-1c" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Создание через API

```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/1/create-1c-expense-request" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"upload_attachment": true}' | jq
```

---

## Следующие шаги

После успешного тестирования:

1. **Frontend UI**: Создать UI для:
   - Выбора категории (dropdown с поиском)
   - Валидации перед отправкой
   - Кнопка "Отправить в 1С"
   - Отображение статуса (external_id_1c)

2. **Улучшение AI**: Расширить keyword mapping в `suggest_cash_flow_category()`

3. **Мониторинг**: Добавить логирование успешных/неуспешных создаий

4. **Автоматизация**: Настроить автоматическую отправку при одобрении invoice

---

## Контакты и поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f backend.log`
2. Включите DEBUG logging
3. Проверьте документацию: `docs/INVOICE_TO_1C_INTEGRATION.md`
4. API документация: `http://localhost:8000/docs`
