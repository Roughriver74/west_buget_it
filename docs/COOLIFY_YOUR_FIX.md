# Инструкция по исправлению для вашего Coolify

## Текущая проблема

Frontend пытается обратиться к `http://localhost:8888` вместо реального API.

**Причина**: Конфликт между переменными в Coolify и docker-compose.prod.yml

## ✅ РЕКОМЕНДУЕМОЕ РЕШЕНИЕ (Вариант 1 - один домен)

Этот вариант проще и не имеет проблем с CORS.

### Шаг 1: Измените переменные в Coolify

#### Backend (без изменений):
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru"]
# Остальное без изменений
```

#### Frontend - ИЗМЕНИТЕ:
```bash
# БЫЛО:
VITE_API_URL=https://api.budget-west.shknv.ru

# ДОЛЖНО БЫТЬ:
VITE_API_URL=/api/v1
```

### Шаг 2: Проверьте что nginx работает

Nginx уже настроен правильно - он будет проксировать `/api/*` на backend.

### Шаг 3: Rebuild Frontend

⚠️ **ВАЖНО**: Нажмите **Rebuild** (не Restart!) для Frontend в Coolify.

### Шаг 4: Проверка

После деплоя:

```bash
# Проверьте что API доступен через nginx прокси
curl https://budget-west.shknv.ru/api/v1/health

# Должно вернуть:
# {"status":"ok"}

# Проверьте конфигурацию frontend
curl https://budget-west.shknv.ru/config-check

# Должно показать:
# window.ENV_CONFIG = {
#   VITE_API_URL: '/api/v1'
# };
```

В браузере:
1. Откройте https://budget-west.shknv.ru/login
2. Откройте DevTools (F12) → Network tab
3. Попробуйте залогиниться
4. Проверьте что запросы идут на `https://budget-west.shknv.ru/api/v1/auth/login`

---

## 🔄 АЛЬТЕРНАТИВА (Вариант 2 - отдельные домены)

Если хотите использовать отдельный API домен `api.budget-west.shknv.ru`:

### Что НЕ ТАК сейчас:

Ваша текущая настройка:
```bash
VITE_API_URL=https://api.budget-west.shknv.ru
```

Но docker-compose.prod.yml переопределяет на `/api`, поэтому не работает.

### Решение:

#### Вариант 2А: Убрать docker-compose (использовать отдельные Dockerfile)

В Coolify:
1. Создайте 2 отдельных приложения (не Docker Compose):
   - Backend → использует `backend/Dockerfile.prod`
   - Frontend → использует `frontend/Dockerfile.prod`

2. Frontend Environment Variables:
```bash
VITE_API_URL=https://api.budget-west.shknv.ru/api/v1
```

3. Backend Environment Variables:
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]
```

4. Rebuild оба сервиса

#### Вариант 2Б: Изменить docker-compose.prod.yml

Если используете Docker Compose в Coolify, нужно обновить файл:

1. Создайте альтернативный файл `docker-compose.coolify.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      DEBUG: "False"
      APP_NAME: "IT Budget Manager"
      API_PREFIX: /api/v1
      # ВАЖНО: Оба домена в CORS
      CORS_ORIGINS: '["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]'
      REDIS_URL: redis://redis:6379
    ports:
      - "${BACKEND_PORT:-8888}:8000"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/logs:/app/logs
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        # ИЗМЕНЕНО: Используем полный URL вместо относительного пути
        VITE_API_URL: ${VITE_API_URL}
    restart: always
    environment:
      # ИЗМЕНЕНО: Runtime env для полного URL
      VITE_API_URL: ${VITE_API_URL}
    ports:
      - "${FRONTEND_PORT:-3001}:80"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1/"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

volumes:
  postgres_data:
  redis_data:
```

2. В Coolify укажите этот файл вместо docker-compose.prod.yml

3. Переменные будут браться из Coolify Environment Variables

---

## ❓ Какой вариант выбрать?

### Выберите Вариант 1 (один домен), если:
- ✅ Хотите простое решение
- ✅ Не хотите проблем с CORS
- ✅ Достаточно одного домена для всего приложения
- ✅ **РЕКОМЕНДУЕТСЯ**

### Выберите Вариант 2 (разные домены), если:
- Нужен отдельный API endpoint для других клиентов
- Хотите изолировать API от frontend
- Готовы настраивать CORS

---

## 📝 Чеклист после исправления

- [ ] Измените `VITE_API_URL` в Coolify
- [ ] Rebuild Frontend (обязательно Rebuild, не Restart!)
- [ ] Проверьте `curl https://budget-west.shknv.ru/api/v1/health`
- [ ] Проверьте `curl https://budget-west.shknv.ru/config-check`
- [ ] Откройте сайт и проверьте DevTools Console (не должно быть ошибок CORS)
- [ ] Попробуйте залогиниться
- [ ] Проверьте что запросы идут на правильный URL в Network tab

---

## 🐛 Если всё ещё не работает

### 1. Проверьте логи Frontend

```bash
ssh root@93.189.228.52
docker logs <frontend_container_name> -f
```

Найдите строку:
```
Generated env-config.js with VITE_API_URL: ...
```

### 2. Проверьте логи Backend

```bash
docker logs <backend_container_name> -f
```

Ищите CORS ошибки или 404.

### 3. Проверьте что контейнеры в одной сети

```bash
docker network inspect <network_name>
```

### 4. Проверьте env-config.js напрямую

```bash
docker exec <frontend_container> cat /usr/share/nginx/html/env-config.js
```

Должно показать правильный VITE_API_URL.

### 5. Очистите кэш браузера

Ctrl+Shift+R (hard reload) или очистите кэш полностью.

---

## 📞 Нужна помощь?

Если проблема не решилась:

1. Пришлите вывод команд:
```bash
curl https://budget-west.shknv.ru/config-check
curl https://budget-west.shknv.ru/api/v1/health
docker logs <frontend_container> --tail 50
```

2. Скриншот из DevTools:
   - Console tab (ошибки)
   - Network tab (неудачный запрос к API)
