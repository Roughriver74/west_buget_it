# VPN Setup для доступа к 1С

## Обзор

На production-сервере настроено постоянное VPN-подключение для доступа к 1С OData API через защищенный туннель.

## Конфигурация VPN

**VPN Server**: `217.119.19.100:55155` (UDP)
**VPN Client IP**: `10.10.100.108/24`
**1C Server IP**: `10.10.100.77`
**1C OData URL**: `http://10.10.100.77/trade/odata/standard.odata`

## Установленные компоненты

### 1. OpenVPN Client
- **Package**: openvpn (2.6.14)
- **Config**: `/etc/openvpn/client/1c-vpn.conf`
- **Service**: `openvpn-client@1c-vpn.service`

### 2. Systemd Service
Автоматический запуск VPN при загрузке системы с возможностью auto-reconnect.

**Service file**: `/etc/systemd/system/openvpn-client@.service`

Основные параметры:
- `Restart=on-failure` - автоматический перезапуск при сбое
- `RestartSec=5s` - интервал перезапуска 5 секунд
- `WantedBy=multi-user.target` - запуск при старте системы

### 3. Route Management
Автоматическое добавление маршрута к сети 1С при подключении VPN.

**Script**: `/etc/openvpn/client/route-up.sh`

```bash
#!/bin/bash
# Add route to 1C server through VPN
sleep 2
ip route add 10.10.100.0/24 dev tun0 2>/dev/null || true
echo "$(date): Added route to 1C network via tun0" >> /var/log/openvpn-routes.log
ip route show | grep tun0 >> /var/log/openvpn-routes.log
```

## Управление VPN

### Проверка статуса
```bash
ssh root@31.129.107.178 systemctl status openvpn-client@1c-vpn
```

### Перезапуск VPN
```bash
ssh root@31.129.107.178 systemctl restart openvpn-client@1c-vpn
```

### Остановка VPN
```bash
ssh root@31.129.107.178 systemctl stop openvpn-client@1c-vpn
```

### Запуск VPN
```bash
ssh root@31.129.107.178 systemctl start openvpn-client@1c-vpn
```

### Просмотр логов
```bash
# Все логи VPN
ssh root@31.129.107.178 journalctl -u openvpn-client@1c-vpn

# Последние 50 строк
ssh root@31.129.107.178 journalctl -u openvpn-client@1c-vpn -n 50

# Реальное время (follow)
ssh root@31.129.107.178 journalctl -u openvpn-client@1c-vpn -f

# Логи маршрутов
ssh root@31.129.107.178 cat /var/log/openvpn-routes.log
```

## Проверка подключения

### 1. Проверка интерфейса tun0
```bash
ssh root@31.129.107.178 ip addr show tun0
```

Ожидаемый вывод:
```
tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500
    inet 10.10.100.108/24 scope global tun0
```

### 2. Проверка маршрутов
```bash
ssh root@31.129.107.178 ip route show | grep tun0
```

Ожидаемый вывод:
```
10.10.100.0/24 dev tun0 proto kernel scope link src 10.10.100.108
```

### 3. Проверка доступности 1С
```bash
# HTTP-доступность
ssh root@31.129.107.178 'curl -v --connect-timeout 5 http://10.10.100.77/trade/odata/standard.odata'

# OData с аутентификацией
ssh root@31.129.107.178 'curl -s -u "odata.user:ak228Hu2hbs28" "http://10.10.100.77/trade/odata/standard.odata/\$metadata" | head -20'
```

## Настройки VPN-конфига

Важные параметры в `/etc/openvpn/client/1c-vpn.conf`:

```conf
# Не использовать VPN как шлюз по умолчанию (только для 1С)
pull-filter ignore "redirect-gateway"
route-nopull

# Не изменять DNS
pull-filter ignore "dhcp-option"

# Низкий приоритет маршрута
route-metric 500

# Скрипт для добавления маршрутов
route-up /etc/openvpn/client/route-up.sh
script-security 2
```

Это гарантирует, что:
- VPN используется только для доступа к 1С
- Основной интернет-трафик идет через обычное соединение
- DNS-настройки не изменяются

## Интеграция с Backend

Backend приложение должно использовать следующие параметры для доступа к 1С:

**Environment variables** (в Docker или .env):
```bash
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28
```

**Python код** (уже настроен в `backend/app/services/odata_1c_client.py`):
```python
from app.core.config import settings

odata_client = OData1CClient(
    base_url=settings.ODATA_1C_URL,
    username=settings.ODATA_1C_USERNAME,
    password=settings.ODATA_1C_PASSWORD
)
```

