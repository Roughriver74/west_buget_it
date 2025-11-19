# IT Budget Manager

Веб-приложение для управления бюджетом IT-отдела с возможностью управления заявками, справочниками и аналитикой.

## Возможности

- ✅ Управление заявками на расходы с различными статусами
- ✅ Справочники статей расходов (OPEX/CAPEX)
- ✅ Справочник контрагентов и организаций
- ✅ Динамический расчет остатков бюджета
- ✅ Аналитические дашборды и отчеты
- ✅ Планирование и факт с визуализацией
- ✅ Помесячный и понедельный учет

## Технологии

### Backend
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Pydantic

### Frontend
- React 18
- TypeScript
- Vite
- Ant Design
- Recharts
- React Query
- React Router

## Структура проекта

```
acme_budget_it/
├── backend/           # FastAPI бэкенд
├── frontend/          # React фронтенд
├── docker-compose.yml
└── README.md
```

## Быстрый старт

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker (опционально)

### Запуск с Docker

```bash
# Запуск всех сервисов
docker-compose up -d

# Применить миграции
docker-compose exec backend alembic upgrade head

# Загрузить данные из Excel
docker-compose exec backend python scripts/import_excel.py
```

Приложение будет доступно:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Запуск без Docker

#### Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev
```

## API Документация

После запуска backend, документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Миграция данных из Excel

```bash
cd backend
python scripts/import_excel.py --file ../IT_Budget_Analysis_Full.xlsx
```

## Разработка

### Backend

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Запустить тесты
pytest
```
### Pre-commit hooks

> Форматирование (black, isort) и статический анализ (flake8, mypy) запускаются автоматически перед коммитом.

```bash
# Установить pre-commit (если еще не установлен)
pip install pre-commit

# Настроить git-хуки в репозитории
pre-commit install

# Запустить проверки для всех файлов
pre-commit run --all-files
```

### Мониторинг: Sentry (опционально)

1. Создайте проект в [Sentry](https://sentry.io/) и получите DSN.
2. Добавьте переменные окружения:

Backend (`.env`):

```env
SENTRY_DSN=your-sentry-dsn
SENTRY_TRACES_SAMPLE_RATE=0.1   # 0.0–1.0
SENTRY_PROFILES_SAMPLE_RATE=0.0 # 0.0–1.0
```

Frontend (`.env` в каталоге `frontend`):

```env
VITE_SENTRY_DSN=your-sentry-dsn
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

3. Перезапустите приложения. Ошибки и перформанс-трейсы будут попадать в Sentry.

### Метрики: Prometheus (опционально)

1. Установите переменную окружения для backend (`.env`):

```env
ENABLE_PROMETHEUS=True
```

2. Перезапустите backend. Эндпоинт `/metrics` станет доступен для Prometheus.

### Frontend

```bash
# Запуск в dev режиме
npm run dev

# Сборка для production
npm run build

# Предпросмотр production сборки
npm run preview

# Линтинг
npm run lint
```

### Генерация TypeScript типов из OpenAPI

```bash
# Экспортировать актуальную схему (запустит backend/app и сохранит openapi.json в frontend)
python backend/scripts/export_openapi.py --output frontend/openapi.json

# Сгенерировать типы в frontend/src/types/api.generated.ts
cd frontend
npm install
npm run generate:types
```

## Основные эндпоинты API

### Заявки на расходы
- `GET /api/v1/expenses` - Список заявок
- `POST /api/v1/expenses` - Создать заявку
- `GET /api/v1/expenses/{id}` - Получить заявку
- `PUT /api/v1/expenses/{id}` - Обновить заявку
- `PATCH /api/v1/expenses/{id}/status` - Изменить статус

### Аналитика
- `GET /api/v1/analytics/dashboard` - Данные для дашборда
- `GET /api/v1/analytics/budget-execution` - Исполнение бюджета
- `GET /api/v1/analytics/by-category` - Аналитика по категориям

### Справочники
- `GET /api/v1/categories` - Статьи расходов
- `GET /api/v1/contractors` - Контрагенты
- `GET /api/v1/organizations` - Организации

## Документация

- [ROADMAP.md](./ROADMAP.md) - план развития проекта и история изменений
- [AUTH_SETUP.md](./AUTH_SETUP.md) - настройка системы аутентификации
- [SETUP.md](./SETUP.md) - детальная инструкция по установке
- [PAYROLL_KPI_SUMMARY.md](./PAYROLL_KPI_SUMMARY.md) - краткое описание модулей ФОТ и KPI
- [PAYROLL_KPI_PLAN.md](./PAYROLL_KPI_PLAN.md) - детальный технический план модулей ФОТ и KPI

## Лицензия

MIT
