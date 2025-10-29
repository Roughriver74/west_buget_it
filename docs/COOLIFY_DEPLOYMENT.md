# Развертывание на Coolify

Полное руководство по развертыванию IT Budget Manager на платформе Coolify.

## Оглавление

- [Обзор архитектуры](#обзор-архитектуры)
- [Подготовка](#подготовка)
- [Настройка приложения в Coolify](#настройка-приложения-в-coolify)
- [Конфигурация переменных окружения](#конфигурация-переменных-окружения)
- [Настройка доменов](#настройка-доменов)
- [Решение проблем](#решение-проблем)

---

## Обзор архитектуры

Приложение состоит из трех Docker-контейнеров:

1. **PostgreSQL** (db) - База данных
2. **Backend** (FastAPI) - API сервер на порту 8000 (внутри контейнера)
3. **Frontend** (React + Nginx) - Веб-интерфейс на порту 80 (внутри контейнера)

### Важные особенности

- **Runtime конфигурация frontend**: Frontend использует runtime конфигурацию через `docker-entrypoint.sh`, что позволяет изменять `VITE_API_URL` без пересборки образа
- **Multi-stage сборка**: Frontend собирается в два этапа (builder → runtime)
- **HTTPS обязателен**: В продакшене используется только HTTPS

---

## Подготовка

### 1. DNS записи

Настройте A-записи для ваших доменов, указывающие на IP сервера Coolify:

```
api.budget-west.shknv.ru  →  93.189.228.52
budget-west.shknv.ru      →  93.189.228.52
```

### 2. GitHub репозиторий

Убедитесь, что код находится в Git репозитории, доступном для Coolify.

---

## Настройка приложения в Coolify

### Шаг 1: Создание нового приложения

1. Войдите в Coolify
2. Создайте новый проект или выберите существующий
3. Добавьте новое приложение:
   - Type: **Docker Compose**
   - Source: Ваш Git репозиторий
   - Branch: `main` (или нужная вам ветка)

### Шаг 2: Указание файла docker-compose

В настройках приложения укажите:
- **Docker Compose File**: `docker-compose.prod.yml`

### Шаг 3: Настройка Build Pack

Coolify автоматически определит, что это Docker Compose приложение.

---

## Конфигурация переменных окружения

⚠️ **КРИТИЧЕСКИ ВАЖНО**: Некоторые переменные должны быть установлены ОБЯЗАТЕЛЬНО.

### Обязательные переменные

Добавьте следующие переменные в разделе Environment Variables:

```bash
# ============================================
# SECURITY - ОБЯЗАТЕЛЬНО ИЗМЕНИТЬ!
# ============================================
SECRET_KEY=xK9vL2mN5pQ8rS4tU7wV0yA3bC6dE9fG2hI5jK8lM1nO4pR7sT0uV3wX6yZ9aB2c
ADMIN_PASSWORD=!QAZ2wsx
DB_PASSWORD=U33d8hd33

# ============================================
# DATABASE
# ============================================
DB_HOST=db
DB_PORT=5432
DB_NAME=it_budget_db
DB_USER=budget_user

# ============================================
# APPLICATION
# ============================================
APP_NAME=Budget Manager
APP_VERSION=0.5.0
DEBUG=False
API_PREFIX=/api/v1

# ============================================
# FRONTEND CONFIGURATION
# ============================================
# ВАЖНО: Это должен быть адрес BACKEND API!
VITE_API_URL=https://api.budget-west.shknv.ru

# ============================================
# CORS ORIGINS
# ============================================
# Формат: JSON массив в строке
CORS_ORIGINS=["https://budget-west.shknv.ru"]

# ============================================
# ADMIN USER
# ============================================
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_FULL_NAME=System Administrator
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# PORTS (для docker-compose mapping)
# ============================================
BACKEND_PORT=8888
FRONTEND_PORT=3001

# ============================================
# OPTIONAL - Мониторинг
# ============================================
PROMETHEUS_ENABLED=true
REDIS_URL=redis://redis:6379
SENTRY_DSN=
```

### Пояснения к переменным

#### VITE_API_URL - САМОЕ ВАЖНОЕ! ⚠️

```bash
VITE_API_URL=https://api.budget-west.shknv.ru
```

- Это адрес **BACKEND API**, а НЕ frontend!
- Должен быть указан **БЕЗ** суффикса `/api/v1` (frontend добавит автоматически)
- Должен использовать `https://` в продакшене
- Frontend будет делать запросы на `https://api.budget-west.shknv.ru/api/v1/*`

❌ **НЕПРАВИЛЬНО**:
```bash
VITE_API_URL=https://budget-west.shknv.ru          # Это frontend домен!
VITE_API_URL=https://api.budget-west.shknv.ru/api/v1  # Не нужен /api/v1
VITE_API_URL=http://api.budget-west.shknv.ru       # Используйте HTTPS!
```

✅ **ПРАВИЛЬНО**:
```bash
VITE_API_URL=https://api.budget-west.shknv.ru
```

#### CORS_ORIGINS

```bash
CORS_ORIGINS=["https://budget-west.shknv.ru"]
```

- Должен содержать адрес **FRONTEND** (откуда приходят запросы)
- Формат: JSON массив в виде строки
- Можно указать несколько доменов: `["https://budget-west.shknv.ru","https://www.budget-west.shknv.ru"]`
- Backend автоматически парсит escaped quotes от Coolify

#### SECRET_KEY

```bash
SECRET_KEY=xK9vL2mN5pQ8rS4tU7wV0yA3bC6dE9fG2hI5jK8lM1nO4pR7sT0uV3wX6yZ9aB2c
```

- Минимум 32 символа
- Используется для подписи JWT токенов
- Сгенерируйте случайную строку:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

---

## Настройка доменов

### Backend API

1. В настройках сервиса **backend**:
   - **Domain**: `api.budget-west.shknv.ru`
   - **Force HTTPS**: ✅ Включить
   - **Port**: `8888` (из BACKEND_PORT)

### Frontend

1. В настройках сервиса **frontend**:
   - **Domain**: `budget-west.shknv.ru`
   - **Force HTTPS**: ✅ Включить
   - **Port**: `3001` (из FRONTEND_PORT)

### Database (PostgreSQL)

База данных НЕ должна быть доступна из интернета:
- **No public domain** - доступна только внутри Docker сети
- Порт 5432 доступен только для backend контейнера

---

## Как работает Runtime конфигурация

### Проблема

Coolify не передает переменные окружения как build arguments при сборке Docker образа. Это значит, что:

- Vite собирает frontend на этапе `npm run build`
- На этом этапе `VITE_API_URL` должен быть известен
- Но переменные окружения Coolify доступны только во время запуска контейнера

### Решение

Мы используем **runtime конфигурацию** через entrypoint script:

1. **Build time**: Frontend собирается с placeholder `__VITE_API_URL__`
   ```dockerfile
   # frontend/Dockerfile.prod
   ARG VITE_API_URL=http://localhost:8888
   ENV VITE_API_URL=$VITE_API_URL
   RUN npm run build
   ```

2. **Runtime**: Entrypoint заменяет placeholder на реальное значение
   ```bash
   # frontend/docker-entrypoint.sh
   sed -i "s|__VITE_API_URL__|${VITE_API_URL}|g" /usr/share/nginx/html/env-config.js
   ```

3. **Application**: Frontend читает из `window.ENV_CONFIG`
   ```typescript
   // frontend/src/config/api.ts
   const getRawApiUrl = (): string => {
     if (window.ENV_CONFIG?.VITE_API_URL) {
       return window.ENV_CONFIG.VITE_API_URL;
     }
     return import.meta.env.VITE_API_URL || '';
   };
   ```

Это позволяет:
- ✅ Изменять API URL без пересборки образа
- ✅ Использовать разные URL для разных environments
- ✅ Работать с переменными окружения Coolify

---

## Решение проблем

### Ошибка 404 при запросах к API

**Симптомы**:
- Frontend загружается
- Но все API запросы возвращают 404
- В консоли браузера ошибки CORS или Network Error

**Проверка**:

1. Откройте консоль браузера (F12)
2. Выполните:
   ```javascript
   console.log(window.ENV_CONFIG)
   ```

**Возможные проблемы**:

❌ **Проблема 1**: `VITE_API_URL` указывает на frontend домен
```javascript
// НЕПРАВИЛЬНО
window.ENV_CONFIG = {
  VITE_API_URL: "https://budget-west.shknv.ru"  // Это frontend!
}
```

✅ **Решение**: Установите правильный backend URL в Coolify
```bash
VITE_API_URL=https://api.budget-west.shknv.ru
```

---

❌ **Проблема 2**: `VITE_API_URL` содержит placeholder
```javascript
// НЕПРАВИЛЬНО
window.ENV_CONFIG = {
  VITE_API_URL: "__VITE_API_URL__"  // Не заменено!
}
```

✅ **Решение**:
- Проверьте, что контейнер запустился с переменной `VITE_API_URL`
- Проверьте логи контейнера:
  ```bash
  docker logs <frontend-container-id>
  ```
- Должно быть: "Configuring frontend with: VITE_API_URL: https://api.budget-west.shknv.ru"

---

❌ **Проблема 3**: `VITE_API_URL` содержит `/api/v1`
```javascript
// НЕПРАВИЛЬНО
window.ENV_CONFIG = {
  VITE_API_URL: "https://api.budget-west.shknv.ru/api/v1"
}
```

✅ **Решение**: Удалите `/api/v1` из переменной окружения
```bash
# ПРАВИЛЬНО
VITE_API_URL=https://api.budget-west.shknv.ru
```

---

### CORS ошибки

**Симптомы**:
```
Access to XMLHttpRequest at 'https://api.budget-west.shknv.ru/api/v1/auth/login'
from origin 'https://budget-west.shknv.ru' has been blocked by CORS policy
```

**Решение**:

1. Проверьте `CORS_ORIGINS` в backend:
   ```bash
   # В Coolify Environment Variables
   CORS_ORIGINS=["https://budget-west.shknv.ru"]
   ```

2. Убедитесь, что используется **HTTPS** (не HTTP):
   ```bash
   # ПРАВИЛЬНО
   CORS_ORIGINS=["https://budget-west.shknv.ru"]

   # НЕПРАВИЛЬНО
   CORS_ORIGINS=["http://budget-west.shknv.ru"]
   ```

3. Проверьте логи backend для ошибок парсинга CORS_ORIGINS

---

### SSL/HTTPS проблемы

**Симптомы**:
- Mixed Content errors
- Certificate errors

**Решение**:

1. Убедитесь, что **Force HTTPS** включен для обоих доменов в Coolify
2. Проверьте, что сертификаты успешно выпущены (Let's Encrypt)
3. Все URL в переменных окружения должны использовать `https://`

---

### База данных не подключается

**Симптомы**:
```
Database is not available after 30 attempts
```

**Решение**:

1. Проверьте, что все сервисы в одной Docker сети
2. Убедитесь, что `DB_HOST=db` (имя сервиса из docker-compose)
3. Проверьте логи PostgreSQL:
   ```bash
   docker logs <db-container-id>
   ```

---

### Полезные команды для диагностики

**Проверка переменных окружения в контейнере**:
```bash
docker exec <container-id> env | grep VITE_API_URL
docker exec <container-id> env | grep CORS_ORIGINS
```

**Просмотр логов**:
```bash
docker logs <container-id>
docker logs -f <container-id>  # Follow mode
```

**Проверка сети**:
```bash
docker network inspect <network-name>
```

**Тестирование API из контейнера**:
```bash
docker exec <frontend-container> wget -O- http://backend:8000/health
```

---

## Миграции базы данных

Миграции выполняются **автоматически** при запуске backend контейнера через `entrypoint.sh`:

```bash
echo "Running database migrations..."
alembic upgrade head
```

Если миграция не прошла:
1. Проверьте логи backend контейнера
2. Проверьте подключение к базе данных
3. Вручную запустите миграции:
   ```bash
   docker exec <backend-container> alembic upgrade head
   ```

---

## Создание админ пользователя

Админ пользователь создается автоматически при первом запуске с параметрами:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=!QAZ2wsx
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_FULL_NAME=System Administrator
```

⚠️ **ВАЖНО**: Измените пароль после первого входа!

Для ручного создания админа:
```bash
docker exec <backend-container> python create_admin.py
```

---

## Рекомендации по безопасности

1. ✅ Используйте HTTPS для всех доменов
2. ✅ Измените все дефолтные пароли (ADMIN_PASSWORD, DB_PASSWORD)
3. ✅ Используйте сильный SECRET_KEY (минимум 32 символа)
4. ✅ Ограничьте доступ к базе данных (только из backend)
5. ✅ Настройте регулярные бекапы базы данных
6. ✅ Включите мониторинг (Sentry, Prometheus)
7. ✅ Регулярно обновляйте зависимости

---

## Чеклист перед деплоем

- [ ] DNS записи настроены
- [ ] Все переменные окружения заполнены
- [ ] `VITE_API_URL` указывает на backend (не frontend!)
- [ ] `CORS_ORIGINS` содержит frontend домен
- [ ] `SECRET_KEY` изменен на случайное значение (32+ символа)
- [ ] `DB_PASSWORD` изменен на сильный пароль
- [ ] `ADMIN_PASSWORD` изменен на сильный пароль
- [ ] Force HTTPS включен для обоих доменов
- [ ] Docker Compose файл: `docker-compose.prod.yml`
- [ ] Git branch: `main` (или нужная вам)

---

## Поддержка

Если проблема не решена:

1. Проверьте логи всех контейнеров
2. Проверьте переменные окружения в Coolify UI
3. Проверьте `window.ENV_CONFIG` в браузере
4. Создайте issue в репозитории с:
   - Описанием проблемы
   - Логами контейнеров
   - Скриншотами из браузера (консоль + Network tab)
