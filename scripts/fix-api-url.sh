#!/bin/bash

echo "================================================"
echo "Fixing API URL Configuration (307 Redirect Fix)"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Диагностика проблемы...${NC}"
echo ""

# Check if we're on the server
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не найден. Этот скрипт должен выполняться на сервере.${NC}"
    echo "Подключитесь к серверу: ssh root@93.189.228.52"
    exit 1
fi

echo "✅ Docker найден"
echo ""

# Check current env-config.js in running container
echo -e "${YELLOW}Проверяю текущую конфигурацию в контейнере...${NC}"
if docker ps | grep -q it_budget_frontend_prod; then
    echo "Текущий env-config.js:"
    docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js 2>/dev/null || echo "❌ Не удалось прочитать файл"
    echo ""
else
    echo -e "${RED}❌ Контейнер it_budget_frontend_prod не запущен${NC}"
fi

echo ""
echo -e "${YELLOW}Выберите решение:${NC}"
echo "1) Использовать nginx proxy (РЕКОМЕНДУЕТСЯ) - VITE_API_URL=/api"
echo "2) Использовать прямой HTTPS URL - VITE_API_URL=https://api.budget-west.shknv.ru"
echo "3) Показать текущие переменные окружения"
echo "4) Только перезапустить frontend"
echo "5) Выход"
echo ""

read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Устанавливаю VITE_API_URL=/api (nginx proxy)${NC}"

        # Update docker-compose.prod.yml or set environment variable
        export VITE_API_URL="/api"

        echo "Останавливаю frontend..."
        docker-compose down frontend 2>/dev/null || docker stop it_budget_frontend_prod 2>/dev/null

        echo "Пересоздаю контейнер с новой конфигурацией..."
        VITE_API_URL="/api" docker-compose up -d frontend

        echo ""
        echo "Ждём 5 секунд..."
        sleep 5

        echo ""
        echo "Проверяю результат:"
        docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js

        echo ""
        echo -e "${GREEN}✅ Готово!${NC}"
        echo "Теперь frontend использует nginx proxy."
        echo "API запросы идут через: https://budget-west.shknv.ru/api/v1/..."
        ;;

    2)
        echo ""
        echo -e "${GREEN}Устанавливаю VITE_API_URL=https://api.budget-west.shknv.ru${NC}"

        export VITE_API_URL="https://api.budget-west.shknv.ru"

        echo "Останавливаю frontend..."
        docker-compose down frontend 2>/dev/null || docker stop it_budget_frontend_prod 2>/dev/null

        echo "Пересоздаю контейнер с новой конфигурацией..."
        VITE_API_URL="https://api.budget-west.shknv.ru" docker-compose up -d frontend

        echo ""
        echo "Ждём 5 секунд..."
        sleep 5

        echo ""
        echo "Проверяю результат:"
        docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js

        echo ""
        echo -e "${GREEN}✅ Готово!${NC}"
        echo "Теперь frontend использует прямой HTTPS URL."
        echo "Убедитесь что в backend правильно настроен CORS!"
        ;;

    3)
        echo ""
        echo "Переменные окружения контейнера:"
        docker exec it_budget_frontend_prod env | grep -i vite
        echo ""

        echo "Переменные окружения shell:"
        env | grep -i vite
        ;;

    4)
        echo ""
        echo "Перезапускаю frontend..."
        docker-compose restart frontend

        echo ""
        echo "Ждём 5 секунд..."
        sleep 5

        echo ""
        echo "Проверяю результат:"
        docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js
        ;;

    5)
        echo "Выход."
        exit 0
        ;;

    *)
        echo -e "${RED}Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Дополнительные проверки:${NC}"
echo ""

# Check if container is running
if docker ps | grep -q it_budget_frontend_prod; then
    echo "✅ Контейнер frontend запущен"
else
    echo "❌ Контейнер frontend НЕ запущен"
fi

# Check nginx config endpoint
echo ""
echo "Проверка через curl (internal):"
curl -s http://127.0.0.1:3001/config-check || echo "❌ Не удалось получить конфигурацию"

echo ""
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Что делать дальше:${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "1. Откройте браузер в режиме Инкогнито: Ctrl+Shift+N"
echo "2. Зайдите на https://budget-west.shknv.ru"
echo "3. Откройте DevTools (F12) → Console"
echo "4. Выполните: console.log(window.ENV_CONFIG)"
echo "5. Убедитесь что VITE_API_URL правильный"
echo ""
echo "Если всё ещё ошибка 307:"
echo "- Очистите кеш браузера: Ctrl+Shift+Delete"
echo "- Или используйте режим Инкогнито"
echo ""
