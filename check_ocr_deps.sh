#!/bin/bash
# Скрипт проверки наличия OCR зависимостей в production контейнере

echo "=== Проверка зависимостей для OCR и PDF обработки ==="
echo ""

# Найти имя backend контейнера
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --filter "status=running" --format "{{.Names}}" | head -n 1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Backend контейнер не найден или не запущен"
    echo ""
    echo "Доступные контейнеры:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    exit 1
fi

echo "✅ Найден backend контейнер: $BACKEND_CONTAINER"
echo ""

# Проверка poppler-utils
echo "Проверка poppler-utils..."
if docker exec "$BACKEND_CONTAINER" which pdfinfo > /dev/null 2>&1; then
    VERSION=$(docker exec "$BACKEND_CONTAINER" pdfinfo -v 2>&1 | head -n 1)
    echo "✅ poppler-utils установлен: $VERSION"
else
    echo "❌ poppler-utils НЕ установлен"
fi

# Проверка tesseract-ocr
echo ""
echo "Проверка tesseract-ocr..."
if docker exec "$BACKEND_CONTAINER" which tesseract > /dev/null 2>&1; then
    VERSION=$(docker exec "$BACKEND_CONTAINER" tesseract --version 2>&1 | head -n 1)
    echo "✅ tesseract-ocr установлен: $VERSION"

    # Проверка русского языка
    echo ""
    echo "Проверка языковых пакетов..."
    LANGS=$(docker exec "$BACKEND_CONTAINER" tesseract --list-langs 2>&1 | tail -n +2)
    echo "Доступные языки:"
    echo "$LANGS"

    if echo "$LANGS" | grep -q "rus"; then
        echo "✅ Русский язык (rus) установлен"
    else
        echo "❌ Русский язык (rus) НЕ установлен"
    fi

    if echo "$LANGS" | grep -q "eng"; then
        echo "✅ Английский язык (eng) установлен"
    else
        echo "❌ Английский язык (eng) НЕ установлен"
    fi
else
    echo "❌ tesseract-ocr НЕ установлен"
fi

# Проверка Python зависимостей
echo ""
echo "Проверка Python библиотек..."
docker exec "$BACKEND_CONTAINER" pip list | grep -E "pdf2image|pytesseract|pypdf|Pillow"

echo ""
echo "=== Проверка завершена ==="
