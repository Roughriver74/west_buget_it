#!/bin/bash
#
# Hourly 1C Bank Transactions Sync Script
# Предназначен для запуска по расписанию через cron
#

# Переменные окружения
PROJECT_DIR="/Users/evgenijsikunov/projects/acme/acme_buget_it/backend"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/sync_hourly.log"

# Создать директорию для логов, если не существует
mkdir -p "$LOG_DIR"

# Активировать виртуальное окружение и запустить скрипт
cd "$PROJECT_DIR" || exit 1

# Логировать начало синхронизации
echo "============================================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting hourly sync" >> "$LOG_FILE"
echo "============================================================" >> "$LOG_FILE"

# Запустить Python скрипт
source "$VENV_DIR/bin/activate" && python scripts/sync_1c_hourly.py >> "$LOG_FILE" 2>&1

# Проверить код возврата
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Hourly sync completed successfully" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Hourly sync failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

# Ротация логов: оставить только последние 100000 строк
tail -n 100000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"

exit $EXIT_CODE
