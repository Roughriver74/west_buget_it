#!/bin/bash
# Шаг за шагом - поиск проекта и исправление

echo "========================================="
echo "ШАГ 1: ПОИСК ПРОЕКТА"
echo "========================================="
echo ""

# Проверяем где может быть проект
echo "Ищем проект west_buget_it..."
echo ""

# Вариант 1: Coolify стандартное расположение
if [ -d "/data/coolify" ]; then
    echo "✓ Coolify найден, ищем проект..."
    find /data/coolify -type d -name "*west*" -o -name "*budget*" 2>/dev/null | head -10
    echo ""
fi

# Вариант 2: В домашней директории
echo "Проверяем домашнюю директорию..."
find /root -type d -name "*west*" -o -name "*budget*" 2>/dev/null | head -10
echo ""

# Вариант 3: Ищем по docker-compose файлам
echo "Ищем docker-compose.prod.yml..."
find / -name "docker-compose.prod.yml" -type f 2>/dev/null | grep -i budget | head -5
echo ""

# Вариант 4: Спросить у docker где volume примонтированы
echo "Проверяем Docker volumes..."
docker volume ls | grep budget
echo ""

# Вариант 5: Проверяем работающие контейнеры
echo "Проверяем работающие контейнеры..."
docker ps --format "table {{.Names}}\t{{.Mounts}}" | grep budget
echo ""

echo "========================================="
echo "НАЙДЕННЫЕ ВАРИАНТЫ"
echo "========================================="
echo ""
echo "Если нашли путь выше, скопируйте его."
echo "Обычно это что-то вроде:"
echo "  /data/coolify/sources/..."
echo "  /data/coolify/applications/..."
echo "  /root/west_buget_it"
echo ""
echo "Или посмотрите вывод docker ps выше - там могут быть пути к файлам."
echo ""