## Автоматическое развертывание

Для установки VPN на новом сервере используйте скрипт:

```bash
# Из корня проекта
./setup_vpn.sh
```

Скрипт автоматически:
1. Создает необходимые директории
2. Копирует конфиг на сервер
3. Устанавливает OpenVPN
4. Создает systemd service
5. Настраивает маршруты
6. Запускает VPN
7. Проверяет подключение

## Troubleshooting

### VPN не подключается
```bash
# Проверить логи
ssh root@31.129.107.178 journalctl -u openvpn-client@1c-vpn -n 100

# Проверить конфиг
ssh root@31.129.107.178 openvpn --config /etc/openvpn/client/1c-vpn.conf --verb 3
```

### Нет маршрута к 1С
```bash
# Добавить маршрут вручную
ssh root@31.129.107.178 ip route add 10.10.100.0/24 dev tun0

# Проверить, что tun0 поднят
ssh root@31.129.107.178 ip link show tun0
```

### 1С недоступен через VPN
```bash
# Проверить, что VPN работает
ssh root@31.129.107.178 systemctl status openvpn-client@1c-vpn

# Проверить маршруты
ssh root@31.129.107.178 ip route show

# Тест HTTP
ssh root@31.129.107.178 curl -v --connect-timeout 10 http://10.10.100.77
```

### VPN отключается автоматически
Проверьте логи на наличие ошибок аутентификации:
```bash
ssh root@31.129.107.178 journalctl -u openvpn-client@1c-vpn | grep -i error
```

## Безопасность

⚠️ **Важно**:
- VPN credentials хранятся в `/etc/openvpn/client/1c-vpn.conf` (root:root 600)
- OData credentials хранятся в environment variables (Docker Secrets)
- Файл `client08.ovpn` содержит приватные ключи - **НЕ КОММИТИТЬ В GIT**
- Backup конфига: периодически делайте backup `/etc/openvpn/client/`

## Мониторинг

Для автоматического мониторинга VPN-подключения можно настроить:

```bash
# Создать скрипт мониторинга
cat > /usr/local/bin/check-1c-vpn.sh << 'EOF'
#!/bin/bash
if ! curl -s --connect-timeout 5 http://10.10.100.77 > /dev/null; then
    echo "1C unreachable, restarting VPN..."
    systemctl restart openvpn-client@1c-vpn
    sleep 10
    if curl -s --connect-timeout 5 http://10.10.100.77 > /dev/null; then
        echo "VPN restored successfully"
    else
        echo "Failed to restore VPN connection" | mail -s "VPN Alert" admin@example.com
    fi
fi
EOF

chmod +x /usr/local/bin/check-1c-vpn.sh

# Добавить в cron (проверка каждые 5 минут)
echo "*/5 * * * * /usr/local/bin/check-1c-vpn.sh >> /var/log/vpn-monitor.log 2>&1" | crontab -
```

## Диагностика производительности

```bash
# Проверка задержки (latency)
ssh root@31.129.107.178 ping -c 10 10.10.100.77

# Проверка пропускной способности
ssh root@31.129.107.178 'time curl -o /dev/null http://10.10.100.77/trade/odata/standard.odata/\$metadata'

# Статистика интерфейса
ssh root@31.129.107.178 'cat /proc/net/dev | grep tun0'
```

## Обновление VPN конфига

Если нужно обновить конфигурацию:

```bash
# 1. Скопировать новый конфиг
scp client08.ovpn root@31.129.107.178:/etc/openvpn/client/1c-vpn.conf

# 2. Перезапустить сервис
ssh root@31.129.107.178 systemctl restart openvpn-client@1c-vpn

# 3. Проверить статус
ssh root@31.129.107.178 systemctl status openvpn-client@1c-vpn
```

## Полезные команды

```bash
# Проверить все VPN-подключения
ssh root@31.129.107.178 ip -br addr show type tun

# Посмотреть таблицу маршрутизации
ssh root@31.129.107.178 ip route show table all | grep tun

# Проверить открытые соединения к 1С
ssh root@31.129.107.178 netstat -an | grep 10.10.100.77

# Отладочный запуск VPN (для диагностики)
ssh root@31.129.107.178 'openvpn --config /etc/openvpn/client/1c-vpn.conf --verb 6'
```

## Связь с другими документами

- [1C Expense Requests Sync](1C_EXPENSE_REQUESTS_SYNC.md) - использует VPN для доступа к OData
- [Docker Setup](docker_SETUP.md) - конфигурация environment variables
- [OData 1C Client](../backend/app/services/odata_1c_client.py) - Python клиент для работы с 1С
