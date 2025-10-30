# IT Budget Manager - Быстрый справочник

## 🚀 Статус системы

### ✅ Все работает!
- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **Документация API:** http://localhost:8000/docs

### 📊 Загруженные данные
- **Период:** Весь 2025 год (январь-декабрь)
- **Категорий:** 43
- **План бюджета:** 229 записей
- **Заявок на расходы:** 277
- **Плановая сумма:** 30,510,000 руб
- **Фактические расходы:** 19,944,242 руб
- **Исполнение бюджета:** 65.37%

---

## 📖 Основные документы

### Отчеты
1. **[SESSION_SUMMARY.md](SESSION_SUMMARY.md)** - Полный отчет о проделанной работе
2. **[BUGFIX_REPORT_FINAL.md](BUGFIX_REPORT_FINAL.md)** - Отчет об исправленных ошибках
3. **[DATA_IMPORT_REPORT.md](DATA_IMPORT_REPORT.md)** - Детали импорта данных из Excel

### Инструкции
4. **[QUICKSTART.md](QUICKSTART.md)** - Быстрый старт
5. **[SETUP.md](SETUP.md)** - Установка и настройка
6. **[USER_GUIDE.md](USER_GUIDE.md)** - Руководство пользователя

### Архитектура
7. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Архитектура проекта
8. **[ROADMAP.md](ROADMAP.md)** - План развития

---

## 🔧 Команды управления

### Запуск системы

#### Backend (если остановлен)
```bash
cd /Users/evgenijsikunov/projects/west/west_buget_it/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
echo $! > ../backend.pid
```

#### Frontend (если остановлен)
```bash
cd /Users/evgenijsikunov/projects/west/west_buget_it/frontend
npm run dev > ../frontend.log 2>&1 &
echo $! > ../frontend.pid
```

### Остановка системы

```bash
# Backend
kill $(cat backend.pid)

# Frontend
kill $(cat frontend.pid)
```

### Проверка статуса

```bash
# Проверить, что процессы запущены
ps aux | grep -E "(uvicorn|vite)" | grep -v grep

# Проверить логи backend
tail -f backend.log

# Проверить логи frontend
tail -f frontend.log
```

---

## 📥 Импорт данных

### Повторный импорт из Excel
```bash
cd backend
python3 scripts/import_plan_fact_2025.py
```

### Что импортируется
- **Лист 1 (План):** Плановые показатели бюджета
- **Лист 2 (Факт):** Фактические расходы

### Структура Excel файла

Файл должен находиться здесь: `/Users/evgenijsikunov/projects/west/west_buget_it/Планфакт2025.xlsx`

**Формат листа 1 (План):**
```
СТАТЬЯ       | январь | февраль | март | ...
Аутсорс      | 25000  | 25000   | ...  | ...
Техника      | 160000 | 0       | ...  | ...
...
```

**Формат листа 2 (Факт):**
```
СТАТЬЯ       | январь | февраль | март | ...
Аутсорс      | 23000  | 24500   | ...  | ...
Техника      | 150000 | 0       | ...  | ...
...
```

---

## 🔍 Проверка работоспособности

### Быстрая проверка API

```bash
# Общая статистика
curl http://localhost:8000/api/v1/analytics/dashboard | python3 -m json.tool

# Сводка по бюджету за 2025
curl 'http://localhost:8000/api/v1/budget/summary?year=2025' | python3 -m json.tool

# Обзор бюджета за январь 2025
curl http://localhost:8000/api/v1/budget/overview/2025/1 | python3 -m json.tool

# Список всех заявок (первые 10)
curl 'http://localhost:8000/api/v1/expenses/?skip=0&limit=10' | python3 -m json.tool

# Список категорий
curl http://localhost:8000/api/v1/categories/ | python3 -m json.tool
```

### Проверка frontend

Откройте в браузере: http://localhost:5173

Должны быть доступны страницы:
- **Dashboard** - главная панель с графиками
- **Заявки** - список всех заявок на расходы
- **Бюджет** - план/факт по категориям
- **Категории** - управление категориями
- **Контрагенты** - список контрагентов

---

## 🗄️ База данных

### Подключение к PostgreSQL

```bash
psql -h localhost -U budget_user -d budget_db
```

### Полезные запросы

```sql
-- Количество записей
SELECT COUNT(*) FROM expenses;
SELECT COUNT(*) FROM budget_plans;
SELECT COUNT(*) FROM budget_categories;

-- Суммы по статусам
SELECT status, COUNT(*), SUM(amount)
FROM expenses
GROUP BY status;

-- План/факт по месяцам 2025
SELECT
  bp.month,
  SUM(bp.planned_amount) as planned,
  (SELECT SUM(amount) FROM expenses
   WHERE EXTRACT(year FROM request_date) = 2025
   AND EXTRACT(month FROM request_date) = bp.month) as actual
FROM budget_plans bp
WHERE bp.year = 2025
GROUP BY bp.month
ORDER BY bp.month;
```

