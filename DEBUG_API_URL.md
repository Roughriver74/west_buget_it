# Диагностика проблемы с API URL (307 редирект)

## Проблема
Frontend пытается обратиться по `http://api.budget-west.shknv.ru`, хотя должен использовать `https://`.

## Шаги диагностики

### 1. Проверить что реально загружается в браузер

Откройте в браузере DevTools (F12) и выполните в консоли:

```javascript
// Проверка 1: Что в window.ENV_CONFIG?
console.log('ENV_CONFIG:', window.ENV_CONFIG);

// Проверка 2: Что в import.meta.env?
// (Это доступно только если DevTools открыт на странице с Vite)

// Проверка 3: Какой API_BASE_URL используется?
// Откройте Network tab и посмотрите на URL запросов
```

### 2. Проверить загрузку env-config.js

В DevTools → Network:
- Найдите запрос к `env-config.js`
- Посмотрите Response
- Убедитесь что там `https://`, а не `http://`

Или прямо в браузере откройте:
```
https://budget-west.shknv.ru/env-config.js
```

### 3. Проверить на сервере

```bash
ssh root@93.189.228.52

# Проверка 1: Что в контейнере?
docker exec it_budget_frontend_prod cat /usr/share/nginx/html/env-config.js

# Проверка 2: Какие environment variables?
docker exec it_budget_frontend_prod env | grep VITE

# Проверка 3: Перезапустите frontend с правильной переменной
docker-compose down frontend
docker-compose up -d frontend

# Проверка 4: Посмотрите логи запуска
docker logs it_budget_frontend_prod --tail 50
```

### 4. Если env-config.js правильный, но проблема остаётся

Значит проблема в кеше браузера:

```javascript
// В консоли браузера:
localStorage.clear();
sessionStorage.clear();
location.reload(true); // Hard reload
```

Или:
- Chrome: Ctrl+Shift+Delete → Очистить кеш
- Firefox: Ctrl+Shift+Delete → Кеш

### 5. Если это не помогает - проверьте Service Worker

```javascript
// В консоли браузера:
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister();
    console.log('Unregistered:', registration);
  }
  location.reload();
});
```

## Быстрое решение (если на сервере всё правильно)

```bash
# На сервере:
ssh root@93.189.228.52

# 1. Пересоздайте контейнер frontend с новой конфигурацией
docker-compose down frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend

# 2. Проверьте результат
docker logs it_budget_frontend_prod --tail 20
curl http://127.0.0.1:3001/config-check
```

## Проверка через curl (с сервера)

```bash
# Должен вернуть правильный env-config.js
curl http://127.0.0.1:3001/config-check

# Ожидаемый результат:
# window.ENV_CONFIG = {
#   VITE_API_URL: 'https://api.budget-west.shknv.ru'
# };
```

## Альтернативное решение: Использовать nginx proxy

Самый надёжный способ - использовать относительный URL:

```bash
# В Coolify или docker-compose.prod.yml:
VITE_API_URL=/api

# Это заставит frontend использовать:
# https://budget-west.shknv.ru/api/v1/...
# А nginx проксирует на backend:8000
```

Преимущества:
- ✅ Нет проблем с CORS
- ✅ Нет проблем с HTTPS редиректами
- ✅ Проще настройка
- ✅ Единый домен для frontend и API

## Если нужно использовать отдельный API домен

Убедитесь что:
1. ✅ В `VITE_API_URL` используется `https://` (не `http://`)
2. ✅ Backend имеет правильный CORS: `["https://budget-west.shknv.ru"]`
3. ✅ Нет редиректов с http на https на уровне API
4. ✅ SSL сертификат валиден для api.budget-west.shknv.ru
