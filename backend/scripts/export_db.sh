#!/bin/bash

# Скрипт экспорта локальной БД в SQL дамп
# Использование: ./scripts/export_db.sh

set -e

echo "======================================"
echo "IT Budget Manager - Database Export"
echo "======================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры локальной БД (из .env или defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-54329}"
DB_NAME="${DB_NAME:-it_budget_db}"
DB_USER="${DB_USER:-budget_user}"
DB_PASS="${DB_PASS:-budget_pass}"

# Имя выходного файла с датой
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="db_export_${TIMESTAMP}.sql"
OUTPUT_DIR="./backups"

# Создать директорию для бэкапов
mkdir -p "$OUTPUT_DIR"
FULL_PATH="$OUTPUT_DIR/$OUTPUT_FILE"

echo -e "${YELLOW}Экспорт БД из:${NC}"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""
echo -e "${YELLOW}Файл экспорта:${NC} $FULL_PATH"
echo ""

# Экспорт БД
echo "Экспортирую данные..."

# Проверить наличие pg_dump
if command -v pg_dump &> /dev/null; then
    # Использовать локальный pg_dump
    PGPASSWORD="$DB_PASS" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        -f "$FULL_PATH"
else
    # Использовать Docker контейнер PostgreSQL
    echo -e "${YELLOW}pg_dump не найден, использую Docker...${NC}"

    # Найти Docker контейнер с PostgreSQL
    CONTAINER_NAME="it_budget_db"

    if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}✗ Docker контейнер '$CONTAINER_NAME' не найден!${NC}"
        echo "Запустите: docker-compose up -d"
        exit 1
    fi

    docker exec "$CONTAINER_NAME" pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        > "$FULL_PATH"
fi

# Проверка успешности
if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$FULL_PATH" | cut -f1)
    echo ""
    echo -e "${GREEN}✓ Экспорт завершен успешно!${NC}"
    echo ""
    echo "Файл: $FULL_PATH"
    echo "Размер: $FILE_SIZE"
    echo ""
    echo -e "${YELLOW}Следующие шаги:${NC}"
    echo "1. Скопируйте этот файл на сервер:"
    echo "   scp $FULL_PATH user@your-server:/path/to/backups/"
    echo ""
    echo "2. На сервере выполните импорт:"
    echo "   ./scripts/import_db.sh /path/to/backups/$OUTPUT_FILE"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Ошибка при экспорте БД${NC}"
    exit 1
fi
