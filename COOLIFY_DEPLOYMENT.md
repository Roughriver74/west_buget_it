# IT Budget Manager - Deployment to Coolify

Подробное руководство по развертыванию IT Budget Manager на **Coolify** - self-hosted PaaS платформе.

## Содержание

1. [Введение в Coolify](#введение-в-coolify)
2. [Предварительные требования](#предварительные-требования)
3. [Подготовка проекта](#подготовка-проекта)
4. [Создание приложения в Coolify](#создание-приложения-в-coolify)
5. [Настройка переменных окружения](#настройка-переменных-окружения)
6. [Настройка баз данных](#настройка-баз-данных)
7. [Первое развертывание](#первое-развертывание)
8. [Настройка домена и SSL](#настройка-домена-и-ssl)
9. [Автоматический деплой (CI/CD)](#автоматический-деплой-cicd)
10. [Мониторинг и логи](#мониторинг-и-логи)
11. [Обновление приложения](#обновление-приложения)
12. [Troubleshooting](#troubleshooting)

---

## Введение в Coolify

**Coolify** - это open-source self-hosted альтернатива Heroku/Vercel/Netlify, которая позволяет деплоить приложения на собственном сервере.

### Преимущества Coolify для нашего проекта:

- ✅ Поддержка Docker и docker-compose
- ✅ Автоматический деплой из GitHub
- ✅ Встроенное управление базами данных (PostgreSQL, Redis)
- ✅ Автоматические SSL сертификаты (Let's Encrypt)
- ✅ Простой UI для управления
- ✅ Поддержка environment variables
- ✅ Логи и мониторинг
- ✅ Rollback в один клик

---

## Предварительные требования

### 1. Сервер

- **VPS/Dedicated сервер** с:
  - Ubuntu 22.04 LTS или Debian 11+ (рекомендуется)
  - Минимум 2GB RAM, рекомендуется 4GB+
  - Минимум 2 CPU cores, рекомендуется 4+
  - Минимум 20GB свободного места на диске
  - Публичный IP адрес

### 2. Coolify установлен

Если Coolify еще не установлен на сервере:

```bash
# Подключитесь к серверу по SSH
ssh user@your-server-ip

# Установите Coolify (одна команда!)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# После установки Coolify будет доступен на http://your-server-ip:8000
```

Следуйте инструкциям установки и создайте аккаунт администратора.

### 3. Домен (опционально, но рекомендуется)

- Зарегистрированный домен
- DNS записи настроены на IP вашего сервера:
  ```
  A    @                  your-server-ip
  A    budget             your-server-ip
  CNAME www               budget.yourdomain.com
  ```

---

## Подготовка проекта

### 1. GitHub репозиторий

Убедитесь, что проект находится в GitHub репозитории с правильной структурой:

```
your-repo/
├── backend/
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile.prod
│   ├── package.json
│   └── src/
├── docker-compose.prod.yml
└── .env.prod.example
```

### 2. Файл docker-compose для Coolify

Coolify автоматически использует `docker-compose.yml` или `docker-compose.prod.yml`. Наш проект уже готов!

Coolify будет использовать файл `docker-compose.prod.yml`.

---

## Создание приложения в Coolify

### Шаг 1: Войдите в Coolify Dashboard

Откройте браузер и перейдите:
```
http://your-server-ip:8000
```

### Шаг 2: Создайте новый проект

1. Кликните **"+ New"** → **"Project"**
2. Введите имя проекта: `IT Budget Manager`
3. Добавьте описание (опционально)
4. Сохраните

### Шаг 3: Добавьте новый ресурс (Resource)

1. Внутри проекта кликните **"+ Add Resource"**
2. Выберите **"New Resource"** → **"GitHub App"**

### Шаг 4: Подключите GitHub

1. Кликните **"Connect to GitHub"**
2. Авторизуйте Coolify в GitHub
3. Выберите репозиторий: `your-username/it-budget-manager`
4. Выберите ветку: `main` (или ту, которую хотите деплоить)

### Шаг 5: Настройте тип приложения

1. **Build Pack**: Выберите **"Docker Compose"**
2. **Docker Compose File**: Укажите `docker-compose.prod.yml`
3. **Base Directory**: Оставьте `/` (корень репозитория)
4. Сохраните

---

## Настройка переменных окружения

Coolify позволяет управлять environment variables через UI.

### Шаг 1: Откройте настройки Environment Variables

В настройках вашего приложения перейдите в раздел **"Environment Variables"**.

### Шаг 2: Добавьте необходимые переменные

Скопируйте все переменные из `.env.prod.example` и добавьте в Coolify:

#### Обязательные переменные:

```bash
# Database
DB_USER=budget_user
DB_PASSWORD=ИЗМЕНИТЕ_strong_random_password
DB_NAME=it_budget_db
DB_PORT=5432

# Security - ВАЖНО!
SECRET_KEY=ИЗМЕНИТЕ_minimum_32_characters_random_key_here

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Укажите ваш домен!
CORS_ORIGINS='["https://budget.yourdomain.com","https://www.yourdomain.com"]'

# Application
APP_NAME=IT Budget Manager
APP_VERSION=0.5.0
API_PREFIX=/api/v1
DEBUG=False

# Frontend
VITE_API_URL=https://budget.yourdomain.com

# Ports (для Coolify обычно не нужны, он сам управляет)
BACKEND_PORT=8000
FRONTEND_PORT=80

# Redis (если используете)
REDIS_URL=redis://redis:6379
```

#### Опциональные (но рекомендуемые):

```bash
# Monitoring
SENTRY_DSN=your-sentry-dsn-here
PROMETHEUS_ENABLED=true
```

### Шаг 3: Генерация SECRET_KEY

**ВАЖНО:** Сгенерируйте безопасный SECRET_KEY:

```bash
# На вашем локальном компьютере или сервере
openssl rand -hex 32
```

Скопируйте результат и используйте как значение `SECRET_KEY`.

---

## Настройка баз данных

Coolify может автоматически создавать и управлять базами данных.

### Вариант 1: Использовать встроенную PostgreSQL в docker-compose

Наш `docker-compose.prod.yml` уже включает PostgreSQL. Coolify автоматически запустит его.

**Ничего дополнительно делать не нужно!**

### Вариант 2: Использовать managed PostgreSQL от Coolify

1. В проекте кликните **"+ Add Resource"** → **"Database"**
2. Выберите **"PostgreSQL"**
3. Настройте:
   - Name: `it-budget-db`
   - Version: `15` (или последняя)
   - User: `budget_user`
   - Password: (сгенерируйте сильный пароль)
   - Database: `it_budget_db`
4. Сохраните и запустите

После создания БД, Coolify предоставит вам **connection string**. Обновите переменные окружения:

```bash
# Замените значения на те, что предоставил Coolify
DB_USER=budget_user
DB_PASSWORD=generated_password_from_coolify
DB_NAME=it_budget_db
DB_HOST=postgres-service-name  # Coolify покажет это
DB_PORT=5432
```

### Redis (опционально)

Аналогично создайте Redis:
1. **"+ Add Resource"** → **"Database"** → **"Redis"**
2. Coolify предоставит `REDIS_URL`
3. Добавьте в environment variables

---

## Первое развертывание

### Шаг 1: Проверьте конфигурацию

Убедитесь, что:
- ✅ Репозиторий подключен
- ✅ Ветка выбрана
- ✅ Environment variables заполнены
- ✅ База данных настроена

### Шаг 2: Запустите деплой

1. В настройках приложения найдите кнопку **"Deploy"**
2. Кликните **"Deploy Now"**
3. Coolify начнет:
   - Клонировать репозиторий
   - Собирать Docker образы
   - Запускать контейнеры
   - Применять health checks

### Шаг 3: Следите за логами

В Coolify UI вы увидите логи в реальном времени:
- Сборка образов
- Запуск контейнеров
- Вывод приложения

### Шаг 4: Инициализация базы данных

**После первого успешного деплоя нужно выполнить миграции:**

В Coolify найдите **"Execute Command"** (или подключитесь по SSH к серверу):

```bash
# Применить миграции Alembic
docker exec -it <backend-container-name> alembic upgrade head

# Создать администратора
docker exec -it <backend-container-name> python create_admin.py
```

**Альтернатива через Coolify UI:**
1. Перейдите в **"Containers"** → Найдите `backend`
2. Кликните **"Execute Command"**
3. Выполните команды:
   ```bash
   alembic upgrade head
   python create_admin.py
   ```

### Шаг 5: Проверьте работоспособность

Coolify автоматически предоставит временный URL (например, `http://app-xyz.coolify.io`).

Откройте его в браузере и проверьте:
- ✅ Frontend загружается
- ✅ Можно войти с логином: `admin` / `admin`
- ✅ API работает

---

## Настройка домена и SSL

### Шаг 1: Добавьте свой домен

1. В настройках приложения найдите **"Domains"**
2. Кликните **"+ Add Domain"**
3. Введите ваш домен: `budget.yourdomain.com`
4. Сохраните

### Шаг 2: Настройте DNS

Убедитесь, что DNS записи указывают на IP вашего сервера:

```bash
# Проверка DNS
nslookup budget.yourdomain.com

# Или через dig
dig budget.yourdomain.com
```

### Шаг 3: Включите SSL (Let's Encrypt)

Coolify автоматически получит SSL сертификаты!

1. В настройках домена найдите **"Enable SSL"** или **"Generate SSL Certificate"**
2. Кликните и дождитесь завершения (обычно 1-2 минуты)
3. Coolify автоматически настроит HTTPS redirect

### Шаг 4: Обновите CORS и frontend URL

После настройки домена обновите environment variables:

```bash
CORS_ORIGINS='["https://budget.yourdomain.com"]'
VITE_API_URL=https://budget.yourdomain.com
```

**Важно:** После изменения `VITE_API_URL` нужно пересобрать frontend:
1. Кликните **"Redeploy"** в Coolify
2. Coolify пересоберет образы с новыми переменными

---

## Автоматический деплой (CI/CD)

Coolify поддерживает автоматический деплой при push в GitHub!

### Шаг 1: Включите Auto Deploy

В настройках приложения найдите:
- **"Auto Deploy"** → Включите toggle
- **"Branch"**: Укажите `main` (или другую ветку)

### Шаг 2: Настройте Webhook (если нужно)

Coolify автоматически настроит GitHub webhook. Проверьте в:
- GitHub → Repository → Settings → Webhooks
- Должен быть webhook с URL от Coolify

### Шаг 3: GitHub Actions Integration

Наш проект уже имеет `.github/workflows/ci.yml`, который:
1. ✅ Запускает тесты
2. ✅ Проверяет code quality
3. ✅ Собирает Docker образы
4. ✅ Уведомляет о готовности к деплою

После успешного прохождения CI, Coolify автоматически задеплоит изменения!

### Workflow:

```
Developer → Push to GitHub → GitHub Actions CI
    ↓
CI passes ✅
    ↓
Coolify webhook triggered
    ↓
Coolify pulls latest code
    ↓
Builds Docker images
    ↓
Deploys with zero-downtime
    ↓
Health checks pass ✅
    ↓
New version live! 🚀
```

---

## Мониторинг и логи

### Просмотр логов

В Coolify UI:
1. Перейдите в ваше приложение
2. Вкладка **"Logs"**
3. Выберите контейнер (backend, frontend, db)
4. Логи отображаются в реальном времени

### Логи через SSH

Подключитесь к серверу:

```bash
# Все контейнеры
docker ps

# Логи конкретного контейнера
docker logs -f <container-name>

# Логи backend
docker logs -f it_budget_backend_prod

# Логи frontend
docker logs -f it_budget_frontend_prod

# Логи PostgreSQL
docker logs -f it_budget_db_prod
```

### Monitoring

Coolify показывает:
- CPU usage
- Memory usage
- Network I/O
- Disk usage
- Container status

### Health Checks

Coolify автоматически проверяет health endpoints:
- Backend: `http://backend:8000/health`
- Frontend: `http://frontend/health`

Если health check fails, Coolify может:
- Отправить уведомление
- Автоматически перезапустить контейнер
- Откатиться на предыдущую версию

---

## Обновление приложения

### Автоматическое обновление

Если Auto Deploy включен:
1. Пушите изменения в GitHub
2. GitHub Actions запускает CI
3. После успешного CI, Coolify автоматически деплоит

### Ручное обновление

В Coolify UI:
1. Кликните **"Redeploy"**
2. Coolify пересоберет образы и перезапустит контейнеры

### Миграции базы данных

После обновления кода, если есть новые миграции:

```bash
docker exec -it <backend-container> alembic upgrade head
```

**Рекомендуется настроить автоматический запуск миграций:**

Отредактируйте `backend/Dockerfile.prod` (добавьте entrypoint script):

```dockerfile
# Создайте entrypoint.sh
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
```

`entrypoint.sh`:
```bash
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Rollback

Если что-то пошло не так:
1. В Coolify найдите **"Deployments"** → **"History"**
2. Выберите предыдущую успешную версию
3. Кликните **"Redeploy this version"**
4. Coolify откатится на стабильную версию

---

## Troubleshooting

### Проблема: Backend не запускается

**Проверьте логи:**
```bash
docker logs it_budget_backend_prod
```

**Типичные причины:**
1. **База данных недоступна:**
   ```bash
   # Проверьте, запущена ли БД
   docker ps | grep postgres

   # Проверьте connection string
   docker exec -it <backend-container> env | grep DATABASE_URL
   ```

2. **Неправильный SECRET_KEY:**
   - Убедитесь, что SECRET_KEY установлен в environment variables
   - Минимум 32 символа

3. **Миграции не применены:**
   ```bash
   docker exec -it <backend-container> alembic current
   docker exec -it <backend-container> alembic upgrade head
   ```

### Проблема: Frontend показывает ошибки API

**Проверьте CORS и API URL:**

```bash
# В Coolify Environment Variables
CORS_ORIGINS='["https://budget.yourdomain.com"]'
VITE_API_URL=https://budget.yourdomain.com
```

**Важно:** После изменения VITE_API_URL нужно **Redeploy** (пересборка)!

### Проблема: SSL сертификат не выпускается

1. Проверьте DNS:
   ```bash
   nslookup budget.yourdomain.com
   ```

2. Убедитесь, что порты 80 и 443 открыты:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. Проверьте логи Coolify (раздел System Logs)

### Проблема: Высокое потребление памяти

Уменьшите количество workers в `backend/Dockerfile.prod`:

```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--workers", "2",  # Было 4, стало 2
     ...
```

### Проблема: База данных заполнена

```bash
# Подключитесь к PostgreSQL
docker exec -it <postgres-container> psql -U budget_user -d it_budget_db

# Проверьте размер
SELECT pg_size_pretty(pg_database_size('it_budget_db'));

# Очистите старые audit logs (пример)
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';

# VACUUM
VACUUM FULL ANALYZE;
```

---

## Полезные команды

```bash
# Список всех контейнеров
docker ps

# Статистика ресурсов
docker stats

# Подключение к контейнеру
docker exec -it <container-name> bash

# Перезапуск контейнера
docker restart <container-name>

# Просмотр сетей
docker network ls

# Проверка volumes
docker volume ls

# Бэкап базы данных
docker exec -t <postgres-container> pg_dump -U budget_user it_budget_db > backup.sql

# Восстановление
cat backup.sql | docker exec -i <postgres-container> psql -U budget_user it_budget_db
```

---

## Дополнительные ресурсы

- **Coolify Documentation**: https://coolify.io/docs
- **Coolify Discord**: https://discord.gg/coolify
- **IT Budget Manager GitHub**: https://github.com/your-username/it-budget-manager
- **Общая документация деплоя**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Заключение

Coolify значительно упрощает процесс деплоя Docker-приложений. После первоначальной настройки вы получаете:

- ✅ Автоматический деплой из GitHub
- ✅ SSL сертификаты из коробки
- ✅ Удобное управление через UI
- ✅ Логи и мониторинг
- ✅ Rollback в один клик
- ✅ Zero-downtime deployments

**Happy deploying! 🚀**

---

**Версия документа**: 1.0
**Дата**: 2025-10-28
**Для приложения**: IT Budget Manager v0.5.0
