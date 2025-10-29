#!/bin/bash

# Скрипт импорта SQL дампа в БД на сервере
# Использование: ./scripts/import_db.sh <path_to_dump.sql>

set -e

echo "======================================"
echo "IT Budget Manager - Database Import"
echo "======================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ -z "$1" ]; then
    echo -e "${RED}Ошибка: Необходимо указать путь к SQL файлу${NC}"
    echo ""
    echo "Использование:"
    echo "  ./scripts/import_db.sh <path_to_dump.sql>"
    echo ""
    echo "Пример:"
    echo "  ./scripts/import_db.sh ./backups/db_export_20251029_120000.sql"
    exit 1
fi

SQL_FILE="$1"

# Проверка существования файла
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}Ошибка: Файл не найден: $SQL_FILE${NC}"
    exit 1
fi

# Параметры БД (из переменных окружения или defaults)
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-it_budget_db}"
DB_USER="${DATABASE_USER:-budget_user}"
DB_PASS="${DATABASE_PASSWORD:-budget_pass}"

echo -e "${YELLOW}Импорт в БД:${NC}"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo -e "${YELLOW}Файл импорта:${NC} $SQL_FILE"
FILE_SIZE=$(du -h "$SQL_FILE" | cut -f1)
echo -e "${YELLOW}Размер:${NC} $FILE_SIZE"
echo ""

# Предупреждение
echo -e "${RED}⚠️  ВНИМАНИЕ: Эта операция УДАЛИТ все существующие данные!${NC}"
echo ""
read -p "Продолжить импорт? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Импорт отменен."
    exit 0
fi

# Импорт БД
echo "Импортирую данные..."
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "$SQL_FILE" \
    -v ON_ERROR_STOP=1

# Проверка успешности
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Импорт завершен успешно!${NC}"
    echo ""
    echo "Данные успешно импортированы в:"
    echo "  $DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Ошибка при импорте БД${NC}"
    echo "Проверьте логи выше для деталей."
    exit 1
fi
