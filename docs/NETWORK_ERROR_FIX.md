# 🔥 Исправление Network Error на /revenue/categories

## Диагностика

Network Error означает, что frontend не может подключиться к backend API. Проверим несколько вещей:

### 1. Проверка API URL в браузере

Откройте в браузере: **https://budget-west.shknv.ru/config-check**

Вы должны увидеть:
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: '/api'
};
```

**Если видите что-то другое** (например `undefined` или `http://localhost:8888`):
```bash
# SSH на сервер
ssh root@93.189.228.52

# Найти frontend контейнер
docker ps | grep frontend

# Проверить env-config.js
docker exec <frontend_container_name> cat /usr/share/nginx/html/env-config.js
```

### 2. Проверка доступности backend

Проверьте что backend отвечает:
```bash
# Из браузера или curl
curl https://budget-west.shknv.ru/api/v1/health

# Должен вернуть:
{"status":"ok"}
```

**Если 502 Bad Gateway или таймаут** - backend недоступен.

### 3. Проверка Docker сети

```bash
# SSH на сервер
ssh root@93.189.228.52

# Найти имя frontend контейнера
docker ps | grep frontend
# Пример: coolify-prod-frontend-abc123

# Проверить может ли frontend достучаться до backend
docker exec <frontend_container_name> ping -c 3 backend

# Если "ping: bad address" - backend не доступен по имени "backend"
```

## Решение 1: Исправить имя backend в nginx (если Docker сеть не настроена)

Если backend недоступен по имени `backend`, нужно найти реальное имя:

```bash
# Найти реальное имя/IP backend контейнера
docker ps | grep backend
# Пример: coolify-prod-backend-xyz789

# Проверить в какой сети находятся контейнеры
docker network ls
docker network inspect <network_name>
```

**Вариант A: Использовать имя контейнера**

Обновите `frontend/nginx.conf` строку 36:
```nginx
# Было:
proxy_pass http://backend:8000;

# Стало (используйте реальное имя):
proxy_pass http://coolify-prod-backend-xyz789:8000;
```

**Вариант B: Использовать имя сервиса из Coolify**

В Coolify обычно сервисы доступны по имени приложения. Проверьте имя backend приложения в Coolify.

```nginx
proxy_pass http://<backend_service_name>:8000;
```

## Решение 2: Использовать прямой URL к backend (быстрое решение)

Если backend развернут на отдельном домене:

### В Coolify Frontend настройках:

**Environment Variables:**
```bash
VITE_API_URL=https://api.budget-west.shknv.ru/api/v1
# или
VITE_API_URL=https://budget-west.shknv.ru/api/v1
```

**Rebuild frontend** после изменения переменных!

### В Coolify Backend настройках:

**Environment Variables:**
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru"]
```

**Restart backend** после изменения.

## Решение 3: Проверить CORS настройки

Откройте DevTools (F12) на странице https://budget-west.shknv.ru/revenue/categories

Проверьте Console и Network tabs:

**Если видите CORS error:**
```
Access to XMLHttpRequest at 'https://...' from origin 'https://budget-west.shknv.ru'
has been blocked by CORS policy
```

**Исправление:**
```bash
# SSH на сервер
ssh root@93.189.228.52

# Найти backend контейнер
docker ps | grep backend

# Проверить CORS настройки
docker exec <backend_container> env | grep CORS

# Если CORS_ORIGINS не содержит ваш домен:
# Обновите в Coolify Backend -> Environment Variables:
CORS_ORIGINS=["https://budget-west.shknv.ru","http://localhost:5173"]

# Restart backend
docker restart <backend_container>
```

## Решение 4: Проверить маршрут endpoint

Backend должен отвечать на `/api/v1/revenue/categories/`:

```bash
# Проверить напрямую
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://budget-west.shknv.ru/api/v1/revenue/categories/

# Если 404 - endpoint не зарегистрирован
# Если 401 - проблема с аутентификацией (это норма без токена)
# Если 500 - проблема на backend
# Если connection refused - backend недоступен
```

## Решение 5: Проверить логи

```bash
# Backend логи
docker logs <backend_container_name> -f --tail 100

# Frontend nginx логи
docker logs <frontend_container_name> -f --tail 100

# Ищите ошибки:
# - Connection refused
# - 502 Bad Gateway
# - Timeout
# - CORS errors
```

## Быстрая проверка (копируй-пасти)

```bash
#!/bin/bash
# Диагностика Network Error

echo "=== 1. Проверка frontend env-config ==="
curl -s https://budget-west.shknv.ru/config-check

echo -e "\n=== 2. Проверка backend health ==="
curl -s https://budget-west.shknv.ru/api/v1/health

echo -e "\n=== 3. Проверка Docker контейнеров ==="
ssh root@93.189.228.52 "docker ps | grep -E 'frontend|backend'"

echo -e "\n=== 4. Проверка CORS настроек ==="
ssh root@93.189.228.52 "docker ps --format '{{.Names}}' | grep backend | xargs -I {} docker exec {} env | grep CORS"

echo -e "\n=== 5. Backend логи (последние 20 строк) ==="
ssh root@93.189.228.52 "docker ps --format '{{.Names}}' | grep backend | head -1 | xargs docker logs --tail 20"
```

## Рекомендованное решение для Coolify

**Шаг 1**: В Coolify Frontend:
```bash
VITE_API_URL=/api
```

**Шаг 2**: В Coolify Backend:
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru"]
```

**Шаг 3**: Убедитесь что оба сервиса в одной Docker сети

**Шаг 4**: Rebuild frontend, Restart backend

**Шаг 5**: Проверка
```bash
curl https://budget-west.shknv.ru/api/v1/health
```

## Если ничего не помогло

Отправьте вывод этих команд:

```bash
# 1. Config check
curl https://budget-west.shknv.ru/config-check

# 2. Health check
curl -v https://budget-west.shknv.ru/api/v1/health 2>&1

# 3. Docker network
ssh root@93.189.228.52 "docker network ls && docker ps"

# 4. Backend env
ssh root@93.189.228.52 "docker ps --format '{{.Names}}' | grep backend | xargs -I {} docker exec {} env | grep -E 'CORS|DB_HOST|API_PREFIX'"

# 5. Frontend env-config
ssh root@93.189.228.52 "docker ps --format '{{.Names}}' | grep frontend | xargs -I {} docker exec {} cat /usr/share/nginx/html/env-config.js"
```

---

**Версия:** 1.0
**Дата:** 2025-11-05
