# Исправление ошибки 503 при логине

## Проблема

При попытке логина возникает ошибка:
```
[Error] Preflight response is not successful. Status code: 503
[Error] Fetch API cannot load https://api.budget-west.shknv.ru/api/v1/auth/login due to access control checks.
```

## Причина

Backend не разрешает CORS запросы с домена `https://api.budget-west.shknv.ru`, так как в переменной окружения `CORS_ORIGINS` отсутствует этот домен.

## Решение

### 1. Обновить CORS_ORIGINS в Coolify

Зайдите в Coolify и обновите переменную окружения `CORS_ORIGINS` для backend сервиса:

**Текущее значение:**
```json
["https://budget-west.shknv.ru","http://loo408gk48sck40kk0so8gwc.93.189.228.52.sslip.io"]
```

**Новое значение:**
```json
["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru","http://localhost:5173"]
```

#### Инструкция:

1. Откройте Coolify UI по адресу: http://93.189.228.52:8000
2. Найдите проект "IT Budget Manager" (или соответствующее название)
3. Перейдите в раздел "Environment Variables" для backend сервиса
4. Найдите переменную `CORS_ORIGINS`
5. Обновите значение на:
   ```
   ["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru","http://localhost:5173"]
   ```
6. Сохраните изменения
7. Перезапустите backend сервис

### 2. Или обновить через .env.prod файл (если есть доступ)

Если вы деплоите через git push, создайте файл `.env.prod` в корне проекта:

```bash
# .env.prod
CORS_ORIGINS=["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru","http://localhost:5173"]
DEBUG=False
SECRET_KEY=<ваш-секретный-ключ>
DB_NAME=it_budget_db
DB_USER=budget_user
DB_PASSWORD=<ваш-пароль-БД>
VITE_API_URL=https://api.budget-west.shknv.ru
```

### 3. Изменения в docker-compose.prod.yml

Файл `docker-compose.prod.yml` был обновлен:
- Удалены неработающие Traefik labels (Coolify использует Caddy)
- CORS теперь настраивается только через переменную окружения

### 4. Перезапуск сервисов

После обновления переменных окружения в Coolify:

```bash
# Coolify автоматически перезапустит контейнер
# Или вручную через UI: Deploy > Restart
```

Если деплоите напрямую на сервере:

```bash
ssh root@93.189.228.52
cd /path/to/project
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Проверка

После перезапуска проверьте:

1. CORS настройки в контейнере:
   ```bash
   docker inspect backend-io00swck8gss4kosckwwwo88-110014958352 --format '{{json .Config.Env}}' | grep CORS
   ```

2. Попробуйте залогиниться на https://budget-west.shknv.ru

3. Проверьте логи backend:
   ```bash
   docker logs backend-io00swck8gss4kosckwwwo88-110014958352 --tail 50
   ```

## Предотвращение проблемы в будущем

1. **Всегда проверяйте CORS_ORIGINS** перед деплоем
2. **Включите в CORS_ORIGINS все домены**, с которых может идти запрос:
   - Frontend домен: `https://budget-west.shknv.ru`
   - API домен: `https://api.budget-west.shknv.ru`
   - Localhost для разработки: `http://localhost:5173`

3. **Используйте .env.prod.example** как шаблон для production конфигурации

## Дополнительная информация

### Почему это произошло?

Coolify использует Caddy для reverse proxy, а не Traefik. Traefik labels в docker-compose.prod.yml не работали и создавали ошибки в логах. CORS должен настраиваться на уровне FastAPI приложения через переменную окружения.

### Архитектура CORS в проекте

```
Frontend (budget-west.shknv.ru)
     ↓ fetch()
API (api.budget-west.shknv.ru)
     ↓ Caddy proxy (Coolify)
     ↓
Backend Container :8000
     ↓ FastAPI CORS Middleware
     ↓ Проверка CORS_ORIGINS
     ↓ Разрешение/отклонение запроса
```

Если `api.budget-west.shknv.ru` не в списке CORS_ORIGINS → 503 error при preflight request (OPTIONS).

## Контакты

При возникновении проблем проверьте:
- [CLAUDE.md](CLAUDE.md) - архитектура проекта
- [backend/app/main.py](backend/app/main.py:51-57) - конфигурация CORS
- [backend/app/core/config.py](backend/app/core/config.py:80-88) - парсинг CORS_ORIGINS
