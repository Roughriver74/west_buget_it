# Настройка автоматической синхронизации с 1С (Cron Job)

## Обзор

Данная инструкция описывает настройку автоматического импорта банковских и кассовых операций из 1С через OData API по расписанию.

**Что импортируется:**
- ✅ Банковские поступления (безналичные)
- ✅ Банковские списания (безналичные)
- ✅ Кассовые поступления (ПКО)
- ✅ Кассовые списания (РКО)

**Особенности:**
- Синхронизация каждый час
- Загрузка последних 24 часов данных (предотвращает пропуск операций)
- Автоматическая категоризация через AI (TransactionClassifier)
- Защита от дублирования через `external_id_1c`
- Логирование в файл с автоматической ротацией

---

## 1. Скрипты для синхронизации

### Hourly Sync (ежечасная синхронизация)
**Файл:** `backend/scripts/sync_1c_hourly.py`

**Назначение:** Загружает операции за последние 24 часа для ВСЕХ активных отделов

**Особенности:**
- Запускается каждый час через cron
- Синхронизирует данные для всех активных отделов (is_active = True)
- Логирует в `backend/logs/sync_hourly.log`
- Не создает дубликатов (проверка по `external_id_1c`)
- Автоматическая категоризация включена
- Выводит статистику по каждому отделу отдельно

### Full 2025 Sync (полная загрузка 2025 года)
**Файл:** `backend/scripts/sync_1c_full_2025.py`

**Назначение:** Загружает все операции с 1 января 2025 года

**Особенности:**
- Для первоначальной загрузки или полного обновления
- Запускается вручную
- Защита от дублей встроена

---

## 2. Установка Cron Job

### Шаг 1: Проверить пути в скрипте

Откройте файл `backend/scripts/cron_hourly_sync.sh` и убедитесь, что пути корректны:

```bash
PROJECT_DIR="/Users/evgenijsikunov/projects/west/west_buget_it/backend"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
```

### Шаг 2: Сделать скрипт исполняемым

```bash
chmod +x /Users/evgenijsikunov/projects/west/west_buget_it/backend/scripts/cron_hourly_sync.sh
```

### Шаг 3: Настроить переменные окружения (если нужно)

Если вы используете custom OData credentials, создайте файл `.env` в `backend/`:

```bash
# backend/.env
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28
```

По умолчанию используются эти credentials (захардкожены в `odata_1c_client.py`).

### Шаг 4: Добавить задачу в crontab

Откройте редактор crontab:

```bash
crontab -e
```

Добавьте следующую строку для **ежечасного запуска** в начале каждого часа:

```cron
# 1C Bank Transactions Hourly Sync
0 * * * * /Users/evgenijsikunov/projects/west/west_buget_it/backend/scripts/cron_hourly_sync.sh
```

**Альтернативные расписания:**

```cron
# Каждые 30 минут
*/30 * * * * /path/to/cron_hourly_sync.sh

# Каждые 2 часа
0 */2 * * * /path/to/cron_hourly_sync.sh

# Рабочие часы (9:00 - 18:00) каждый час в будни
0 9-18 * * 1-5 /path/to/cron_hourly_sync.sh

# Каждый день в 2:00 AM
0 2 * * * /path/to/cron_hourly_sync.sh
```

Сохраните и закройте редактор (`:wq` в vim, `Ctrl+X` в nano).

### Шаг 5: Проверить, что задача добавлена

```bash
crontab -l
```

Вы должны увидеть вашу задачу в списке.

---

## 3. Тестирование

### Ручной запуск скрипта

```bash
cd /Users/evgenijsikunov/projects/west/west_buget_it/backend
./scripts/cron_hourly_sync.sh
```

### Проверка логов

```bash
tail -f /Users/evgenijsikunov/projects/west/west_buget_it/backend/logs/sync_hourly.log
```

### Ожидаемый вывод (успешная синхронизация):

```
============================================================
2025-11-16 10:00:01 - Starting hourly sync
============================================================
2025-11-16 10:00:01 - INFO - ... - Starting 1C import: date_from=2025-11-15, date_to=2025-11-16
2025-11-16 10:00:05 - INFO - ... - Fetching bank receipts: ...
2025-11-16 10:00:10 - INFO - ... - Fetching bank payments: ...
2025-11-16 10:00:15 - INFO - ... - Fetching cash receipts (PKO): ...
2025-11-16 10:00:20 - INFO - ... - Fetching cash payments (RKO): ...
2025-11-16 10:00:25 - INFO - ... - 1C import completed: {'total_fetched': 150, ...}
2025-11-16 10:00:25 - Hourly sync completed successfully
```

---

## 4. Мониторинг и обслуживание

### Просмотр статистики синхронизации

Логи автоматически ротируются (последние 100,000 строк). Для анализа:

