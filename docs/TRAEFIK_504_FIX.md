# Исправление ошибки 504 Gateway Timeout

## 🔥 Проблема

Периодически появляется **HTTP 504 Gateway Timeout** на production сервере, особенно при выполнении длительных запросов (импорт данных, сложная аналитика, генерация отчетов).

## 🔍 Диагностика

### Симптомы
- ✅ Backend работает нормально (логи показывают успешную обработку запросов)
- ✅ Память в пределах нормы (51% использования из 768MB)
- ✅ Нет OOM killer событий
- ✅ Gunicorn workers работают стабильно (2 workers, max-requests 1000)
- ❌ Периодически возникает 504 Gateway Timeout

### Причина: Несоответствие timeout'ов Traefik и Gunicorn

**Текущая конфигурация:**
- **Traefik responseHeaderTimeout**: 60 секунд (по умолчанию)
- **Gunicorn timeout**: 120 секунд

**Проблема:**
Если запрос выполняется дольше 60 секунд, Traefik прерывает соединение и возвращает 504, даже если Gunicorn еще обрабатывает запрос.

```
Клиент → Traefik (timeout 60s) → Backend/Gunicorn (timeout 120s)
                ↓
        504 через 60 секунд!
        (даже если backend еще работает)
```

### Диагностические команды

```bash
# Проверить текущие timeout настройки
ssh root@93.189.228.52 "docker inspect backend-io00swck8gss4kosckwwwo88-141926652486 --format='{{range \$k, \$v := .Config.Labels}}{{printf \"%s=%s\n\" \$k \$v}}{{end}}' | grep timeout"

# Проверить переменные окружения Gunicorn
ssh root@93.189.228.52 "docker inspect backend-io00swck8gss4kosckwwwo88-141926652486 --format='{{range .Config.Env}}{{println .}}{{end}}' | grep GUNICORN"

# Проверить запущенные workers
ssh root@93.189.228.52 "docker top backend-io00swck8gss4kosckwwwo88-141926652486"

# Проверить использование памяти
ssh root@93.189.228.52 "docker stats --no-stream | grep backend"
```

## ✅ Решение

### Увеличение Traefik Timeout'ов

Добавлены два Traefik label в [docker-compose.prod.yml](../docker-compose.prod.yml):

```yaml
labels:
  # Timeout configuration - prevent 504 Gateway Timeout
  - "traefik.http.services.backend.loadbalancer.responseHeaderTimeout=180s"
  - "traefik.http.services.backend.loadbalancer.healthcheck.timeout=10s"
```

**Эффект:**
- ✅ `responseHeaderTimeout=180s` - Traefik будет ждать до 3 минут ответа от backend
- ✅ Больше времени Gunicorn timeout (120s), предотвращает преждевременные 504
- ✅ Healthcheck timeout 10s - быстрое определение проблем с backend

### Таймлайн timeout'ов после исправления

```
Запрос → Traefik (180s) → Gunicorn (120s) → Backend обработка
                                ↓
                    Gunicorn timeout через 120s
                    (корректная обработка ошибки)
```

Теперь если запрос действительно "завис":
1. **Gunicorn timeout (120s)** сработает первым → вернет 503 Service Unavailable
2. Traefik дождется ответа от Gunicorn (до 180s)
3. Клиент получит корректную ошибку 503 вместо 504

## 🚀 Деплой Исправления

### 1. Commit и Push изменений

```bash
# Commit изменения
git add docker-compose.prod.yml docs/TRAEFIK_504_FIX.md
git commit -m "fix: increase Traefik timeout to prevent 504 Gateway Timeout

- Add responseHeaderTimeout=180s for backend service
- Add healthcheck timeout=10s
- Prevents premature 504 when requests take >60s
- Aligns with Gunicorn timeout (120s)"

# Push в репозиторий
git push origin main
```

### 2. Деплой через Docker

**Вариант A: Автоматический (если настроен webhook)**
- Docker автоматически обнаружит изменения и задеплоит

