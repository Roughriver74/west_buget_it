# 📊 IT Budget Manager - Сводка проекта

## 🎯 Описание проекта

**IT Budget Manager** - это современное веб-приложение для управления бюджетом IT-отдела с возможностью:
- Управления заявками на расходы
- Ведения справочников (категории, контрагенты, организации)
- Планирования бюджета и отслеживания исполнения
- Аналитики расходов с визуализацией
- Динамического расчета остатков бюджета

## 📁 Структура проекта

```
west_budget_it/
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/              # API endpoints
│   │   │   ├── expenses.py      # Заявки на расходы
│   │   │   ├── categories.py    # Категории расходов
│   │   │   ├── contractors.py   # Контрагенты
│   │   │   ├── organizations.py # Организации
│   │   │   ├── budget.py        # Бюджет
│   │   │   └── analytics.py     # Аналитика
│   │   ├── core/                # Настройки приложения
│   │   ├── db/                  # База данных
│   │   │   ├── models.py        # SQLAlchemy модели
│   │   │   └── session.py       # Сессии БД
│   │   ├── schemas/             # Pydantic схемы
│   │   └── main.py              # Точка входа FastAPI
│   ├── alembic/                 # Миграции БД
│   ├── scripts/
│   │   └── import_excel.py      # Импорт из Excel
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── api/                 # API клиенты
│   │   │   ├── client.ts        # Axios конфигурация
│   │   │   ├── expenses.ts      # Expenses API
│   │   │   ├── categories.ts    # Categories API
│   │   │   ├── contractors.ts   # Contractors API
│   │   │   └── analytics.ts     # Analytics API
│   │   ├── components/
│   │   │   └── common/
│   │   │       └── AppLayout.tsx # Главный layout
│   │   ├── pages/               # Страницы приложения
│   │   │   ├── DashboardPage.tsx    # Дашборд
│   │   │   ├── ExpensesPage.tsx     # Заявки
│   │   │   ├── BudgetPage.tsx       # Бюджет
│   │   │   ├── AnalyticsPage.tsx    # Аналитика
│   │   │   └── ReferencesPage.tsx   # Справочники
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript типы
│   │   ├── main.tsx             # Точка входа React
│   │   ├── App.tsx              # Главный компонент
│   │   └── index.css            # Глобальные стили
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env
│
├── docker-compose.yml            # Оркестрация контейнеров
├── .gitignore
├── README.md                     # Основная документация
├── QUICKSTART.md                 # Быстрый старт
├── SETUP.md                      # Подробная установка
├── ARCHITECTURE.md               # Архитектура системы
├── ROADMAP.md                    # План развития
└── check_setup.sh                # Проверка готовности

Excel файлы (данные):
├── IT_Budget_Analysis_Full.xlsx  # Аналитика бюджета
├── Бюджет по статьям Отдел IT 2025.xlsx
└── заявки на расходы по дням.xlsx
```

## 🛠️ Технологический стек

### Backend
| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.11+ | Язык программирования |
| FastAPI | 0.104+ | Web framework |
| SQLAlchemy | 2.0 | ORM |
| Alembic | 1.12+ | Миграции БД |
| Pydantic | 2.5+ | Валидация данных |
| PostgreSQL | 15+ | База данных |
| Uvicorn | 0.24+ | ASGI сервер |

### Frontend
| Технология | Версия | Назначение |
|-----------|--------|------------|
| React | 18.2 | UI библиотека |
| TypeScript | 5.2+ | Типизация |
| Vite | 5.0+ | Build tool |
| React Router | 6.20+ | Маршрутизация |
| TanStack Query | 5.12+ | State management |
| Ant Design | 5.11+ | UI компоненты |
| Recharts | 2.10+ | Графики |
| Axios | 1.6+ | HTTP клиент |

### DevOps
| Технология | Назначение |
|-----------|------------|
| Docker | Контейнеризация |
| Docker Compose | Оркестрация |

## 📊 База данных

### Таблицы

1. **budget_categories** - Статьи расходов
   - Типы: OPEX, CAPEX
   - Активность: is_active

2. **contractors** - Контрагенты
   - ИНН, название, контакты

3. **organizations** - Организации
   - ВЕСТ ООО, ВЕСТ ГРУПП ООО

4. **expenses** - Заявки на расходы
   - Номер, сумма, даты
   - Статусы: Черновик, К оплате, Оплачена, Отклонена, Закрыта
   - Связи: категория, контрагент, организация

5. **budget_plans** - Планы бюджета
   - Год, месяц
   - План по CAPEX/OPEX

## 🌐 API Endpoints

### Заявки (Expenses)
```
GET    /api/v1/expenses              # Список с фильтрами
POST   /api/v1/expenses              # Создать
GET    /api/v1/expenses/{id}         # Получить
PUT    /api/v1/expenses/{id}         # Обновить
PATCH  /api/v1/expenses/{id}/status  # Изменить статус
DELETE /api/v1/expenses/{id}         # Удалить
GET    /api/v1/expenses/stats/totals # Статистика
```

### Категории (Categories)
```
GET    /api/v1/categories       # Список
POST   /api/v1/categories       # Создать
GET    /api/v1/categories/{id}  # Получить
PUT    /api/v1/categories/{id}  # Обновить
DELETE /api/v1/categories/{id}  # Удалить
```

