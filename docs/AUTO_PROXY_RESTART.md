# Auto Proxy Restart After Deployment

## Проблема

После деплоя новой версии приложения через Coolify, Traefik proxy не всегда автоматически подхватывает новые Docker labels и маршруты контейнеров. Это приводит к:
- Timeout при обращении к frontend/backend
- 504 Gateway Timeout на API запросах
- Необходимости ручного рестарта proxy: `docker restart coolify-proxy`

## Решение

Автоматический systemd сервис, который:
1. **Мониторит Docker события** в реальном времени
2. **Детектирует старт** новых контейнеров приложения Budget Manager
3. **Автоматически рестартит** Traefik proxy через 3 секунды после старта контейнера

## Установленные Компоненты

### 1. Docker Events Listener Service

**Файл:** `/etc/systemd/system/docker-events-proxy-restart.service`

```ini
[Unit]
Description=Auto-restart Traefik proxy on budget app container start
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/local/bin/docker-events-proxy-restart.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Event Listener Script

**Файл:** `/usr/local/bin/docker-events-proxy-restart.sh`

Скрипт слушает Docker events и автоматически рестартит proxy при обнаружении старта контейнеров с префиксом `io00swck8gss4kosckwwwo88`.

**Логика (с debounce):**
1. Слушает `docker events --filter 'event=start'`
2. Проверяет имя контейнера на соответствие префиксу Budget Manager
3. При обнаружении контейнера - **запускает таймер на 15 секунд**
4. Если за эти 15 секунд стартуют еще контейнеры - **таймер сбрасывается**
5. Через 15 секунд после **последнего** контейнера - выполняет **ОДИН** рестарт proxy
6. Это предотвращает множественные рестарты при одновременном старте всех контейнеров

### 3. Manual Restart Script

**Файл:** `/root/restart-proxy.sh`

Можно использовать для ручного рестарта:
```bash
/root/restart-proxy.sh
```

## Управление Сервисом

### Проверка Статуса
```bash
systemctl status docker-events-proxy-restart.service
```

### Просмотр Логов
```bash
# Последние 20 строк
journalctl -u docker-events-proxy-restart.service -n 20

# В реальном времени
journalctl -u docker-events-proxy-restart.service -f

# Полный лог за сегодня
journalctl -u docker-events-proxy-restart.service --since today
```

### Перезапуск Сервиса
```bash
systemctl restart docker-events-proxy-restart.service
```

### Остановка/Запуск
```bash
systemctl stop docker-events-proxy-restart.service
systemctl start docker-events-proxy-restart.service
```

### Отключение (если нужно)
```bash
systemctl disable docker-events-proxy-restart.service
systemctl stop docker-events-proxy-restart.service
```

## Логирование

Логи записываются в:
- **systemd journal**: `journalctl -u docker-events-proxy-restart.service`
- **файл**: `/var/log/traefik-auto-restart.log`

Формат лога:
```
[2025-11-05 06:48:21] Starting Docker events monitor for auto-restart...
[2025-11-05 06:50:15] Detected start of budget container: backend-io00swck8gss4kosckwwwo88-063311069720
[2025-11-05 06:50:18] Auto-restarting Traefik proxy...
[2025-11-05 06:50:23] ✅ Proxy restarted successfully
```

## Тестирование

### Ручное Тестирование
```bash
# 1. Остановить контейнер
docker stop backend-io00swck8gss4kosckwwwo88-XXXXX

# 2. Запустить контейнер
docker start backend-io00swck8gss4kosckwwwo88-XXXXX

# 3. Проверить логи (должен показать автоматический рестарт)
journalctl -u docker-events-proxy-restart.service -n 10
```

### Проверка После Деплоя
```bash
# Сразу после деплоя от Coolify проверить:
journalctl -u docker-events-proxy-restart.service --since "2 minutes ago"

# Должно быть сообщение о рестарте proxy
```

## Устранение Проблем

### Сервис Не Запускается
```bash
# Проверить статус
systemctl status docker-events-proxy-restart.service

# Проверить логи
journalctl -u docker-events-proxy-restart.service -n 50

# Проверить права на скрипт
ls -la /usr/local/bin/docker-events-proxy-restart.sh
chmod +x /usr/local/bin/docker-events-proxy-restart.sh

# Перезапустить
systemctl restart docker-events-proxy-restart.service
```

### Proxy Не Рестартится
```bash
# Проверить что сервис работает
systemctl is-active docker-events-proxy-restart.service

# Проверить docker events вручную
docker events --filter 'event=start' --format '{{.Actor.Attributes.name}}'

# Ручной рестарт proxy
/root/restart-proxy.sh
```

### Слишком Частые Рестарты
Если proxy рестартится слишком часто (например, при рестарте нескольких контейнеров):
- Скрипт имеет встроенную паузу 10 секунд
- Можно увеличить паузу в `/usr/local/bin/docker-events-proxy-restart.sh`

## Удаление

Если нужно полностью удалить автоматический рестарт:

```bash
# Остановить и отключить сервис
systemctl stop docker-events-proxy-restart.service
systemctl disable docker-events-proxy-restart.service

# Удалить файлы
rm /etc/systemd/system/docker-events-proxy-restart.service
rm /usr/local/bin/docker-events-proxy-restart.sh
rm /root/restart-proxy.sh

# Перезагрузить systemd
systemctl daemon-reload
```

## История Изменений

- **2025-11-05**: Создан автоматический сервис для решения проблемы с Traefik после деплоя
- **Причина**: После каждого деплоя через Coolify требовался ручной рестарт proxy
- **Решение**: Docker events listener с автоматическим рестартом

## См. Также

- [COOLIFY_SETUP.md](COOLIFY_SETUP.md) - Настройка деплоя через Coolify
- [COOLIFY_FIX.md](COOLIFY_FIX.md) - Решение проблем с CORS и API URL
