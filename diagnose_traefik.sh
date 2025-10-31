#!/bin/bash
# Диагностика Traefik и связи с бэкендом

echo "========================================="
echo "Диагностика Traefik и Backend"
echo "========================================="
echo ""

# Найти docker-compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif command -v docker &> /dev/null; then
    DC="docker compose"
else
    echo "❌ Docker не найден"
    exit 1
fi

COMPOSE_FILE=""
for file in docker-compose.prod.yml docker-compose.yml; do
    if [ -f "$file" ]; then
        COMPOSE_FILE="$file"
        break
    fi
done

echo "Используется: $COMPOSE_FILE"
echo ""

# 1. Проверка статуса контейнеров
echo "========================================="
echo "1. Статус контейнеров"
echo "========================================="
$DC -f $COMPOSE_FILE ps
echo ""

# 2. Проверка Traefik
echo "========================================="
echo "2. Проверка Traefik"
echo "========================================="
if docker ps | grep -q traefik; then
    echo "✅ Traefik запущен"
    TRAEFIK_CONTAINER=$(docker ps --filter "name=traefik" --format "{{.Names}}" | head -1)
    echo "Контейнер: $TRAEFIK_CONTAINER"
else
    echo "❌ Traefik НЕ запущен!"
    echo ""
    echo "Это критическая проблема! Без Traefik запросы не доходят до backend/frontend."
    exit 1
fi
echo ""

# 3. Проверка backend контейнера
echo "========================================="
echo "3. Backend контейнер"
echo "========================================="
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -1)
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "✅ Backend запущен: $BACKEND_CONTAINER"

    # Проверка healthcheck
    echo ""
    echo "Healthcheck status:"
    docker inspect $BACKEND_CONTAINER --format='{{.State.Health.Status}}' 2>/dev/null || echo "No healthcheck configured"

    # Проверка внутреннего API
    echo ""
    echo "Тест API изнутри контейнера:"
    docker exec $BACKEND_CONTAINER curl -s http://localhost:8000/health 2>/dev/null || echo "❌ API не отвечает внутри контейнера!"
else
    echo "❌ Backend НЕ запущен!"
    exit 1
fi
echo ""

# 4. Проверка сети
echo "========================================="
echo "4. Сетевая конфигурация"
echo "========================================="
echo "Backend IP:"
docker inspect $BACKEND_CONTAINER --format='{{range .NetworkSettings.Networks}}{{.IPAddress}} ({{.NetworkID}}){{"\n"}}{{end}}'

echo ""
echo "Traefik IP:"
docker inspect $TRAEFIK_CONTAINER --format='{{range .NetworkSettings.Networks}}{{.IPAddress}} ({{.NetworkID}}){{"\n"}}{{end}}'

echo ""
echo "Общие сети:"
BACKEND_NETS=$(docker inspect $BACKEND_CONTAINER --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}')
TRAEFIK_NETS=$(docker inspect $TRAEFIK_CONTAINER --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}')

echo "Backend сети: $BACKEND_NETS"
echo "Traefik сети: $TRAEFIK_NETS"

# Проверка что они в одной сети
for net in $BACKEND_NETS; do
    if echo "$TRAEFIK_NETS" | grep -q "$net"; then
        echo "✅ Общая сеть найдена: $net"
        COMMON_NETWORK="$net"
    fi
done

if [ -z "$COMMON_NETWORK" ]; then
    echo "❌ КРИТИЧЕСКАЯ ОШИБКА: Backend и Traefik НЕ в одной сети!"
    echo "   Traefik не может достучаться до Backend!"
fi
echo ""

# 5. Проверка Traefik labels на backend
echo "========================================="
echo "5. Traefik Labels на Backend"
echo "========================================="
docker inspect $BACKEND_CONTAINER --format='{{range $key, $value := .Config.Labels}}{{if or (contains $key "traefik")}}{{$key}}={{$value}}{{"\n"}}{{end}}{{end}}' | sort
echo ""

# 6. Проверка Traefik логов
echo "========================================="
echo "6. Traefik Логи (последние 30 строк)"
echo "========================================="
docker logs $TRAEFIK_CONTAINER --tail=30 2>&1 | grep -E "backend|error|503" || echo "Нет ошибок связанных с backend"
echo ""

# 7. Попытка обратиться от Traefik к Backend
echo "========================================="
echo "7. Тест связи: Traefik → Backend"
echo "========================================="
echo "Попытка curl от Traefik к Backend:"
if [ -n "$COMMON_NETWORK" ]; then
    BACKEND_IP=$(docker inspect $BACKEND_CONTAINER --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | head -1)
    docker exec $TRAEFIK_CONTAINER wget -O- -T 5 http://$BACKEND_IP:8000/health 2>&1 || echo "❌ Traefik не может достучаться до Backend!"
else
    echo "❌ Пропущено - нет общей сети"
fi
echo ""

# 8. Проверка внешнего доступа к API
echo "========================================="
echo "8. Внешний доступ к API"
echo "========================================="
echo "Тест: https://api.budget-west.shknv.ru/health"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://api.budget-west.shknv.ru/health
echo ""
echo "Детали:"
curl -v https://api.budget-west.shknv.ru/health 2>&1 | head -30
echo ""

# 9. Проверка OPTIONS запроса
echo "========================================="
echo "9. Тест OPTIONS (CORS Preflight)"
echo "========================================="
echo "Тест: OPTIONS /api/v1/auth/login"
curl -v -X OPTIONS https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Origin: https://budget-west.shknv.ru" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  2>&1 | grep -E "HTTP|< |access-control" | head -15
echo ""

# 10. Рекомендации
echo "========================================="
echo "10. Диагноз и Рекомендации"
echo "========================================="
echo ""

# Проверяем проблемы
ISSUES=()

# Проверка Traefik
if ! docker ps | grep -q traefik; then
    ISSUES+=("❌ Traefik не запущен - запустите: docker start traefik")
fi

# Проверка Backend
HEALTH=$(docker inspect $BACKEND_CONTAINER --format='{{.State.Health.Status}}' 2>/dev/null)
if [ "$HEALTH" != "healthy" ]; then
    ISSUES+=("❌ Backend healthcheck failed - проверьте логи: docker logs $BACKEND_CONTAINER")
fi

# Проверка сети
if [ -z "$COMMON_NETWORK" ]; then
    ISSUES+=("❌ Backend и Traefik в разных сетях - нужно пересоздать контейнеры")
fi

# Проверка внешнего доступа
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.budget-west.shknv.ru/health 2>/dev/null)
if [ "$HTTP_CODE" != "200" ]; then
    ISSUES+=("❌ API возвращает HTTP $HTTP_CODE вместо 200")
fi

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo "✅ Все проверки пройдены!"
    echo ""
    echo "Если сайт всё равно не работает, проблема может быть в:"
    echo "1. DNS - проверьте: nslookup api.budget-west.shknv.ru"
    echo "2. SSL - проверьте сертификаты в Traefik"
    echo "3. CORS - проверьте переменную CORS_ORIGINS в backend"
else
    echo "Найдены проблемы:"
    for issue in "${ISSUES[@]}"; do
        echo "$issue"
    done
    echo ""
    echo "Исправьте проблемы выше и повторите диагностику."
fi

echo ""
echo "========================================="
echo "Диагностика завершена"
echo "========================================="
