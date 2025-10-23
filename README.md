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
west_budget_it/
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

## Лицензия

MIT
