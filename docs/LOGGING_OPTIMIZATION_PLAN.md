# Logging Optimization Plan

## 📊 Текущая ситуация

**Проблемы:**
- 434 вызова logger в 31 файле
- 390,000+ строк в основном логе
- Каждый HTTP запрос логируется
- Избыточное логирование в OData клиенте (48 logger.info)
- Дублирующиеся логи фильтров (3-4 раза на один запрос)
- Весь код использует уровень INFO вместо DEBUG
- Console + File логирование дублируется

## 🎯 Цели оптимизации

1. **Снизить объем логов на 70-80%**
2. **Разделить логирование по уровням** (DEBUG/INFO/WARNING/ERROR)
3. **Убрать дублирование** логов
4. **Оставить только важные события в INFO**
5. **Перенести детальную отладку в DEBUG**

## 📋 План действий

### 1. Изменить уровень логирования по умолчанию

**Файл:** `backend/app/utils/logger.py`

```python
# Было:
LOG_LEVEL = logging.INFO

# Стало:
LOG_LEVEL = logging.WARNING  # Production
# Или через env:
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')
```

**Рекомендация:**
- Production: `WARNING` (только предупреждения и ошибки)
- Development: `INFO` (важные события)
- Debug: `DEBUG` (всё)

### 2. Убрать логирование каждого HTTP запроса

**Файл:** `backend/app/main.py:100`

```python
# ❌ УДАЛИТЬ эту строку:
logger.info(f"Request: {request.method} {request.url.path} - User: {user}")

# ✅ Оставить только timing и errors:
response = await call_next(request)
process_time = time.time() - start_time

# Логировать только медленные запросы (> 5 сек)
if process_time > 5.0:
    logger.warning(f"Slow request: {request.method} {request.url.path} - {process_time:.2f}s")

# Логировать только ошибки
if response.status_code >= 400:
    logger.error(f"Failed request: {request.method} {request.url.path} - Status: {response.status_code}")
```

### 3. Оптимизировать OData клиент

**Файл:** `backend/app/services/odata_1c_client.py`

**Проблемные места:**
- Строки 241-257: дублирование логов фильтров
- Строки 318-334: еще дублирование
- Строки 396-414: еще раз
- Строки 579-580: логирование каждого поиска

**Изменения:**

```python
# ❌ БЫЛО (строки 241-257):
if date_from:
    filters.append(f"Дата ge datetime'{date_from.isoformat()}'")
    logger.info(f"Using OData filter: {filter_str}")
if date_to:
    filters.append(f"Дата le datetime'{date_to.isoformat()}'")
    logger.info(f"Using OData filter: {filter_str}")
# ... еще 4 раза!
logger.info(f"Fetching bank receipts: date_from={date_from}, date_to={date_to}, top={top}, skip={skip}")

# ✅ СТАЛО:
if date_from:
    filters.append(f"Дата ge datetime'{date_from.isoformat()}'")
if date_to:
    filters.append(f"Дата le datetime'{date_to.isoformat()}'")
if only_posted is not None:
    filters.append(f"Posted eq {str(only_posted).lower()}")

# Один лог вместо 6:
logger.debug(f"Fetching bank receipts: filters={filters}, top={top}, skip={skip}")
```

**Применить ко всем методам:**
- `get_bank_receipts()` - строки 236-257
- `get_bank_payments()` - строки 313-334
- `get_cash_receipts()` - строки 391-414
- `get_cash_payments()` - строки 471-494
- `get_expense_requests()` - строки 637-658

**Убрать логирование auth:**
```python
# ❌ УДАЛИТЬ (строки 43, 50):
logger.info("Using custom authorization token")
logger.info(f"Using HTTPBasicAuth with username: {username}")

# Auth - это sensitive data, не нужно логировать
```

### 4. Оптимизировать Invoice to 1C Converter

**Файл:** `backend/app/services/invoice_to_1c_converter.py`

**Изменения:**

```python
# ❌ БЫЛО - 26 logger.info в validate_invoice():
logger.info(f"Validating invoice {invoice.id} for 1C export")
logger.info(f"Found cash flow category: {category.name}")
logger.info(f"Found counterparty in 1C: {result.counterparty_name}")
# ... еще 23 раза

# ✅ СТАЛО - один лог в начале (INFO), остальные DEBUG:
logger.info(f"Validating invoice {invoice.id} for 1C export")

logger.debug(f"Found cash flow category: {category.name}")
logger.debug(f"Found counterparty: {result.counterparty_name}")
# ... все остальные в DEBUG

# Итоговый результат - INFO:
if result.is_valid:
    logger.info(f"Invoice {invoice.id} validation PASSED")
else:
    logger.warning(f"Invoice {invoice.id} validation FAILED: {result.errors}")
```

**Убрать JSON payload logging:**
```python
# ❌ УДАЛИТЬ (строка 445):
logger.info(f"1C expense request data prepared (complete format): {expense_request_data}")

# Это ОГРОМНЫЙ JSON, засоряет логи. Оставить только в DEBUG:
logger.debug(f"Request data keys: {list(expense_request_data.keys())}")
```

### 5. Оптимизировать Category 1C Sync

**Файл:** `backend/app/services/category_1c_sync.py`

**Изменения:**

```python
# Логировать только важные события:
logger.info(f"Starting category sync from 1C (department_id={self.department_id})")
# ... обработка ...
logger.info(f"Category sync completed: created={created}, updated={updated}, skipped={skipped}")

# Детали - в DEBUG:
logger.debug(f"Processing category: {cat_1c.get('Description')}")
logger.debug(f"Checking for duplicates...")
```

