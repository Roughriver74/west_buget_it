# Исправление проблемы с API URL в Coolify

## Проблема

После деплоя на Coolify frontend показывает ошибку:
```
[Warning] [blocked] The page at https://budget-west.shknv.ru/login requested
insecure content from http://localhost:8888/api/v1/auth/login
```

**Причина**: Frontend пытается обратиться к `http://localhost:8888` вместо реального API URL.

## Решение

Есть 2 варианта решения:

### Вариант 1: Один домен с проксированием (Рекомендуется) ⭐

Frontend и Backend работают на одном домене через Coolify proxy.

#### Шаг 1: Настройка Backend

1. Откройте Backend приложение в Coolify
2. Перейдите в **Environment Variables**
3. Добавьте/обновите переменные:

```bash
# CORS - ВАЖНО! Добавьте домен frontend
CORS_ORIGINS=["https://budget-west.shknv.ru"]

# Остальные переменные
DB_HOST=<ваш_db_host>
DB_PORT=5432
DB_NAME=it_budget_db
DB_USER=budget_user
DB_PASSWORD=<strong_password>
SECRET_KEY=<strong_secret_key_min_32_chars>
DEBUG=False
API_PREFIX=/api/v1
```

4. В разделе **Domains** для Backend:
   - Оставьте основной домен или настройте поддомен (например `api.budget-west.shknv.ru`)
   - Главное чтобы Backend был доступен

#### Шаг 2: Настройка Frontend

1. Откройте Frontend приложение в Coolify
2. Перейдите в **Environment Variables**
3. **ВАЖНО**: Установите `VITE_API_URL=/api`

```bash
VITE_API_URL=/api
```

**Почему `/api`?**
- Это относительный путь от текущего домена
- Nginx внутри frontend контейнера проксирует `/api/*` запросы на backend
- Нет проблем с HTTPS/mixed content

4. В разделе **Domains** для Frontend:
   - Основной домен: `budget-west.shknv.ru`

#### Шаг 3: Настройка Coolify Proxy

1. Убедитесь что оба сервиса (frontend и backend) находятся в **одной Docker сети**
2. В Coolify это обычно настроено автоматически

#### Шаг 4: Rebuild и Deploy

1. **Backend**:
   - Нажмите **Restart** (если изменили только env vars)
   - Или **Rebuild** (если изменили код)

2. **Frontend**:
   - **ВАЖНО**: Нажмите **Rebuild** (не Restart!)
   - Build args должны включать `VITE_API_URL=/api`

3. Проверьте логи:
```bash
# Backend logs
docker logs <backend_container_name> -f

# Frontend logs
docker logs <frontend_container_name> -f
```

#### Шаг 5: Обновление nginx.conf (если нужно)

Если используете отдельный nginx в frontend:

```nginx
# В frontend/nginx.conf должен быть прокси:
location /api/ {
    # ВАЖНО: замените backend на реальное имя сервиса в Docker
    proxy_pass http://<backend_container_name>:8000;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Узнать имя backend контейнера:
```bash
ssh root@93.189.228.52
docker ps | grep backend
```

### Вариант 2: Разные домены для Frontend и Backend

Используйте если хотите API на отдельном поддомене.

#### Шаг 1: Настройка DNS

Добавьте A записи:
```
budget-west.shknv.ru     A    93.189.228.52
api.budget-west.shknv.ru A    93.189.228.52
```

#### Шаг 2: Backend настройки

```bash
# CORS - разрешить frontend домен
CORS_ORIGINS=["https://budget-west.shknv.ru"]
```

Domain: `api.budget-west.shknv.ru`

#### Шаг 3: Frontend настройки

```bash
# Полный URL к API
VITE_API_URL=https://api.budget-west.shknv.ru/api/v1
```

Domain: `budget-west.shknv.ru`

#### Шаг 4: Rebuild и Deploy

Rebuild оба сервиса.

## Проверка

### 1. Проверьте что API доступен

```bash
# Если используете вариант 1 (один домен)
curl https://budget-west.shknv.ru/api/v1/health

# Если используете вариант 2 (разные домены)
curl https://api.budget-west.shknv.ru/api/v1/health
```

Ожидаемый ответ:
```json
{"status":"ok"}
```

### 2. Проверьте env-config.js

Откройте в браузере:
```
https://budget-west.shknv.ru/config-check
```

Должно показать:
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: '/api'  // или полный URL для варианта 2
};
```

### 3. Проверьте CORS в консоли

Откройте DevTools в браузере (F12) и попробуйте залогиниться. Не должно быть ошибок CORS.

## Устранение проблем

### Проблема: 404 на env-config.js

**Решение**: Убедитесь что используете `Dockerfile.prod`, а не `Dockerfile` для production

### Проблема: CORS ошибки

**Решение**:
1. Проверьте `CORS_ORIGINS` в backend
2. Убедитесь что домен точно совпадает (https vs http, www vs без www)
3. Restart backend после изменения CORS_ORIGINS

### Проблема: Nginx не может найти backend

**Решение**:
1. Проверьте Docker сеть:
```bash
docker network ls
docker network inspect <network_name>
```

2. Проверьте что backend и frontend в одной сети
3. В nginx.conf используйте имя контейнера backend или имя сервиса

### Проблема: Mixed content error

**Решение**: Убедитесь что:
- VITE_API_URL начинается с `https://` или использует относительный путь `/api`
- НЕ используйте `http://` в production

## Docker Compose альтернатива

Если хотите использовать docker-compose.prod.yml для деплоя всего стека:

1. В Coolify создайте **Docker Compose** приложение
2. Укажите `docker-compose.prod.yml`
3. Установите переменные из `.env.production`
4. Deploy

Это автоматически настроит сеть между сервисами.

## Важные файлы

- [frontend/Dockerfile.prod](../frontend/Dockerfile.prod) - production build для frontend
- [frontend/nginx.conf](../frontend/nginx.conf) - настройки прокси
- [frontend/docker-entrypoint.sh](../frontend/docker-entrypoint.sh) - генерация env-config.js
- [.env.production](../.env.production) - пример production переменных
- [docker-compose.prod.yml](../docker-compose.prod.yml) - production стек

## Дополнительно

### Проверка переменных окружения внутри контейнера

```bash
# Frontend
docker exec <frontend_container> cat /usr/share/nginx/html/env-config.js

# Backend
docker exec <backend_container> env | grep -E "DB_|SECRET_|CORS_"
```

### Логи для диагностики

```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Только frontend
docker logs <frontend_container> -f --tail 100

# Только backend
docker logs <backend_container> -f --tail 100
```

### Health checks

```bash
# Frontend
curl https://budget-west.shknv.ru/health

# Backend
curl https://budget-west.shknv.ru/api/v1/health
# или
curl https://api.budget-west.shknv.ru/api/v1/health
```
