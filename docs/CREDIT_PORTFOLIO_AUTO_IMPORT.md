# Автоматический импорт Кредитного Портфеля из 1С

**Дата**: 14 ноября 2025
**Статус**: Полностью готово к использованию ✅

---

## 📋 Обзор

Система автоматического импорта данных кредитного портфеля из 1С через FTP.

**Особенности**:
- ✅ Автоматическая загрузка файлов с FTP сервера
- ✅ Парсинг XLSX файлов (поступления, списания, расшифровка)
- ✅ UPSERT логика (идемпотентность)
- ✅ Авто-создание организаций, счетов, договоров
- ✅ Multi-tenancy поддержка
- ✅ Scheduled импорт (ежедневно в 8:00 по Москве)
- ✅ Ручной запуск через API

---

## 🏗️ Архитектура

```
┌─────────────────┐
│   FTP Server    │  floppisw.beget.tech
│  (1С выгрузка)  │
└────────┬────────┘
         │
         │ XLSX files
         ↓
┌─────────────────┐
│  FTPClient      │  Загрузка файлов
│  (credit_       │  → data/credit_portfolio/
│   portfolio_    │
│   ftp.py)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  XLSXParser     │  Парсинг Excel
│  (credit_       │  → Python dicts
│   portfolio_    │
│   parser.py)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  DataImporter   │  UPSERT в БД
│  (credit_       │  → PostgreSQL
│   portfolio_    │
│   importer.py)  │
└─────────────────┘
```

---

## 📂 Структура файлов

### Backend сервисы

**1. FTP Клиент**
`backend/app/services/credit_portfolio_ftp.py`
- Подключение к FTP серверу
- Загрузка XLSX файлов
- Сохранение в `data/credit_portfolio/`

**2. XLSX Парсер**
`backend/app/services/credit_portfolio_parser.py`
- Определение типа файла (поступление/списание/расшифровка)
- Маппинг колонок на поля модели
- Валидация и очистка данных
- Поддержка различных форматов дат

**3. Импортер данных**
`backend/app/services/credit_portfolio_importer.py`
- UPSERT логика для receipts, expenses, details
- Авто-создание связанных сущностей
- Multi-tenancy (department_id)
- Логирование импорта

**4. Scheduler**
`backend/app/services/scheduler.py`
- APScheduler для фоновых задач
- Cron расписание (8:00 AM Moscow time)
- Логирование выполнения
- Graceful shutdown

---

## ⚙️ Конфигурация

### .env переменные

```env
# Credit Portfolio FTP
CREDIT_PORTFOLIO_FTP_HOST=floppisw.beget.tech
CREDIT_PORTFOLIO_FTP_USER=floppisw_fin
CREDIT_PORTFOLIO_FTP_PASSWORD=G!5zb1FiL8!d
CREDIT_PORTFOLIO_FTP_REMOTE_DIR=/
CREDIT_PORTFOLIO_FTP_LOCAL_DIR=data/credit_portfolio
```

**Файлы обновлены**:
- ✅ `backend/app/core/config.py` - добавлены настройки FTP
- ✅ `backend/.env.example` - документация переменных

---

## 🔄 Автоматический импорт

### Scheduler настройка

**Расписание**: Ежедневно в 8:00 по Москве (Europe/Moscow)

**Процесс**:
1. Загрузка всех XLSX файлов с FTP
2. Импорт для каждого активного отдела (department)
3. Логирование результатов в `fin_import_logs`

**Файлы**:
- `backend/app/services/scheduler.py` - scheduler
- `backend/app/main.py` - интеграция в startup/shutdown events

**Логи**:
```bash
# При старте приложения
[Startup] Background scheduler started
[Startup] Scheduled jobs:
  - Import Credit Portfolio Data from FTP (ID: credit_portfolio_import, Next run: 2025-11-15 08:00:00+03:00)
```

---

## 🎯 Ручной запуск импорта

### API Endpoint

```bash
POST /api/v1/credit-portfolio/import/trigger
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "department_id": 1  # Optional, defaults to current user's department
}
```

**Доступ**: только MANAGER, ADMIN, ACCOUNTANT

**Пример**:
```bash
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"department_id": 1}'
```

**Ответ**:
```json
{
  "success": true,
  "message": "Import completed: 3/3 files imported",
  "files_processed": 3,
  "files_failed": 0,
  "total_files": 3,
  "department_id": 1
}
```

---

## 📊 Модели данных

### FinReceipt (Поступления)
```python
operation_id          # Уникальный ID операции (1С)
organization_id       # FK → FinOrganization
bank_account_id       # FK → FinBankAccount
contract_id           # FK → FinContract
document_date         # Дата документа
payer                 # Плательщик
amount                # Сумма
payment_purpose       # Назначение платежа
department_id         # Multi-tenancy (ОБЯЗАТЕЛЬНО)
```

### FinExpense (Списания)
```python
operation_id          # Уникальный ID операции (1С)
organization_id       # FK → FinOrganization
bank_account_id       # FK → FinBankAccount
contract_id           # FK → FinContract
document_date         # Дата документа
recipient             # Получатель
amount                # Сумма
payment_purpose       # Назначение платежа
department_id         # Multi-tenancy (ОБЯЗАТЕЛЬНО)
```

### FinExpenseDetail (Расшифровка платежей)
```python
expense_operation_id  # FK → FinExpense.operation_id
payment_type          # Тип платежа (тело/проценты)
payment_amount        # Сумма платежа
vat_amount            # НДС
department_id         # Multi-tenancy (ОБЯЗАТЕЛЬНО)
```

