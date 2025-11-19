# Настройка тестового сервера

## Общая информация

**Сервер**: 46.173.18.143 (root)
**Пароль**: z!e1823%DkEY
**Директория проекта**: /root/acme_budget_test
**Ветка**: test

## URLs

- **Frontend**: http://46.173.18.143:3002
- **Backend API**: http://46.173.18.143:8889
- **API Docs**: http://46.173.18.143:8889/docs
- **Database**: PostgreSQL 15 (порт 54330)
- **Redis**: порт 6379

## Учетные данные администратора

- **Username**: `admin`
- **Email**: `admin@test.com`
- **Password**: `admin123test`

⚠️ **ВАЖНО**: Email должен быть `admin@test.com`, НЕ `admin@test.local` (не проходит валидацию)

## Порты

- Frontend: 3002 (маппинг на 5173 внутри контейнера)
- Backend: 8889 (маппинг на 8000 внутри контейнера)
- PostgreSQL: 54330 (маппинг на 5432 внутри контейнера)
- Redis: 6379 (внутренний)

## Конфигурация (.env)

Файл `/root/acme_budget_test/.env`:

```bash
# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=it_budget_db_test
DB_USER=budget_user_test
DB_PASSWORD=t5bz300CK7a3IgVAGt0sBg

# Security
SECRET_KEY=JI312MF-K-I2NHpzCwN_X-6erGdZPjO9ekPdSOJb0mfpu1WvNK7jKYD-GusrzDQ2YKGLRPM3D9sQjolme2KPoQ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
APP_NAME=IT Budget Manager (TEST)

# CORS - ВАЖНО для работы frontend
CORS_ORIGINS=["http://46.173.18.143:3002","http://localhost:3002"]

# Ports
FRONTEND_PORT=3002
BACKEND_PORT=8889
DB_PORT=54330

# Frontend API URL
VITE_API_URL=http://46.173.18.143:8889/api/v1

# Docker Compose
COMPOSE_PROJECT_NAME=it-budget-test

# Admin password для create_admin.py
ADMIN_PASSWORD=admin123test
```

## Docker Compose

Файл: `/root/acme_budget_test/docker-compose.test.yml`

**Важные моменты**:

1. **Backend command**: Обязательно указан `command: uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. **Frontend port mapping**: `3002:5173` (НЕ 3002:80!)
3. **Frontend healthcheck**: Удален (curl не установлен в контейнере)
4. **Backend healthcheck**: Использует curl для проверки /health

## GitHub Actions автоматический деплой

### Workflow файл

`.github/workflows/deploy-test.yml` - автоматический деплой при push в ветку `test`

### GitHub Secrets (настроены)

Необходимые секреты в Settings → Secrets and variables → Actions:

1. **TEST_SERVER_SSH_KEY** - приватный SSH ключ для доступа к серверу
2. **TEST_SERVER_IP** - `46.173.18.143`
3. **TEST_SERVER_USER** - `root`
4. **TEST_SERVER_PROJECT_PATH** - `/root/acme_budget_test`

### Как работает CI/CD

1. Push в ветку `test` → автоматически запускается workflow
2. Workflow подключается по SSH к серверу
3. Выполняет на сервере:
   ```bash
   cd /root/acme_budget_test
   git fetch origin test
   git reset --hard origin/test
   docker compose -f docker-compose.test.yml down
   docker compose -f docker-compose.test.yml up -d --build
   ```

## Проблемы и решения

### 1. Email валидация (КРИТИЧНО!)

**Проблема**: Email `admin@test.local` не проходит валидацию Pydantic, потому что `.local` - зарезервированный домен.

**Ошибка**:
```
ResponseValidationError: value is not a valid email address:
The part after the @-sign is a special-use or reserved name that cannot be used with email.
```

**Решение**: Использовать `admin@test.com` вместо `admin@test.local`

```sql
-- Исправление в базе:
UPDATE users SET email = 'admin@test.com' WHERE username = 'admin';
```

### 2. Отсутствующая колонка default_category_id

**Проблема**: Модель `Department` имеет поле `default_category_id`, но в базе данных колонки нет.

**Ошибка**:
```
ProgrammingError: column departments.default_category_id does not exist
```

**Решение**: Добавить колонку в базу данных

```sql
ALTER TABLE departments ADD COLUMN IF NOT EXISTS default_category_id INTEGER;
ALTER TABLE departments ADD CONSTRAINT fk_departments_default_category
    FOREIGN KEY (default_category_id) REFERENCES budget_categories(id);
