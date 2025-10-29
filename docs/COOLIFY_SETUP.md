# Настройка Coolify для развертывания IT Budget Manager

## ⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ

**OAuth callback URL (`/api/oauth/github/callback`) НЕ НУЖЕН!**

В современном Coolify (v4+) GitHub подключается через **Personal Access Token** или **GitHub App**, а НЕ через OAuth callback. Если вы видите ошибку 404 на `/api/oauth/github/callback` - это нормально и НЕ является проблемой.

## Предварительные требования

- Установленный и запущенный Coolify на вашем сервере
- Доступ к серверу https://west-it.ru
- GitHub аккаунт с доступом к репозиторию проекта
- SSH доступ к серверу (если требуется)

## Шаг 1: Создание GitHub Personal Access Token

**ВАЖНО**: В современном Coolify используется Personal Access Token, а НЕ OAuth App!

### 1.1. Создайте Personal Access Token

1. Откройте: https://github.com/settings/tokens
2. Нажмите **"Generate new token"** → **"Generate new token (classic)"**

### 1.2. Настройте токен

```
Note: Coolify - west-it.ru
Expiration: No expiration (или выберите срок)

Scopes (галочки):
✅ repo (полный доступ к репозиториям)
✅ admin:repo_hook (управление webhooks)
✅ admin:public_key (управление deploy keys)
✅ read:user (чтение профиля)
```

### 1.3. Сохраните токен

Нажмите **"Generate token"** и **СОХРАНИТЕ ТОКЕН** - он будет показан только один раз!

Пример токена: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Шаг 2: Подключение GitHub к Coolify

### 2.1. Откройте веб-интерфейс Coolify

Откройте в браузере: **https://west-it.ru** (или http://93.189.228.52:8000)

Войдите используя ваши учетные данные Coolify.

### 2.2. Добавьте GitHub Source

1. В левом меню найдите **"Sources"** (Источники)
2. Нажмите **"+ New Source"** или **"Add Source"**
3. Выберите **"GitHub"** или **"Private Repository"**
4. Выберите тип: **"GitHub via Personal Access Token"**

### 2.3. Введите данные GitHub

1. **Name**: `GitHub - My Projects` (любое имя)
2. **Type**: `GitHub`
3. **Personal Access Token**: вставьте токен из Шага 1
4. Нажмите **"Save"** или **"Connect"**

### 2.4. Проверьте подключение

Coolify автоматически проверит токен и подключится к GitHub. Вы увидите список ваших репозиториев.

## Шаг 3: Выбор репозитория для деплоя

После подключения GitHub Source, вы увидите список ваших репозиториев:

1. Найдите репозиторий **west_buget_it** (или ваше имя репозитория)
2. Нажмите на него или выберите для деплоя

## Шаг 4: Создание приложения в Coolify

### 4.1. Создайте новый проект

1. В Coolify: **Projects** → **New Project**
2. Имя проекта: `IT Budget Manager`

### 4.2. Создайте приложение

1. В проекте: **Add Resource** → **Application**
2. Выберите источник: **GitHub**
3. Выберите репозиторий
4. Выберите ветку: `main` (или другую)

### 4.3. Настройте тип развертывания

**Вариант A: Docker Compose (Рекомендуется)**

1. Build Pack: **Docker Compose**
2. Docker Compose File: `docker-compose.prod.yml`
3. Coolify автоматически обнаружит ваш файл

**Вариант B: Dockerfile**

Если хотите деплоить отдельно backend и frontend:
1. Создайте 2 приложения (backend и frontend)
2. Для каждого укажите соответствующий Dockerfile

## Шаг 5: Настройка переменных окружения

### 5.1. Backend Environment Variables

В Coolify для backend приложения добавьте:

```bash
# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=it_budget_db
DB_USER=budget_user
DB_PASSWORD=STRONG_PASSWORD_HERE

# Security
SECRET_KEY=GENERATE_WITH_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=STRONG_ADMIN_PASSWORD
ADMIN_EMAIL=admin@west-it.ru

# CORS - ВАЖНО!
CORS_ORIGINS='["https://west-it.ru","https://api.west-it.ru"]'

# Application
APP_NAME=IT Budget Manager
DEBUG=False
API_PREFIX=/api/v1

# Redis
REDIS_URL=redis://redis:6379

# FTP Import
FTP_HOST=floppisw.beget.tech
FTP_USER=floppisw_zrds
FTP_PASS=4yZUaloOBmU!
FTP_REMOTE_PATH=/Zayavki na raszkhod(spisok) XLSX.xlsx
```