---

## 🔧 Установка и запуск

### 1. Установить зависимости

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Новая зависимость**: APScheduler==3.10.4 (добавлена автоматически)

### 2. Применить миграции

```bash
cd backend
source venv/bin/activate

# Запустить БД
docker-compose up -d db

# Создать миграцию
DEBUG=True alembic revision --autogenerate -m "add credit portfolio tables"

# Применить
DEBUG=True alembic upgrade head
```

### 3. Запустить систему

```bash
./run.sh
```

**Scheduler запустится автоматически** при старте приложения.

**Логи startup**:
```
[Startup] Starting IT Budget Manager v0.5.0
[Startup] Background scheduler started
[Startup] Scheduled jobs:
  - Import Credit Portfolio Data from FTP (ID: credit_portfolio_import, Next run: 2025-11-15 08:00:00+03:00)
```

---

## 📝 Логирование импорта

### FinImportLog таблица

Все импорты логируются в БД:

```sql
SELECT
  source_file,
  table_name,
  rows_inserted,
  rows_updated,
  rows_failed,
  status,
  processing_time_seconds,
  import_date
FROM fin_import_logs
ORDER BY import_date DESC
LIMIT 10;
```

**API endpoint для логов**:
```bash
GET /api/v1/credit-portfolio/import-logs?department_id=1
```

---

## 🎨 Frontend интеграция

### Страницы кредитного портфеля

**Меню**: Финансы → Кредитный портфель

1. **Аналитика** (`/credit-portfolio`)
   - Сводные карточки (поступления, списания, баланс)
   - Помесячная динамика
   - Последние операции

2. **KPI метрики** (`/credit-portfolio/kpi`)
   - Коэффициент погашения
   - Доля процентов/тела кредита
   - Активные договоры

3. **Денежные потоки** (`/credit-portfolio/cash-flow`)
   - График помесячной динамики
   - Накопительный баланс
   - Детализация по месяцам

4. **Договоры** (`/credit-portfolio/contracts`)
   - Список договоров
   - Фильтры и поиск
   - Статистика

**Все страницы используют** `useDepartment()` hook для multi-tenancy.

---

## ✅ Тестирование

### 1. Проверить FTP подключение

```python
from app.services.credit_portfolio_ftp import download_credit_portfolio_files

# Загрузить файлы
files = download_credit_portfolio_files()
print(f"Downloaded {len(files)} files: {files}")
```

### 2. Протестировать парсер

```python
from app.services.credit_portfolio_parser import CreditPortfolioParser

parser = CreditPortfolioParser()
file_type, records = parser.parse_file('data/credit_portfolio/postuplenie_2025.xlsx')

print(f"File type: {file_type}")
print(f"Records: {len(records)}")
```

### 3. Ручной импорт

```bash
# Через API
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Проверить scheduler

```bash
# В логах приложения
grep "credit_portfolio_import" backend.log
```

---

## 🚨 Troubleshooting

### FTP не подключается

**Симптомы**: "FTP connection failed"

**Решение**:
```bash
# Проверить credentials
echo $CREDIT_PORTFOLIO_FTP_HOST
echo $CREDIT_PORTFOLIO_FTP_USER

# Тест подключения
ftp floppisw.beget.tech
# User: floppisw_fin
# Password: G!5zb1FiL8!d
```

### Файлы не парсятся

**Симптомы**: "Cannot determine file type"

**Причина**: Неправильное имя файла

**Требования к именам**:
- Поступления: содержит "postuplenie" или "поступление"
- Списания: содержит "spisanie" или "списание"
- Расшифровка: содержит "rasshifrovka" или "расшифровка"

### Scheduler не запускается

**Симптомы**: "Failed to start scheduler"

**Решение**:
```bash
# Проверить зависимости
pip install APScheduler==3.10.4

# Проверить логи
tail -f backend.log | grep scheduler
```

### Импорт дублирует данные

**Причина**: UPSERT работает на основе `(operation_id, department_id)`

**Решение**: Убедитесь, что `operation_id` уникален в пределах отдела.

---

## 📊 Мониторинг

### Статус scheduler

```bash
# Логи при старте
[Startup] Background scheduler started
[Startup] Scheduled jobs:
  - Import Credit Portfolio Data from FTP (Next run: 2025-11-15 08:00:00+03:00)
```

### Импорт логи

```bash
# Успешный импорт
[INFO] Starting scheduled credit portfolio import
[INFO] Downloaded 3 files from FTP
[INFO] Department ООО Вест: 3/3 files imported
[INFO] Scheduled import completed: 3 files imported, 0 failed

# Ошибка
[ERROR] Error during FTP import: Connection timeout
```

---

## 🎉 Итог

**Автоматический импорт Кредитного Портфеля полностью готов!**

### ✅ Готово:
1. FTP клиент для загрузки файлов
2. XLSX парсер с поддержкой 3 типов файлов
3. Импортер с UPSERT логикой и multi-tenancy
4. Scheduler для ежедневного импорта в 8:00
5. API endpoint для ручного запуска
6. Логирование всех операций
7. Интеграция в main.py (startup/shutdown)
8. Документация

### 🚀 Запуск:
```bash
./run.sh  # Scheduler запустится автоматически
```

### 📅 Расписание:
- **Автоматически**: Ежедневно в 8:00 по Москве
- **Вручную**: `POST /api/v1/credit-portfolio/import/trigger`

**Готово к продакшену!** 🎊
