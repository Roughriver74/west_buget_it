# Автоматическая синхронизация справочников из 1С (Cron Setup)

Настройка ежедневной автоматической синхронизации справочников из 1С.

## Обзор

Cron job автоматически синхронизирует справочники из 1С каждую ночь:
- **Catalog_Организации** → Organizations
- **Catalog_СтатьиДвиженияДенежныхСредств** → BudgetCategories

**График**: Ежедневно в 02:00 AM (можно изменить)

## Установка

### 1. Проверить скрипт

Скрипт уже создан: `backend/scripts/cron_daily_1c_sync.sh`

```bash
cd backend
ls -la scripts/cron_daily_1c_sync.sh
```

Должен быть исполняемым (`-rwxr-xr-x`). Если нет:
```bash
chmod +x scripts/cron_daily_1c_sync.sh
```

### 2. Тестовый запуск

Запустите вручную для проверки:

```bash
cd backend
./scripts/cron_daily_1c_sync.sh
```

Проверьте лог:
```bash
tail -f logs/1c_catalog_sync.log
```

### 3. Добавить в crontab

**Для локальной машины:**

```bash
# Открыть crontab
crontab -e

# Добавить строку (заменить /path/to на реальный путь):
0 2 * * * /Users/evgenijsikunov/projects/west/west_buget_it/backend/scripts/cron_daily_1c_sync.sh

# Сохранить и выйти
```

**Для production (сервер):**

1. SSH на сервер:
```bash
ssh root@31.129.107.178
```

2. Скопировать проект:
```bash
cd /path/to/west_buget_it/backend
```

3. Добавить в crontab:
```bash
crontab -e
```

```cron
# 1C Catalog Sync - Daily at 2 AM
0 2 * * * /path/to/west_buget_it/backend/scripts/cron_daily_1c_sync.sh

# Alternative: Weekly on Sunday at 3 AM (менее частая синхронизация)
0 3 * * 0 /path/to/west_buget_it/backend/scripts/cron_daily_1c_sync.sh
```

4. Проверить crontab:
```bash
crontab -l
```

### 4. Проверить логи после первого запуска

```bash
# На следующий день после 02:00
cd /path/to/west_buget_it/backend
tail -100 logs/1c_catalog_sync.log
```

## Альтернативные графики

```cron
# Каждый день в 02:00
0 2 * * * /path/to/script.sh

# Каждый день в 03:30
30 3 * * * /path/to/script.sh

# Каждое воскресенье в 03:00
0 3 * * 0 /path/to/script.sh

# Каждый первый день месяца в 04:00
0 4 1 * * /path/to/script.sh

# Каждые 6 часов
0 */6 * * * /path/to/script.sh

# Каждый час
0 * * * * /path/to/script.sh
```

## Мониторинг

### 1. Просмотр логов

```bash
# Последние 100 строк
tail -100 logs/1c_catalog_sync.log

# Следить в реальном времени
tail -f logs/1c_catalog_sync.log

# Поиск ошибок
grep "ERROR\|❌" logs/1c_catalog_sync.log

# Успешные синхронизации
grep "✅" logs/1c_catalog_sync.log
```

### 2. Ротация логов

Настройте logrotate чтобы избежать переполнения диска:

```bash
sudo nano /etc/logrotate.d/1c-catalog-sync
```

Содержимое:
```
/path/to/west_buget_it/backend/logs/1c_catalog_sync.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### 3. Email уведомления

Для получения email при ошибке добавьте в начало crontab:

```cron
MAILTO=your-email@example.com
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 2 * * * /path/to/script.sh
```

Cron отправит email только если скрипт завершится с ошибкой (exit code != 0).

### 4. Webhook уведомления

Можно отправлять webhook в Slack/Telegram при ошибке.

Добавьте в конец `cron_daily_1c_sync.sh`:

```bash
# Send Slack notification on failure
if [ "$FAILED_DEPTS" -gt 0 ]; then
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
      -H 'Content-Type: application/json' \
      -d "{\"text\":\"❌ 1C Catalog Sync failed for $FAILED_DEPTS departments\"}"
fi
```

## Ручной запуск

Если нужно запустить синхронизацию вручную:

```bash
# Все отделы
cd backend
./scripts/cron_daily_1c_sync.sh

# Конкретный отдел
DEBUG=true python3 scripts/sync_1c_catalogs_auto.py --department-id 2 --all

# Только организации
DEBUG=true python3 scripts/sync_1c_catalogs_auto.py --department-id 2 --orgs

# Только категории
DEBUG=true python3 scripts/sync_1c_catalogs_auto.py --department-id 2 --cats
```

## Проверка работы cron

```bash
# Проверить статус cron
sudo systemctl status cron

# Проверить логи cron
sudo grep CRON /var/log/syslog | tail -20

# Проверить запущенные cron задачи
ps aux | grep cron

# Список всех cron jobs
crontab -l
```

## Troubleshooting

### Cron job не запускается

1. **Проверить права на файл:**
```bash
ls -l scripts/cron_daily_1c_sync.sh
# Должно быть -rwxr-xr-x
chmod +x scripts/cron_daily_1c_sync.sh
```

2. **Проверить путь в crontab:**
```bash
crontab -l
# Путь должен быть абсолютным, не относительным
```

3. **Проверить PATH в cron:**
```bash
# Добавить в начало crontab:
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
```

4. **Проверить логи cron:**
```bash
sudo tail -f /var/log/syslog | grep CRON
```

### База данных недоступна

```bash
# Проверить что PostgreSQL запущен
docker ps | grep it_budget_db

# Проверить подключение
docker exec it_budget_db psql -U budget_user -d it_budget_db -c "SELECT 1;"
```

### 1C OData недоступен

```bash
# Проверить сетевой доступ
curl -I http://10.10.100.77/trade/odata/standard.odata

# Проверить credentials
DEBUG=true python3 scripts/check_1c_catalogs.py
```

### Скрипт падает с ошибкой

```bash
# Проверить логи
tail -100 logs/1c_catalog_sync.log | grep ERROR

# Запустить вручную для детальной информации
cd backend
DEBUG=true ./scripts/cron_daily_1c_sync.sh
```

## Production рекомендации

1. **Установить разумный график**
   - Не каждый час (избыточно)
   - Оптимально: 1-2 раза в день в ночное время
   - Или еженедельно если справочники редко меняются

2. **Мониторинг и уведомления**
   - Настроить email/webhook при ошибке
   - Регулярно проверять логи

3. **Ротация логов**
   - Настроить logrotate
   - Хранить логи 30-90 дней

4. **Резервное копирование**
   - Делать backup БД перед синхронизацией (опционально)

5. **Тестирование**
   - Сначала запускать в тестовой среде
   - Проверять результаты вручную первую неделю

## Интеграция с CI/CD

Можно запускать синхронизацию после deploy:

```yaml
# .github/workflows/deploy.yml
- name: Sync 1C Catalogs
  run: |
    cd backend
    ./scripts/cron_daily_1c_sync.sh
```

## См. также

- [1C Catalog Sync Guide](1C_CATALOG_SYNC.md)
- [1C OData Integration](1C_ODATA_INTEGRATION.md)
- [Bank Transactions Import](BANK_TRANSACTIONS_IMPORT_GUIDE.md)