```bash
# Последние 50 строк
tail -n 50 backend/logs/sync_hourly.log

# Поиск ошибок
grep ERROR backend/logs/sync_hourly.log

# Статистика за сегодня
grep "$(date '+%Y-%m-%d')" backend/logs/sync_hourly.log | grep "1C import completed"
```

### Проверка статуса cron

```bash
# macOS
sudo log stream --predicate 'process == "cron"' --level info

# Linux
systemctl status cron
journalctl -u cron
```

### Отключить синхронизацию

```bash
crontab -e
# Закомментировать строку с задачей (добавить # в начало)
# 0 * * * * /path/to/cron_hourly_sync.sh

# Или удалить задачу полностью
crontab -r  # Удалить все задачи (ОСТОРОЖНО!)
```

---

## 5. Первоначальная загрузка данных

Перед запуском ежечасной синхронизации рекомендуется загрузить исторические данные:

### Загрузка всех данных 2025 года

```bash
cd backend
source venv/bin/activate
python scripts/sync_1c_full_2025.py
```

Это займет несколько минут в зависимости от объема данных.

После успешной загрузки cron job будет поддерживать данные актуальными.

---

## 6. Устранение неполадок

### Проблема: Cron job не запускается

**Решение 1:** Проверить права на выполнение скрипта

```bash
ls -l backend/scripts/cron_hourly_sync.sh
# Должно быть: -rwxr-xr-x (исполняемый)

chmod +x backend/scripts/cron_hourly_sync.sh
```

**Решение 2:** Проверить синтаксис crontab

```bash
crontab -l
# Убедиться, что нет опечаток в пути к скрипту
```

**Решение 3:** Проверить логи cron (macOS)

```bash
log show --predicate 'process == "cron"' --last 1h
```

### Проблема: Скрипт падает с ошибкой

Проверьте логи:

```bash
tail -n 100 backend/logs/sync_hourly.log
```

Типичные ошибки:

1. **Ошибка подключения к 1С:**
   ```
   Failed to connect to 1C OData!
   ```
   - Проверить доступность сервера 1С
   - Проверить credentials в `.env` или `odata_1c_client.py`

2. **Ошибка базы данных:**
   ```
   could not connect to server: Connection refused
   ```
   - Проверить, запущен ли PostgreSQL
   - Проверить `DATABASE_URL` в `.env`

3. **Ошибка импорта модулей:**
   ```
   ModuleNotFoundError: No module named 'app'
   ```
   - Убедиться, что виртуальное окружение активно
   - Переустановить зависимости: `pip install -r requirements.txt`

### Проблема: Дублирование транзакций

**Не должно происходить** благодаря `external_id_1c`, но если дубли появляются:

```bash
# Запустить скрипт очистки (будьте осторожны!)
cd backend
source venv/bin/activate

# Удалить все транзакции (для полной переимпорта)
python -c "
from app.db.session import SessionLocal
from app.db.models import BankTransaction
db = SessionLocal()
db.query(BankTransaction).delete()
db.commit()
print('All transactions deleted')
"

# Затем заново импортировать
python scripts/sync_1c_full_2025.py
```

---

## 7. Производительность

### Рекомендуемые настройки

- **Частота синхронизации:** Каждый час (баланс между актуальностью и нагрузкой)
- **Период загрузки:** Последние 24 часа (гарантирует отсутствие пропусков)
- **Batch size:** 100 операций (по умолчанию, оптимально для большинства случаев)

### Оптимизация для больших объемов

Если за час создается > 1000 операций, можно:

1. Увеличить `batch_size` в `sync_1c_hourly.py`:
   ```python
   result = importer.import_transactions(
       date_from=date_from,
       date_to=date_to,
       batch_size=500  # Вместо 100
   )
   ```

2. Запускать синхронизацию чаще (каждые 30 минут):
   ```cron
   */30 * * * * /path/to/cron_hourly_sync.sh
   ```

---

## 8. Безопасность

**ВАЖНО:** Убедитесь, что файлы с credentials не доступны публично:

```bash
# backend/.env должен быть в .gitignore
echo ".env" >> backend/.gitignore

# Установить правильные права
chmod 600 backend/.env
```

**Рекомендация:** Использовать переменные окружения вместо хардкода паролей.

---

## Резюме

После настройки cron job система будет:
- ✅ Автоматически загружать новые операции каждый час
- ✅ Предотвращать дублирование
- ✅ Автоматически категоризировать транзакции
- ✅ Логировать все операции
- ✅ Поддерживать данные актуальными без ручного вмешательства

**Первый запуск:**
1. Запустить `sync_1c_full_2025.py` для загрузки исторических данных
2. Настроить cron job для ежечасной синхронизации
3. Мониторить логи первые несколько дней

**Поддержка:**
- Проверять логи раз в неделю
- Очищать старые логи при необходимости
- Обновлять credentials при смене паролей в 1С
