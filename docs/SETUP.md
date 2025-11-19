# Инструкция по запуску IT Budget Manager

## Быстрый старт с Docker (рекомендуется)

### 1. Запуск всех сервисов

```bash
# Запустить все сервисы (PostgreSQL, Backend, Frontend)
docker-compose up -d

# Проверить статус
docker-compose ps
```

### 2. Применить миграции и загрузить данные

```bash
# Войти в контейнер backend
docker-compose exec backend bash

# Применить миграции
alembic upgrade head

# Загрузить данные из Excel
python scripts/import_excel.py

# Выйти из контейнера
exit
```

### 3. Открыть приложение

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Запуск без Docker (для разработки)

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### 1. Настройка PostgreSQL

```bash
# Создать пользователя и базу данных
psql -U postgres

CREATE USER budget_user WITH PASSWORD 'budget_pass';
CREATE DATABASE it_budget_db OWNER budget_user;
GRANT ALL PRIVILEGES ON DATABASE it_budget_db TO budget_user;
\q
```

### 2. Запуск Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv

# Активировать (Mac/Linux)
source venv/bin/activate
# или Windows
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Файл .env уже создан, проверьте настройки подключения к БД

# Применить миграции
alembic upgrade head

# Загрузить данные из Excel
python scripts/import_excel.py

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен на http://localhost:8000

### 3. Запуск Frontend

Откройте новый терминал:

```bash
cd frontend

# Установить зависимости
npm install

# Файл .env уже создан

# Запустить dev сервер
npm run dev
```

Frontend будет доступен на http://localhost:5173

---

## Структура проекта

```
acme_budget_it/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── core/           # Конфигурация
│   │   ├── db/             # Модели БД
│   │   ├── schemas/        # Pydantic схемы
│   │   └── main.py         # Точка входа
│   ├── alembic/            # Миграции
│   ├── scripts/            # Утилиты
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API клиент
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы
│   │   ├── types/         # TypeScript типы
│   │   └── main.tsx       # Точка входа
│   └── package.json
└── docker-compose.yml     # Оркестрация
```

---

## Основные функции

### 1. Дашборд
- Общие метрики бюджета (План vs Факт)
- График CAPEX vs OPEX
- Топ-5 категорий по расходам
- Распределение по статусам

### 2. Заявки
- Список всех заявок с фильтрами
- Поиск по номеру, комментарию, заявителю
- Фильтры по статусу, категории, дате
- Создание и редактирование заявок

### 3. Бюджет
- Планирование помесячное
- Сравнение План vs Факт
- Разбивка CAPEX/OPEX

### 4. Аналитика
- Графики и тренды
- Аналитика по категориям
- Экспорт отчетов

### 5. Справочники
- Статьи расходов (OPEX/CAPEX)
- Контрагенты
- Организации

---

## API Эндпоинты

### Заявки
- `GET /api/v1/expenses` - Список заявок
- `POST /api/v1/expenses` - Создать заявку
- `GET /api/v1/expenses/{id}` - Получить заявку
- `PUT /api/v1/expenses/{id}` - Обновить заявку
- `PATCH /api/v1/expenses/{id}/status` - Изменить статус

### Аналитика
- `GET /api/v1/analytics/dashboard` - Данные дашборда
- `GET /api/v1/analytics/budget-execution` - Исполнение бюджета
- `GET /api/v1/analytics/by-category` - По категориям

### Справочники
- `GET /api/v1/categories` - Категории
- `GET /api/v1/contractors` - Контрагенты
- `GET /api/v1/organizations` - Организации

Полная документация: http://localhost:8000/docs

---

## Остановка сервисов

### Docker
```bash
# Остановить все сервисы
docker-compose down

# Остановить с удалением данных
docker-compose down -v
```

### Без Docker
```bash
# Остановить процессы (Ctrl+C в каждом терминале)
```

---

## Разработка

### Backend

```bash
# Создать новую миграцию
cd backend
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
cd frontend

# Сборка для production
npm run build

# Предпросмотр production сборки
npm run preview

# Линтинг
npm run lint
```

---

## Решение проблем

### Backend не запускается
1. Проверьте, что PostgreSQL запущен
2. Проверьте настройки подключения в [.env](backend/.env)
3. Убедитесь, что применены миграции: `alembic upgrade head`

### Frontend не подключается к Backend
1. Проверьте, что Backend запущен на http://localhost:8000
2. Проверьте настройки в [frontend/.env](frontend/.env)
3. Проверьте CORS настройки в [backend/.env](backend/.env)

### База данных пустая
1. Запустите скрипт импорта: `python scripts/import_excel.py`
2. Убедитесь, что Excel файлы находятся в корне проекта

---

## Поддержка

Для вопросов и предложений создавайте Issue в репозитории проекта.
