#!/bin/bash
# Быстрое исправление memory limit без rebuild контейнера

SERVER="root@93.189.228.52"

echo "=== ИСПРАВЛЕНИЕ MEMORY LIMIT ==="
echo ""
echo "Текущая проблема: Backend использует 374MB/512MB (73%)"
echo "Решение: Увеличить лимит до 768MB"
echo ""

read -p "Продолжить? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo "1. Найти backend контейнер..."
BACKEND_CONTAINER=$(ssh "$SERVER" "docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -n 1")

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Backend контейнер не найден!"
    exit 1
fi

echo "   Найден: $BACKEND_CONTAINER"
echo ""

echo "2. Проверить текущий лимит памяти..."
CURRENT_LIMIT=$(ssh "$SERVER" "docker inspect $BACKEND_CONTAINER --format='{{.HostConfig.Memory}}'" | awk '{print $1/1024/1024 "MB"}')
echo "   Текущий лимит: $CURRENT_LIMIT"
echo ""

echo "3. ВАЖНО: Docker не позволяет изменить лимиты памяти для запущенного контейнера"
echo "   Нужно пересоздать контейнер с новыми лимитами"
echo ""

echo "Варианты:"
echo "A. Пересоздать через Coolify (рекомендуется)"
echo "B. Пересоздать вручную через docker-compose"
echo "C. Временно увеличить SWAP (не решает проблему полностью)"
echo ""

read -p "Выберите вариант (A/B/C): " choice

case $choice in
    [Aa])
        echo ""
        echo "✅ Вариант A: Через Coolify"
        echo ""
        echo "Шаги:"
        echo "1. Закоммитить изменения:"
        echo "   git add docker-compose.prod.yml"
        echo "   git commit -m 'fix: increase memory limit to 768MB'"
        echo "   git push origin main"
        echo ""
        echo "2. Coolify автоматически задеплоит через webhook"
        echo "   ИЛИ вручную: зайти в Coolify UI и нажать 'Redeploy'"
        echo ""
        ;;

    [Bb])
        echo ""
        echo "✅ Вариант B: Вручную через docker-compose"
        echo ""
        echo "Выполняется на сервере..."

        # Найти путь к проекту
        PROJECT_PATH=$(ssh "$SERVER" "docker inspect $BACKEND_CONTAINER --format='{{.Config.Labels.\"com.docker.compose.project.working_dir\"}}'" 2>/dev/null)

        if [ -z "$PROJECT_PATH" ]; then
            echo "⚠️  Не удалось определить путь к проекту автоматически"
            echo ""
            echo "Выполните вручную на сервере:"
            echo "  ssh $SERVER"
            echo "  cd /path/to/project  # Найти через: docker inspect $BACKEND_CONTAINER"
            echo "  git pull origin main"
            echo "  docker-compose -f docker-compose.prod.yml up -d --force-recreate --no-deps backend"
            exit 1
        fi

        echo "   Путь к проекту: $PROJECT_PATH"
        echo ""

        ssh "$SERVER" bash << ENDSSH
set -e
cd "$PROJECT_PATH"

echo "   Pulling latest changes..."
git pull origin main

echo "   Recreating backend container..."
docker-compose -f docker-compose.prod.yml up -d --force-recreate --no-deps backend

echo "   Waiting for backend to start..."
sleep 10

echo "   Checking status..."
docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format 'table {{.Names}}\t{{.Status}}'

echo ""
echo "   Checking new memory limit..."
BACKEND=\$(docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -n 1)
docker inspect \$BACKEND --format='Memory limit: {{.HostConfig.Memory}}' | awk '{print \$1, \$2/1024/1024 "MB"}'

echo ""
echo "   Current memory usage..."
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}' | grep backend
ENDSSH

        echo ""
        echo "✅ Backend пересоздан с новым лимитом памяти!"
        ;;

    [Cc])
        echo ""
        echo "✅ Вариант C: Увеличить SWAP (временное решение)"
        echo ""
        echo "SWAP уже настроен (2GB)"
        ssh "$SERVER" "swapon --show"
        echo ""
        echo "⚠️  Это НЕ решает проблему с docker memory limit!"
        echo "   Нужно все равно увеличить лимит через вариант A или B"
        ;;

    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "=== ГОТОВО ==="
