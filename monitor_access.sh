#!/bin/bash
# Непрерывный мониторинг доступности приложения для отслеживания момента потери доступа

SERVER="root@93.189.228.52"
FRONTEND_URL="https://budget-west.shknv.ru"
BACKEND_URL="https://budget-west.shknv.ru/api/v1/health"
CHECK_INTERVAL=30  # Проверка каждые 30 секунд
LOG_FILE="./monitoring_$(date +%Y%m%d_%H%M%S).log"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 Начинаю мониторинг доступности приложения"
log "Интервал проверки: ${CHECK_INTERVAL}s"
log "Frontend: $FRONTEND_URL"
log "Backend: $BACKEND_URL"
log "Лог файл: $LOG_FILE"
log "---"

CONSECUTIVE_FAILURES=0
LAST_STATUS="unknown"
START_TIME=$(date +%s)

check_memory() {
    # Проверка памяти на сервере
    MEMORY_INFO=$(ssh "$SERVER" "free -m | awk '/^Mem:/ {printf \"Used: %d MB / %d MB (%.0f%%)\", \$3, \$2, \$3/\$2*100}'")
    echo "$MEMORY_INFO"
}

check_containers() {
    # Проверка статуса контейнеров
    CONTAINER_COUNT=$(ssh "$SERVER" "docker ps --filter 'name=io00swck8gss4kosckwwwo88' --format '{{.Names}}' | wc -l")
    echo "Контейнеров запущено: $CONTAINER_COUNT"
}

check_health() {
    # Проверка healthcheck статуса
    UNHEALTHY=$(ssh "$SERVER" "docker ps --filter 'name=io00swck8gss4kosckwwwo88' --format '{{.Names}}' | xargs -I {} docker inspect --format='{{.Name}} {{.State.Health.Status}}' {} 2>/dev/null | grep unhealthy | wc -l")
    if [ "$UNHEALTHY" -gt 0 ]; then
        echo "⚠️  Unhealthy контейнеров: $UNHEALTHY"
    else
        echo "✅ Все контейнеры healthy"
    fi
}

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    ELAPSED_MIN=$((ELAPSED / 60))

    # Проверка frontend
    FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$FRONTEND_URL")
    FRONTEND_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$FRONTEND_URL")

    # Проверка backend
    BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BACKEND_URL")
    BACKEND_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$BACKEND_URL")

    # Проверка памяти
    MEMORY=$(check_memory)
    CONTAINERS=$(check_containers)
    HEALTH=$(check_health)

    # Определение статуса
    if [ "$FRONTEND_CODE" = "200" ] && [ "$BACKEND_CODE" = "200" ]; then
        STATUS="UP"
        STATUS_COLOR=$GREEN
        CONSECUTIVE_FAILURES=0

        if [ "$LAST_STATUS" != "UP" ]; then
            log "${GREEN}✅ Приложение ВОССТАНОВЛЕНО после ${ELAPSED_MIN} минут мониторинга${NC}"
            log "   Frontend: HTTP $FRONTEND_CODE (${FRONTEND_TIME}s)"
            log "   Backend: HTTP $BACKEND_CODE (${BACKEND_TIME}s)"
        fi

        echo -ne "\r[${ELAPSED_MIN}m] ${STATUS_COLOR}●${NC} UP | Frontend: $FRONTEND_CODE (${FRONTEND_TIME}s) | Backend: $BACKEND_CODE (${BACKEND_TIME}s) | $MEMORY | $CONTAINERS | $HEALTH    "
    else
        STATUS="DOWN"
        STATUS_COLOR=$RED
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))

        log "${RED}❌ ПРИЛОЖЕНИЕ НЕДОСТУПНО (попытка #$CONSECUTIVE_FAILURES)${NC}"
        log "   Время с начала мониторинга: ${ELAPSED_MIN} минут"
        log "   Frontend: HTTP $FRONTEND_CODE (${FRONTEND_TIME}s)"
        log "   Backend: HTTP $BACKEND_CODE (${BACKEND_TIME}s)"
        log "   $MEMORY"
        log "   $CONTAINERS"
        log "   $HEALTH"

        # Детальная диагностика при первой неудаче
        if [ $CONSECUTIVE_FAILURES -eq 1 ]; then
            log "--- Детальная диагностика ---"

            # Проверка OOM
            OOM_COUNT=$(ssh "$SERVER" "dmesg -T | grep -i 'out of memory' | tail -n 1")
            if [ -n "$OOM_COUNT" ]; then
                log "${RED}🔥 OOM обнаружен: $OOM_COUNT${NC}"
            fi

            # Проверка последних событий Docker
            log "Последние Docker events:"
            ssh "$SERVER" "docker events --since '5m' --until '0s' --filter 'type=container' --format '{{.Time}} {{.Action}} {{.Actor.Attributes.name}}' | grep 'io00swck8gss4kosckwwwo88' | tail -n 10" | tee -a "$LOG_FILE"

            # Статус контейнеров
            log "Статус контейнеров:"
            ssh "$SERVER" "docker ps --filter 'name=io00swck8gss4kosckwwwo88' --format 'table {{.Names}}\t{{.Status}}\t{{.State}}'" | tee -a "$LOG_FILE"

            # Healthcheck статус
            log "Healthcheck статус:"
            ssh "$SERVER" "docker ps --filter 'name=io00swck8gss4kosckwwwo88' --format '{{.Names}}' | xargs -I {} docker inspect --format='{{.Name}}: {{.State.Health.Status}}' {} 2>/dev/null" | tee -a "$LOG_FILE"

            log "---"
        fi

        # Попытка автоматического рестарта proxy после 3 неудач
        if [ $CONSECUTIVE_FAILURES -eq 3 ]; then
            log "${YELLOW}⚠️  3 неудачные попытки подряд - рестарт proxy...${NC}"
            ssh "$SERVER" "docker restart coolify-proxy" 2>&1 | tee -a "$LOG_FILE"
            log "Ожидание 30 секунд после рестарта..."
            sleep 30
        fi
    fi

    LAST_STATUS=$STATUS

    # Периодическая запись статистики (каждые 5 минут)
    if [ $((ELAPSED % 300)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        log "--- Периодическая статистика (${ELAPSED_MIN} минут) ---"
        log "   Статус: $STATUS"
        log "   $MEMORY"
        log "   $CONTAINERS"
        log "   $HEALTH"
        log "   Frontend response time: ${FRONTEND_TIME}s"
        log "   Backend response time: ${BACKEND_TIME}s"
    fi

    sleep $CHECK_INTERVAL
done
