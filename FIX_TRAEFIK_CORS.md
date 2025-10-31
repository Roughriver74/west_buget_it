# 🔧 Исправление проблемы Traefik + CORS

## Проблема

Сайт не открывается, в логах контейнеров нет ошибок, но запросы не доходят до backend. Это проблема с **Traefik routing**.

### Типичные симптомы:
- ✅ Backend контейнер запущен и healthy
- ✅ В логах backend нет ошибок
- ❌ Сайт не открывается (белый экран / 502 / 503)
- ❌ API не отвечает через Traefik
- ✅ API отвечает напрямую: `curl http://localhost:8888/health` работает

---

## 🔍 Диагностика

### Шаг 1: Запустите диагностический скрипт

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# Получить скрипт
git pull origin claude/fix-login-preflight-error-011CUf7ZUKWBMJkHRvpy7bKf

# Запустить диагностику
chmod +x diagnose_traefik.sh
./diagnose_traefik.sh
```

Скрипт проверит:
1. ✅ Traefik запущен
2. ✅ Backend запущен и healthy
3. ✅ Backend и Traefik в одной сети
4. ✅ Traefik может достучаться до Backend
5. ✅ Traefik labels правильно настроены
6. ✅ API доступен извне

### Шаг 2: Ручная диагностика

Если скрипт недоступен:

```bash
# 1. Проверка Traefik
docker ps | grep traefik
# Должен быть запущен!

# 2. Проверка Backend
docker ps | grep backend
docker inspect it_budget_backend_prod --format='{{.State.Health.Status}}'
# Должно быть: healthy

# 3. Проверка что backend отвечает ВНУТРИ контейнера
docker exec it_budget_backend_prod curl http://localhost:8000/health
# Должно вернуть: {"status":"healthy"}