### 6. Оптимизировать другие сервисы

**Применить аналогичные изменения:**
- `backend/app/services/expense_1c_sync.py`
- `backend/app/services/organization_1c_sync.py`
- `backend/app/services/catalog_1c_sync.py`
- `backend/app/services/bank_transaction_1c_import.py`

**Паттерн:**
```python
# ✅ INFO - только начало/конец операции + важные события
logger.info(f"Starting {operation_name}")
logger.info(f"Completed {operation_name}: stats={stats}")

# ✅ DEBUG - детали обработки
logger.debug(f"Processing item: {item}")
logger.debug(f"Found match: {match}")

# ✅ WARNING - проблемы, но не критичные
logger.warning(f"Duplicate found: {item}")
logger.warning(f"Validation failed: {error}")

# ✅ ERROR - критичные ошибки
logger.error(f"Failed to process: {error}", exc_info=True)
```

### 7. Настроить environment-based logging

**Файл:** `backend/app/core/config.py`

```python
# Добавить настройки:
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'WARNING')  # WARNING по умолчанию
LOG_SQL_QUERIES: bool = os.getenv('LOG_SQL_QUERIES', 'false').lower() == 'true'
LOG_HTTP_REQUESTS: bool = os.getenv('LOG_HTTP_REQUESTS', 'false').lower() == 'true'
```

**Файл:** `.env`

```bash
# Development
LOG_LEVEL=INFO
LOG_SQL_QUERIES=false
LOG_HTTP_REQUESTS=false

# Production
LOG_LEVEL=WARNING
LOG_SQL_QUERIES=false
LOG_HTTP_REQUESTS=false

# Debug (only when needed!)
LOG_LEVEL=DEBUG
LOG_SQL_QUERIES=true
LOG_HTTP_REQUESTS=true
```

### 8. Настроить rotation логов

**Файл:** `backend/app/utils/logger.py`

```python
# Было: 10MB, 5 backup files
RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)

# Стало: 5MB, 3 backup files (меньше места на диске)
RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
```

### 9. Добавить structured logging (опционально)

**Установка:**
```bash
pip install structlog
```

**Использование:**
```python
import structlog

logger = structlog.get_logger()

# Вместо:
logger.info(f"User {user_id} created expense {expense_id}")

# Используем:
logger.info("expense_created", user_id=user_id, expense_id=expense_id, amount=amount)

# Преимущества:
# - Легко парсить логи
# - Легко фильтровать
# - Легко анализировать
```

## 📈 Ожидаемый результат

**До оптимизации:**
- 390,000 строк в логе
- Каждый HTTP запрос логируется
- Один OData запрос = 5-6 логов
- Размер логов: ~100-200MB в день

**После оптимизации:**
- ~50,000-80,000 строк в логе (80% снижение)
- Только медленные/ошибочные HTTP запросы
- Один OData запрос = 1 лог (DEBUG) или 0 (production)
- Размер логов: ~20-40MB в день

## 🚀 Порядок внедрения

1. ✅ Создать feature branch: `git checkout -b optimize/reduce-logging`
2. ✅ Изменить `LOG_LEVEL` на `WARNING` в production
3. ✅ Убрать HTTP request logging из middleware
4. ✅ Оптимизировать OData клиент (самый шумный)
5. ✅ Оптимизировать Invoice converter
6. ✅ Оптимизировать sync сервисы
7. ✅ Добавить environment-based настройки
8. ✅ Тестирование на dev окружении
9. ✅ Деплой на production
10. ✅ Мониторинг размера логов

## 📝 Чек-лист изменений

### Критичные (сразу):
- [ ] Изменить `LOG_LEVEL = logging.WARNING` в `logger.py`
- [ ] Удалить HTTP request logging из `main.py`
- [ ] Оптимизировать `odata_1c_client.py` (убрать дубли)
- [ ] Перевести детальные логи в DEBUG в `invoice_to_1c_converter.py`

### Важные (в течение недели):
- [ ] Оптимизировать все sync сервисы
- [ ] Добавить environment-based настройки
- [ ] Настроить rotation логов (5MB, 3 файла)

### Опционально (при желании):
- [ ] Внедрить structured logging (structlog)
- [ ] Добавить log aggregation (ELK/Loki)
- [ ] Настроить alerts на ERROR logs

## 🔍 Мониторинг после внедрения

**Метрики для отслеживания:**
- Размер log файлов (до/после)
- Количество строк в день
- Дисковое пространство
- Performance приложения (не должно ухудшиться)

**Команды для проверки:**
```bash
# Размер логов
du -sh backend/logs/

# Количество строк
wc -l backend/logs/app.log

# Логи за последний час
tail -1000 backend/logs/app.log | grep -E "(ERROR|WARNING)"

# Топ-5 самых шумных модулей
grep -oP '(?<=- )[^ ]+(?= -)' backend/logs/app.log | sort | uniq -c | sort -rn | head -5
```

## ⚠️ Важно!

**НЕ удалять:**
- ERROR логи (критичные ошибки)
- WARNING логи (важные предупреждения)
- Security-related логи (auth failures, rate limiting)
- Business-critical events (создание заявок в 1С)

**Удалять:**
- Дублирующиеся логи
- Логирование каждого шага
- Sensitive data (пароли, токены)
- Избыточные детали (JSON payloads целиком)
