# Настройка Coolify для развертывания IT Budget Manager

## Предварительные требования

- Установленный и запущенный Coolify на вашем сервере
- Доступ к серверу https://west-it.ru
- GitHub аккаунт с доступом к репозиторию проекта
- SSH доступ к серверу (если требуется)

## Шаг 1: Создание GitHub OAuth App

### 1.1. Перейдите в настройки GitHub

1. Откройте https://github.com/settings/developers
2. Нажмите **"OAuth Apps"** → **"New OAuth App"**

### 1.2. Заполните форму создания OAuth App

```
Application name: Coolify - west-it.ru
Homepage URL: https://west-it.ru
Authorization callback URL: https://west-it.ru/api/oauth/github/callback
```

**ВАЖНО**: URL должен быть ТОЧНО `https://west-it.ru/api/oauth/github/callback` (с https://)

### 1.3. Получите учетные данные

После создания приложения вы увидите:
- **Client ID** (например: `Iv1.a629f14a22f03b49`)
- **Client Secret** (нажмите "Generate a new client secret")

**СОХРАНИТЕ ОБА ЗНАЧЕНИЯ** - они понадобятся для Coolify!

## Шаг 2: Настройка Coolify

### 2.1. Проверьте доступность Coolify

Откройте в браузере: https://west-it.ru

Если видите интерфейс Coolify - все ок. Если нет - проверьте:
- Запущен ли Coolify на сервере
- Правильно ли настроен nginx/reverse proxy
- Есть ли SSL сертификат

### 2.2. Настройте переменные окружения в Coolify

**Вариант A: Через веб-интерфейс Coolify**

1. Войдите в Coolify (https://west-it.ru)
2. Перейдите в **Settings** → **Configuration**
3. Найдите секцию **GitHub OAuth**
4. Введите:
   - **GitHub Client ID**: `ваш_client_id`
   - **GitHub Client Secret**: `ваш_client_secret`
5. Сохраните настройки
6. Перезапустите Coolify

**Вариант B: Через SSH на сервере**

Подключитесь к серверу:
```bash
ssh root@93.189.228.52
```

Найдите `.env` файл Coolify (обычно в `/data/coolify/.env`):
```bash
cd /data/coolify
nano .env
```

Добавьте или обновите:
```bash
GITHUB_APP_CLIENT_ID=ваш_client_id
GITHUB_APP_CLIENT_SECRET=ваш_client_secret
APP_URL=https://west-it.ru
```

Перезапустите Coolify:
```bash
docker restart coolify
```

### 2.3. Проверьте callback URL

После настройки проверьте:
```bash
curl https://west-it.ru/api/oauth/github/callback
```

Теперь вместо `{"message":"Not found."}` должен быть редирект или другой ответ.

## Шаг 3: Подключение GitHub репозитория

### 3.1. Добавьте Source в Coolify

1. В Coolify перейдите в **Sources** → **Add Source**
2. Выберите **GitHub**
3. Авторизуйтесь через GitHub OAuth (это использует настроенный выше OAuth App)
4. Дайте доступ Coolify к вашим репозиториям

### 3.2. Выберите репозиторий

После подключения GitHub:
1. Найдите ваш репозиторий с IT Budget Manager
2. Выберите его для деплоя

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

### Ошибка 404 на callback

Если все еще видите ошибку на `/api/oauth/github/callback`:

1. **Проверьте переменные окружения Coolify**:
```bash
docker exec coolify env | grep GITHUB
```

2. **Проверьте логи Coolify**:
```bash
docker logs coolify -f
```

3. **Убедитесь, что APP_URL настроен**:
```bash
# В .env файле Coolify
APP_URL=https://west-it.ru
```

4. **Перезапустите Coolify**:
```bash
docker restart coolify
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