### 5.2. Frontend Environment Variables

```bash
VITE_API_URL=https://api.west-it.ru
```

## Шаг 6: Настройка доменов

### 6.1. Настройте домены в Coolify

Для **Backend**:
- Domain: `api.west-it.ru`
- Port: 8888

Для **Frontend**:
- Domain: `west-it.ru`
- Port: 3001

### 6.2. Настройте DNS записи

В вашем DNS провайдере добавьте A записи:

```
api.west-it.ru    →  93.189.228.52
west-it.ru        →  93.189.228.52
```

### 6.3. Настройте SSL сертификаты

Coolify автоматически настроит Let's Encrypt сертификаты для обоих доменов.

## Шаг 7: Деплой

### 7.1. Первый деплой

1. В Coolify нажмите **Deploy**
2. Coolify:
   - Клонирует репозиторий
   - Построит Docker образы
   - Запустит контейнеры
   - Настроит nginx reverse proxy
   - Получит SSL сертификаты

### 7.2. Проверьте статус

Следите за логами деплоя в интерфейсе Coolify.

### 7.3. Проверьте приложение

После успешного деплоя:
- Frontend: https://west-it.ru
- Backend API: https://api.west-it.ru/docs
- Health check: https://api.west-it.ru/health

## Шаг 8: Автоматический деплой

### 8.1. Настройте Webhook

Coolify автоматически создаст GitHub webhook для автоматического деплоя при push в main ветку.

Проверить можно в:
- GitHub: **Settings** → **Webhooks**
- Coolify: **Application** → **Webhooks**

## Решение проблем

### GitHub не подключается

Если не можете подключить GitHub:

1. **Проверьте токен**:
   - Токен должен быть Classic (не Fine-grained)
   - Должны быть выбраны нужные scopes (repo, admin:repo_hook, etc.)
   - Токен не должен быть истекшим

2. **Проверьте доступ к репозиториям**:
   - Убедитесь что у вас есть доступ к нужному репозиторию
   - Для приватных репозиториев токен должен иметь полный доступ

3. **Проверьте логи Coolify**:
```bash
ssh root@93.189.228.52
docker logs coolify -f
```

### CORS ошибки

Если видите CORS ошибки в браузере:

1. Проверьте `CORS_ORIGINS` в backend:
```bash
CORS_ORIGINS='["https://west-it.ru","https://api.west-it.ru"]'
```

2. Убедитесь, что используете HTTPS везде

### База данных не подключается

1. Проверьте, что PostgreSQL контейнер запущен
2. Проверьте DB_HOST (должен быть `db` для Docker Compose)
3. Проверьте пароли и имена БД

### Frontend не может подключиться к Backend

1. Проверьте `VITE_API_URL` в frontend
2. Убедитесь, что backend доступен по этому URL
3. Проверьте CORS настройки

## Дополнительные настройки

### Backup базы данных

Настройте регулярные бэкапы PostgreSQL:

```bash
# Создайте cron job на сервере
0 2 * * * docker exec it_budget_db_prod pg_dump -U budget_user it_budget_db | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Мониторинг

1. Настройте Sentry для отслеживания ошибок
2. Используйте встроенный мониторинг Coolify
3. Настройте уведомления о проблемах деплоя

### Масштабирование

Если потребуется увеличить производительность:
1. Увеличьте количество workers в backend
2. Настройте Redis для кэширования
3. Используйте CDN для статических файлов frontend

## Полезные команды

### Просмотр логов в Coolify

```bash
# Логи backend
docker logs it_budget_backend_prod -f

# Логи frontend
docker logs it_budget_frontend_prod -f

# Логи базы данных
docker logs it_budget_db_prod -f
```

### Миграции базы данных

```bash
# Выполнить миграции
docker exec it_budget_backend_prod alembic upgrade head

# Откатить миграцию
docker exec it_budget_backend_prod alembic downgrade -1
```

### Очистка Docker

```bash
# Очистить неиспользуемые образы
docker system prune -a

# Очистить volumes
docker volume prune
```

## Контакты и поддержка

- Документация Coolify: https://coolify.io/docs
- GitHub Issues: https://github.com/coollabsio/coolify/issues
- Discord сообщество: https://discord.gg/coolify