```

**Миграция**: Создан файл `backend/alembic/versions/2025_11_19_2124-add_default_category_id_to_departments.py`

### 3. Frontend healthcheck ошибка

**Проблема**: Frontend контейнер показывал статус "unhealthy", хотя работал.

**Причина**: В healthcheck использовался `curl`, который не установлен в контейнере.

**Решение**: Удален healthcheck из `docker-compose.test.yml` для frontend сервиса.

### 4. Backend не запускался (Exit code 0)

**Проблема**: Backend контейнер сразу завершался с exit code 0.

**Причина**: Dockerfile содержал только healthcheck команду вместо команды запуска приложения.

**Решение**: Добавлен `command: uvicorn app.main:app --host 0.0.0.0 --port 8000` в docker-compose.test.yml

### 5. Frontend port mismatch

**Проблема**: Frontend был недоступен, порт 80 не работал.

**Причина**: Vite dev server работает на порту 5173, а docker-compose маппил порт 80.

**Решение**: Изменен port mapping с `3002:80` на `3002:5173`

### 6. Database migration errors

**Проблема**: Миграции падали с ошибками "index/table does not exist".

**Решение**: Исправлены все `op.drop_index()` и `op.drop_table()` на условные операции:
```python
# Вместо:
op.drop_index('idx_name', table_name='table')
op.drop_table('table')

# Используем:
op.execute('DROP INDEX IF EXISTS idx_name')
op.execute('DROP TABLE IF EXISTS table CASCADE')
```

## Команды управления

### Подключение по SSH

```bash
ssh root@46.173.18.143
cd /root/acme_budget_test
```

### Управление контейнерами

```bash
# Запуск всех сервисов
docker compose -f docker-compose.test.yml up -d

# Остановка всех сервисов
docker compose -f docker-compose.test.yml down

# Перезапуск конкретного сервиса
docker compose -f docker-compose.test.yml restart backend
docker compose -f docker-compose.test.yml restart frontend

# Пересборка и запуск
docker compose -f docker-compose.test.yml up -d --build

# Просмотр статуса
docker compose -f docker-compose.test.yml ps

# Просмотр логов
docker logs budget_backend_test --tail 100
docker logs budget_frontend_test --tail 100
docker logs budget_db_test --tail 100
```

### База данных

```bash
# Подключение к PostgreSQL
docker exec -i budget_db_test psql -U budget_user_test -d it_budget_db_test

# Проверка структуры таблицы
docker exec -i budget_db_test psql -U budget_user_test -d it_budget_db_test -c '\d departments'

# Выполнение SQL запроса
docker exec -i budget_db_test psql -U budget_user_test -d it_budget_db_test -c "SELECT * FROM users LIMIT 5"

# Обновление email администратора
docker exec -i budget_db_test psql -U budget_user_test -d it_budget_db_test << 'EOF'
UPDATE users SET email = 'admin@test.com' WHERE username = 'admin';
EOF
```

### Миграции базы данных

```bash
# Войти в backend контейнер
docker exec -it budget_backend_test bash

# Применить миграции
cd /app
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Откат миграции
alembic downgrade -1
```

### Обновление с GitHub

```bash
cd /root/acme_budget_test
git fetch origin test
git reset --hard origin/test
docker compose -f docker-compose.test.yml down
docker compose -f docker-compose.test.yml up -d --build
```

### Тестирование API

```bash
# Health check
curl http://46.173.18.143:8889/health

