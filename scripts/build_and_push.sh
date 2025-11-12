#!/bin/bash
# Локальная сборка Docker образа и загрузка на production сервер
# Используется когда на сервере недостаточно памяти для сборки

set -e

SERVER="root@93.189.228.52"
IMAGE_NAME="it-budget-backend"
IMAGE_TAG="prod"
TARBALL="${IMAGE_NAME}-${IMAGE_TAG}.tar"

echo "=== Локальная сборка и отправка Docker образа на production ==="
echo ""
echo "Сервер: $SERVER"
echo "Образ: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Проверка что мы в правильной директории
if [ ! -f "backend/Dockerfile.prod" ]; then
    echo "❌ Ошибка: Запустите скрипт из корня проекта"
    exit 1
fi

# Выбор Dockerfile
echo "Выберите Dockerfile для сборки:"
echo "1. Dockerfile.prod (стандартный)"
echo "2. Dockerfile.prod.optimized (оптимизированный для малой памяти)"
echo ""
read -p "Выбор (1 или 2, по умолчанию 2): " dockerfile_choice

DOCKERFILE="backend/Dockerfile.prod.optimized"
if [ "$dockerfile_choice" = "1" ]; then
    DOCKERFILE="backend/Dockerfile.prod"
fi

echo ""
echo "Используется: $DOCKERFILE"
echo ""

# Шаг 1: Сборка образа локально
echo "=== Шаг 1: Сборка Docker образа локально ==="
echo ""

cd backend

# Проверка доступности Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен или недоступен"
    exit 1
fi

# Сборка
echo "Сборка образа..."
if [ "$DOCKERFILE" = "backend/Dockerfile.prod.optimized" ]; then
    docker build -f Dockerfile.prod.optimized -t "${IMAGE_NAME}:${IMAGE_TAG}" .
else
    docker build -f Dockerfile.prod -t "${IMAGE_NAME}:${IMAGE_TAG}" .
fi

echo ""
echo "✅ Образ собран локально"
echo ""

cd ..

# Шаг 2: Экспорт образа в tarball
echo "=== Шаг 2: Экспорт образа в файл ==="
echo ""

if [ -f "$TARBALL" ]; then
    echo "Удаление старого файла..."
    rm "$TARBALL"
fi

echo "Экспорт образа (это может занять несколько минут)..."
docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "$TARBALL"

TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)
echo ""
echo "✅ Образ экспортирован: $TARBALL ($TARBALL_SIZE)"
echo ""

# Шаг 3: Загрузка на сервер
echo "=== Шаг 3: Загрузка образа на сервер ==="
echo ""

echo "Загрузка файла на сервер (это может занять несколько минут)..."
scp "$TARBALL" "${SERVER}:/tmp/${TARBALL}"

echo ""
echo "✅ Файл загружен на сервер"
echo ""

# Шаг 4: Импорт образа на сервере
echo "=== Шаг 4: Импорт образа на сервере ==="
echo ""

ssh "$SERVER" bash << ENDSSH
set -e

echo "Импорт образа..."
docker load -i /tmp/${TARBALL}

echo ""
echo "Удаление временного файла..."
rm /tmp/${TARBALL}

echo ""
echo "Проверка образа..."
docker images | grep "${IMAGE_NAME}"

echo ""
echo "✅ Образ импортирован на сервер"
ENDSSH

echo ""

# Шаг 5: Перезапуск контейнера
echo "=== Шаг 5: Перезапуск backend контейнера ==="
echo ""

read -p "Перезапустить backend контейнер сейчас? (y/N): " restart_confirm

if [[ "$restart_confirm" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Перезапуск контейнера..."

    ssh "$SERVER" bash << 'ENDSSH'
set -e

# Найти имя backend контейнера
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -n 1)

if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Остановка контейнера: $BACKEND_CONTAINER"
    docker stop "$BACKEND_CONTAINER"

    echo "Удаление контейнера: $BACKEND_CONTAINER"
    docker rm "$BACKEND_CONTAINER"
fi

# Если используется docker-compose
if [ -d "/root/west_buget_it" ]; then
    cd /root/west_buget_it
    echo "Запуск через docker-compose..."
    docker-compose -f docker-compose.prod.yml up -d backend
else
    echo "⚠️  docker-compose.prod.yml не найден"
    echo "Запустите backend контейнер вручную"
fi

# Проверка статуса
echo ""
echo "Статус контейнера:"
docker ps | grep backend

ENDSSH

    echo ""
    echo "✅ Backend контейнер перезапущен"
else
    echo ""
    echo "⚠️  Контейнер не перезапущен"
    echo ""
    echo "Для перезапуска выполните на сервере:"
    echo "  ssh $SERVER 'cd /root/west_buget_it && docker-compose -f docker-compose.prod.yml up -d backend'"
fi

# Очистка локального tarball
echo ""
echo "=== Очистка ==="
echo ""

read -p "Удалить локальный файл образа ($TARBALL)? (Y/n): " cleanup_confirm

if [[ ! "$cleanup_confirm" =~ ^[Nn]$ ]]; then
    rm "$TARBALL"
    echo "✅ Локальный файл удален"
else
    echo "⚠️  Файл сохранен: $TARBALL"
fi

echo ""
echo "=== Деплой завершен! ==="
echo ""
echo "Проверьте работу:"
echo "  ./check_ocr_remote.sh"
echo ""
echo "Или проверьте логи:"
echo "  ssh $SERVER 'docker logs \$(docker ps --filter name=backend -q) -f'"
echo ""