**Вариант B: Ручной деплой**
1. Зайти в Docker UI (https://93.189.228.52:8000)
2. Найти проект "west-buget-it"
3. Нажать кнопку **"Redeploy"**
4. Дождаться завершения деплоя (~2-3 минуты)

### 3. Проверка применения изменений

```bash
# Проверить, что новые labels применены
ssh root@93.189.228.52 "docker inspect \$(docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -1) --format='{{range \$k, \$v := .Config.Labels}}{{printf \"%s=%s\n\" \$k \$v}}{{end}}' | grep timeout"

# Ожидаемый результат:
# traefik.http.services.backend.loadbalancer.responseHeaderTimeout=180s
# traefik.http.services.backend.loadbalancer.healthcheck.timeout=10s
```

## 📊 Ожидаемые Результаты

### До исправления:
- ❌ 504 Gateway Timeout при запросах >60 секунд
- ❌ Traefik прерывает соединение раньше Gunicorn
- ❌ Backend продолжает обработку, но клиент получает ошибку

### После исправления:
- ✅ Запросы до 120 секунд обрабатываются корректно
- ✅ Traefik ждет до 180 секунд (больше Gunicorn timeout)
- ✅ Корректная обработка timeout'ов: Gunicorn → 503, не 504

## 🔍 Мониторинг и Проверка

### Проверка после деплоя

```bash
# 1. Проверить доступность
curl -I https://api.budget-west.shknv.ru/health
# Ожидается: HTTP/2 200

# 2. Проверить работу длительного запроса (например, импорт)
# Выполнить импорт большого файла через UI или API
# Ожидается: Запрос завершится успешно, даже если занимает >60 секунд

# 3. Мониторинг логов Traefik
ssh root@93.189.228.52 "docker logs -f traefik"

# 4. Мониторинг логов Backend
ssh root@93.189.228.52 "docker logs -f \$(docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -1)"
```

### Тестирование длительных запросов

```bash
# Тест 1: Импорт данных
curl -X POST "https://api.budget-west.shknv.ru/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=expenses" \
  -F "file=@large_expenses.xlsx" \
  --max-time 150

# Тест 2: Генерация отчета
curl -X GET "https://api.budget-west.shknv.ru/api/v1/analytics/annual-report?year=2025" \
  -H "Authorization: Bearer $TOKEN" \
  --max-time 150
```

## 🔧 Дополнительные Рекомендации

### Если проблема 504 сохраняется

1. **Проверить глобальные timeout'ы Traefik:**
```bash
# Посмотреть конфигурацию Traefik
ssh root@93.189.228.52 "docker exec traefik cat /etc/traefik/traefik.yaml"
```

2. **Увеличить Gunicorn timeout:**
```yaml
# В docker-compose.prod.yml
environment:
  GUNICORN_TIMEOUT: 180  # Увеличить с 120 до 180
```

3. **Оптимизировать медленные запросы:**
- Добавить индексы в БД
- Использовать фоновые задачи (Celery) для долгих операций
- Кэшировать результаты

4. **Использовать асинхронные операции:**
```python
# Вместо синхронного импорта
@router.post("/import")
async def import_data():
    # Запустить фоновую задачу
    task_id = await start_background_import()
    return {"task_id": task_id, "status": "processing"}

# Проверка статуса
@router.get("/import/{task_id}/status")
async def check_import_status(task_id: str):
    return await get_task_status(task_id)
```

## 📚 Связанные Документы

- [MEMORY_OPTIMIZATION.md](MEMORY_OPTIMIZATION.md) - Оптимизация памяти
- [MEMORY_FIX.md](MEMORY_FIX.md) - Быстрое решение проблем с памятью
- [docker_SETUP.md](docker_SETUP.md) - Настройка Docker
- [AUTO_PROXY_RESTART.md](AUTO_PROXY_RESTART.md) - Автоматический рестарт proxy

## 🎯 Технические Детали

### Traefik Timeout Parameters

| Parameter | Default | Новое значение | Описание |
|-----------|---------|----------------|----------|
| `responseHeaderTimeout` | 60s | **180s** | Время ожидания response headers от backend |
| `readTimeout` | 60s | 60s (default) | Время чтения response body |
| `writeTimeout` | 60s | 60s (default) | Время записи request body |
| `idleTimeout` | 180s | 180s (default) | Время простоя keep-alive соединения |
| `healthcheck.timeout` | 5s | **10s** | Timeout для healthcheck запросов |

### Gunicorn Timeout Configuration

```bash
--timeout 120               # Worker timeout (2 минуты)
--keep-alive 5              # Keep-alive соединений
--max-requests 1000         # Auto-restart after N requests
--max-requests-jitter 50    # Random jitter для рестартов
```

## ✅ Проверка Решения

После деплоя и 30 минут работы:

```bash
# 1. Нет ошибок 504 в логах Traefik
ssh root@93.189.228.52 "docker logs traefik --since 30m 2>&1 | grep -c ' 504 '"
# Ожидается: 0

# 2. Backend обрабатывает запросы корректно
ssh root@93.189.228.52 "docker logs \$(docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -1) --since 30m 2>&1 | grep 'Status: 200' | wc -l"
# Ожидается: >0 успешных запросов

# 3. Нет timeout'ов в backend логах
ssh root@93.189.228.52 "docker logs \$(docker ps --filter 'name=backend-io00swck8gss4kosckwwwo88' --format '{{.Names}}' | head -1) --since 30m 2>&1 | grep -c timeout"
# Ожидается: 0
```

---

**Дата исправления:** 07.11.2025
**Версия:** 0.5.1
**Статус:** ✅ Исправлено и готово к деплою
**Приоритет:** 🔥 Высокий (критическая ошибка production)
