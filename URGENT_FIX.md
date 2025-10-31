# 🚨 СРОЧНОЕ ВОССТАНОВЛЕНИЕ САЙТА

## Сайт не открывается - быстрое решение

### Вариант 1: ОТКАТ (самое быстрое - 2 минуты)

```bash
# Подключитесь к серверу
ssh root@93.189.228.52

# Перейдите в директорию проекта
cd /path/to/your/project

# Запустите скрипт отката
chmod +x URGENT_ROLLBACK.sh
./URGENT_ROLLBACK.sh

# Выберите опцию 1 (Откатить к предыдущему коммиту)
```

Это вернёт код на предыдущую рабочую версию и перезапустит сайт.

---

### Вариант 2: ДИАГНОСТИКА (если нужно понять проблему)

```bash
# Подключитесь к серверу
ssh root@93.189.228.52
cd /path/to/your/project

# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Посмотрите логи backend (ищите ошибки)
docker-compose -f docker-compose.prod.yml logs backend --tail=100

# Посмотрите логи frontend
docker-compose -f docker-compose.prod.yml logs frontend --tail=50
```

**Ищите в логах:**
- ❌ `ModuleNotFoundError` - проблема с импортами Python
- ❌ `SyntaxError` - ошибка в коде
- ❌ `Exception` - ошибка при запуске
- ❌ `unhealthy` - контейнер не прошёл healthcheck

---

### Вариант 3: РУЧНОЙ ОТКАТ (если скрипт не работает)

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# Посмотреть последние коммиты
git log --oneline -5

# Откатиться на один коммит назад (до моих изменений)
git reset --hard HEAD~1

# Или откатиться на конкретный коммит
git reset --hard 533080f  # Замените на хеш рабочего коммита

# Остановить backend
docker-compose -f docker-compose.prod.yml down backend

# Пересобрать без кеша
docker-compose -f docker-compose.prod.yml build --no-cache backend

# Запустить заново
docker-compose -f docker-compose.prod.yml up -d backend

# Дождаться запуска (1-2 минуты)
sleep 60

# Проверить статус
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs backend --tail=30
```

---

### Вариант 4: БЫСТРЫЙ ПЕРЕЗАПУСК (если код правильный, но что-то зависло)

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# Перезапустить все контейнеры
docker-compose -f docker-compose.prod.yml restart

# Дождаться (30 секунд)
sleep 30

# Проверить
docker-compose -f docker-compose.prod.yml ps
```

---

## Возможные причины проблемы

### 1. Ошибка в Python коде (OptionsMiddleware)

**Симптомы в логах:**
```
SyntaxError: ...
ModuleNotFoundError: No module named '...'
AttributeError: ...
```

**Решение:** Откат к предыдущему коммиту (Вариант 1 или 3)

### 2. Контейнер не запустился

**Симптомы:**
```bash
docker-compose ps
# Backend показывает: Exited (1) или unhealthy
```

**Решение:**
```bash
# Посмотреть логи
docker-compose -f docker-compose.prod.yml logs backend --tail=200

# Если проблема с БД - перезапустить БД
docker-compose -f docker-compose.prod.yml restart db
sleep 10
docker-compose -f docker-compose.prod.yml restart backend
```

### 3. Traefik не может достучаться до backend

**Симптомы:**
```bash
curl https://api.budget-west.shknv.ru/health
# Возвращает 502 или 503
```

**Решение:**
```bash
# Проверить что backend запущен
docker exec it_budget_backend_prod curl http://localhost:8000/health

# Если внутри отвечает - проблема в Traefik
docker restart traefik

# Проверить логи Traefik
docker logs traefik --tail=50
```

### 4. Frontend не может собраться

**Проверить:**
```bash
docker-compose -f docker-compose.prod.yml logs frontend --tail=100
```

---

## После восстановления

### Проверьте что всё работает:

```bash
# 1. Все контейнеры должны быть Up (healthy)
docker-compose -f docker-compose.prod.yml ps

# 2. API отвечает
curl https://api.budget-west.shknv.ru/health
# Должен вернуть: {"status":"healthy"}

# 3. Frontend открывается
curl -I https://budget-west.shknv.ru
# Должен вернуть: HTTP/2 200

# 4. Откройте в браузере
# https://budget-west.shknv.ru
```

---

## Что пошло не так с моими изменениями?

Я добавил `OptionsMiddleware` для обработки CORS preflight запросов. Возможные проблемы:

1. **Ошибка импорта** - не импортировал `Response` или `BaseHTTPMiddleware`
2. **Конфликт middleware** - новый middleware конфликтует с существующими
3. **Проблема с async** - ошибка в async/await логике
4. **Проблема с Gunicorn** - не работает с новым middleware

---

## Если ничего не помогает

### Полный сброс:

```bash
ssh root@93.189.228.52
cd /path/to/your/project

# ВНИМАНИЕ: это удалит все контейнеры и пересоздаст с нуля

# 1. Остановить всё
docker-compose -f docker-compose.prod.yml down

# 2. Откатить код
git reset --hard 533080f  # Последний РАБОЧИЙ коммит

# 3. Удалить образы
docker rmi it-budget-backend:prod it-budget-frontend:prod

# 4. Пересобрать всё заново
docker-compose -f docker-compose.prod.yml build --no-cache

# 5. Запустить
docker-compose -f docker-compose.prod.yml up -d

# 6. Ждать 2 минуты
sleep 120

# 7. Проверить
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

---

## Контакты для срочной помощи

Если нужна помощь:
1. Запустите `./URGENT_ROLLBACK.sh` и выберите опцию 3
2. Скопируйте логи
3. Отправьте мне:
   - Логи backend
   - Статус контейнеров (`docker-compose ps`)
   - Что показывает `curl https://api.budget-west.shknv.ru/health`

---

## После восстановления - правильное исправление

После того как сайт будет работать, я создам исправленную версию кода с правильной обработкой OPTIONS запросов.
