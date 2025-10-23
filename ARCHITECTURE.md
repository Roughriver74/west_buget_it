# Архитектура IT Budget Manager

## 📐 Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                         ПОЛЬЗОВАТЕЛЬ                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │   Expenses   │  │  Analytics   │          │
│  │    Page      │  │     Page     │  │     Page     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │           React Query (State Management)          │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │              API Client (Axios)                   │          │
│  └────────────────────┬─────────────────────────────┘          │
└─────────────────────────┼────────────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│                                                                  │
│  ┌─────────────────── API Routes ──────────────────┐           │
│  │  /expenses  /categories  /budget  /analytics    │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       │                                          │
│  ┌────────────────── Services ─────────────────────┐           │
│  │     Business Logic & Data Processing            │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       │                                          │
│  ┌─────────────── ORM (SQLAlchemy) ────────────────┐           │
│  │        Models, Schemas, Relationships            │           │
│  └────────────────────┬─────────────────────────────┘           │
└─────────────────────────┼────────────────────────────────────────┘
                          │ SQL
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE (PostgreSQL)                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   expenses   │  │  categories  │  │ contractors  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ organizations│  │ budget_plans │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## 🗃️ Модель данных

### Основные сущности

```
BudgetCategory (Статьи расходов)
├── id: int (PK)
├── name: string (unique)
├── type: OPEX | CAPEX
├── description: text
└── is_active: boolean

Contractor (Контрагенты)
├── id: int (PK)
├── name: string
├── inn: string (unique)
├── contact_info: text
└── is_active: boolean

Organization (Организации)
├── id: int (PK)
├── name: string (unique)
├── legal_name: string
└── is_active: boolean

Expense (Заявки на расходы)
├── id: int (PK)
├── number: string (unique)
├── category_id: int (FK -> BudgetCategory)
├── contractor_id: int (FK -> Contractor)
├── organization_id: int (FK -> Organization)
├── amount: decimal
├── request_date: datetime
├── payment_date: datetime
├── status: Черновик | К оплате | Оплачена | Отклонена | Закрыта
├── is_paid: boolean
├── comment: text
└── requester: string

BudgetPlan (Планы бюджета)
├── id: int (PK)
├── year: int
├── month: int
├── category_id: int (FK -> BudgetCategory)
├── planned_amount: decimal
├── capex_planned: decimal
└── opex_planned: decimal
```

### Связи между таблицами

```
BudgetCategory ──┬── 1:N ──> Expense
                 └── 1:N ──> BudgetPlan

Contractor ────── 1:N ──> Expense

Organization ──── 1:N ──> Expense
```

## 🔄 Потоки данных

### 1. Загрузка дашборда

```
User → Frontend → GET /api/v1/analytics/dashboard
                      ↓
                   FastAPI → analyticsApi.getDashboard()
                      ↓
                   SQLAlchemy → aggregates data from:
                      - expenses
                      - budget_plans
                      - categories
                      ↓
                   PostgreSQL → executes queries
                      ↓
                   FastAPI → formats response
                      ↓
                   Frontend → React Query cache
                      ↓
                   Dashboard Page → renders charts
```

### 2. Создание заявки

```
User fills form → ExpenseForm component
                      ↓
                   POST /api/v1/expenses
                      ↓
                   FastAPI validates (Pydantic)
                      ↓
                   SQLAlchemy creates Expense
                      ↓
                   PostgreSQL inserts row
                      ↓
                   FastAPI returns created expense
                      ↓
                   React Query invalidates cache
                      ↓
                   ExpensesList re-fetches data
```

### 3. Фильтрация заявок

```
User changes filters → ExpensesPage state updates
                      ↓
                   React Query re-fetches:
                   GET /api/v1/expenses?status=...&category_id=...
                      ↓
                   FastAPI applies filters
                      ↓
                   SQLAlchemy builds WHERE clause
                      ↓
                   PostgreSQL executes query
                      ↓
                   FastAPI paginates results
                      ↓
                   Frontend updates table
```

## 🏗️ Технологический стек

### Backend
```
FastAPI 0.104+          # Web framework
├── Uvicorn             # ASGI server
├── SQLAlchemy 2.0      # ORM
├── Alembic             # Migrations
├── Pydantic 2.5        # Validation
└── psycopg2            # PostgreSQL driver
```

### Frontend
```
React 18                # UI library
├── TypeScript          # Type safety
├── Vite 5             # Build tool
├── React Router 6      # Routing
├── TanStack Query 5    # State management
├── Ant Design 5        # UI components
└── Recharts 2          # Charts
```

### Database
```
PostgreSQL 15
├── JSON support        # Flexible data
├── Window functions    # Analytics
└── Full-text search    # Search capabilities
```

### DevOps
```
Docker & Docker Compose
├── PostgreSQL container
├── Backend container
└── Frontend container
```

## 📊 API Структура

### REST Endpoints

```
/api/v1
├── /expenses
│   ├── GET    /               # List with filters
│   ├── POST   /               # Create
│   ├── GET    /{id}           # Get by ID
│   ├── PUT    /{id}           # Update
│   ├── PATCH  /{id}/status    # Update status
│   └── DELETE /{id}           # Delete
│
├── /categories
│   ├── GET    /               # List
│   ├── POST   /               # Create
│   ├── GET    /{id}           # Get
│   ├── PUT    /{id}           # Update
│   └── DELETE /{id}           # Delete
│
├── /contractors
│   └── ... (same CRUD)
│
├── /organizations
│   └── ... (same CRUD)
│
├── /budget
│   ├── GET    /plans          # Budget plans
│   ├── POST   /plans          # Create plan
│   └── GET    /summary        # Plan vs Actual
│
└── /analytics
    ├── GET    /dashboard      # Dashboard data
    ├── GET    /budget-execution  # Monthly execution
    ├── GET    /by-category    # Category analytics
    └── GET    /trends         # Spending trends
```

## 🔐 Безопасность (для будущего)

### Текущее состояние
- Базовая CORS защита
- Валидация входных данных (Pydantic)

### Планируется
- JWT аутентификация
- Роли и права доступа
- Rate limiting
- SQL injection защита (SQLAlchemy)
- XSS защита (React)

## 🚀 Масштабирование

### Горизонтальное
- Backend: множественные инстансы за Load Balancer
- Frontend: CDN для статики
- Database: Read replicas

### Вертикальное
- Увеличение ресурсов контейнеров
- Оптимизация запросов
- Индексы в PostgreSQL

## 📈 Мониторинг и логирование

### Будущие улучшения
- Prometheus + Grafana для метрик
- ELK stack для логов
- Sentry для ошибок
- Health checks

## 🔄 CI/CD Pipeline (планируется)

```
Git Push → GitHub Actions
    ↓
  Linting & Tests
    ↓
  Build Docker images
    ↓
  Push to Registry
    ↓
  Deploy to Server
    ↓
  Health Check
```

## 📝 Соглашения о коде

### Backend (Python)
- PEP 8 style guide
- Type hints everywhere
- Docstrings for functions
- Black formatter

### Frontend (TypeScript)
- ESLint rules
- Prettier formatting
- Named exports
- Functional components

### Git
- Conventional commits
- Feature branches
- Pull requests
- Code reviews
