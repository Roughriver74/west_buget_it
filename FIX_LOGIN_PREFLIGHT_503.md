# 🔧 Исправление ошибки 503 на preflight запросе при логине

## Описание проблемы

**Ошибка:**
```
[Error] Preflight response is not successful. Status code: 503
[Error] Fetch API cannot load https://api.budget-west.shknv.ru/api/v1/auth/login
due to access control checks.
```

**Причина:**
OPTIONS запросы (CORS preflight) блокируются или не доходят до бэкенда, возвращая 503 от Traefik.

## Решение

Добавлен специальный `OptionsMiddleware` в `backend/app/main.py`, который:
1. **Обрабатывает OPTIONS запросы немедленно** - до rate limiting и других middleware
2. **Возвращает правильные CORS заголовки** для preflight
3. **Предотвращает 503 ошибки** от Traefik

## 🚀 Инструкция по деплою

### Шаг 1: Подключитесь к серверу

```bash
ssh root@93.189.228.52
cd /path/to/your/project  # Перейдите в директорию проекта
```

### Шаг 2: Получите последние изменения

```bash
# Получить последние изменения из ветки
git fetch origin
git pull origin claude/fix-login-preflight-error-011CUf7ZUKWBMJkHRvpy7bKf
```

### Шаг 3: Проверьте изменения

```bash
# Проверьте, что изменения есть
git log --oneline -3

# Должны увидеть коммит с текстом "fix: add OPTIONS middleware to handle CORS preflight"
```

### Шаг 4: Пересоберите и перезапустите бэкенд

```bash
# Остановите текущий контейнер
docker-compose -f docker-compose.prod.yml stop backend

# Пересоберите образ с новыми изменениями
docker-compose -f docker-compose.prod.yml build --no-cache backend

# Запустите обновленный контейнер
docker-compose -f docker-compose.prod.yml up -d backend

# Посмотрите логи запуска (должны увидеть новое сообщение)
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Ожидаемые сообщения в логах:**
```
✅ Database is ready!
✅ Migrations completed successfully
OPTIONS preflight middleware enabled (handles CORS preflight immediately)
Security headers enabled (production mode: True)
Rate limiting enabled: 500 req/min, 5000 req/hour per IP
Starting Gunicorn application server
```

### Шаг 5: Проверьте работу OPTIONS запроса

**Тест 1: Проверка healthcheck**
```bash
curl https://api.budget-west.shknv.ru/health
# Ожидается: {"status":"healthy"}
```

**Тест 2: Проверка OPTIONS для login**
```bash
curl -X OPTIONS https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Origin: https://budget-west.shknv.ru" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Ожидаемый результат:**
```
< HTTP/2 200
< access-control-allow-origin: https://budget-west.shknv.ru
< access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
< access-control-allow-headers: Content-Type, Authorization, X-Requested-With
< access-control-allow-credentials: true
< access-control-max-age: 3600
```

**Тест 3: Проверка реального логина**
```bash
curl -X POST https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: https://budget-west.shknv.ru" \
  -d '{"username":"admin","password":"admin"}' \
  -v
```

**Ожидается:** JSON с токеном доступа (или ошибка 401 если неправильный пароль)

### Шаг 6: Проверьте в браузере

1. Откройте https://budget-west.shknv.ru
2. Откройте DevTools (F12) → вкладка Console
3. Попробуйте залогиниться
4. **Не должно быть ошибок 503** в консоли

## 🔍 Диагностика проблем

### Проблема: Контейнер не запускается

```bash
# Проверьте логи на ошибки
docker-compose -f docker-compose.prod.yml logs backend --tail=100

# Проверьте статус
docker-compose -f docker-compose.prod.yml ps
```

**Частые причины:**
- База данных не готова → Перезапустите БД: `docker-compose -f docker-compose.prod.yml restart db`
- Ошибка миграции → Проверьте логи миграций
- Ошибка импорта → Проверьте синтаксис Python