# Login
curl -X POST http://46.173.18.143:8889/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123test"}'

# Получить token и сделать запрос
TOKEN=$(curl -s -X POST http://46.173.18.143:8889/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123test"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

curl "http://46.173.18.143:8889/api/v1/departments/?is_active=true" \
  -H "Authorization: Bearer $TOKEN"
```

## Структура проекта на сервере

```
/root/acme_budget_test/
├── .git/                           # Git репозиторий
├── .env                            # Environment переменные (TEST)
├── docker-compose.test.yml         # Docker Compose для тестового сервера
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       └── 2025_11_19_2124-add_default_category_id_to_departments.py
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   │   └── models.py          # Department model с default_category_id
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── Dockerfile
└── docs/
    └── TEST_SERVER_SETUP.md        # Этот документ
```

## Безопасность

⚠️ **ВАЖНО**:

1. Это ТЕСТОВЫЙ сервер - не использовать в production
2. DEBUG=True включен для удобства разработки
3. Пароли указаны в открытом виде (только для тестирования)
4. CORS разрешает запросы с любого origin (для тестирования)
5. Используется HTTP, не HTTPS

## Troubleshooting

### Frontend не загружается

1. Проверить работает ли контейнер:
   ```bash
   docker compose -f docker-compose.test.yml ps
   ```

2. Проверить логи:
   ```bash
   docker logs budget_frontend_test --tail 50
   ```

3. Очистить кеш браузера или открыть в инкогнито

4. Проверить доступность:
   ```bash
   curl -I http://46.173.18.143:3002
   ```

### API возвращает 500 ошибки

1. Проверить логи backend:
   ```bash
   docker logs budget_backend_test --tail 100
   ```

2. Проверить что база данных доступна:
   ```bash
   docker exec budget_backend_test curl http://localhost:8000/health
   ```

3. Проверить структуру базы данных (особенно departments таблицу)

### CORS ошибки

1. Проверить что CORS_ORIGINS в .env содержит правильный URL
2. Перезапустить backend:
   ```bash
   docker compose -f docker-compose.test.yml restart backend
   ```

3. Проверить CORS заголовки:
   ```bash
   curl -I http://46.173.18.143:8889/api/v1/departments/ \
     -H "Origin: http://46.173.18.143:3002"
   ```

### Database migration ошибки

1. Проверить текущую версию миграции:
   ```bash
   docker exec -it budget_backend_test alembic current
   ```

2. Применить миграции вручную:
   ```bash
   docker exec -it budget_backend_test alembic upgrade head
   ```

3. Если миграция падает - проверить логи и исправить SQL в миграции

## Контакты и ссылки

- **GitHub Repository**: https://github.com/[your-repo]/acme_budget_it
- **GitHub Actions**: https://github.com/[your-repo]/acme_budget_it/actions
- **Ветка test**: https://github.com/[your-repo]/acme_budget_it/tree/test

## История изменений

### 2025-11-19

- ✅ Создан тестовый сервер на 46.173.18.143
- ✅ Настроен беспарольный SSH доступ
- ✅ Установлены Docker, Docker Compose, git
- ✅ Клонирован репозиторий в /root/acme_budget_test
- ✅ Настроены .env файлы для тестовой среды
- ✅ Исправлены ошибки миграций базы данных
- ✅ Исправлен запуск backend контейнера (добавлен uvicorn command)
- ✅ Исправлен port mapping для frontend (5173)
- ✅ Создан GitHub Actions workflow для автоматического деплоя
- ✅ Настроены GitHub Secrets
- ✅ Создан администратор с корректным email
- ✅ Добавлена отсутствующая колонка default_category_id в таблицу departments
- ✅ Протестирована работа всех сервисов
- ✅ Создана эта документация
