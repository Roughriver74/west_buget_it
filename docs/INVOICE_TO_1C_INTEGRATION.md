# Invoice to 1C Expense Request Integration

## Обзор

Автоматическое создание заявок на расходование денежных средств в 1С на основе распознанных счетов (invoices).

## Workflow

```
1. ЗАГРУЗКА СЧЕТА
   POST /api/v1/invoice-processing/upload
   → invoice_id, status=PENDING

2. ОБРАБОТКА OCR + AI
   POST /api/v1/invoice-processing/{invoice_id}/process
   → status=PROCESSED, parsed_data заполнен

3. ВЫБОР СТАТЬИ ДДС (Обязательно!)

   a) Получить список доступных статей:
      GET /api/v1/invoice-processing/cash-flow-categories
      → List[{id, name, external_id_1c}]

   b) (Опционально) AI-предложение:
      POST /api/v1/invoice-processing/{invoice_id}/suggest-category
      → suggested_category_id

   c) Установить категорию:
      PUT /api/v1/invoice-processing/{invoice_id}/category
      {"category_id": 15}

4. ВАЛИДАЦИЯ ПЕРЕД ОТПРАВКОЙ
   POST /api/v1/invoice-processing/{invoice_id}/validate-for-1c
   → {is_valid, errors[], warnings[], found_data}

5. СОЗДАНИЕ ЗАЯВКИ В 1С
   POST /api/v1/invoice-processing/{invoice_id}/create-1c-expense-request
   {"upload_attachment": true}
   → {success, external_id_1c, message}

6. СИНХРОНИЗАЦИЯ ОБРАТНО
   При следующей синхронизации из 1С заявка подцепится как Expense
```

## API Endpoints

### 1. GET /api/v1/invoice-processing/cash-flow-categories

**Описание**: Получить список статей ДДС для выбора

**Query Parameters:**
- `department_id` (optional): Фильтр по отделу

**Response:**
```json
[
  {
    "id": 15,
    "name": "Аренда помещений",
    "code": "01.002",
    "external_id_1c": "a1b2c3d4-...",
    "parent_id": null,
    "is_folder": false,
    "order_index": 10
  }
]
```

**Пример запроса:**
```bash
curl -X GET "http://localhost:8000/api/v1/invoice-processing/cash-flow-categories" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2. POST /api/v1/invoice-processing/{invoice_id}/suggest-category

**Описание**: AI-предложение статьи ДДС на основе назначения платежа

**Response:**
```json
{
  "suggested_category_id": 15,
  "category_name": "Услуги связи",
  "confidence": 75.0,
  "reasoning": "На основе назначения платежа: 'Оплата услуг связи...'"
}
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/123/suggest-category" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. PUT /api/v1/invoice-processing/{invoice_id}/category

**Описание**: Установить категорию (статью ДДС) для invoice

**Request Body:**
```json
{
  "category_id": 15
}
```

**Response:**
```json
{
  "success": true,
  "message": "Категория обновлена: Аренда помещений"
}
```

**Пример запроса:**
```bash
curl -X PUT "http://localhost:8000/api/v1/invoice-processing/123/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category_id": 15}'
```

---

### 4. POST /api/v1/invoice-processing/{invoice_id}/validate-for-1c

**Описание**: Валидация invoice перед отправкой в 1С

**Проверяет:**
- Обязательные поля заполнены
- Контрагент найден в 1С по ИНН
- Организация найдена в 1С по ИНН
- Статья ДДС выбрана и синхронизирована

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Назначение платежа не заполнено"],
  "found_data": {
    "counterparty": {
      "guid": "a1b2c3d4-...",
      "name": "ООО ТРАСТ ТЕЛЕКОМ"
    },
    "organization": {
      "guid": "e5f6g7h8-...",
      "name": "ООО ВЕСТ ГРУПП"
    },
    "cash_flow_category": {
      "guid": "i9j0k1l2-...",
      "name": "Услуги связи"
    }
  }
}
```

**Возможные ошибки:**
```json
{
  "is_valid": false,
  "errors": [
    "Контрагент с ИНН 7734640247 не найден в 1С. Создайте контрагента в 1С перед отправкой.",
    "Статья ДДС не выбрана. Выберите категорию бюджета перед отправкой в 1С."
  ],
  "warnings": [],
  "found_data": {...}
}
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/123/validate-for-1c" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5. POST /api/v1/invoice-processing/{invoice_id}/create-1c-expense-request

**Описание**: Создать заявку на расход в 1С из invoice

**Request Body:**
```json
{
  "upload_attachment": true
}
```

**Response (Success):**
```json
{
  "success": true,
  "external_id_1c": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Заявка на расход успешно создана в 1С (GUID: a1b2c3d4-...)",
  "created_at": "2025-11-17T12:34:56.789Z"
}
```

**Response (Validation Error):**
```json
{
  "detail": "Invoice validation failed: Контрагент с ИНН 7734640247 не найден в 1С"
}
```

**Response (Already Created):**
```json
{
  "detail": "Invoice уже отправлен в 1С (external_id_1c=a1b2c3d4-...)"
}
```

**Пример запроса:**
```bash
curl -X POST "http://localhost:8000/api/v1/invoice-processing/123/create-1c-expense-request" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"upload_attachment": true}'
```

