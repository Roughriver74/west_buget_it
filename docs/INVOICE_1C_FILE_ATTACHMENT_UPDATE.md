# Invoice to 1C Integration - File Attachment Update

## Обзор изменений

Доработана отправка счетов в 1С с добавлением следующих функций:

1. ✅ **Автоматическое прикрепление файла** к созданной заявке на расход
2. ✅ **Проведение документа** (Posted=true) сразу при создании
3. ✅ **ФИО пользователя** в начале комментария

## Workflow

```
1. Создание заявки на расход в 1С
   ↓
   POST Document_ЗаявкаНаРасходованиеДенежныхСредств
   - Posted: true (документ проведен)
   - Комментарий: "{ФИО пользователя}: {текст комментария}"

2. Прикрепление файла к заявке
   ↓
   POST Catalog_ЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы
   - ВладелецФайла_Key: GUID заявки
   - ФайлХранилище_Base64Data: Base64-encoded file
   - Description: Имя файла
   - Расширение: pdf/png/jpg/...

3. Сохранение в БД
   ↓
   ProcessedInvoice.external_id_1c = GUID заявки
   ProcessedInvoice.created_in_1c_at = NOW()
```

## Изменения в коде

### 1. InvoiceTo1CConverter (`backend/app/services/invoice_to_1c_converter.py`)

**Изменения в методе `create_expense_request_in_1c`:**

```python
def create_expense_request_in_1c(
    self,
    invoice: ProcessedInvoice,
    upload_attachment: bool = True,
    user_comment: Optional[str] = None,
    current_user = None  # NEW: Добавлен параметр current_user
) -> str:
```

**Формирование комментария с ФИО:**

```python
# Формирование комментария с ФИО пользователя
user_full_name = "Система"
if current_user:
    user_full_name = current_user.full_name or current_user.email or "Система"

base_comment = user_comment or f"Создано автоматически из счета №{invoice.invoice_number}"
full_comment = f"{user_full_name}: {base_comment}"
```

**Проведение документа:**

```python
expense_request_data = {
    "Date": invoice.invoice_date.isoformat() + "T00:00:00",
    "Posted": True,  # Провести документ автоматически (было False)
    # ...
    "Комментарий": full_comment,  # С ФИО пользователя
}
```

**Прикрепление файла:**

```python
# 4. Загрузка файла invoice как прикрепленного файла
if upload_attachment and invoice.file_path:
    try:
        # Прочитать файл
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Загрузить в 1С
        attachment_result = self.odata_client.upload_attachment_to_expense_request(
            file_content=file_content,
            filename=original_filename,
            owner_guid=ref_key,
            file_extension=file_extension
        )
    except Exception as e:
        logger.warning(f"Failed to upload attachment: {e} (non-critical)")
```

### 2. OData1CClient (`backend/app/services/odata_1c_client.py`)

**Новый метод `upload_attachment_to_expense_request`:**

```python
def upload_attachment_to_expense_request(
    self,
    file_content: bytes,
    filename: str,
    owner_guid: str,
    file_extension: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Загрузить файл к заявке на расход в 1С

    Endpoint: Catalog_ЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы
    """
    # Кодирование в Base64
    base64_content = base64.b64encode(file_content).decode('utf-8')

    # Определить MIME type
    mime_types = {
        'pdf': 'application/pdf',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        # ...
    }
    mime_type = mime_types.get(file_extension.lower(), 'application/octet-stream')

    # Данные для создания вложения (из рабочего примера)
    attachment_data = {
        "Description": filename,
        "Расширение": file_extension or "pdf",
        "ТипХраненияФайла": "ВИнформационнойБазе",
        "ВладелецФайла_Key": owner_guid,
        "ФайлХранилище_Type": mime_type,
        "ФайлХранилище_Base64Data": base64_content,
        "Размер": len(file_content)
    }

    # POST запрос
    endpoint = "Catalog_ЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы"
    response = self._make_request(method='POST', endpoint=endpoint, data=attachment_data)

    return response
```

### 3. API Endpoint (`backend/app/api/v1/invoice_processing.py`)

