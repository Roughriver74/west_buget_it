# 🔧 Troubleshooting: Login Failed - Load Failed

## Проблема
После деплоя приложение загружается, но при попытке логина возникает ошибка:
```
Login Failed
Load failed
```

Это означает, что **frontend не может подключиться к backend API**.

---

## 🔍 Диагностика

### Шаг 1: Откройте браузер DevTools (F12)

1. Перейдите на вкладку **Console**
2. Попробуйте войти
3. Проверьте ошибки в консоли

#### Что искать:

**A) CORS Error:**
```
Access to XMLHttpRequest at 'https://api.budget-west.shknv.ru/api/v1/auth/login'
from origin 'https://budget-west.shknv.ru' has been blocked by CORS policy
```
👉 **Проблема:** Backend не разрешает запросы от frontend домена

**B) Network Error / ERR_NAME_NOT_RESOLVED:**
```
Failed to load resource: net::ERR_NAME_NOT_RESOLVED
```
👉 **Проблема:** Backend домен не резолвится (DNS проблема или Traefik не работает)

**C) 502 Bad Gateway / 504 Gateway Timeout:**
```
GET https://api.budget-west.shknv.ru/api/v1/auth/login 504
```
👉 **Проблема:** Backend контейнер не работает или Traefik не может к нему подключиться

**D) Mixed Content:**
```
Mixed Content: The page at 'https://...' was loaded over HTTPS,
but requested an insecure XMLHttpRequest endpoint 'http://...'
```
👉 **Проблема:** Frontend пытается подключиться к HTTP вместо HTTPS

---

### Шаг 2: Проверьте Network Tab

1. Откройте вкладку **Network** в DevTools
2. Попробуйте войти снова
3. Найдите запрос к `/api/v1/auth/login`
4. Проверьте:
   - **Request URL** - должен быть `https://api.budget-west.shknv.ru/api/v1/auth/login`
   - **Status Code** - что возвращает сервер
   - **Headers** - есть ли CORS заголовки

---

## ✅ Решения

### Решение 1: Проверить переменные окружения на сервере

**На Coolify:**

1. Откройте ваше приложение в Coolify
2. Перейдите в **Environment Variables**
3. **Убедитесь, что следующие переменные установлены:**

```bash
# Frontend domain (без https://)
FRONTEND_DOMAIN=budget-west.shknv.ru

# Backend domain (без https://)
BACKEND_DOMAIN=api.budget-west.shknv.ru

# CORS - ДОЛЖЕН ВКЛЮЧАТЬ FRONTEND DOMAIN С https://
CORS_ORIGINS=["https://budget-west.shknv.ru"]
# или если несколько:
CORS_ORIGINS=["https://budget-west.shknv.ru","https://another-domain.com"]

# VITE_API_URL - backend URL ДЛЯ FRONTEND (с https://, БЕЗ /api/v1)
VITE_API_URL=https://api.budget-west.shknv.ru

# SECRET_KEY - минимум 32 символа
SECRET_KEY=your-secure-random-key-here-min-32-chars

# Database credentials
DB_USER=budget_user
DB_PASSWORD=your-secure-password
DB_NAME=it_budget_db
```

4. **После изменения** - пересоберите и перезапустите приложение

---

### Решение 2: Проверить логи контейнеров

**SSH на сервер:**

```bash
ssh root@93.189.228.52
cd /path/to/your/project
```

**Проверьте логи backend:**

```bash
docker-compose -f docker-compose.prod.yml logs backend --tail=100
```

**Что искать:**
- ✅ `Database is ready!`
- ✅ `Migrations completed successfully`
- ✅ `Starting Gunicorn application server`
- ✅ `Booting worker with pid: XXXX`
- ❌ Ошибки подключения к БД
- ❌ Ошибки импорта модулей
- ❌ Validation errors для настроек

**Проверьте логи frontend:**

```bash
docker-compose -f docker-compose.prod.yml logs frontend --tail=50
```

**Что искать:**
- ✅ `Configuring frontend with:`
- ✅ `VITE_API_URL: https://api.budget-west.shknv.ru`
- ✅ `Starting Nginx web server`
- ❌ Wrong VITE_API_URL (localhost или неправильный домен)

---

### Решение 3: Проверить доступность backend API

**Из браузера или curl:**

```bash
# Проверить health endpoint
curl https://api.budget-west.shknv.ru/health

# Должен вернуть:
# {"status":"healthy"}

# Проверить root endpoint
curl https://api.budget-west.shknv.ru/

# Должен вернуть:
# {"message":"IT Budget Manager API","version":"0.5.0",...}

# Проверить docs
curl https://api.budget-west.shknv.ru/docs

# Должен вернуть HTML страницу Swagger
```

**Если возвращает 502/504:**
👉 Backend контейнер не работает - смотри логи