# 4. Проверка что Traefik может достучаться до backend
BACKEND_IP=$(docker inspect it_budget_backend_prod --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
TRAEFIK_CONTAINER=$(docker ps --filter "name=traefik" --format "{{.Names}}" | head -1)
docker exec $TRAEFIK_CONTAINER wget -O- http://$BACKEND_IP:8000/health

# 5. Проверка внешнего доступа
curl https://api.budget-west.shknv.ru/health
```

---

## 🛠️ Причина проблемы

**Traefik CORS middleware не обрабатывает OPTIONS запросы правильно!**

В текущей конфигурации (`docker-compose.prod.yml:113`):
```yaml
- "traefik.http.routers.backend.middlewares=backend-cors"
```

Traefik headers middleware только **добавляет заголовки** к существующим ответам, но **НЕ создаёт ответы на OPTIONS**. Когда браузер шлёт OPTIONS, Traefik пытается передать его на backend, но что-то идёт не так, и возвращается 503.

### Проблемы с Traefik CORS middleware:
1. ❌ Не создаёт ответы на OPTIONS
2. ❌ Не обрабатывает preflight правильно
3. ❌ Может конфликтовать с CORS в FastAPI
4. ❌ Не валидирует origin

---

## ✅ Решение

**Убрать CORS middleware из Traefik и дать FastAPI обрабатывать CORS самостоятельно.**

FastAPI уже имеет `CORSMiddleware` который правильно обрабатывает:
- ✅ OPTIONS preflight запросы
- ✅ Access-Control-* заголовки
- ✅ Валидацию origin
- ✅ Credentials

### Применить исправление:

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# Резервная копия текущей конфигурации
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# Применить исправленную конфигурацию
cp docker-compose.prod.FIXED.yml docker-compose.prod.yml

# Пересоздать контейнеры с новыми labels
docker-compose -f docker-compose.prod.yml up -d --force-recreate backend frontend

# Ждать запуска (1 минута)
sleep 60

# Проверить
docker-compose -f docker-compose.prod.yml ps
```

### Что изменилось в docker-compose.prod.FIXED.yml:

#### ДО (строка 113):
```yaml
- "traefik.http.routers.backend.middlewares=backend-cors"

# И дальше (строки 120-125):
- "traefik.http.middlewares.backend-cors.headers.accesscontrolallowmethods=..."
- "traefik.http.middlewares.backend-cors.headers.accesscontrolalloworiginlist=..."
# ...
```

#### ПОСЛЕ:
```yaml
# Убрана строка с middlewares
# - "traefik.http.routers.backend.middlewares=backend-cors"

# Убраны CORS headers middleware (строки 120-125)
# FastAPI обрабатывает CORS самостоятельно
```

---

## 🧪 Тестирование после исправления

### 1. Проверка healthcheck
```bash
curl https://api.budget-west.shknv.ru/health
# Ожидается: {"status":"healthy"}
```

### 2. Проверка OPTIONS (CORS preflight)
```bash
curl -v -X OPTIONS https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Origin: https://budget-west.shknv.ru" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# Ожидается:
# HTTP/2 200
# access-control-allow-origin: https://budget-west.shknv.ru
# access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
# access-control-allow-credentials: true
```

### 3. Проверка реального логина
```bash
curl -X POST https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: https://budget-west.shknv.ru" \
  -d '{"username":"admin","password":"admin"}'

# Ожидается: JSON с access_token или 401 Unauthorized
```

### 4. Проверка в браузере
1. Откройте https://budget-west.shknv.ru
2. Откройте DevTools (F12) → Network
3. Попробуйте залогиниться
4. Проверьте:
   - ✅ OPTIONS запрос возвращает 200
   - ✅ POST запрос возвращает 200 (при правильных credentials)
   - ✅ Нет ошибок 503 или CORS

---

## 🔍 Если проблема НЕ в Traefik middleware

### Проблема 1: Traefik не видит Backend (разные сети)

**Симптомы:**
```bash
./diagnose_traefik.sh
# Показывает: "❌ Backend и Traefik НЕ в одной сети!"
```

**Решение:**
```bash
# Проверить сети
docker network ls

# Посмотреть какую сеть использует Coolify для Traefik
docker inspect traefik --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
# Например: coolify

# Добавить backend в эту сеть
docker network connect coolify it_budget_backend_prod

# Перезапустить Traefik
docker restart traefik
```

Или изменить `docker-compose.prod.yml`:
```yaml
networks:
  budget_network:
    external: true
    name: coolify  # Имя сети Coolify
```

### Проблема 2: Backend healthcheck fails

**Симптомы:**
```bash
docker inspect it_budget_backend_prod --format='{{.State.Health.Status}}'
# Возвращает: unhealthy или starting
```

**Решение:**
```bash
# Посмотреть логи
docker logs it_budget_backend_prod --tail=100

# Если база не готова
docker-compose -f docker-compose.prod.yml restart db
sleep 10
docker-compose -f docker-compose.prod.yml restart backend

# Если код не запускается - откатиться
git reset --hard 533080f
docker-compose -f docker-compose.prod.yml build --no-cache backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### Проблема 3: Traefik не запущен

**Симптомы:**
```bash
docker ps | grep traefik
# Ничего не выводит
```

**Решение:**
```bash
# Найти контейнер
docker ps -a | grep traefik

# Если остановлен - запустить
docker start traefik

# Если нет контейнера - проверить Coolify настройки
# Traefik должен быть запущен Coolify автоматически
```

---

## 🔄 Полный сброс (если ничего не помогает)

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# 1. Остановить всё
docker-compose -f docker-compose.prod.yml down

# 2. Применить исправленную конфигурацию
cp docker-compose.prod.FIXED.yml docker-compose.prod.yml

# 3. Убедиться что код на рабочей версии
git log --oneline -3
# Если последний коммит мой с OPTIONS middleware - откатить
git reset --hard 533080f

# 4. Удалить старые образы
docker rmi it-budget-backend:prod it-budget-frontend:prod

# 5. Пересобрать
docker-compose -f docker-compose.prod.yml build --no-cache

# 6. Запустить
docker-compose -f docker-compose.prod.yml up -d

# 7. Ждать (2 минуты)
sleep 120

# 8. Проверить
docker-compose -f docker-compose.prod.yml ps
curl https://api.budget-west.shknv.ru/health
```

---

## 📋 Checklist после исправления

- [ ] Traefik запущен и healthy
- [ ] Backend запущен и healthy
- [ ] Backend отвечает изнутри: `docker exec ... curl localhost:8000/health`
- [ ] Backend отвечает через Traefik: `curl https://api.budget-west.shknv.ru/health`
- [ ] OPTIONS возвращает 200 с CORS headers
- [ ] Frontend открывается: https://budget-west.shknv.ru
- [ ] Логин работает без ошибок в консоли

---

## 📚 Дополнительная информация

### Почему FastAPI лучше обрабатывает CORS чем Traefik?

1. **FastAPI CORSMiddleware** - специально разработан для CORS:
   - Правильно обрабатывает OPTIONS
   - Валидирует origin
   - Поддерживает credentials
   - Настраивается через Python код

2. **Traefik headers middleware** - общий инструмент:
   - Только добавляет заголовки
   - Не создаёт ответы на OPTIONS
   - Не валидирует origin
   - Может конфликтовать с CORS в приложении

### Альтернативное решение (если нужен CORS в Traefik)

Если по какой-то причине нужно обрабатывать CORS в Traefik:

1. Использовать **Traefik plugin** для CORS (например, `traefik-cors-plugin`)
2. Настроить **custom middleware** в динамической конфигурации
3. Использовать **InFlightReq** middleware для ограничения OPTIONS

Но проще и надёжнее - дать FastAPI обрабатывать CORS.

---

## 🆘 Нужна помощь?

Если после всех шагов сайт не работает, соберите диагностику:

```bash
# Запустить полную диагностику
./diagnose_traefik.sh > traefik-diagnostic.txt 2>&1

# Собрать логи
docker-compose -f docker-compose.prod.yml logs > all-logs.txt 2>&1

# Проверить конфигурацию
docker inspect it_budget_backend_prod > backend-inspect.txt
docker inspect traefik > traefik-inspect.txt

# Сжать
tar -czf diagnostic-traefik.tar.gz traefik-diagnostic.txt all-logs.txt backend-inspect.txt traefik-inspect.txt
```

Отправьте `diagnostic-traefik.tar.gz` с описанием проблемы.
