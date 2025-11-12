# 🔧 Глобальное решение проблемы деплоя в Coolify

## Проблема
При каждом деплое Traefik не может найти backend, возвращает Gateway Timeout и 404.

## Причина
Coolify добавляет Traefik labels с middleware `redirect-to-https@docker`, но этот middleware определён несколько раз разными приложениями, что вызывает конфликт. Также отсутствует определение service.

## ✅ РЕШЕНИЕ: Добавить Environment Variables в Coolify

### Шаг 1: Зайдите в Coolify UI

1. Откройте https://west-it.ru (Coolify dashboard)
2. Найдите ваше приложение "roughriver74west-buget-itmain"
3. Перейдите в раздел **Environment Variables**

### Шаг 2: Добавьте Traefik Labels для Backend

Добавьте следующие переменные (они будут автоматически преобразованы в Docker labels):

```bash
# Отключаем автоматические labels от Coolify
TRAEFIK_ENABLE=true

# Service definition (САМОЕ ВАЖНОЕ!)
TRAEFIK_HTTP_SERVICES_BACKEND_LOADBALANCER_SERVER_PORT=8000

# Routers для HTTP (редирект на HTTPS)
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTP_RULE=Host(`api.budget-west.shknv.ru`)
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTP_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTP_MIDDLEWARES=redirect-to-https@file
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTP_SERVICE=backend

# Routers для HTTPS
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_RULE=Host(`api.budget-west.shknv.ru`)
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_ENTRYPOINTS=https
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_TLS=true
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_TLS_CERTRESOLVER=letsencrypt
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_MIDDLEWARES=gzip@file
TRAEFIK_HTTP_ROUTERS_BACKEND_HTTPS_SERVICE=backend
```

### Шаг 3: Добавьте Traefik Labels для Frontend

```bash
# Service definition
TRAEFIK_HTTP_SERVICES_FRONTEND_LOADBALANCER_SERVER_PORT=80

# Routers для HTTP
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTP_RULE=Host(`budget-west.shknv.ru`)
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTP_ENTRYPOINTS=http
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTP_MIDDLEWARES=redirect-to-https@file
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTP_SERVICE=frontend

# Routers для HTTPS
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_RULE=Host(`budget-west.shknv.ru`)
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_ENTRYPOINTS=https
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_TLS=true
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_TLS_CERTRESOLVER=letsencrypt
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_MIDDLEWARES=gzip@file
TRAEFIK_HTTP_ROUTERS_FRONTEND_HTTPS_SERVICE=frontend
```

### Шаг 4: Redeploy

После добавления переменных, нажмите **Redeploy**. Coolify автоматически преобразует эти переменные в Docker labels.

## 🎯 Почему это работает?

1. **Service definition** - указываем порт, на котором работает приложение
2. **@file** вместо **@docker** - используем middleware из coolify.yaml, а не из Docker labels (избегаем конфликтов)
3. **Стабильные имена** - используем короткие имена (backend, frontend), которые не меняются при деплое

## 🔄 Альтернативное решение: Docker Compose Labels

Если Coolify использует ваш `docker-compose.prod.yml`, добавьте labels туда:

```yaml
services:
  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"
      - "traefik.http.routers.backend-http.rule=Host(`api.budget-west.shknv.ru`)"
      - "traefik.http.routers.backend-http.entrypoints=http"
      - "traefik.http.routers.backend-http.middlewares=redirect-to-https@file"
      - "traefik.http.routers.backend-http.service=backend"
      - "traefik.http.routers.backend-https.rule=Host(`api.budget-west.shknv.ru`)"
      - "traefik.http.routers.backend-https.entrypoints=https"
      - "traefik.http.routers.backend-https.tls=true"
      - "traefik.http.routers.backend-https.tls.certresolver=letsencrypt"
      - "traefik.http.routers.backend-https.middlewares=gzip@file"
      - "traefik.http.routers.backend-https.service=backend"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
      - "traefik.http.routers.frontend-http.rule=Host(`budget-west.shknv.ru`)"
      - "traefik.http.routers.frontend-http.entrypoints=http"
      - "traefik.http.routers.frontend-http.middlewares=redirect-to-https@file"
      - "traefik.http.routers.frontend-http.service=frontend"
      - "traefik.http.routers.frontend-https.rule=Host(`budget-west.shknv.ru`)"
      - "traefik.http.routers.frontend-https.entrypoints=https"
      - "traefik.http.routers.frontend-https.tls=true"
      - "traefik.http.routers.frontend-https.tls.certresolver=letsencrypt"
      - "traefik.http.routers.frontend-https.middlewares=gzip@file"
      - "traefik.http.routers.frontend-https.service=frontend"
```

## 🚨 Если снова сломается

Выполните на сервере:

```bash
# 1. Проверьте, что контейнеры запущены
docker ps | grep io00swck8gss4kosckwwwo88

# 2. Перезапустите Traefik
docker restart coolify-proxy

# 3. Проверьте logs
docker logs coolify-proxy --tail 50

# 4. Проверьте работу
curl -I https://api.budget-west.shknv.ru/health
curl -I https://budget-west.shknv.ru/
```

## 📝 Проверка настроек

После деплоя проверьте labels контейнера:

```bash
docker inspect $(docker ps -q --filter "name=backend-io00swck8gss4kosckwwwo88") --format '{{json .Config.Labels}}' | python3 -m json.tool | grep traefik
```

Должны быть:
- `traefik.enable: true`
- `traefik.http.services.backend.loadbalancer.server.port: 8000`
- Все роутеры с `@file` middleware

---

**Ключевой момент**: Используем `@file` для middleware вместо `@docker`, чтобы избежать конфликтов!