---

## Полный пример использования

```bash
# 1. Загрузить счет
INVOICE_ID=$(curl -X POST "http://localhost:8000/api/v1/invoice-processing/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf" \
  | jq -r '.invoice_id')

# 2. Обработать OCR + AI
curl -X POST "http://localhost:8000/api/v1/invoice-processing/${INVOICE_ID}/process" \
  -H "Authorization: Bearer $TOKEN"

# 3. Получить AI-предложение категории
SUGGESTED_CATEGORY=$(curl -X POST "http://localhost:8000/api/v1/invoice-processing/${INVOICE_ID}/suggest-category" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.suggested_category_id')

# 4. Установить категорию
curl -X PUT "http://localhost:8000/api/v1/invoice-processing/${INVOICE_ID}/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"category_id\": ${SUGGESTED_CATEGORY}}"

# 5. Валидация
curl -X POST "http://localhost:8000/api/v1/invoice-processing/${INVOICE_ID}/validate-for-1c" \
  -H "Authorization: Bearer $TOKEN"

# 6. Создать заявку в 1С
curl -X POST "http://localhost:8000/api/v1/invoice-processing/${INVOICE_ID}/create-1c-expense-request" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"upload_attachment": true}'
```

---

## Требования

### Предварительная настройка

1. **Синхронизация справочников из 1С**:
   ```bash
   # Синхронизировать статьи ДДС
   curl -X POST "http://localhost:8000/api/v1/sync-1c/categories/sync" \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Контрагенты должны существовать в 1С**:
   - Система НЕ создает контрагентов автоматически
   - При ошибке "Контрагент не найден" → создайте в 1С вручную

3. **Организация (покупатель) должна существовать в 1С**:
   - Обычно организация уже есть (это ваша компания)
   - Проверяется по ИНН из `parsed_data.buyer.inn`

### Обязательные поля invoice

- `invoice_number` - номер счета
- `invoice_date` - дата счета
- `total_amount` - сумма (> 0)
- `supplier_inn` - ИНН поставщика
- `category_id` - выбранная статья ДДС (с `external_id_1c`)
- `parsed_data.buyer.inn` - ИНН покупателя

---

## Структура создаваемого документа в 1С

```json
{
  "Дата": "2025-10-31T00:00:00",
  "Организация_Key": "guid-организации",
  "Получатель_Key": "guid-контрагента",
  "СуммаДокумента": 2000.00,
  "Валюта_Key": "RUB-guid",
  "СтатьяДДС_Key": "guid-статьи-ДДС",
  "НазначениеПлатежа": "Оплата по счету №2635...",
  "ДатаПлатежа": "2025-11-03T00:00:00",
  "ХозяйственнаяОперация": "ОплатаПоставщику"
}
```

**Поля:**
- `Дата` - дата из `invoice_date`
- `Организация_Key` - GUID организации (найден по buyer.inn)
- `Получатель_Key` - GUID контрагента (найден по supplier.inn)
- `СуммаДокумента` - сумма из `total_amount`
- `СтатьяДДС_Key` - GUID статьи ДДС (из `category.external_id_1c`)
- `НазначениеПлатежа` - назначение из `payment_purpose`
- `ДатаПлатежа` - дата счета + 3 дня
- `ХозяйственнаяОперация` - фиксированное значение "ОплатаПоставщику"

---

## Troubleshooting

### Ошибка: "Контрагент не найден в 1С"

**Решение:**
1. Откройте 1С
2. Перейдите в Справочник "Контрагенты"
3. Создайте нового контрагента с ИНН из счета
4. Повторите попытку создания заявки

### Ошибка: "Категория не синхронизирована с 1С"

**Решение:**
1. Запустите синхронизацию справочников:
   ```bash
   POST /api/v1/sync-1c/categories/sync
   ```
2. Выберите другую категорию из списка `/cash-flow-categories`

### Ошибка: "ИНН покупателя не найден в parsed_data"

**Решение:**
1. AI не распознал данные покупателя
2. Проверьте invoice в UI
3. Вручную добавьте `parsed_data.buyer.inn` через API update

### Invoice уже отправлен в 1С

**Решение:**
- Проверьте `external_id_1c` в invoice
- Если нужно создать новый документ → создайте новый invoice

---

## Ограничения

1. **Загрузка файлов в 1С**:
   - Максимальный размер: ~4-6MB (Base64 encoding)
   - Файлы > 6MB не загружаются (пропускаются)

2. **Валюта**:
   - Только RUB (hardcoded GUID)
   - Для других валют нужно добавить mapping

3. **Хозяйственная операция**:
   - Только "ОплатаПоставщику"
   - Фиксированное значение

4. **Табличная часть**:
   - В текущей версии НЕ передается
   - Только общая сумма

---

## TODO / Future Enhancements

- [ ] Поддержка других валют (USD, EUR)
- [ ] Передача табличной части (`parsed_data.items[]`)
- [ ] Автоматическое создание контрагентов в 1С
- [ ] Webhook от 1С при изменении статуса заявки
- [ ] Bulk создание заявок (для нескольких invoices сразу)
- [ ] UI для выбора статьи ДДС и создания заявки
