#!/bin/bash
# Автоматическая настройка SWAP на production сервере

SERVER="root@93.189.228.52"
SWAP_SIZE="2G"  # Размер swap файла

echo "=== Настройка SWAP на production сервере ==="
echo ""
echo "Сервер: $SERVER"
echo "Размер SWAP: $SWAP_SIZE"
echo ""

# Проверка подключения
echo "Проверка подключения..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Не удалось подключиться к серверу"
    exit 1
fi

echo "✅ Подключение установлено"
echo ""

# Проверка существующего swap
echo "Проверка существующего SWAP..."
EXISTING_SWAP=$(ssh "$SERVER" "swapon --show")

if [ -n "$EXISTING_SWAP" ]; then
    echo "⚠️  SWAP уже настроен:"
    echo "$EXISTING_SWAP"
    echo ""
    read -p "Хотите пересоздать SWAP? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Отменено"
        exit 0
    fi

    echo ""
    echo "Отключение существующего SWAP..."
    ssh "$SERVER" "sudo swapoff -a"
fi

echo ""
echo "Создание SWAP файла ($SWAP_SIZE)..."

# Создаем swap на сервере
ssh "$SERVER" bash << 'ENDSSH'
set -e

# Проверка наличия /swapfile
if [ -f /swapfile ]; then
    echo "Удаление старого swap файла..."
    sudo rm /swapfile
fi

# Создание swap файла
echo "Создание swap файла (2GB)..."
sudo fallocate -l 2G /swapfile

# Установка прав
echo "Установка прав доступа..."
sudo chmod 600 /swapfile

# Создание swap
echo "Создание swap области..."
sudo mkswap /swapfile

# Активация swap
echo "Активация swap..."
sudo swapon /swapfile

# Проверка что swap активен
if swapon --show | grep -q "/swapfile"; then
    echo "✅ SWAP успешно активирован"
else
    echo "❌ Ошибка активации SWAP"
    exit 1
fi

# Добавление в /etc/fstab для автозапуска
if ! grep -q "/swapfile" /etc/fstab; then
    echo "Добавление в /etc/fstab для автозапуска..."
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Настройка swappiness (как часто использовать swap, 0-100)
# 10 = использовать swap только при критической нехватке памяти
echo "Настройка vm.swappiness=10..."
sudo sysctl vm.swappiness=10
if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
fi

echo ""
echo "=== Информация о SWAP ==="
free -h
echo ""
swapon --show
echo ""

ENDSSH

echo ""
echo "✅ SWAP успешно настроен!"
echo ""
echo "Информация:"
ssh "$SERVER" "free -h"
echo ""

echo "Теперь можно попробовать снова собрать Docker образ:"
echo "1. В Coolify: нажмите 'Rebuild'"
echo "2. Или вручную: ssh $SERVER 'cd /root/west_buget_it && docker-compose -f docker-compose.prod.yml build --no-cache backend'"
echo ""
