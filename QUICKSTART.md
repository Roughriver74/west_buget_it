# 🚀 Быстрый старт IT Budget Manager

## Вариант 1: Запуск с Docker (самый простой)

### Шаг 1: Запустить все сервисы

```bash
# Убедитесь, что вы находитесь в корне проекта
cd /Users/evgenijsikunov/projects/west/west_buget_it

# Запустить PostgreSQL, Backend и Frontend
docker-compose up -d
```

### Шаг 2: Применить миграции и загрузить данные

```bash
# Дождитесь запуска всех контейнеров (около 30 секунд)
# Затем выполните:

# Войти в контейнер backend
docker-compose exec backend bash

# Применить миграции базы данных
alembic upgrade head

# Загрузить данные из Excel файлов
python scripts/import_excel.py

# Выйти из контейнера
exit
```

### Шаг 3: Открыть приложение

Откройте в браузере:
- **Приложение**: http://localhost:5173
- **API документация**: http://localhost:8000/docs

✅ Готово! Приложение запущено и готово к использованию.

---

## Вариант 2: Запуск без Docker (для разработки)

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Шаг 1: Настройка PostgreSQL

```bash
# Запустите PostgreSQL и создайте БД
psql -U postgres

CREATE USER budget_user WITH PASSWORD 'budget_pass';
CREATE DATABASE it_budget_db OWNER budget_user;
GRANT ALL PRIVILEGES ON DATABASE it_budget_db TO budget_user;
\q
```

### Шаг 2: Backend

Откройте терминал:

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv venv

# Активировать (Mac/Linux)
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Применить миграции
alembic upgrade head

# Загрузить данные
python scripts/import_excel.py

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 3: Frontend

Откройте НОВЫЙ терминал:

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev
```

### Шаг 4: Открыть приложение

- **Приложение**: http://localhost:5173
- **API**: http://localhost:8000/docs

---

## 📊 Что вы увидите после запуска

### Дашборд
- Карточки с метриками: План, Факт, Остаток, % исполнения
- График CAPEX vs OPEX
- Топ-5 категорий по расходам
- Распределение заявок по статусам

### Заявки
- Таблица всех заявок с фильтрами
- Поиск по номеру, комментарию
- Фильтры по статусу, категории, дате
- Возможность создания новых заявок

### Справочники
- Категории расходов (OPEX/CAPEX)
- Контрагенты
- Организации

---

## 🔧 Полезные команды

### Docker

```bash
# Посмотреть логи
docker-compose logs -f backend
docker-compose logs -f frontend

# Перезапустить сервис
docker-compose restart backend

# Остановить все
docker-compose down

# Остановить с удалением данных
docker-compose down -v
```

### Backend (без Docker)

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Применить миграции
alembic upgrade head

# Запустить тесты
pytest
```

### Frontend (без Docker)

```bash
# Сборка для production
npm run build

# Линтинг
npm run lint
```

---

## 📝 Примеры данных

После импорта в базе будут:

**Категории:**
- Аутсорс (OPEX)
- Техника (CAPEX)
- Покупка ПО (OPEX)
- Интернет (OPEX)

**Организации:**
- ВЕСТ ООО
- ВЕСТ ГРУПП ООО

**Заявки:**
- Все заявки из файла "заявки на расходы по дням.xlsx"

---

## 🐛 Решение проблем

### Ошибка подключения к БД
```bash
# Проверьте, что PostgreSQL запущен
docker-compose ps
# или
pg_isready -h localhost -p 5432
```

### Frontend не подключается к Backend
```bash
# Проверьте, что Backend запущен
curl http://localhost:8000/health

# Должен вернуть: {"status":"healthy"}
```

### Порты заняты
Если порты 5432, 8000 или 5173 заняты, измените их в docker-compose.yml или .env файлах.

---

## 📚 Документация

- Полная инструкция: [SETUP.md](SETUP.md)
- README: [README.md](README.md)
- API документация: http://localhost:8000/docs

---

## 🎯 Следующие шаги

1. Изучите дашборд и данные
2. Попробуйте создать новую заявку
3. Поэкспериментируйте с фильтрами
4. Изучите API документацию
5. Начните кастомизацию под свои нужды

Приятной работы! 🚀
