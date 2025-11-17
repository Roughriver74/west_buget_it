#!/bin/bash
# Диагностика проблемы потери доступа через 15-20 минут после деплоя

SERVER="root@93.189.228.52"
LOG_FILE="./diagnosis_$(date +%Y%m%d_%H%M%S).log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
}

log_section "🔍 ДИАГНОСТИКА ПРОБЛЕМЫ ПОТЕРИ ДОСТУПА"
log "Дата: $(date)"
log "Лог файл: $LOG_FILE"

# Проверка подключения
log_section "1. Проверка подключения к серверу"
if ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    log "${GREEN}✅ Подключение установлено${NC}"
else
    log "${RED}❌ Не удалось подключиться к серверу${NC}"
    exit 1
fi

# Проверка памяти
log_section "2. Проверка памяти и ресурсов"
log "--- Память ---"
ssh "$SERVER" "free -h" | tee -a "$LOG_FILE"
log ""

log "--- SWAP ---"
SWAP_INFO=$(ssh "$SERVER" "swapon --show")
if [ -z "$SWAP_INFO" ]; then
    log "${YELLOW}⚠️  SWAP не настроен - это может быть причиной проблем!${NC}"
else
    echo "$SWAP_INFO" | tee -a "$LOG_FILE"
fi
log ""

# Проверка OOM ошибок
log_section "3. Проверка OOM (Out of Memory) ошибок"
OOM_COUNT=$(ssh "$SERVER" "dmesg -T | grep -i 'out of memory' | wc -l")
if [ "$OOM_COUNT" -gt 0 ]; then
    log "${RED}❌ Обнаружено $OOM_COUNT OOM событий!${NC}"
    log "Последние 10 OOM событий:"
    ssh "$SERVER" "dmesg -T | grep -i 'out of memory' | tail -n 10" | tee -a "$LOG_FILE"
    log ""
    log "${RED}🔥 ОСНОВНАЯ ПРИЧИНА: Нехватка памяти!${NC}"
    log "Решения:"
    log "  1. Настроить SWAP: ./setup_swap.sh"
    log "  2. Собирать образы локально: ./build_and_push.sh"
    log "  3. Увеличить ресурсы сервера"
else
    log "${GREEN}✅ OOM ошибок не обнаружено${NC}"
fi

# Проверка Docker контейнеров
log_section "4. Проверка статуса Docker контейнеров"
log "--- Запущенные контейнеры ---"
ssh "$SERVER" "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.State}}'" | tee -a "$LOG_FILE"
log ""

log "--- Использование памяти контейнерами ---"
ssh "$SERVER" "docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}'" | tee -a "$LOG_FILE"
log ""

# Проверка healthcheck статуса
log_section "5. Проверка Healthcheck статуса контейнеров"
CONTAINERS=$(ssh "$SERVER" "docker ps --filter 'name=io00swck8gss4kosckwwwo88' --format '{{.Names}}'")

for container in $CONTAINERS; do
    log "--- $container ---"
    HEALTH=$(ssh "$SERVER" "docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null")
    if [ "$HEALTH" = "healthy" ]; then
        log "${GREEN}✅ Healthy${NC}"
    elif [ "$HEALTH" = "unhealthy" ]; then
        log "${RED}❌ Unhealthy${NC}"
        log "Последние healthcheck логи:"
        ssh "$SERVER" "docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' $container" | tail -n 20 | tee -a "$LOG_FILE"
    elif [ -z "$HEALTH" ]; then
        log "${YELLOW}⚠️  Healthcheck не настроен${NC}"
    else
        log "${YELLOW}⚠️  Статус: $HEALTH${NC}"
    fi
done
log ""

# Проверка логов контейнеров на ошибки
log_section "6. Проверка логов контейнеров на ошибки"
for container in $CONTAINERS; do
    log "--- Последние ошибки в $container ---"
    ERROR_LINES=$(ssh "$SERVER" "docker logs $container --since 30m 2>&1 | grep -i -E '(error|exception|fatal|killed|fail)' | tail -n 20")
    if [ -n "$ERROR_LINES" ]; then
        log "${YELLOW}Найдены ошибки:${NC}"
        echo "$ERROR_LINES" | tee -a "$LOG_FILE"
    else
        log "${GREEN}✅ Критических ошибок не найдено${NC}"
    fi
    log ""
done

# Проверка Traefik proxy
log_section "7. Проверка Traefik Proxy"
PROXY_STATUS=$(ssh "$SERVER" "docker ps --filter 'name=traefik' --format '{{.Status}}'")
if [ -n "$PROXY_STATUS" ]; then
    log "Статус прокси: $PROXY_STATUS"

    # Проверка последних рестартов прокси
    PROXY_RESTARTS=$(ssh "$SERVER" "docker inspect --format='{{.RestartCount}}' traefik 2>/dev/null")
    log "Количество рестартов: $PROXY_RESTARTS"

    # Проверка логов прокси на ошибки
    log "--- Последние ошибки прокси ---"
    PROXY_ERRORS=$(ssh "$SERVER" "docker logs traefik --since 30m 2>&1 | grep -i -E '(error|fail|timeout)' | tail -n 10")
    if [ -n "$PROXY_ERRORS" ]; then
        log "${YELLOW}Найдены ошибки в прокси:${NC}"
        echo "$PROXY_ERRORS" | tee -a "$LOG_FILE"
    else
        log "${GREEN}✅ Ошибок в прокси не найдено${NC}"
    fi
else
    log "${YELLOW}⚠️  Traefik proxy не найден${NC}"
fi
log ""