### Проблема: OPTIONS всё ещё возвращает 503

```bash
# Проверьте, что контейнер ЗДОРОВ
docker-compose -f docker-compose.prod.yml ps backend
# Должно быть: Up (healthy)

# Проверьте логи Traefik
docker logs traefik --tail=50 2>&1 | grep -i backend

# Проверьте, что Traefik видит бэкенд
docker exec traefik wget -O- http://it_budget_backend_prod:8000/health
```

### Проблема: Логи показывают старую версию

```bash
# Убедитесь, что образ пересобран
docker images | grep it-budget-backend

# Удалите старый образ и пересоберите
docker-compose -f docker-compose.prod.yml down backend
docker rmi it-budget-backend:prod
docker-compose -f docker-compose.prod.yml build --no-cache backend
docker-compose -f docker-compose.prod.yml up -d backend
```

## 📊 Проверка переменных окружения

**Убедитесь, что в Coolify установлены:**

```bash
# Проверьте CORS_ORIGINS
docker exec it_budget_backend_prod python -c \
  "from app.core.config import settings; print('CORS:', settings.CORS_ORIGINS)"

# Должно быть: CORS: ['https://budget-west.shknv.ru']
```

**Если CORS неправильный:**
1. Откройте Coolify
2. Перейдите в Environment Variables
3. Установите: `CORS_ORIGINS=["https://budget-west.shknv.ru"]`
4. Перезапустите: `docker-compose -f docker-compose.prod.yml restart backend`

## 🎯 Технические детали

### Что изменилось

**Файл:** `backend/app/main.py`

**Добавлено:**
1. `OptionsMiddleware` - обрабатывает OPTIONS запросы немедленно
2. Middleware добавляется **ПЕРВЫМ** - до CORS, security headers, rate limiting
3. Проверяет origin против `CORS_ORIGINS`
4. Возвращает правильные CORS заголовки

**Преимущества:**
- ✅ OPTIONS не блокируются rate limiting
- ✅ OPTIONS обрабатываются даже при проблемах с другими middleware
- ✅ Traefik получает быстрый ответ 200 OK
- ✅ Браузер получает правильные CORS заголовки
- ✅ Логин работает корректно

### Порядок middleware (критично!)

```python
1. OptionsMiddleware           ← НОВЫЙ! Обрабатывает OPTIONS сразу
2. CORSMiddleware              ← Для обычных запросов
3. SecurityHeadersMiddleware   ← Заголовки безопасности
4. RateLimiterMiddleware       ← Ограничение запросов
5. RequestLoggingMiddleware    ← Логирование
```

## 🆘 Всё ещё не работает?

Если после выполнения всех шагов логин не работает:

1. **Соберите диагностическую информацию:**

```bash
# Запустите диагностику
./scripts/diagnose-503.sh > diagnostic-output.txt 2>&1

# Соберите логи
docker-compose -f docker-compose.prod.yml logs > all-logs.txt

# Проверьте статус
docker-compose -f docker-compose.prod.yml ps > status.txt

# Сожмите файлы
tar -czf diagnostics.tar.gz diagnostic-output.txt all-logs.txt status.txt
```

2. **Проверьте:**
   - DNS правильно настроен: `nslookup api.budget-west.shknv.ru`
   - SSL сертификаты валидны: `curl -I https://api.budget-west.shknv.ru`
   - Traefik работает: `docker ps | grep traefik`

3. **Отправьте:**
   - `diagnostics.tar.gz`
   - Скриншот ошибки из браузера (DevTools Console)
   - Переменные окружения (БЕЗ паролей!)

---

## ✅ Успешный результат

После правильного деплоя:
- ✅ OPTIONS запросы возвращают 200 OK с CORS заголовками
- ✅ Логин работает без ошибок в консоли
- ✅ Preflight requests обрабатываются быстро (< 100ms)
- ✅ В логах видно: "OPTIONS preflight middleware enabled"