### Контрагенты (Contractors)
```
GET    /api/v1/contractors       # Список с поиском
POST   /api/v1/contractors       # Создать
GET    /api/v1/contractors/{id}  # Получить
PUT    /api/v1/contractors/{id}  # Обновить
DELETE /api/v1/contractors/{id}  # Удалить
```

### Организации (Organizations)
```
GET    /api/v1/organizations       # Список
POST   /api/v1/organizations       # Создать
GET    /api/v1/organizations/{id}  # Получить
PUT    /api/v1/organizations/{id}  # Обновить
DELETE /api/v1/organizations/{id}  # Удалить
```

### Бюджет (Budget)
```
GET  /api/v1/budget/plans     # Планы бюджета
POST /api/v1/budget/plans     # Создать план
GET  /api/v1/budget/summary   # План vs Факт
```

### Аналитика (Analytics)
```
GET /api/v1/analytics/dashboard         # Дашборд
GET /api/v1/analytics/budget-execution  # Исполнение по месяцам
GET /api/v1/analytics/by-category       # По категориям
GET /api/v1/analytics/trends            # Тренды
```

## 🎨 Страницы приложения

### 1. Дашборд (`/dashboard`)
- Карточки с метриками
- График CAPEX vs OPEX
- Топ-5 категорий
- Распределение по статусам
- Последние заявки

### 2. Заявки (`/expenses`)
- Таблица с фильтрами
- Поиск
- Создание/редактирование
- Изменение статуса
- Пагинация

### 3. Бюджет (`/budget`)
- Планирование
- План vs Факт
- CAPEX/OPEX разбивка

### 4. Аналитика (`/analytics`)
- Графики и тренды
- Прогнозы
- Экспорт отчетов

### 5. Справочники (`/references`)
- CRUD категорий
- CRUD контрагентов
- CRUD организаций

## 🚀 Запуск проекта

### Вариант 1: Docker (рекомендуется)

```bash
# 1. Запустить контейнеры
docker-compose up -d

# 2. Применить миграции
docker-compose exec backend alembic upgrade head

# 3. Загрузить данные
docker-compose exec backend python scripts/import_excel.py

# 4. Открыть приложение
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Вариант 2: Без Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python scripts/import_excel.py
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📈 Примеры использования

### 1. Получить дашборд за 2025 год
```bash
curl http://localhost:8000/api/v1/analytics/dashboard?year=2025
```

### 2. Получить заявки со статусом "К оплате"
```bash
curl "http://localhost:8000/api/v1/expenses?status=К оплате&limit=10"
```

### 3. Создать новую заявку
```bash
curl -X POST http://localhost:8000/api/v1/expenses \
  -H "Content-Type: application/json" \
  -d '{
    "number": "TEST-001",
    "category_id": 1,
    "organization_id": 1,
    "amount": 10000,
    "request_date": "2025-10-23T00:00:00",
    "status": "Черновик"
  }'
```

## 📊 Статистика проекта

### Код
- **Backend**: ~2000 строк Python кода
- **Frontend**: ~1500 строк TypeScript/React кода
- **Файлов**: ~50
- **API endpoints**: 30+

### Функционал
- ✅ CRUD для 5 сущностей
- ✅ 4 аналитических эндпоинта
- ✅ 5 страниц приложения
- ✅ Фильтры и поиск
- ✅ Графики и диаграммы
- ✅ Импорт из Excel

## 🔒 Безопасность

### Текущие меры
- ✅ CORS защита
- ✅ Pydantic валидация
- ✅ SQLAlchemy (защита от SQL injection)
- ✅ Type safety (TypeScript)

### Планируется
- ⏳ JWT аутентификация
- ⏳ RBAC (роли и права)
- ⏳ Rate limiting
- ⏳ HTTPS

## 📝 Документация

| Файл | Описание |
|------|----------|
| [README.md](README.md) | Основная документация |
| [QUICKSTART.md](QUICKSTART.md) | Быстрый старт |
| [SETUP.md](SETUP.md) | Подробная установка |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура |
| [ROADMAP.md](ROADMAP.md) | План развития |
| API Docs | http://localhost:8000/docs |

## 🎯 Следующие шаги

1. **Запустить проект** (см. QUICKSTART.md)
2. **Изучить данные** на дашборде
3. **Создать тестовую заявку**
4. **Изучить API** в Swagger UI
5. **Настроить под себя** (категории, контрагенты)

## 🐛 Известные ограничения

1. Нет аутентификации (все данные доступны всем)
2. Нет workflow согласования заявок
3. Нельзя загружать файлы к заявкам
4. Базовая аналитика (только графики)
5. Нет мобильной версии

## 💡 Возможности расширения

- Интеграция с 1С
- Email уведомления
- Мобильное приложение
- Machine Learning прогнозы
- Экспорт в Excel/PDF
- Telegram бот
- Workflow согласования
- Multi-tenancy

## 🤝 Вклад в проект

Приветствуются:
- 🐛 Баг репорты
- 💡 Предложения
- 📝 Документация
- 🌍 Переводы
- 🔧 Pull Requests

## 📞 Контакты

- **GitHub**: [ссылка на репозиторий]
- **Email**: [ваш email]
- **Telegram**: [ваш username]

## 📜 Лицензия

MIT License - используйте свободно в коммерческих и личных проектах.

---

**Дата создания**: 23 октября 2025
**Версия**: 0.1.0
**Статус**: ✅ MVP готов к использованию
