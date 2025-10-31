#!/bin/bash
# Быстрая диагностика - что именно не работает

echo "========================================="
echo "БЫСТРАЯ ДИАГНОСТИКА - Load Failed"
echo "========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Найти docker-compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif command -v docker &> /dev/null; then
    DC="docker compose"
else
    echo -e "${RED}❌ Docker не найден${NC}"
    exit 1
fi

COMPOSE_FILE="docker-compose.prod.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.yml"
fi

echo "Используется: $COMPOSE_FILE"
echo ""

# 1. Проверка контейнеров
echo "========================================="
echo "1. СТАТУС КОНТЕЙНЕРОВ"
echo "========================================="
$DC -f $COMPOSE_FILE ps
echo ""

# Подсчёт работающих контейнеров
BACKEND_STATUS=$($DC -f $COMPOSE_FILE ps backend 2>/dev/null | grep -c "Up")
FRONTEND_STATUS=$($DC -f $COMPOSE_FILE ps frontend 2>/dev/null | grep -c "Up")
DB_STATUS=$($DC -f $COMPOSE_FILE ps db 2>/dev/null | grep -c "Up")

if [ "$BACKEND_STATUS" -eq 0 ]; then
    echo -e "${RED}❌ Backend НЕ ЗАПУЩЕН - это критично!${NC}"
    echo ""
    echo "РЕШЕНИЕ:"
    echo "docker-compose -f $COMPOSE_FILE up -d backend"
    echo ""
fi

if [ "$FRONTEND_STATUS" -eq 0 ]; then
    echo -e "${RED}❌ Frontend НЕ ЗАПУЩЕН${NC}"
    echo ""
fi

if [ "$DB_STATUS" -eq 0 ]; then
    echo -e "${RED}❌ Database НЕ ЗАПУЩЕНА${NC}"
    echo ""
fi

# 2. Проверка изменений применены ли
echo "========================================="
echo "2. ПРОВЕРКА ИЗМЕНЕНИЙ (git log)"
echo "========================================="
CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null)
echo "Текущий коммит: $CURRENT_COMMIT"
echo ""
echo "Последние 3 коммита:"
git log --oneline -3 2>/dev/null || echo "Git не доступен"
echo ""

if git log --oneline -1 | grep -q "Traefik CORS"; then
    echo -e "${GREEN}✅ Изменения ПРИМЕНЕНЫ (есть коммит про Traefik CORS)${NC}"
else
    echo -e "${YELLOW}⚠️  Возможно изменения НЕ применены${NC}"
    echo "Нужно: git pull origin claude/fix-login-preflight-error-011CUf7ZUKWBMJkHRvpy7bKf"
fi
echo ""