### Миграции

```bash
cd backend

# Проверить текущую версию
alembic current

# Список всех миграций
alembic history

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

---

## 🎯 Основные функции

### 1. Просмотр данных
- Открыть http://localhost:5173
- Выбрать раздел "Dashboard" для общей статистики
- Выбрать "Заявки" для списка всех расходов
- Выбрать "Бюджет" для план/факт анализа

### 2. Фильтрация
- По датам (год, месяц)
- По статусу заявки
- По категории
- По контрагенту

### 3. Экспорт в Excel
- Перейти на страницу "Заявки"
- Нажать кнопку "Экспорт в Excel"
- Файл скачается автоматически

### 4. Создание заявки
- Перейти на страницу "Заявки"
- Нажать кнопку "Создать заявку"
- Заполнить форму
- Сохранить

---

## ⚠️ Решение проблем

### Backend не запускается

```bash
# Проверить, не занят ли порт 8000
lsof -ti:8000

# Убить процесс на порту 8000
kill $(lsof -ti:8000)

# Проверить логи
tail -50 backend.log
```

### Frontend не запускается

```bash
# Проверить, не занят ли порт 5173
lsof -ti:5173

# Убить процесс на порту 5173
kill $(lsof -ti:5173)

# Переустановить зависимости
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### База данных недоступна

```bash
# Проверить статус PostgreSQL
brew services list

# Запустить PostgreSQL
brew services start postgresql@14

# Проверить подключение
psql -h localhost -U budget_user -d budget_db -c "SELECT 1"
```

### Ошибки enum values

Если видите ошибки типа "Unknown enum value", проверьте:

```bash
# Применены ли все миграции
cd backend
alembic current
alembic upgrade head

# Проверить enum в БД
psql budget_db -c "\dT+ expensestatusenum"
psql budget_db -c "\dT+ budgetstatusenum"
```

Должны быть английские значения:
- `expensestatusenum`: DRAFT, PENDING, PAID, REJECTED, CLOSED
- `budgetstatusenum`: DRAFT, APPROVED

---

## 📈 Статистика по данным

### Топ-5 категорий по расходам

1. **Аутсорс** - 3,140,370 руб (OPEX)
2. **Связь** - 2,278,189 руб (OPEX)
3. **Техника** - 1,992,873 руб (CAPEX)
4. **Битрикс 24 Разработка** - 1,328,500 руб (OPEX)
5. **Непредвиденные расходы** - 1,187,810 руб (OPEX)

### Распределение CAPEX/OPEX

- **CAPEX:** 7,131,099 руб (35.76%)
- **OPEX:** 12,813,143 руб (64.24%)

### Статусы заявок

- **PAID (Оплачено):** 262 заявки на 19,174,822 руб
- **PENDING (К оплате):** 12 заявок на 740,420 руб
- **REJECTED (Отклонено):** 3 заявки на 29,000 руб

---

## 🔐 Доступ и безопасность

### Текущие настройки
- **Backend порт:** 8000
- **Frontend порт:** 5173
- **БД порт:** 5432

### Переменные окружения

**Backend (.env):**
```env
DATABASE_URL=postgresql://budget_user:budget_password@localhost:5432/budget_db
SECRET_KEY=your-secret-key-here
```

**Frontend (.env):**
```env
VITE_API_URL=http://localhost:8000
```

---

## 📞 Что дальше?

### Рекомендуемые действия

1. ✅ **Открыть приложение в браузере**
   - http://localhost:5173
   - Проверить все разделы

2. ✅ **Проверить данные**
   - Dashboard с графиками
   - Список заявок
   - План/факт по месяцам

3. ✅ **Протестировать функции**
   - Создание заявки
   - Фильтрация
   - Экспорт в Excel

4. ✅ **Ознакомиться с документацией**
   - Прочитать SESSION_SUMMARY.md
   - Изучить ARCHITECTURE.md

### Если нужна помощь

Все отчеты и документация находятся в корне проекта:
```
/Users/evgenijsikunov/projects/west/west_buget_it/
```

---

## ✨ Заключение

**Система полностью работоспособна и готова к использованию!**

- Backend API работает ✅
- Frontend доступен ✅
- База данных настроена ✅
- Данные на 2025 год загружены ✅
- Все ошибки исправлены ✅

**Приятной работы с IT Budget Manager! 🚀**
