# Инструкция по исправлению проблем с API после деплоя

## Найденные проблемы

1. ❌ **Backend**: Health endpoint не был доступен по пути `/api/v1/health`
2. ❌ **Frontend**: `VITE_API_URL` установлен на `https://api.budget-west.shknv.ru` вместо `/api`

## Решение

### Шаг 1: Commit и Push изменений в Backend

```bash
# Уже исправлено в main.py - добавлен health endpoint с API_PREFIX
git add backend/app/main.py
git commit -m "fix: add health endpoint with API prefix for proper frontend connectivity"
git push origin main
```

### Шаг 2: Настройка Frontend в Coolify

1. Откройте **Frontend** приложение в Coolify (https://budget-west.shknv.ru:8000)
2. Перейдите в раздел **Environment Variables**
3. Найдите переменную `VITE_API_URL`
4. **Измените значение на**: `/api` (без кавычек)
5. Нажмите **Save**

### Шаг 3: Rebuild Backend

1. Откройте **Backend** приложение в Coolify
2. Нажмите **Rebuild** (не Restart!)
3. Дождитесь завершения сборки (обычно 2-3 минуты)
4. Проверьте логи на наличие ошибок

### Шаг 4: Rebuild Frontend

1. Откройте **Frontend** приложение в Coolify
2. **ВАЖНО**: Нажмите **Rebuild** (не Restart!)
   - Rebuild пересоздаст контейнер с новыми переменными окружения
   - Restart просто перезапустит существующий контейнер
3. Дождитесь завершения сборки (обычно 1-2 минуты)
4. Проверьте логи на наличие ошибок

### Шаг 5: Проверка работоспособности

#### 5.1 Проверьте env-config.js

Откройте в браузере:
```
https://budget-west.shknv.ru/config-check
```

Должно показать:
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: '/api'
};
```

❌ **Если показывает**: `https://api.budget-west.shknv.ru` - значит Frontend НЕ был пересобран (rebuild)

#### 5.2 Проверьте Health endpoint

```bash
# Должен вернуть: {"status":"healthy"}
curl https://budget-west.shknv.ru/api/v1/health
```

#### 5.3 Проверьте логин в браузере

1. Откройте https://budget-west.shknv.ru
2. Попробуйте войти с учетными данными
3. Откройте DevTools (F12) → Network tab
4. Проверьте что запросы идут на `/api/v1/...` (не на `api.budget-west.shknv.ru`)

### Шаг 6: Дополнительная диагностика (если проблемы остались)

#### Проверка логов Backend:
```bash
ssh root@93.189.228.52
docker logs backend-io00swck8gss4kosckwwwo88-083101661773 --tail 100 -f
```

#### Проверка логов Frontend:
```bash
ssh root@93.189.228.52
docker logs frontend-io00swck8gss4kosckwwwo88-083101693018 --tail 100 -f
```

#### Проверка прокси из Frontend контейнера:
```bash
ssh root@93.189.228.52
docker exec frontend-io00swck8gss4kosckwwwo88-083101693018 curl -s http://localhost/api/v1/health
# Должно вернуть: {"status":"healthy"}
```

#### Проверка Backend напрямую:
```bash
ssh root@93.189.228.52
docker exec backend-io00swck8gss4kosckwwwo88-083101661773 curl -s http://localhost:8000/api/v1/health
# Должно вернуть: {"status":"healthy"}
```

## Архитектура работы (для понимания)

```
Browser
  ↓
https://budget-west.shknv.ru
  ↓
Coolify Proxy (Traefik)
  ↓
Frontend Container (nginx)
  ↓ /api/* → proxy_pass http://backend:8000
  ↓
Backend Container (FastAPI)
  ↓
/api/v1/health → 200 OK {"status":"healthy"}
```

## Важные замечания

1. **Всегда используйте Rebuild**, если меняете переменные окружения
2. **VITE_API_URL** должен быть `/api` (относительный путь)
3. **CORS_ORIGINS** в Backend должен включать `https://budget-west.shknv.ru`
4. **Nginx в Frontend** проксирует `/api/*` на `http://backend:8000`
5. **Имя хоста `backend`** резолвится автоматически в Docker network

## Если нужен отдельный поддомен для API

Если по какой-то причине нужен api.budget-west.shknv.ru:

1. Создайте DNS запись: `api.budget-west.shknv.ru A 93.189.228.52`
2. В Coolify Backend добавьте домен: `api.budget-west.shknv.ru`
3. В Frontend установите: `VITE_API_URL=https://api.budget-west.shknv.ru/api/v1`
4. В Backend добавьте в CORS: `https://api.budget-west.shknv.ru`

Но **рекомендуемый подход** - использовать один домен с проксированием через nginx.

## Контакты для помощи

- Документация Coolify: https://coolify.io/docs
- GitHub Issues: https://github.com/coollabsio/coolify/issues
- Документация проекта: `/docs/COOLIFY_FIX.md`