**Передача current_user в converter:**

```python
@router.post("/{invoice_id}/create-1c-expense-request")
async def create_1c_expense_request_from_invoice(
    invoice_id: int,
    request: Create1CExpenseRequestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # ...
    external_id_1c = converter.create_expense_request_in_1c(
        invoice=invoice,
        upload_attachment=request.upload_attachment,
        user_comment=request.user_comment,
        current_user=current_user  # NEW: Передаем пользователя
    )
```

## Тестирование

### Запуск тестового скрипта

```bash
cd backend
python scripts/test_invoice_with_attachment.py
```

### Проверка в 1С

После выполнения скрипта проверьте в 1С:

1. **Заявка создана** с указанным Ref_Key
2. **Документ проведен** (Posted=true)
3. **Комментарий** содержит ФИО пользователя: "Иванов Иван Иванович: Тестовая заявка..."
4. **Файл прикреплен** к заявке (test_invoice.png)

### Проверка через API

```bash
# 1. Загрузить счет
curl -X POST "http://localhost:8000/api/v1/invoice-processing/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf" \
  -F "department_id=1"

# 2. Обработать счет (OCR + AI)
curl -X POST "http://localhost:8000/api/v1/invoice-processing/process" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invoice_id": 123}'

# 3. Выбрать категорию (статью ДДС)
curl -X PUT "http://localhost:8000/api/v1/invoice-processing/123/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category_id": 15, "desired_payment_date": "2025-11-23"}'

# 4. Валидация перед отправкой
curl -X POST "http://localhost:8000/api/v1/invoice-processing/123/validate-for-1c" \
  -H "Authorization: Bearer $TOKEN"

# 5. Создать заявку в 1С с прикреплением файла
curl -X POST "http://localhost:8000/api/v1/invoice-processing/123/create-1c-expense-request" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_attachment": true,
    "user_comment": "Срочная оплата по договору"
  }'
```

## Поддерживаемые форматы файлов

- ✅ PDF (application/pdf)
- ✅ PNG (image/png)
- ✅ JPG/JPEG (image/jpeg)
- ✅ GIF (image/gif)
- ✅ BMP (image/bmp)
- ✅ TIFF (image/tiff)

## Ограничения

- **Размер файла**: Рекомендуется до 6MB (из-за Base64 overhead)
- **Ошибки прикрепления**: Не критичны - заявка создается даже если файл не прикрепился
- **Права доступа**: Требуются соответствующие права OData в 1С

## Логирование

```python
# Успешное создание
logger.info(f"✅ Expense request created in 1C with Ref_Key: {ref_key}")
logger.info(f"✅ Attachment uploaded successfully to 1C expense request")

# Ошибки
logger.warning(f"⚠️ Failed to upload attachment to 1C (non-critical)")
logger.error(f"❌ Failed to create expense request in 1C: {e}")
```

## Troubleshooting

### Файл не прикрепляется

**Проблема**: Заявка создается, но файл не прикрепляется

**Решение**:
1. Проверить права OData пользователя в 1С
2. Проверить endpoint: `Catalog_ЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы`
3. Проверить размер файла (< 6MB)
4. Проверить формат файла (поддерживаемые MIME types)

### Комментарий без ФИО

**Проблема**: Комментарий не содержит ФИО пользователя

**Решение**:
1. Убедиться что `current_user` передается в `create_expense_request_in_1c`
2. Проверить что у пользователя заполнено поле `full_name` или `email`
3. Проверить логи: должен быть лог с формированием комментария

### Документ не проведен

**Проблема**: Документ создан но не проведен (Posted=false)

**Решение**:
1. Убедиться что `Posted: True` в `expense_request_data`
2. Проверить права пользователя OData на проведение документов
3. Проверить бизнес-логику 1С (возможны блокировки проведения)

## См. также

- [Invoice to 1C Integration Guide](INVOICE_TO_1C_INTEGRATION.md)
- [1C OData Integration](1C_ODATA_INTEGRATION.md)
- [CLAUDE.md](../CLAUDE.md) - Раздел "AI Invoice Processing"
