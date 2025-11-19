# IT Budget Manager - Production Deployment Guide

## Проблемы, которые были исправлены

### 1. Mixed Content Error
**Проблема**: HTTPS сайт (https://budget-acme.shknv.ru) пытался обращаться к HTTP API (http://localhost:8888), браузер блокировал запросы.

**Решение**: 
- Nginx фронтенда теперь проксирует `/api/*` запросы к бэкенду
- Фронтенд использует относительный путь `/api` вместо абсолютного URL
- Все запросы идут через один домен по HTTPS

### 2. Localhost в Production
**Проблема**: Фронтенд был собран с `VITE_API_URL=http://localhost:8888`.

**Решение**:
- Изменен default в `Dockerfile.prod`: `VITE_API_URL=/api`
- Обновлен `docker-compose.prod.yml` для передачи правильного значения
- Обновлен `docker-entrypoint.sh` с правильным default

## Быстрый деплой

### Шаг 1: Настройте .env.production

```bash
# Скопируйте и отредактируйте файл
cp .env.production .env.production.local
nano .env.production

# ОБЯЗАТЕЛЬНО измените:
# 1. DB_PASSWORD - сильный пароль для БД
# 2. SECRET_KEY - случайная строка минимум 32 символа
```

Генерация SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Шаг 2: Запустите деплой

```bash
./deploy.sh
```

Скрипт автоматически:
1. ✅ Проверит конфигурацию
2. ✅ Создаст deployment пакет
3. ✅ Загрузит файлы на сервер
4. ✅ Соберет Docker образы
5. ✅ Запустит сервисы

### Шаг 3: Проверьте статус

```bash
# Подключитесь к серверу
ssh root@93.189.228.52

# Перейдите в директорию проекта
cd /root/it_budget

# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Посмотрите логи
docker-compose -f docker-compose.prod.yml logs -f
```

## Архитектура Production

```
[Браузер] HTTPS
    ↓
[budget-acme.shknv.ru] (Caddy/Cloudflare)
    ↓
[Frontend Container:80] Nginx
    ├─→ /api/* → proxy_pass http://backend:8000/api/v1
    └─→ /* → React SPA (static files)
    
[Backend Container:8000] FastAPI
    ↓
[Database Container:5432] PostgreSQL
```

## Ключевые изменения

### 1. frontend/nginx.conf
Добавлено проксирование API:
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    # ... proxy headers
}
```

### 2. frontend/Dockerfile.prod
```dockerfile
ARG VITE_API_URL=/api  # Изменено с http://localhost:8888
```

### 3. frontend/docker-entrypoint.sh
```bash
VITE_API_URL=${VITE_API_URL:-"/api"}  # Изменено с http://localhost:8888
```

### 4. docker-compose.prod.yml
```yaml
frontend:
  build:
    args:
      VITE_API_URL: /api  # Используем относительный путь
  environment:
    VITE_API_URL: /api
```

## Проверка конфигурации

### Проверить API URL фронтенда
```bash
# На сервере
curl http://localhost:3001/config-check
```

Должен вернуть:
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: '/api'
};
```

### Проверить проксирование Nginx
```bash
# Внутри frontend контейнера
docker exec -it it_budget_frontend_prod sh

# Проверить конфиг
cat /etc/nginx/conf.d/default.conf | grep -A 10 "location /api/"
```

### Проверить работу API через фронтенд
```bash
# Должно вернуть данные от бэкенда
curl http://localhost:3001/api/v1/health
```

## Управление сервисами

### Перезапуск
```bash
cd /root/it_budget
docker-compose -f docker-compose.prod.yml restart
```

### Остановка
```bash
docker-compose -f docker-compose.prod.yml down
```

### Пересборка (после изменений кода)
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Просмотр логов
```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Только фронтенд
docker-compose -f docker-compose.prod.yml logs -f frontend

# Только бэкенд
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Миграции БД

После первого деплоя или изменений в моделях:

```bash
# Зайти в контейнер бэкенда
docker exec -it it_budget_backend_prod bash

# Применить миграции
cd /app
alembic upgrade head

# Создать админа (если нужно)
python create_admin.py
```

## Troubleshooting

### Фронтенд не может подключиться к API

1. Проверьте, что бэкенд запущен:
   ```bash
   docker-compose -f docker-compose.prod.yml ps backend
   ```

2. Проверьте API URL в env-config.js:
   ```bash
   curl http://localhost:3001/config-check
   ```

3. Проверьте логи Nginx:
   ```bash
   docker-compose -f docker-compose.prod.yml logs frontend | grep -i error
   ```

### Mixed Content Error в браузере

Убедитесь, что:
- `VITE_API_URL=/api` (НЕ http://...)
- Nginx проксирует `/api/*` к бэкенду
- Фронтенд собран с правильным VITE_API_URL

### 401 Unauthorized при логине

1. Проверьте CORS в бэкенде:
   ```bash
   docker exec -it it_budget_backend_prod env | grep CORS
   ```

2. Должно быть:
   ```
   CORS_ORIGINS=["https://budget-acme.shknv.ru",...]
   ```

### База данных не запускается

1. Проверьте логи:
   ```bash
   docker-compose -f docker-compose.prod.yml logs db
   ```

2. Проверьте права на volume:
   ```bash
   ls -la /var/lib/docker/volumes/
   ```

## Мониторинг

### Health Checks

- Frontend: http://localhost:3001/health
- Backend: http://localhost:8888/health
- Database: через `pg_isready`

### Метрики (если Prometheus включен)

- http://localhost:8888/metrics

## Безопасность

✅ HTTPS через Caddy/Cloudflare
✅ Security headers в Nginx
✅ CORS настроен только для домена
✅ JWT токены с истечением
✅ PostgreSQL не доступен извне (только через Docker network)
✅ Пароли в .env (не в коде)

## Backup

### Бэкап базы данных
```bash
# Создать бэкап
docker exec it_budget_db pg_dump -U budget_user it_budget_db > backup_$(date +%Y%m%d).sql

# Восстановить бэкап
cat backup_20250102.sql | docker exec -i it_budget_db psql -U budget_user -d it_budget_db
```

### Бэкап volumes
```bash
# Остановить сервисы
docker-compose -f docker-compose.prod.yml down

# Бэкап
tar -czf volumes_backup_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/it-budget-prod*

# Запустить сервисы
docker-compose -f docker-compose.prod.yml up -d
```

## Контакты

- Фронтенд: https://budget-acme.shknv.ru
- API: http://93.189.228.52:8888
- API Docs: http://93.189.228.52:8888/docs
- Server: ssh root@93.189.228.52
