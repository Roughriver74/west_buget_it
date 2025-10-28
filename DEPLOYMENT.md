# IT Budget Manager - Production Deployment Guide

Руководство по развертыванию приложения IT Budget Manager в production-окружении с использованием Docker.

## Содержание

1. [Требования](#требования)
2. [Быстрый старт](#быстрый-старт)
3. [Конфигурация](#конфигурация)
4. [Развертывание](#развертывание)
5. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)
6. [Безопасность](#безопасность)
7. [Резервное копирование](#резервное-копирование)
8. [Устранение неполадок](#устранение-неполадок)

---

## Требования

### Системные требования

- **ОС**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+) или Windows Server
- **Docker**: версия 20.10 или выше
- **Docker Compose**: версия 2.0 или выше
- **RAM**: минимум 2GB, рекомендуется 4GB+
- **Диск**: минимум 10GB свободного места
- **CPU**: минимум 2 ядра, рекомендуется 4+

### Проверка установки Docker

```bash
docker --version
docker-compose --version
```

Если Docker не установлен, следуйте [официальной документации](https://docs.docker.com/engine/install/).

---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/it-budget-manager.git
cd it-budget-manager
```

### 2. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.prod.example .env

# Отредактируйте файл .env
nano .env  # или vim .env
```

**Обязательно измените следующие переменные:**

```bash
# Генерация SECRET_KEY
openssl rand -hex 32

# Сильный пароль для БД
DB_PASSWORD=your_strong_password_here

# SECRET_KEY для JWT
SECRET_KEY=your_generated_secret_key_here

# Домен вашего приложения
CORS_ORIGINS='["https://yourdomain.com","https://www.yourdomain.com"]'
```

### 3. Сборка и запуск

```bash
# Сборка Docker-образов
docker-compose -f docker-compose.prod.yml build

# Запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

### 4. Инициализация базы данных

```bash
# Применение миграций
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Создание администратора
docker-compose -f docker-compose.prod.yml exec backend python create_admin.py
```

### 5. Проверка работоспособности

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost/health

# API documentation
curl http://localhost:8000/docs
```

**Приложение доступно по адресу:** `http://localhost`
**API:** `http://localhost:8000`
**Swagger UI:** `http://localhost:8000/docs`

---

## Конфигурация

### Структура файлов конфигурации

```
.
├── .env                        # Переменные окружения (НЕ коммитить!)
├── .env.prod.example           # Пример конфигурации
├── docker-compose.prod.yml     # Production Docker Compose
├── backend/
│   ├── Dockerfile.prod         # Production Dockerfile для backend
│   └── .dockerignore          # Исключения для Docker build
└── frontend/
    ├── Dockerfile.prod         # Production Dockerfile для frontend
    ├── nginx.conf             # Конфигурация Nginx
    └── .dockerignore          # Исключения для Docker build
```

### Основные переменные окружения

#### База данных

```bash
DB_USER=budget_user              # Имя пользователя PostgreSQL
DB_PASSWORD=strong_password      # Пароль БД (обязательно изменить!)
DB_NAME=it_budget_db            # Имя базы данных
DB_PORT=54329                   # Внешний порт PostgreSQL
```

#### Backend

```bash
SECRET_KEY=minimum_32_chars     # JWT секретный ключ (обязательно изменить!)
ALGORITHM=HS256                 # Алгоритм шифрования JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Время жизни токена
DEBUG=False                     # ВСЕГДА False в production!
```

#### CORS

```bash
# Разрешенные домены для CORS
CORS_ORIGINS='["https://yourdomain.com"]'
```

#### Порты

```bash
BACKEND_PORT=8000               # Внешний порт backend API
FRONTEND_PORT=80                # Внешний порт frontend (HTTP)
```

#### Мониторинг (опционально)

```bash
SENTRY_DSN=your_sentry_dsn      # Sentry для отслеживания ошибок
PROMETHEUS_ENABLED=true         # Включить Prometheus метрики
```

---

## Развертывание

### Сценарий 1: Локальный сервер

```bash
# 1. Подготовка окружения
cp .env.prod.example .env
# Отредактируйте .env с правильными значениями

# 2. Сборка образов
docker-compose -f docker-compose.prod.yml build --no-cache

# 3. Запуск сервисов
docker-compose -f docker-compose.prod.yml up -d

# 4. Инициализация БД
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker-compose -f docker-compose.prod.yml exec backend python create_admin.py

# 5. Проверка логов
docker-compose -f docker-compose.prod.yml logs -f
```

### Сценарий 2: С обратным прокси (Nginx/Traefik)

Если используется внешний reverse proxy (рекомендуется для SSL):

```nginx
# /etc/nginx/sites-available/it-budget-manager
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Увеличить timeout для загрузки файлов
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Обновите `.env`:

```bash
VITE_API_URL=https://yourdomain.com
CORS_ORIGINS='["https://yourdomain.com"]'
```

### Сценарий 3: Docker Swarm / Kubernetes

Для масштабирования на несколько узлов:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.prod.yml it-budget-manager

# Kubernetes
# Требуется конвертация docker-compose.yml в k8s manifests
# Используйте Kompose: kompose convert -f docker-compose.prod.yml
```

---

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f db

# Последние N строк
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Проверка health checks

```bash
# Backend
curl http://localhost:8000/health
# Ожидается: {"status":"healthy"}

# Frontend
curl http://localhost/health
# Ожидается: healthy

# Docker health status
docker ps
# Проверьте колонку STATUS - должно быть "healthy"
```

### Обновление приложения

```bash
# 1. Получить последние изменения
git pull origin main

# 2. Остановить сервисы
docker-compose -f docker-compose.prod.yml down

# 3. Пересобрать образы
docker-compose -f docker-compose.prod.yml build --no-cache

# 4. Запустить сервисы
docker-compose -f docker-compose.prod.yml up -d

# 5. Применить миграции БД
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Проверить логи
docker-compose -f docker-compose.prod.yml logs -f
```

### Масштабирование backend

```bash
# Увеличить количество backend-инстансов
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Требуется настройка load balancer (nginx, traefik)
```

### Очистка неиспользуемых ресурсов

```bash
# Удалить неиспользуемые образы
docker image prune -a

# Удалить неиспользуемые volumes
docker volume prune

# Полная очистка (осторожно!)
docker system prune -a --volumes
```

---

## Безопасность

### Чек-лист безопасности

- [ ] **SECRET_KEY** изменен на уникальное случайное значение (минимум 32 символа)
- [ ] **DB_PASSWORD** установлен сильный пароль
- [ ] **DEBUG=False** в production
- [ ] **CORS_ORIGINS** содержит только разрешенные домены
- [ ] **SSL/HTTPS** настроен через reverse proxy
- [ ] **Firewall** настроен (открыты только необходимые порты)
- [ ] **Регулярные обновления** Docker-образов и зависимостей
- [ ] **Резервное копирование** БД настроено
- [ ] **Логирование** и мониторинг настроены

### Настройка Firewall (UFW)

```bash
# Установка UFW (Ubuntu/Debian)
sudo apt-get install ufw

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Запретить прямой доступ к backend (если есть reverse proxy)
# sudo ufw deny 8000/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Ограничение доступа к PostgreSQL

```bash
# В docker-compose.prod.yml закомментируйте ports для db:
# db:
#   ports:
#     - "54329:5432"  # Удалите эту строку для production!
```

### Настройка SSL сертификатов (Let's Encrypt)

```bash
# Установка certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автообновление
sudo certbot renew --dry-run
```

---

## Резервное копирование

### Бэкап базы данных

```bash
# Создать резервную копию
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U budget_user it_budget_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Или с использованием pg_dump из Docker volume
docker run --rm \
  --volumes-from it_budget_db_prod \
  -v $(pwd):/backup \
  postgres:15-alpine \
  pg_dump -U budget_user -d it_budget_db -f /backup/backup_$(date +%Y%m%d).sql
```

### Восстановление из бэкапа

```bash
# Остановить backend
docker-compose -f docker-compose.prod.yml stop backend

# Восстановить БД
cat backup_20231215.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U budget_user it_budget_db

# Запустить backend
docker-compose -f docker-compose.prod.yml start backend
```

### Автоматизация бэкапов (cron)

```bash
# Создать скрипт бэкапа
cat > /opt/backup-it-budget.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/it-budget"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd /opt/it-budget-manager
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U budget_user it_budget_db > $BACKUP_DIR/backup_$DATE.sql

# Удалить бэкапы старше 30 дней
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
EOF

# Сделать скрипт исполняемым
chmod +x /opt/backup-it-budget.sh

# Добавить в cron (ежедневно в 3:00)
crontab -e
# 0 3 * * * /opt/backup-it-budget.sh >> /var/log/it-budget-backup.log 2>&1
```

### Бэкап файлов (загруженные данные)

```bash
# Создать архив uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz backend/uploads/

# Восстановить uploads
tar -xzf uploads_backup_20231215.tar.gz
```

---

## Устранение неполадок

### Проблема: Backend не запускается

```bash
# Проверить логи
docker-compose -f docker-compose.prod.yml logs backend

# Типичные причины:
# 1. БД не доступна
docker-compose -f docker-compose.prod.yml ps db

# 2. Неправильные переменные окружения
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL

# 3. Проблемы с миграциями
docker-compose -f docker-compose.prod.yml exec backend alembic current
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Проблема: Frontend показывает ошибки API

```bash
# Проверить VITE_API_URL в frontend
docker-compose -f docker-compose.prod.yml exec frontend env | grep VITE_API_URL

# Проверить CORS в backend
docker-compose -f docker-compose.prod.yml exec backend env | grep CORS_ORIGINS

# Пересобрать frontend с правильными переменными
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Проблема: Ошибка при загрузке файлов

```bash
# Проверить права на директорию uploads
docker-compose -f docker-compose.prod.yml exec backend ls -la /app/uploads

# Если проблемы с правами:
docker-compose -f docker-compose.prod.yml exec -u root backend chown -R appuser:appuser /app/uploads
```

### Проблема: Высокое потребление памяти

```bash
# Проверить использование ресурсов
docker stats

# Уменьшить количество workers в backend (docker-compose.prod.yml)
# CMD ["gunicorn", "app.main:app", "--workers", "2", ...]

# Пересобрать и перезапустить
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Проблема: БД переполнена

```bash
# Проверить размер БД
docker-compose -f docker-compose.prod.yml exec db psql -U budget_user -d it_budget_db -c "SELECT pg_size_pretty(pg_database_size('it_budget_db'));"

# Очистить старые логи audit
docker-compose -f docker-compose.prod.yml exec db psql -U budget_user -d it_budget_db -c "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"

# VACUUM БД
docker-compose -f docker-compose.prod.yml exec db psql -U budget_user -d it_budget_db -c "VACUUM FULL ANALYZE;"
```

### Полный перезапуск с очисткой

```bash
# ВНИМАНИЕ: Это удалит все данные!
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker-compose -f docker-compose.prod.yml exec backend python create_admin.py
```

---

## Дополнительные ресурсы

- [README.md](README.md) - Общая информация о проекте
- [DEVELOPMENT_PRINCIPLES.md](docs/DEVELOPMENT_PRINCIPLES.md) - Принципы разработки
- [ROADMAP.md](ROADMAP.md) - Дорожная карта развития
- [API Documentation](http://localhost:8000/docs) - Swagger UI (после запуска)

## Поддержка

При возникновении проблем:

1. Проверьте [раздел Устранение неполадок](#устранение-неполадок)
2. Изучите логи: `docker-compose -f docker-compose.prod.yml logs`
3. Создайте issue в репозитории с подробным описанием проблемы

---

**Версия документа**: 1.0
**Дата обновления**: 2025-10-28
**Приложение**: IT Budget Manager v0.5.0
