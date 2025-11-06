#!/bin/bash
# Проверка ресурсов сервера и Docker

SERVER="root@93.189.228.52"

echo "=== Проверка ресурсов сервера и Docker ==="
echo ""
echo "Сервер: $SERVER"
echo ""

# Проверка подключения
echo "Подключение к серверу..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Не удалось подключиться к серверу"
    exit 1
fi

echo "✅ Подключение установлено"
echo ""

# Проверка памяти
echo "=== ПАМЯТЬ ==="
ssh "$SERVER" "free -h"
echo ""

# Проверка swap
echo "=== SWAP ==="
SWAP_INFO=$(ssh "$SERVER" "swapon --show")
if [ -z "$SWAP_INFO" ]; then
    echo "⚠️  SWAP не настроен!"
    echo ""
    echo "Рекомендация: Создайте swap файл для увеличения доступной памяти"
else
    echo "$SWAP_INFO"
fi
echo ""

# Проверка дискового пространства
echo "=== ДИСКОВОЕ ПРОСТРАНСТВО ==="
ssh "$SERVER" "df -h /"
echo ""

# Проверка Docker информации
echo "=== DOCKER ИНФОРМАЦИЯ ==="
ssh "$SERVER" "docker info --format '{{.MemTotal}}' 2>/dev/null" | {
    read mem_bytes
    if [ -n "$mem_bytes" ]; then
        mem_gb=$(echo "scale=2; $mem_bytes / 1024 / 1024 / 1024" | bc)
        echo "Docker Memory Limit: ${mem_gb} GB"
    fi
}
echo ""

# Проверка запущенных контейнеров
echo "=== ЗАПУЩЕННЫЕ КОНТЕЙНЕРЫ ==="
ssh "$SERVER" "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
echo ""

# Проверка использования памяти контейнерами
echo "=== ИСПОЛЬЗОВАНИЕ ПАМЯТИ КОНТЕЙНЕРАМИ ==="
ssh "$SERVER" "docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'"
echo ""

# Проверка логов последней сборки
echo "=== ОШИБКИ OOM (Out of Memory) ==="
OOM_ERRORS=$(ssh "$SERVER" "dmesg | grep -i 'out of memory' | tail -n 5")
if [ -n "$OOM_ERRORS" ]; then
    echo "⚠️  Обнаружены ошибки OOM:"
    echo "$OOM_ERRORS"
else
    echo "✅ Ошибки OOM не обнаружены"
fi
echo ""

# Рекомендации
echo "=== РЕКОМЕНДАЦИИ ==="
echo ""

# Получаем доступную память
FREE_MEM=$(ssh "$SERVER" "free -m | awk '/^Mem:/ {print \$7}'")
TOTAL_MEM=$(ssh "$SERVER" "free -m | awk '/^Mem:/ {print \$2}'")

echo "Доступная память: ${FREE_MEM} MB из ${TOTAL_MEM} MB"
echo ""

if [ "$FREE_MEM" -lt 1024 ]; then
    echo "❌ КРИТИЧЕСКИ МАЛО ПАМЯТИ (<1GB)"
    echo ""
    echo "Варианты решения:"
    echo "1. Создать SWAP (быстрое решение):"
    echo "   ./setup_swap.sh"
    echo ""
    echo "2. Собрать образ локально и загрузить на сервер:"
    echo "   ./build_and_push.sh"
    echo ""
    echo "3. Увеличить ресурсы сервера (обратитесь к хостинг-провайдеру)"
elif [ "$FREE_MEM" -lt 2048 ]; then
    echo "⚠️  МАЛО ПАМЯТИ (<2GB)"
    echo ""
    echo "Рекомендуется:"
    echo "1. Создать SWAP файл для стабильной сборки"
    echo "2. Или собрать образ локально"
else
    echo "✅ Достаточно памяти для сборки"
fi

# Проверка наличия swap
if [ -z "$SWAP_INFO" ]; then
    echo ""
    echo "💡 SWAP не настроен. Создайте SWAP файл:"
    echo "   sudo fallocate -l 2G /swapfile"
    echo "   sudo chmod 600 /swapfile"
    echo "   sudo mkswap /swapfile"
    echo "   sudo swapon /swapfile"
    echo "   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab"
fi

echo ""
echo "=== Проверка завершена ==="