**Если возвращает 404:**
👉 Traefik не правильно настроен - проверь docker labels

**Если не подключается:**
👉 DNS или Traefik проблема

---

### Решение 4: Проверить env-config.js в frontend

**SSH на сервер:**

```bash
# Посмотреть конфигурацию frontend
docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js
```

**Должен вернуть:**
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: 'https://api.budget-west.shknv.ru'
};
```

**❌ Если видите:**
- `http://localhost:8888` - VITE_API_URL не передан
- `undefined` или `null` - переменная не установлена

**Исправление:**
1. Установите `VITE_API_URL` в environment variables
2. Пересоберите контейнер:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build frontend
   ```

---

### Решение 5: Исправить CORS настройки

**Если видите CORS ошибку в консоли браузера:**

1. **Проверьте CORS_ORIGINS на сервере:**
   ```bash
   # Внутри backend контейнера
   docker exec it_budget_backend_prod python -c "
   from app.core.config import settings
   print('CORS Origins:', settings.CORS_ORIGINS)
   "
   ```

2. **Должно вывести:**
   ```
   CORS Origins: ['https://budget-west.shknv.ru']
   ```

3. **❌ Если НЕ включает ваш frontend домен:**
   - Обновите `CORS_ORIGINS` в environment variables
   - **Формат:** `["https://budget-west.shknv.ru"]` (с квадратными скобками и кавычками!)
   - Перезапустите backend:
     ```bash
     docker-compose -f docker-compose.prod.yml restart backend
     ```

---

### Решение 6: Проверить Traefik routing

**Проверьте Traefik dashboard** (если доступен):

```bash
# Список активных роутеров
docker exec traefik traefik api/http/routers
```

**Или проверьте labels напрямую:**

```bash
docker inspect it_budget_backend_prod | grep -A20 "Labels"
```

**Должны быть labels:**
- `traefik.http.routers.backend.rule=Host(\`api.budget-west.shknv.ru\`)`
- `traefik.http.routers.backend.entrypoints=websecure`
- `traefik.http.services.backend.loadbalancer.server.port=8000`

---

## 🚀 Быстрое исправление (Most Common Issue)

**Проблема #1: VITE_API_URL не установлен**

В Coolify Environment Variables добавьте:
```bash
VITE_API_URL=https://api.budget-west.shknv.ru
```

Затем:
```bash
# Пересоберите frontend
docker-compose -f docker-compose.prod.yml up -d --build frontend

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs frontend

# Проверьте конфигурацию
docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js
```

**Проблема #2: CORS_ORIGINS не включает frontend domain**

В Coolify Environment Variables установите:
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru"]
```

Затем:
```bash
# Перезапустите backend
docker-compose -f docker-compose.prod.yml restart backend

# Проверьте настройки
docker exec it_budget_backend_prod python -c "from app.core.config import settings; print(settings.CORS_ORIGINS)"
```

---

## 📝 Checklist для проверки

- [ ] `FRONTEND_DOMAIN` установлен в env vars
- [ ] `BACKEND_DOMAIN` установлен в env vars
- [ ] `VITE_API_URL=https://api.budget-west.shknv.ru` (с https, БЕЗ /api/v1)
- [ ] `CORS_ORIGINS=["https://budget-west.shknv.ru"]` (включает frontend domain)
- [ ] DNS записи настроены для обоих доменов
- [ ] Backend контейнер запущен и healthy
- [ ] Frontend контейнер запущен и healthy
- [ ] `curl https://api.budget-west.shknv.ru/health` возвращает `{"status":"healthy"}`
- [ ] env-config.js содержит правильный VITE_API_URL
- [ ] Нет CORS ошибок в browser console
- [ ] Нет network errors в browser console

---

## 🆘 Если ничего не помогло

Соберите диагностическую информацию:

```bash
# 1. Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs --tail=200 > logs.txt

# 2. Статус контейнеров
docker-compose -f docker-compose.prod.yml ps > status.txt

# 3. Environment variables backend
docker exec it_budget_backend_prod env | grep -E "CORS|API|DB_|SECRET" > backend_env.txt

# 4. Environment variables frontend
docker exec it_budget_frontend_prod env | grep VITE > frontend_env.txt

# 5. Frontend конфигурация
docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js > frontend_config.txt

# 6. CORS настройки backend
docker exec it_budget_backend_prod python -c "from app.core.config import settings; print('CORS:', settings.CORS_ORIGINS)" > cors_settings.txt

# 7. Тест доступности API
curl -v https://api.budget-west.shknv.ru/health > api_health.txt 2>&1
```

Отправьте эти файлы для диагностики.

---

## 📚 Связанные документы

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Полная инструкция по деплою
- [CLAUDE.md](./CLAUDE.md) - Архитектура приложения
- [.env.prod.example](./.env.prod.example) - Пример переменных окружения
