# FTP Import Status Update Fix

## Проблема

При повторной загрузке заявок из FTP с параметром `skip_duplicates=True` (режим по умолчанию) существующие заявки пропускались без обновления статуса и других важных полей.

## Решение

Изменена логика обработки дубликатов в `FTPImportService.import_expenses()`:

### Было (старое поведение):
```python
if existing:
    if skip_duplicates:
        skipped += 1
        continue  # Заявка просто пропускалась
```

### Стало (новое поведение):
```python
if existing:
    if skip_duplicates:
        # Обновляем критические поля, которые часто меняются
        critical_fields = ['status', 'is_paid', 'is_closed', 'amount', 'payment_date', 'comment']
        for field in critical_fields:
            if field in expense_fields:
                setattr(existing, field, expense_fields[field])
        updated += 1
    else:
        # Полное обновление всех полей
        for key, value in expense_fields.items():
            setattr(existing, key, value)
        updated += 1
```

## Поведение параметра `skip_duplicates`

### `skip_duplicates=True` (режим по умолчанию для cron)
- Обновляет **только критические поля** для существующих заявок:
  - `status` - статус заявки
  - `is_paid` - признак оплаты
  - `is_closed` - признак закрытия
  - `amount` - сумма
  - `payment_date` - дата оплаты
  - `comment` - комментарий

- **Не обновляет**:
  - `category_id` - категория (чтобы не перезаписать ручную категоризацию)
  - `contractor_id` - контрагент
  - `organization_id` - организация
  - `department_id` - подразделение
  - `request_date` - дата запроса
  - и другие поля, которые обычно не меняются

### `skip_duplicates=False` (полное обновление)
- Обновляет **все поля** для существующих заявок
- Используется для полной пересинхронизации данных

## Использование

### 1. API Endpoint (веб-интерфейс)
```http
POST /api/v1/expenses/import/ftp
Content-Type: application/json

{
  "remote_path": "/path/to/file.xlsx",
  "skip_duplicates": true  // Обновит статус существующих заявок
}
```

### 2. Cron задача (автоматический импорт)
```python
# backend/cron_ftp_import.py
result = await import_from_ftp(
    db=db,
    host=ftp_host,
    username=ftp_user,
    password=ftp_pass,
    remote_path=remote_path,
    skip_duplicates=True  # Обновит статус при повторном импорте
)
```

### 3. Программный вызов
```python
from app.services.ftp_import_service import import_from_ftp

result = await import_from_ftp(
    db=db,
    host="ftp.example.com",
    username="user",
    password="pass",
    remote_path="/file.xlsx",
    skip_duplicates=True  # или False для полного обновления
)
```

## Результат

Теперь при повторной загрузке заявок из FTP:
- ✅ Статус обновляется (DRAFT → PENDING → PAID)
- ✅ Сумма обновляется при изменении
- ✅ Дата оплаты обновляется
- ✅ Комментарий обновляется
- ✅ Категория НЕ перезаписывается (сохраняется ручная категоризация)

## Измененные файлы

1. `backend/app/services/ftp_import_service.py` - основная логика
2. `backend/app/api/v1/expenses.py` - API endpoint и документация
3. `backend/cron_ftp_import.py` - комментарии cron задачи

## Дата изменения

2025-11-05
