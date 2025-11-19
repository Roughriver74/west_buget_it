#!/bin/bash
# Удаленная проверка OCR зависимостей на production сервере

SERVER="root@93.189.228.52"
PROJECT_DIR="/root/acme_buget_it"  # Измените на ваш путь

echo "=== Проверка OCR зависимостей на production сервере ==="
echo ""
echo "Сервер: $SERVER"
echo "Проект: $PROJECT_DIR"
echo ""

# Проверка подключения к серверу
echo "Подключаюсь к серверу..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Не удалось подключиться к серверу $SERVER"
    echo ""
    echo "Проверьте:"
    echo "1. SSH доступ: ssh $SERVER"
    echo "2. Правильность адреса сервера"
    exit 1
fi

echo "✅ Подключение установлено"
echo ""

# Найти backend контейнер
echo "Поиск backend контейнера..."
BACKEND_CONTAINER=$(ssh "$SERVER" "docker ps --filter 'name=backend' --filter 'status=running' --format '{{.Names}}' | head -n 1")

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Backend контейнер не найден или не запущен"
    echo ""
    echo "Доступные контейнеры:"
    ssh "$SERVER" "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
    exit 1
fi

echo "✅ Найден backend контейнер: $BACKEND_CONTAINER"
echo ""

# Проверка poppler-utils
echo "Проверка poppler-utils..."
if ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' which pdfinfo" > /dev/null 2>&1; then
    VERSION=$(ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' pdfinfo -v 2>&1 | head -n 1")
    echo "✅ poppler-utils установлен: $VERSION"
else
    echo "❌ poppler-utils НЕ установлен - ТРЕБУЕТСЯ REBUILD!"
    echo ""
    echo "Выполните rebuild контейнера:"
    echo "  ssh $SERVER 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml build backend && docker-compose -f docker-compose.prod.yml up -d backend'"
fi

# Проверка tesseract-ocr
echo ""
echo "Проверка tesseract-ocr..."
if ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' which tesseract" > /dev/null 2>&1; then
    VERSION=$(ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' tesseract --version 2>&1 | head -n 1")
    echo "✅ tesseract-ocr установлен: $VERSION"

    # Проверка языковых пакетов
    echo ""
    echo "Проверка языковых пакетов..."
    LANGS=$(ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' tesseract --list-langs 2>&1 | tail -n +2")

    if echo "$LANGS" | grep -q "rus"; then
        echo "✅ Русский язык (rus) установлен"
    else
        echo "❌ Русский язык (rus) НЕ установлен - ТРЕБУЕТСЯ REBUILD!"
    fi

    if echo "$LANGS" | grep -q "eng"; then
        echo "✅ Английский язык (eng) установлен"
    else
        echo "❌ Английский язык (eng) НЕ установлен - ТРЕБУЕТСЯ REBUILD!"
    fi
else
    echo "❌ tesseract-ocr НЕ установлен - ТРЕБУЕТСЯ REBUILD!"
    echo ""
    echo "Выполните rebuild контейнера:"
    echo "  ssh $SERVER 'cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml build backend && docker-compose -f docker-compose.prod.yml up -d backend'"
fi

# Проверка Python библиотек
echo ""
echo "Проверка Python библиотек..."
ssh "$SERVER" "docker exec '$BACKEND_CONTAINER' pip list | grep -E 'pdf2image|pytesseract|pypdf|Pillow'"

# Проверка последнего build времени
echo ""
echo "Информация о контейнере:"
ssh "$SERVER" "docker inspect '$BACKEND_CONTAINER' --format 'Created: {{.Created}}' | head -n 1"
ssh "$SERVER" "docker inspect '$BACKEND_CONTAINER' --format 'Image: {{.Config.Image}}'"

# Проверка Dockerfile в репозитории
echo ""
echo "Проверка актуальности кода на сервере..."
REMOTE_COMMIT=$(ssh "$SERVER" "cd $PROJECT_DIR && git rev-parse HEAD")
LOCAL_COMMIT=$(git rev-parse HEAD)

if [ "$REMOTE_COMMIT" = "$LOCAL_COMMIT" ]; then
    echo "✅ Код на сервере актуален (commit: ${REMOTE_COMMIT:0:7})"
else
    echo "⚠️  Код на сервере устарел!"
    echo "   Локальный commit:  ${LOCAL_COMMIT:0:7}"
    echo "   Удаленный commit:  ${REMOTE_COMMIT:0:7}"
    echo ""
    echo "Обновите код на сервере:"
    echo "  ssh $SERVER 'cd $PROJECT_DIR && git pull origin main'"
fi

echo ""
echo "=== Проверка завершена ==="
echo ""
echo "📋 Быстрые команды:"
echo ""
echo "  # Rebuild backend на сервере:"
echo "  ssh $SERVER 'cd $PROJECT_DIR && git pull origin main && docker-compose -f docker-compose.prod.yml build --no-cache backend && docker-compose -f docker-compose.prod.yml up -d backend'"
echo ""
echo "  # Проверить логи:"
echo "  ssh $SERVER 'docker logs $BACKEND_CONTAINER -f --tail 100'"
echo ""
echo "  # Полная документация:"
echo "  cat DEPLOY_OCR_FIX.md"