# Проверка systemd сервиса автоматического рестарта
log_section "8. Проверка systemd сервиса автоматического рестарта"
SERVICE_STATUS=$(ssh "$SERVER" "systemctl is-active docker-events-proxy-restart.service 2>/dev/null")
if [ "$SERVICE_STATUS" = "active" ]; then
    log "${GREEN}✅ Сервис docker-events-proxy-restart работает${NC}"

    # Последние логи сервиса
    log "--- Последние события ---"
    ssh "$SERVER" "journalctl -u docker-events-proxy-restart.service --since '30 minutes ago' --no-pager | tail -n 20" | tee -a "$LOG_FILE"
else
    log "${YELLOW}⚠️  Сервис docker-events-proxy-restart не активен (статус: $SERVICE_STATUS)${NC}"
fi
log ""

# Проверка Docker events за последние 30 минут
log_section "9. Проверка Docker events"
log "--- События контейнеров за последние 30 минут ---"
ssh "$SERVER" "docker events --since '30m' --until '0s' --filter 'type=container' --format '{{.Time}} {{.Action}} {{.Actor.Attributes.name}}' | grep -E '(io00swck8gss4kosckwwwo88|die|kill|oom|stop)' | tail -n 30" | tee -a "$LOG_FILE"
log ""

# Проверка сетевой доступности
log_section "10. Проверка доступности приложения"
log "--- Проверка frontend ---"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://budget-west.shknv.ru)
if [ "$FRONTEND_CODE" = "200" ]; then
    log "${GREEN}✅ Frontend доступен (HTTP $FRONTEND_CODE)${NC}"
else
    log "${RED}❌ Frontend недоступен (HTTP $FRONTEND_CODE)${NC}"
fi

log "--- Проверка backend health ---"
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://budget-west.shknv.ru/api/v1/health)
if [ "$BACKEND_CODE" = "200" ]; then
    log "${GREEN}✅ Backend доступен (HTTP $BACKEND_CODE)${NC}"
else
    log "${RED}❌ Backend недоступен (HTTP $BACKEND_CODE)${NC}"
fi
log ""

# Проверка database connections
log_section "11. Проверка подключений к базе данных"
DB_CONTAINER=$(ssh "$SERVER" "docker ps --filter 'name=postgres' --format '{{.Names}}' | head -n 1")
if [ -n "$DB_CONTAINER" ]; then
    log "База данных: $DB_CONTAINER"

    # Количество активных подключений
    CONNECTIONS=$(ssh "$SERVER" "docker exec $DB_CONTAINER psql -U budget_user -d it_budget_db -t -c 'SELECT count(*) FROM pg_stat_activity;' 2>/dev/null" | xargs)
    log "Активные подключения: $CONNECTIONS"

    # Проверка на достижение лимита подключений
    MAX_CONNECTIONS=$(ssh "$SERVER" "docker exec $DB_CONTAINER psql -U budget_user -d it_budget_db -t -c 'SHOW max_connections;' 2>/dev/null" | xargs)
    log "Максимум подключений: $MAX_CONNECTIONS"

    if [ -n "$CONNECTIONS" ] && [ -n "$MAX_CONNECTIONS" ]; then
        USAGE=$((CONNECTIONS * 100 / MAX_CONNECTIONS))
        if [ $USAGE -gt 80 ]; then
            log "${RED}❌ Использовано ${USAGE}% подключений к БД!${NC}"
        else
            log "${GREEN}✅ Использовано ${USAGE}% подключений к БД${NC}"
        fi
    fi
else
    log "${YELLOW}⚠️  Контейнер базы данных не найден${NC}"
fi
log ""

# Итоговый отчет
log_section "📊 ИТОГОВАЯ ДИАГНОСТИКА"

log "Возможные причины потери доступа:"
log ""

# Проверяем OOM
if [ "$OOM_COUNT" -gt 0 ]; then
    log "${RED}🔥 1. НЕХВАТКА ПАМЯТИ (OOM) - ОСНОВНАЯ ПРИЧИНА${NC}"
    log "   - Обнаружено $OOM_COUNT OOM событий"
    log "   - Контейнеры убиваются ядром из-за нехватки памяти"
    log "   - РЕШЕНИЕ:"
    log "     1. Настроить SWAP: ./setup_swap.sh"
    log "     2. Собирать образы локально: ./build_and_push.sh"
    log "     3. Увеличить RAM сервера"
    log ""
fi

# Проверяем healthcheck
UNHEALTHY_COUNT=0
for container in $CONTAINERS; do
    HEALTH=$(ssh "$SERVER" "docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null")
    if [ "$HEALTH" = "unhealthy" ]; then
        UNHEALTHY_COUNT=$((UNHEALTHY_COUNT + 1))
    fi
done

if [ $UNHEALTHY_COUNT -gt 0 ]; then
    log "${YELLOW}⚠️  2. HEALTHCHECK FAILURES${NC}"
    log "   - $UNHEALTHY_COUNT контейнеров имеют статус unhealthy"
    log "   - Проверьте логи выше для деталей"
    log ""
fi

# Проверяем proxy
if [ "$PROXY_RESTARTS" -gt 10 ]; then
    log "${YELLOW}⚠️  3. ЧАСТЫЕ РЕСТАРТЫ PROXY${NC}"
    log "   - Proxy перезапускался $PROXY_RESTARTS раз"
    log "   - Проверьте логи proxy выше"
    log ""
fi

log "${GREEN}✅ Диагностика завершена${NC}"
log "Полный отчет сохранен в: $LOG_FILE"
log ""
log "Следующие шаги:"
log "1. Изучить логи в файле: $LOG_FILE"
log "2. Если найдены OOM ошибки - настроить SWAP"
log "3. Если проблемы с healthcheck - проверить endpoints"
log "4. Мониторить приложение в реальном времени:"
log "   ssh $SERVER 'watch -n 5 docker stats'"