# 3. Проверка Backend внутри контейнера
echo "========================================="
echo "3. BACKEND HEALTH (внутри контейнера)"
echo "========================================="
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -1)
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Backend контейнер: $BACKEND_CONTAINER"
    HEALTH=$(docker exec $BACKEND_CONTAINER curl -s http://localhost:8000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✅ Backend отвечает внутри контейнера: $HEALTH${NC}"
    else
        echo -e "${RED}❌ Backend НЕ отвечает внутри контейнера!${NC}"
        echo "Ответ: $HEALTH"
        echo ""
        echo "Проверьте логи:"
        echo "docker logs $BACKEND_CONTAINER --tail=50"
    fi
else
    echo -e "${RED}❌ Backend контейнер не найден!${NC}"
fi
echo ""

# 4. Проверка Traefik
echo "========================================="
echo "4. TRAEFIK"
echo "========================================="
if docker ps | grep -q traefik; then
    TRAEFIK_CONTAINER=$(docker ps --filter "name=traefik" --format "{{.Names}}" | head -1)
    echo -e "${GREEN}✅ Traefik запущен: $TRAEFIK_CONTAINER${NC}"

    # Проверить связь Traefik → Backend
    if [ -n "$BACKEND_CONTAINER" ]; then
        BACKEND_IP=$(docker inspect $BACKEND_CONTAINER --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | head -1)
        echo ""
        echo "Backend IP: $BACKEND_IP"
        echo "Проверка связи Traefik → Backend:"
        docker exec $TRAEFIK_CONTAINER wget -O- -T 3 http://$BACKEND_IP:8000/health 2>&1 | grep -E "200|healthy" && echo -e "${GREEN}✅ Связь есть${NC}" || echo -e "${RED}❌ Связи нет!${NC}"
    fi
else
    echo -e "${RED}❌ Traefik НЕ ЗАПУЩЕН - сайт не может работать без Traefik!${NC}"
    echo ""
    echo "РЕШЕНИЕ:"
    echo "В Coolify проверьте что Traefik запущен"
    echo "Или запустите вручную: docker start traefik"
fi
echo ""

# 5. Внешний доступ к API
echo "========================================="
echo "5. ВНЕШНИЙ ДОСТУП К API"
echo "========================================="
echo "Тест: https://api.budget-west.shknv.ru/health"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.budget-west.shknv.ru/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ API доступен (HTTP $HTTP_CODE)${NC}"
    curl -s https://api.budget-west.shknv.ru/health
else
    echo -e "${RED}❌ API недоступен (HTTP $HTTP_CODE)${NC}"
    echo ""
    echo "Подробности:"
    curl -v https://api.budget-west.shknv.ru/health 2>&1 | head -20
fi
echo ""

# 6. Внешний доступ к Frontend
echo "========================================="
echo "6. ВНЕШНИЙ ДОСТУП К FRONTEND"
echo "========================================="
echo "Тест: https://budget-west.shknv.ru"
FRONTEND_HTTP=$(curl -s -o /dev/null -w "%{http_code}" https://budget-west.shknv.ru 2>/dev/null)
if [ "$FRONTEND_HTTP" = "200" ]; then
    echo -e "${GREEN}✅ Frontend доступен (HTTP $FRONTEND_HTTP)${NC}"
else
    echo -e "${RED}❌ Frontend недоступен (HTTP $FRONTEND_HTTP)${NC}"
    echo ""
    echo "Подробности:"
    curl -v https://budget-west.shknv.ru 2>&1 | head -20
fi
echo ""

# 7. Последние логи
echo "========================================="
echo "7. ПОСЛЕДНИЕ ЛОГИ (проблемы)"
echo "========================================="

if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Backend логи (ошибки):"
    docker logs $BACKEND_CONTAINER --tail=30 2>&1 | grep -iE "error|exception|failed|traceback" || echo -e "${GREEN}Ошибок нет${NC}"
    echo ""
fi

FRONTEND_CONTAINER=$(docker ps --filter "name=frontend" --format "{{.Names}}" | head -1)
if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "Frontend логи (ошибки):"
    docker logs $FRONTEND_CONTAINER --tail=20 2>&1 | grep -iE "error|failed" || echo -e "${GREEN}Ошибок нет${NC}"
    echo ""
fi

# 8. Резюме и рекомендации
echo "========================================="
echo "8. РЕЗЮМЕ И ДЕЙСТВИЯ"
echo "========================================="
echo ""

# Собрать все проблемы
ISSUES=()

if [ "$BACKEND_STATUS" -eq 0 ]; then
    ISSUES+=("Backend не запущен")
fi

if [ "$FRONTEND_STATUS" -eq 0 ]; then
    ISSUES+=("Frontend не запущен")
fi

if [ "$DB_STATUS" -eq 0 ]; then
    ISSUES+=("Database не запущена")
fi

if ! docker ps | grep -q traefik; then
    ISSUES+=("Traefik не запущен")
fi

if [ "$HTTP_CODE" != "200" ]; then
    ISSUES+=("API недоступен извне (HTTP $HTTP_CODE)")
fi

if [ "$FRONTEND_HTTP" != "200" ]; then
    ISSUES+=("Frontend недоступен извне (HTTP $FRONTEND_HTTP)")
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЁ РАБОТАЕТ! Проблем не найдено.${NC}"
    echo ""
    echo "Если в браузере всё равно 'Load failed', попробуйте:"
    echo "1. Очистить кеш браузера (Ctrl+F5)"
    echo "2. Открыть в режиме инкогнито"
    echo "3. Проверить DevTools → Console на ошибки"
    echo "4. Проверить DevTools → Network что запросы идут"
else
    echo -e "${RED}Найдены проблемы:${NC}"
    for issue in "${ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
    echo -e "${YELLOW}ДЕЙСТВИЯ ДЛЯ ИСПРАВЛЕНИЯ:${NC}"
    echo ""

    if [ "$BACKEND_STATUS" -eq 0 ] || [ "$FRONTEND_STATUS" -eq 0 ] || [ "$DB_STATUS" -eq 0 ]; then
        echo "1. Запустить контейнеры:"
        echo "   docker-compose -f $COMPOSE_FILE up -d"
        echo ""
    fi

    if ! docker ps | grep -q traefik; then
        echo "2. Запустить Traefik (через Coolify или вручную):"
        echo "   docker start traefik"
        echo ""
    fi

    if [ "$HTTP_CODE" != "200" ]; then
        echo "3. Если API не доступен - проверить логи:"
        echo "   docker logs $BACKEND_CONTAINER --tail=100"
        echo ""
        echo "   Или перезапустить:"
        echo "   docker-compose -f $COMPOSE_FILE restart backend"
        echo ""
    fi

    echo "4. Если ничего не помогает - полный перезапуск:"
    echo "   docker-compose -f $COMPOSE_FILE down"
    echo "   docker-compose -f $COMPOSE_FILE up -d"
    echo ""
fi

echo "========================================="
echo "ДИАГНОСТИКА ЗАВЕРШЕНА"
echo "========================================="
