#!/bin/bash
# 🚨 СРОЧНЫЙ ОТКАТ - Восстановление работоспособности сайта

echo "========================================="
echo "🚨 СРОЧНЫЙ ОТКАТ ИЗМЕНЕНИЙ"
echo "========================================="
echo ""

# Найти docker-compose команду
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif command -v docker &> /dev/null; then
    DC="docker compose"
else
    echo "❌ ERROR: Docker not found"
    exit 1
fi

# Найти compose file
COMPOSE_FILE=""
for file in docker-compose.prod.yml docker-compose.yml; do
    if [ -f "$file" ]; then
        COMPOSE_FILE="$file"
        break
    fi
done

if [ -z "$COMPOSE_FILE" ]; then
    echo "❌ ERROR: docker-compose file not found"
    exit 1
fi

echo "Используется: $COMPOSE_FILE"
echo ""

# ШАГ 1: Проверка текущего состояния
echo "========================================="
echo "ШАГ 1: Проверка текущего состояния"
echo "========================================="
$DC -f $COMPOSE_FILE ps
echo ""

# ШАГ 2: Проверка логов backend (последние 50 строк)
echo "========================================="
echo "ШАГ 2: Логи Backend (последние 50 строк)"
echo "========================================="
$DC -f $COMPOSE_FILE logs backend --tail=50
echo ""

# ШАГ 3: Выбор действия
echo "========================================="
echo "ШАГ 3: Выберите действие"
echo "========================================="
echo ""
echo "Что делать?"
echo "1) Откатить к предыдущему коммиту (БЫСТРО)"
echo "2) Просто перезапустить контейнеры"
echo "3) Посмотреть ещё больше логов"
echo "4) Выход (ничего не делать)"
echo ""
read -p "Введите номер (1-4): " choice

case $choice in
    1)
        echo ""
        echo "========================================="
        echo "ОТКАТ К ПРЕДЫДУЩЕМУ КОММИТУ"
        echo "========================================="
        echo ""

        # Показать последние коммиты
        echo "Последние коммиты:"
        git log --oneline -5
        echo ""

        # Откатить последний коммит
        echo "Откатываем последний коммит..."
        git reset --hard HEAD~1

        echo ""
        echo "✅ Откатились на предыдущий коммит"
        echo ""

        # Пересобрать и перезапустить
        echo "Пересборка и перезапуск бэкенда..."
        $DC -f $COMPOSE_FILE down backend
        $DC -f $COMPOSE_FILE build --no-cache backend
        $DC -f $COMPOSE_FILE up -d backend

        echo ""
        echo "⏳ Ожидание запуска (30 секунд)..."
        sleep 30

        # Проверить статус
        echo ""
        echo "Статус после отката:"
        $DC -f $COMPOSE_FILE ps

        echo ""
        echo "Логи после отката:"
        $DC -f $COMPOSE_FILE logs backend --tail=30

        echo ""
        echo "✅ ОТКАТ ЗАВЕРШЁН"
        echo ""
        echo "Проверьте сайт: https://budget-west.shknv.ru"
        ;;

    2)
        echo ""
        echo "========================================="
        echo "ПЕРЕЗАПУСК КОНТЕЙНЕРОВ"
        echo "========================================="
        echo ""

        echo "Перезапуск всех контейнеров..."
        $DC -f $COMPOSE_FILE restart

        echo ""
        echo "⏳ Ожидание запуска (30 секунд)..."
        sleep 30

        # Проверить статус
        echo ""
        echo "Статус после перезапуска:"
        $DC -f $COMPOSE_FILE ps

        echo ""
        echo "Логи backend:"
        $DC -f $COMPOSE_FILE logs backend --tail=30

        echo ""
        echo "✅ ПЕРЕЗАПУСК ЗАВЕРШЁН"
        ;;

    3)
        echo ""
        echo "========================================="
        echo "ПОЛНЫЕ ЛОГИ BACKEND"
        echo "========================================="
        $DC -f $COMPOSE_FILE logs backend --tail=200
        ;;

    4)
        echo ""
        echo "Выход без изменений."
        exit 0
        ;;

    *)
        echo ""
        echo "❌ Неверный выбор. Выход."
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "ГОТОВО"
echo "========================================="
