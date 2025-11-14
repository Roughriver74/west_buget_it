# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IT Budget Manager** - Full-stack web application for managing IT department budgets with expense tracking, forecasting, payroll management, KPI system, and analytics. Written in Russian for Russian-speaking organizations.

**Stack**: FastAPI + React/TypeScript + PostgreSQL + Docker

## Development Commands

### Deploy server

```bash
ssh root@31.129.107.178
```

**Production deployment**: See [Coolify Setup Guide](docs/COOLIFY_SETUP.md)

**Troubleshooting deployment issues**:
- [Coolify Fix Guide](docs/COOLIFY_FIX.md) - решение проблем с API URL и CORS
- [Auto Proxy Restart Guide](docs/AUTO_PROXY_RESTART.md) - автоматический рестарт Traefik после деплоя
- [Memory Optimization](docs/MEMORY_OPTIMIZATION.md) - решение проблемы потери доступа через 15-20 минут (OOM)
- [Memory Fix Quick Reference](docs/MEMORY_FIX.md) - краткая памятка по проблеме с памятью
- [Traefik 504 Fix](docs/TRAEFIK_504_FIX.md) - исправление периодических ошибок 504 Gateway Timeout

### Quick Start
```bash
./run.sh                    # Start all services (PostgreSQL, Backend, Frontend)
./stop.sh                   # Stop all services
```

### Backend (FastAPI)
```bash
cd backend

# Virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Database migrations
alembic revision --autogenerate -m "Description"  # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback one migration
alembic current                                    # Show current revision

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Admin user creation
python create_admin.py      # Creates admin:admin if not exists

# Testing
pytest                      # Run tests
pytest tests/test_auth.py   # Run specific test file
pytest -v -s                # Verbose with output
```

### Frontend (React + Vite)
```bash
cd frontend

npm install                 # Install dependencies
npm run dev                 # Development server (port 5173)
npm run build               # Production build
npm run preview             # Preview production build
npm run lint                # Run ESLint
npm run lint:fix            # Fix ESLint issues
```

### Database Access
```bash
# PostgreSQL connection
docker exec -it it_budget_db psql -U budget_user -d it_budget_db

# Connection string
postgresql://budget_user:budget_pass@localhost:54329/it_budget_db
```

### Data Import

Система поддерживает **два метода импорта данных**:

#### 1. Unified Import API (Excel файлы) - Рекомендуется
```bash
# 1. Get available entities
curl -X GET "http://localhost:8000/api/v1/import/entities" -H "Authorization: Bearer $TOKEN"

# 2. Download template
curl -X GET "http://localhost:8000/api/v1/import/template/employees?language=ru" \
  -H "Authorization: Bearer $TOKEN" -o template.xlsx

# 3. Preview import (analyze file structure)
curl -X POST "http://localhost:8000/api/v1/import/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F "file=@employees.xlsx"

# 4. Validate data
curl -X POST "http://localhost:8000/api/v1/import/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}' \
  -F "file=@employees.xlsx"

# 5. Execute import
curl -X POST "http://localhost:8000/api/v1/import/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "entity_type=employees" \
  -F 'column_mapping={"ФИО":"full_name","Должность":"position","Оклад":"base_salary"}' \
  -F "file=@employees.xlsx"
```

**Features:**
- ✅ Dynamic data type detection
- ✅ Flexible column mapping
- ✅ Preview before import
- ✅ Detailed validation with row-level errors
- ✅ Multi-language templates (RU/EN)
- ✅ Auto-create related entities

**Supported entities:** budget_categories, contractors, organizations, employees, payroll_plans, expenses, budget_plans, budget_plan_details, revenue_streams, revenue_categories, revenue_plan_details

#### 2. External API (JSON/CSV с токенами) - Для автоматизации
```bash
# Создать API Token в веб-интерфейсе (раздел "API Tokens")

# Import data
curl -X POST "http://localhost:8000/api/v1/external/import/expenses" \
  -H "Authorization: Bearer <api_token>" \
  -H "Content-Type: application/json" \
  -d '[{"amount": 50000, "category_id": 1, "contractor_id": 5, ...}]'

# Export data (JSON or CSV)
curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025&format=csv" \
  -H "Authorization: Bearer <api_token>" -o expenses.csv
```

**Supported operations:**
- ✅ Import: expenses, revenue-actuals, contractors, organizations, budget-categories, payroll-plans
- ✅ Export: expenses, revenue-actuals, budget-plans, employees
- ✅ Reference data: categories, contractors, organizations, revenue-streams, revenue-categories

**Полная документация:**
- 📖 **Подробное руководство:** `docs/API_DATA_IMPORT.md`
- 🚀 **Быстрый старт (RU):** `docs/DATA_IMPORT_QUICKSTART_RU.md`
- 🌐 **Swagger UI:** http://localhost:8000/docs

#### Legacy Scripts (Manual)
```bash
cd backend
python scripts/import_excel.py --file ../IT_Budget_Analysis_Full.xlsx
python scripts/import_planfact_2025.py  # Import plan/fact data for 2025
```

## Critical Architecture Principles

### 🔐 1. JWT Authentication - MANDATORY

**ALL functionality requires JWT authentication.** There are NO public endpoints (except /login, /register, /health).

**Backend Pattern:**
```python
# Every endpoint MUST have this dependency
@router.get("/endpoint")
def get_data(
    current_user: User = Depends(get_current_active_user),  # REQUIRED
    db: Session = Depends(get_db)
):
    pass
```

**Frontend Pattern:**
- All pages wrapped in `<ProtectedRoute>`
- JWT token stored in localStorage
- Automatic token injection via axios interceptors
- See: `frontend/src/components/ProtectedRoute.tsx`

### 🏢 2. Multi-Tenancy - MANDATORY

**ALL data entities MUST have `department_id` foreign key.** This is the foundation of data isolation.

**Database Pattern:**
```python
class YourModel(Base):
    __tablename__ = "your_table"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)  # REQUIRED

    department_rel = relationship("Department")
```

**Backend API Pattern:**
```python
@router.get("/items")
def get_items(
    department_id: Optional[int] = None,  # REQUIRED parameter
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Item)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        # USER sees only their department
        query = query.filter(Item.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER/ADMIN can filter by department
        if department_id:
            query = query.filter(Item.department_id == department_id)

    return query.all()
```

**Frontend Pattern:**
```typescript
// MUST use useDepartment hook
import { useDepartment } from '@/contexts/DepartmentContext'

const MyPage = () => {
  const { selectedDepartment } = useDepartment()  // REQUIRED

  const { data } = useQuery({
    queryKey: ['items', selectedDepartment?.id],  // Include in cache key
    queryFn: () => api.getItems({
      department_id: selectedDepartment?.id       // Pass to API
    })
  })
}
```

### 🎭 3. Role-Based Access Control

Four roles with different access levels:

- **USER**: Full access to all features, but **only sees their own department data** (auto-filtered by backend)
- **MANAGER**: Full access to all features, **can view and filter all departments**
- **ACCOUNTANT**: Access to reference data (categories, contractors, organizations), NDFL calculator
- **ADMIN**: Full system access + user management + department management

**Access Control Flow:**
1. Frontend routes check if user has required role (via `requiredRoles` in `ProtectedRoute`)
2. Backend API filters data by `department_id` based on user role:
   - **USER**: queries automatically filtered to `user.department_id`
   - **MANAGER/ADMIN**: can specify `department_id` parameter to filter or see all departments
3. All data entities have `department_id` for multi-tenancy isolation

Check roles on both backend (API endpoints) and frontend (UI components).

## High-Level Architecture

### Backend Structure (`backend/app/`)
```
api/v1/              # API endpoints (20+ modules)
├── auth.py          # Authentication & JWT
├── expenses.py      # Expense management
├── budget.py        # Budget planning & tracking
├── budget_plan_details.py  # Budget plan versioning & approval
├── forecast.py      # Forecasting & predictions
├── payroll.py       # Payroll & employee management
├── kpi.py           # KPI system for performance bonuses
├── analytics.py     # Analytics & reporting
├── bank_transactions.py  # Bank transactions (NEW v0.6.0) 🏦
├── departments.py   # Department management
├── audit.py         # Audit logging
└── ...              # Other endpoints

db/
├── models.py        # SQLAlchemy models (all entities)
└── session.py       # Database session management

core/
├── config.py        # Settings & configuration
└── security.py      # Security headers & CORS

schemas/             # Pydantic schemas (20+ files)
services/            # Business logic services
middleware/          # Custom middleware (rate limiting)
utils/               # Utilities & logging
```

### Frontend Structure (`frontend/src/`)
```
pages/               # 30+ page components
├── DashboardPage.tsx
├── ExpensesPage.tsx
├── BudgetPlanPage.tsx
├── PayrollPlanPage.tsx
├── KpiManagementPage.tsx
└── ...

components/          # Reusable components
├── common/          # Shared components (AppLayout, etc.)
├── budget/          # Budget-specific components
│   ├── BudgetPlanTable.tsx         # Main budget table with sticky controls
│   ├── BudgetPlanDetailsTable.tsx  # Budget details with versioning
│   ├── EditableCell.tsx            # Inline editing
│   └── CopyPlanModal.tsx           # Copy from previous year
├── expenses/        # Expense-specific components
├── payroll/         # Payroll-specific components
└── ...

contexts/            # React contexts
├── AuthContext.tsx      # Authentication state
└── DepartmentContext.tsx # Department selection

api/                 # API client functions
types/               # TypeScript type definitions
hooks/               # Custom React hooks
```

### Database Schema

**Core entities** (all have `department_id`):
- `departments` - Multi-tenancy foundation
- `users` - Authentication & authorization
- `budget_categories` - Expense categories (OPEX/CAPEX)
- `contractors` - Vendors/suppliers
- `organizations` - Internal organizations
- `expenses` - Expense requests with statuses
- `budget_plans` - Budget planning by month
- `budget_plan_versions` - Version control for budget plans
- `budget_plan_details` - Detailed monthly budget data per category
- `forecast_expenses` - Forecasted expenses
- `employees` - Employee records
- `payroll_plans` - Payroll planning with bonus types
- `payroll_actuals` - Actual payroll payments
- `employee_kpis` - KPI tracking per employee
- `kpi_goals` - KPI goals and targets
- `goal_achievements` - KPI achievement tracking
- `bank_transactions` - Bank statement operations (NEW v0.6.0) 🏦
- `audit_logs` - Audit trail (department_id nullable)
- `attachments` - File attachments (linked via expense_id)

**Key indexes**: All tables have indexes on `department_id` and `is_active` for performance.

## API Structure

**Base URL**: `http://localhost:8000`
**API Prefix**: `/api/v1`
**Documentation**: `/docs` (Swagger), `/redoc` (ReDoc)

### Authentication Flow
1. `POST /api/v1/auth/register` - Register new user
2. `POST /api/v1/auth/login` - Login (returns JWT token)
3. Include `Authorization: Bearer <token>` in all requests
4. Token expires after 30 minutes

### Common Patterns

**Pagination**: Most list endpoints support `skip` and `limit` parameters
**Filtering**: Support for `department_id`, `is_active`, date ranges
**Bulk Operations**: Mass activate/deactivate/delete for reference data
**Excel Export/Import**: Available for categories, contractors, organizations, payroll plans
**Versioning**: Budget plans support versioning with approval workflow

---

## 🏦 Bank Transactions - Подробная документация

### Обзор функционала

**Bank Transactions** - модуль для автоматизации обработки банковских выписок с AI-классификацией и smart-matching.

**Ключевые возможности:**
- ✅ Импорт банковских выписок из Excel (авто-определение колонок)
- ✅ AI-классификация по категориям (keyword matching + исторические данные)
- ✅ Smart-matching с заявками на расход (scoring algorithm)
- ✅ Автоматическое назначение категорий (confidence > 90%)
- ✅ Определение регулярных платежей (подписки, аренда и т.д.)
- ✅ Workflow обработки: NEW → CATEGORIZED → MATCHED → APPROVED
- ✅ Сокращает ручную работу на 80-90% для регулярных операций

### Модель данных (BankTransaction)

```python
class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    # Основная информация
    transaction_date: Date              # Дата операции
    amount: Decimal                     # Сумма
    transaction_type: Enum              # DEBIT (списание) / CREDIT (поступление)

    # Контрагент
    counterparty_name: String           # Наименование контрагента
    counterparty_inn: String(12)        # ИНН контрагента
    counterparty_kpp: String(9)         # КПП
    counterparty_account: String(20)    # Счет контрагента
    counterparty_bank: String(500)      # Банк контрагента
    counterparty_bik: String(9)         # БИК банка

    # Назначение платежа (основа для AI)
    payment_purpose: Text               # Назначение платежа (ключ для классификации)

    # Наша организация
    organization_id: FK(organizations)  # Наша организация
    account_number: String(20)          # Наш счет

    # Банковские реквизиты
    document_number: String(50)         # Номер платежного документа
    document_date: Date                 # Дата документа

    # AI Классификация
    category_id: FK(budget_categories)  # Назначенная статья расходов
    category_confidence: Decimal(5,4)   # Уверенность AI (0-1)
    suggested_category_id: FK           # Предложенная AI категория

    # Smart Matching с заявками
    expense_id: FK(expenses)            # Связанная заявка на расход
    matching_score: Decimal(5,2)        # Степень совпадения (0-100)
    suggested_expense_id: FK            # Предложенная заявка

    # Статус обработки
    status: Enum                        # NEW/CATEGORIZED/MATCHED/APPROVED/NEEDS_REVIEW/IGNORED

    # Регулярные платежи
    is_regular_payment: Boolean         # Признак регулярного платежа
    regular_payment_pattern_id: Int     # ID паттерна

    # Обработка
    notes: Text                         # Примечания финансиста
    reviewed_by: FK(users)              # Кто проверил
    reviewed_at: DateTime               # Когда проверено

    # Multi-tenancy
    department_id: FK(departments)      # ОБЯЗАТЕЛЬНО для multi-tenancy

    # Импорт
    import_source: String               # "FTP" / "MANUAL_UPLOAD" / "API"
    import_file_name: String            # Имя файла
    imported_at: DateTime               # Когда импортировано

    # Интеграция с 1С
    external_id_1c: String(100)         # ID в 1С (unique)
```

### Справочники

#### 1. Типы транзакций (BankTransactionTypeEnum)
```python
DEBIT = "DEBIT"      # Списание (расход) - деньги ушли
CREDIT = "CREDIT"    # Поступление (доход) - деньги пришли
```

#### 2. Статусы обработки (BankTransactionStatusEnum)
```python
NEW = "NEW"                    # 🆕 Новая, не обработана
CATEGORIZED = "CATEGORIZED"    # 📋 Категория назначена (вручную или AI)
MATCHED = "MATCHED"            # 🔗 Связана с заявкой на расход
APPROVED = "APPROVED"          # ✅ Проверена и одобрена финансистом
NEEDS_REVIEW = "NEEDS_REVIEW"  # ⚠️ Требует ручной проверки (низкая уверенность AI)
IGNORED = "IGNORED"            # 🚫 Проигнорирована (не относится к учету)
```

#### 3. Категории расходов (из budget_categories)
Используются существующие категории бюджета:
- **OPEX**: Аренда помещений, Услуги связи, Канцтовары, Хозтовары, и т.д.
- **CAPEX**: Компьютеры и оргтехника, Серверы, Лицензии и т.д.
- **Налоги**: НДФЛ, НДС, Страховые взносы и т.д.

Импорт AI-категорий:
```bash
cd backend
python scripts/import_ai_categories.py
```

### API Endpoints

**Base path**: `/api/v1/bank-transactions`

#### Основные операции
```bash
# Получить список транзакций (с фильтрами)
GET /api/v1/bank-transactions
  ?department_id=1
  &status=NEW
  &transaction_type=DEBIT
  &date_from=2025-01-01
  &date_to=2025-12-31
  &search=Яндекс
  &only_unprocessed=true
  &has_expense=false

# Получить статистику
GET /api/v1/bank-transactions/stats?department_id=1

# Получить одну транзакцию
GET /api/v1/bank-transactions/{id}

# Назначить категорию
PUT /api/v1/bank-transactions/{id}/categorize
{
  "category_id": 15,
  "notes": "Аренда офиса за январь"
}

# Связать с заявкой
PUT /api/v1/bank-transactions/{id}/link
{
  "expense_id": 42
}

# Получить предложенные заявки для связывания
GET /api/v1/bank-transactions/{id}/matching-expenses

# Получить предложенные категории
GET /api/v1/bank-transactions/{id}/category-suggestions

# Массовая категоризация
POST /api/v1/bank-transactions/bulk-categorize
{
  "transaction_ids": [1, 2, 3],
  "category_id": 15
}

# Массовое обновление статуса
POST /api/v1/bank-transactions/bulk-status-update
{
  "transaction_ids": [1, 2, 3],
  "status": "APPROVED"
}

# Получить паттерны регулярных платежей
GET /api/v1/bank-transactions/regular-patterns?department_id=1

# Удалить транзакцию
DELETE /api/v1/bank-transactions/{id}
```

#### Импорт из Excel
```bash
# Импорт банковской выписки
POST /api/v1/bank-transactions/import
  -F "file=@bank_statement.xlsx"
  -F "department_id=1"
  -F "auto_classify=true"
  -F "auto_match=true"

Response:
{
  "total_rows": 150,
  "imported": 148,
  "errors": 2,
  "auto_categorized": 120,
  "auto_matched": 85,
  "needs_review": 28
}
```

### Workflow обработки транзакций

```
1. ИМПОРТ
   ↓
   Excel файл → BankTransactionImporter
   ↓
   Создание записей со статусом NEW

2. AI КЛАССИФИКАЦИЯ (если auto_classify=true)
   ↓
   TransactionClassifier анализирует payment_purpose
   ↓
   - Keyword matching (с весами)
   - Исторические данные (прошлые назначения)
   - Контрагент (по ИНН)
   ↓
   Если confidence > 90% → category_id назначается, статус = CATEGORIZED
   Если confidence < 90% → suggested_category_id, статус = NEEDS_REVIEW

3. SMART MATCHING (если auto_match=true)
   ↓
   Поиск подходящих заявок (expenses) по:
   - Контрагент (ИНН)
   - Сумма (±5%)
   - Дата (±30 дней)
   - Категория
   ↓
   Scoring algorithm (0-100)
   ↓
   Если score > 85 → expense_id назначается, статус = MATCHED
   Если score < 85 → suggested_expense_id

4. ОПРЕДЕЛЕНИЕ РЕГУЛЯРНЫХ ПЛАТЕЖЕЙ
   ↓
   RegularPaymentDetector анализирует:
   - Одинаковые контрагенты
   - Близкие суммы
   - Регулярные интервалы (месяц, квартал)
   ↓
   is_regular_payment = true
   regular_payment_pattern_id = N

5. РУЧНАЯ ПРОВЕРКА
   ↓
   Финансист проверяет:
   - Транзакции со статусом NEEDS_REVIEW
   - Предложения AI (suggested_category_id, suggested_expense_id)
   ↓
   Утверждает или корректирует
   ↓
   Статус = APPROVED

6. ЗАВЕРШЕНИЕ
   ↓
   Транзакция связана с категорией и/или заявкой
   ↓
   Используется для аналитики и отчетов
```

### Интеграция с другими модулями

#### 1. Budget Categories (Категории бюджета)
```python
# Связь: BankTransaction.category_id → BudgetCategory.id
# Используется для классификации расходов

# Пример: найти все транзакции по категории "Аренда"
category = db.query(BudgetCategory).filter_by(name="Аренда помещений").first()
transactions = db.query(BankTransaction).filter_by(category_id=category.id).all()
```

#### 2. Expenses (Заявки на расход)
```python
# Связь: BankTransaction.expense_id → Expense.id
# Связывает оплату с заявкой

# Пример: найти оплату для заявки
expense = db.query(Expense).get(42)
payment = db.query(BankTransaction).filter_by(expense_id=expense.id).first()
```

#### 3. Organizations (Организации)
```python
# Связь: BankTransaction.organization_id → Organization.id
# Определяет нашу организацию (плательщика)

# Пример: все транзакции организации "ООО Вест"
org = db.query(Organization).filter_by(short_name="Вест").first()
transactions = db.query(BankTransaction).filter_by(organization_id=org.id).all()
```

#### 4. Departments (Multi-tenancy)
```python
# Связь: BankTransaction.department_id → Department.id
# ОБЯЗАТЕЛЬНАЯ связь для изоляции данных

# USER видит только свой отдел
if current_user.role == UserRoleEnum.USER:
    query = query.filter(BankTransaction.department_id == current_user.department_id)
```

### Frontend интеграция

**Страница**: `frontend/src/pages/BankTransactionsPage.tsx` (если существует)

**API клиент**: `frontend/src/api/bankTransactions.ts`

```typescript
// Пример использования
import { useDepartment } from '@/contexts/DepartmentContext'
import { useQuery } from '@tanstack/react-query'
import * as bankTransactionsApi from '@/api/bankTransactions'

const BankTransactionsPage = () => {
  const { selectedDepartment } = useDepartment()

  const { data } = useQuery({
    queryKey: ['bank-transactions', selectedDepartment?.id, filters],
    queryFn: () => bankTransactionsApi.getBankTransactions({
      department_id: selectedDepartment?.id,
      only_unprocessed: true
    })
  })

  // Назначение категории
  const handleCategorize = async (transactionId: number, categoryId: number) => {
    await bankTransactionsApi.categorizeTransaction(transactionId, {
      category_id: categoryId
    })
    queryClient.invalidateQueries(['bank-transactions'])
  }
}
```

### Сервисы и утилиты

#### TransactionClassifier (AI-классификация)
**Файл**: `backend/app/services/transaction_classifier.py`

```python
classifier = TransactionClassifier(db, department_id)

# Классифицировать транзакцию
result = classifier.classify_transaction(
    payment_purpose="Оплата за аренду офиса Москва январь 2025",
    amount=150000.0,
    counterparty_inn="7727563778"
)
# → { category_id: 5, confidence: 0.95, reasoning: [...] }

# Предложить категории (топ-3)
suggestions = classifier.suggest_categories(payment_purpose, amount)
# → [{ category_id: 5, confidence: 0.95 }, { category_id: 8, confidence: 0.75 }, ...]
```

**Keyword matching** с весами:
- Точное совпадение (exact): вес 10
- Начало строки (startswith): вес 8
- Содержит (contains): вес 5

**Исторические данные**:
- Анализирует прошлые назначения категорий
- Увеличивает уверенность для повторяющихся паттернов

#### RegularPaymentDetector (Регулярные платежи)
**Файл**: `backend/app/services/transaction_classifier.py`

```python
detector = RegularPaymentDetector(db, department_id)

# Найти регулярные паттерны
patterns = detector.detect_patterns()
# → [{ counterparty_inn, avg_amount, frequency, count, pattern_type: "MONTHLY" }, ...]

# Проверить, является ли транзакция регулярной
is_regular = detector.is_regular_payment(
    counterparty_inn="7727563778",
    amount=50000.0
)
```

#### BankTransactionImporter (Импорт из Excel)
**Файл**: `backend/app/services/bank_transaction_import.py`

```python
importer = BankTransactionImporter(db, department_id, current_user.id)

# Импортировать файл
result = await importer.import_from_excel(
    file_content=file.file.read(),
    auto_classify=True,
    auto_match=True
)
# → BankTransactionImportResult
```

**Авто-определение колонок** (поддерживаемые заголовки):
- Дата: "Дата операции", "Дата", "Date", "Transaction Date"
- Сумма: "Сумма", "Amount", "Sum"
- Контрагент: "Контрагент", "Counterparty", "Наименование"
- ИНН: "ИНН", "INN"
- Назначение: "Назначение платежа", "Purpose", "Description"
- И т.д.

### Ключевые слова для классификации

**Примеры категорий и ключевых слов:**

```python
KEYWORDS = {
    "Аренда помещений": [
        "аренд", "rent", "офис", "помещен", "площад"
    ],
    "Услуги связи": [
        "связь", "интернет", "телефон", "мобильн", "сотов", "МТС", "Билайн", "Мегафон"
    ],
    "Канцтовары": [
        "канцтовар", "бумага", "ручк", "папк", "stationery"
    ],
    "Компьютеры и оргтехника": [
        "компьютер", "ноутбук", "монитор", "клавиатур", "мышь", "laptop", "computer"
    ],
    "Лицензии ПО": [
        "лицензи", "подписк", "subscription", "Microsoft", "Adobe", "1С"
    ],
    "НДФЛ": [
        "НДФЛ", "налог на доходы"
    ],
    "Страховые взносы": [
        "страхов", "взнос", "ПФР", "ФСС", "ФФОМС"
    ]
}
```

### Создание новых полей (Регион, Вид документа)

Если нужно добавить дополнительные поля (например, из импортируемого Excel):

```python
# 1. Добавить enum для справочника
class RegionEnum(str, enum.Enum):
    MOSCOW = "MOSCOW"
    SPB = "SPB"
    REGIONS = "REGIONS"

class DocumentTypeEnum(str, enum.Enum):
    PAYMENT_ORDER = "PAYMENT_ORDER"     # Платежное поручение
    CASH_ORDER = "CASH_ORDER"           # Кассовый ордер
    INVOICE = "INVOICE"                 # Счет

# 2. Добавить поля в модель BankTransaction
region = Column(Enum(RegionEnum), nullable=True, index=True)
document_type = Column(Enum(DocumentTypeEnum), nullable=True)

# 3. Создать миграцию
alembic revision --autogenerate -m "add region and document_type to bank_transactions"
alembic upgrade head

# 4. Обновить Pydantic schemas
class BankTransactionCreate(BaseModel):
    region: Optional[RegionEnum]
    document_type: Optional[DocumentTypeEnum]

# 5. Обновить BankTransactionImporter для маппинга колонок
COLUMN_MAPPING = {
    "Регион": "region",
    "Вид документа": "document_type"
}
```

### Производительность и оптимизация

**Индексы** (уже созданы):
```sql
CREATE INDEX ON bank_transactions(department_id);
CREATE INDEX ON bank_transactions(status);
CREATE INDEX ON bank_transactions(transaction_date);
CREATE INDEX ON bank_transactions(transaction_type);
CREATE INDEX ON bank_transactions(counterparty_inn);
CREATE INDEX ON bank_transactions(category_id);
CREATE INDEX ON bank_transactions(expense_id);
CREATE INDEX ON bank_transactions(is_regular_payment);
CREATE INDEX ON bank_transactions(document_number);
CREATE UNIQUE INDEX ON bank_transactions(external_id_1c);
```

**Оптимизация запросов**:
```python
# Используйте joinedload для загрузки связей
query = db.query(BankTransaction).options(
    joinedload(BankTransaction.category_rel),
    joinedload(BankTransaction.expense_rel),
    joinedload(BankTransaction.organization_rel),
)

# Пагинация обязательна для больших выборок
query = query.offset(skip).limit(min(limit, 500))
```

### Типичные сценарии использования

#### 1. Импорт месячной выписки
```bash
curl -X POST "http://localhost:8000/api/v1/bank-transactions/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@january_2025.xlsx" \
  -F "department_id=1" \
  -F "auto_classify=true" \
  -F "auto_match=true"
```

#### 2. Проверка необработанных транзакций
```bash
curl "http://localhost:8000/api/v1/bank-transactions?only_unprocessed=true" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. Массовое утверждение
```bash
curl -X POST "http://localhost:8000/api/v1/bank-transactions/bulk-status-update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_ids": [1, 2, 3, 4, 5],
    "status": "APPROVED"
  }'
```

#### 4. Поиск регулярных платежей
```bash
curl "http://localhost:8000/api/v1/bank-transactions/regular-patterns?department_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Отладка и логи

```python
# Включить подробное логирование классификатора
import logging
logging.getLogger("app.services.transaction_classifier").setLevel(logging.DEBUG)

# Анализ результатов классификации
classifier = TransactionClassifier(db, department_id)
result = classifier.classify_transaction(payment_purpose, amount, counterparty_inn)
print(f"Category: {result['category_id']}, Confidence: {result['confidence']}")
print(f"Reasoning: {result['reasoning']}")
```

### Тестирование

```bash
# Запуск тестов
pytest tests/test_bank_transactions.py -v

# Тесты для классификатора
pytest tests/test_transaction_classifier.py -v
```

---

## Important Development Patterns

### React Component Best Practices

#### 1. **React Hooks Rules - CRITICAL**
```typescript
// ✅ CORRECT - All hooks BEFORE conditional returns
const MyComponent = () => {
  const [state, setState] = useState()
  const data = useQuery()
  const callback = useCallback(() => {}, [])

  // Conditional returns AFTER all hooks
  if (loading) return <Spinner />
  if (!data) return null

  return <div>...</div>
}

// ❌ WRONG - Hooks after conditional returns
const MyComponent = () => {
  if (loading) return <Spinner />  // NEVER do this!

  const [state, setState] = useState()  // Too late!
}
```

#### 2. **Performance Optimization**
```typescript
// Use useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return data.reduce((sum, item) => sum + item.value, 0)
}, [data])

// Use useCallback for functions passed as props
const handleClick = useCallback((id: number) => {
  doSomething(id)
}, [dependencies])

// Memoize components with React.memo
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{data.map(...)}</div>
})
```

#### 3. **Sticky Positioning Pattern**
```typescript
// For sticky headers/controls in tables
<div style={{
  position: 'sticky',
  top: 64,              // Header offset
  zIndex: 10,           // Above table
  backgroundColor: '#fff',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'
}}>
  {/* Control panel content */}
</div>
```

#### 4. **Ant Design Spin Component**
```typescript
// ✅ CORRECT - Spin with tip requires container
<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
  <Spin size="large" tip="Loading..." />
</div>

// ❌ WRONG - Nested content causes warning
<Spin size="large" tip="Loading...">
  <div style={{ minHeight: 200 }} />
</Spin>
```

#### 5. **Table Scroll Synchronization**
```typescript
// Wait for table to render before scrolling
const scrollToColumn = useCallback((columnIndex: number) => {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      setTimeout(() => {
        const target = tableRef.current
        if (!target) return

        // Verify table is rendered
        const tableBody = target.querySelector('.ant-table-body')
        if (!tableBody) {
          // Retry if not ready
          setTimeout(() => scrollToColumn(columnIndex), 100)
          return
        }

        target.scrollTo({ left: columnOffset, behavior: 'smooth' })
      }, 200)
    })
  })
}, [])
```

### Adding New Feature with Database Entity

1. **Create Model** (`backend/app/db/models.py`):
   ```python
   class NewEntity(Base):
       __tablename__ = "new_entities"

       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(255), nullable=False)
       department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
       is_active = Column(Boolean, default=True, nullable=False, index=True)

       department_rel = relationship("Department", back_populates="new_entities")
   ```

2. **Create Migration**:
   ```bash
   alembic revision --autogenerate -m "add new_entities table"
   alembic upgrade head
   ```

3. **Create Pydantic Schemas** (`backend/app/schemas/`):
   ```python
   class NewEntityCreate(BaseModel):
       name: str
       # Do NOT include department_id - taken from current_user

   class NewEntityInDB(BaseModel):
       id: int
       name: str
       department_id: int  # MUST be present
       is_active: bool
   ```

4. **Create API Endpoint** (`backend/app/api/v1/`):
   ```python
   @router.get("/")
   def get_entities(
       department_id: Optional[int] = None,
       current_user: User = Depends(get_current_active_user),
       db: Session = Depends(get_db)
   ):
       query = db.query(NewEntity)

       if current_user.role == UserRoleEnum.USER:
           query = query.filter(NewEntity.department_id == current_user.department_id)
       elif department_id:
           query = query.filter(NewEntity.department_id == department_id)

       return query.all()
   ```

5. **Create Frontend API Client** (`frontend/src/api/`):
   ```typescript
   export const getEntities = (params: { department_id?: number }) =>
     apiClient.get('/new-entities', { params })
   ```

6. **Create Frontend Page** (`frontend/src/pages/`):
   ```typescript
   const { selectedDepartment } = useDepartment()

   const { data } = useQuery({
     queryKey: ['entities', selectedDepartment?.id],
     queryFn: () => api.getEntities({ department_id: selectedDepartment?.id })
   })
   ```

## Recent Features (v0.5.0+)

### Budget Planning Enhancements
- **Versioning System**: Budget plans support multiple versions with approval workflow
- **Monthly Details**: Detailed budget planning per category and month
- **Status Tracking**: Draft → Pending → Approved workflow
- **Plan Comparison**: Compare different versions side-by-side

### KPI System
- **Goal Management**: Define KPI goals with targets and weights
- **Achievement Tracking**: Track actual vs. target performance
- **Performance Bonuses**: Calculate bonuses based on KPI achievement
- **Monthly/Quarterly Tracking**: Support for different bonus periods

### Payroll Enhancements
- **Bonus Types**: FIXED, PERFORMANCE_BASED, MIXED bonus types
- **KPI Integration**: Link bonuses to KPI achievements
- **Analytics**: Breakdown of salary components (base, bonuses, etc.)

### Bank Transactions (NEW v0.6.0)
- **Import from Excel**: Upload bank statements with auto-column detection
- **AI Classification**: Automatic categorization using keyword matching and historical data
- **Smart Matching**: Find matching expenses with scoring algorithm
- **Auto-categorization**: High confidence (>90%) categories applied automatically
- **Regular Patterns**: Detect recurring payments (subscriptions, rent)
- **Multi-status workflow**: NEW → CATEGORIZED → MATCHED → APPROVED
- **Reduces manual work by 80-90%** for recurring transactions

### Monitoring & Security
- **Sentry Integration**: Error tracking and monitoring
- **Prometheus Metrics**: Performance monitoring
- **Security Headers**: HSTS, CSP, X-Frame-Options
- **HTTPS Enforcement**: Automatic redirect in production
- **Redis Rate Limiting**: Distributed rate limiting

## Configuration

### Backend Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql://budget_user:budget_pass@localhost:54329/it_budget_db

# Security (CHANGE IN PRODUCTION)
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Application
DEBUG=True
APP_NAME="IT Budget Manager"
API_PREFIX=/api/v1

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true

# Redis (Optional - for rate limiting)
REDIS_URL=redis://localhost:6379
```

### Frontend Environment Variables (`.env`)
```bash
VITE_API_URL=http://localhost:8000
VITE_SENTRY_DSN=your-sentry-dsn
```

## Testing Strategy

- USER role: Verify they only see their department
- MANAGER/ADMIN roles: Verify department filtering works
- Test department switching updates all data
- Verify JWT authentication on all protected routes
- Test budget version workflow (draft → pending → approved)
- Test KPI calculations and bonus generation

## Key Files to Reference

**Backend Examples**:
- `backend/app/api/v1/expenses.py` - Complete CRUD with roles & filtering
- `backend/app/api/v1/budget_plan_details.py` - Versioning and approval workflow
- `backend/app/api/v1/kpi.py` - KPI system with calculations
- `backend/app/api/v1/bank_transactions.py` - Bank transactions with AI classification 🏦
- `backend/app/services/transaction_classifier.py` - AI classifier implementation 🏦
- `backend/app/services/bank_transaction_import.py` - Excel import service 🏦
- `backend/app/api/v1/analytics.py` - Complex queries with aggregations
- `backend/app/db/models.py` - All database models

**Frontend Examples**:
- `frontend/src/pages/BudgetPlanPage.tsx` - Budget planning with sticky controls
- `frontend/src/components/budget/BudgetPlanTable.tsx` - Complex table with performance optimization
- `frontend/src/components/budget/BudgetPlanDetailsTable.tsx` - Editable table with memoization
- `frontend/src/pages/KpiManagementPage.tsx` - Complex form with multiple sections
- `frontend/src/components/common/AppLayout.tsx` - Layout & navigation
- `frontend/src/contexts/DepartmentContext.tsx` - Department selection

**Documentation**:
- `docs/DEVELOPMENT_PRINCIPLES.md` - Mandatory security & architecture rules
- `docs/MULTI_TENANCY_ARCHITECTURE.md` - Multi-tenancy implementation details
- `docs/BANK_TRANSACTIONS_STATUSES.md` - Bank transaction statuses reference 🏦
- `docs/BANK_TRANSACTIONS_KEYWORDS.md` - AI classification keywords reference 🏦
- `docs/BANK_TRANSACTIONS_IMPORT_GUIDE.md` - Complete import guide 🏦
- `ROADMAP.md` - Project history and future plans
- `README.md` - Quick start guide

## Common Scripts

Located in `backend/scripts/`:
- `import_excel.py` - Import budget data from Excel
- `import_planfact_2025.py` - Import plan/fact data for specific year
- `import_ai_categories.py` - Import AI classifier categories into budget_categories table
- `create_admin.py` - Create admin user
- Various utility scripts for data management

### Import AI Categories
```bash
cd backend
python scripts/import_ai_categories.py
```
This script imports all categories from AI classifier (TransactionClassifier) into the budget_categories table:
- **OPEX categories**: Аренда помещений, Услуги связи, Канцтовары, etc.
- **CAPEX categories**: Компьютеры и оргтехника, Серверы и сетевое оборудование, etc.
- **Tax categories**: НДФЛ, НДС, Страховые взносы, etc.

You can import for all departments or select specific department.

## Docker Services

Defined in `docker-compose.yml`:
- **db**: PostgreSQL 15 (port 54329)
- **backend**: FastAPI (port 8000)
- **frontend**: React/Vite (port 5173)
- **redis**: Redis (port 6379) - Optional, for rate limiting

## Security Notes

⚠️ **PRODUCTION REQUIREMENTS**:
- Change `SECRET_KEY` to strong random value (min 32 chars)
- Set `DEBUG=False`
- Configure proper CORS origins
- Use HTTPS
- Review rate limiting settings
- Enable Redis for distributed rate limiting
- Configure Sentry for error tracking
- Set up proper database backups

## Debugging

**Backend logs**: `tail -f backend.log`
**Frontend logs**: `tail -f frontend.log`
**Process IDs**: Check `backend.pid`, `frontend.pid`

**Common Issues**:
- React hooks order errors: Ensure all hooks are called before conditional returns
- Table scroll issues: Use double requestAnimationFrame + setTimeout for table rendering
- Ant Design warnings: Check prop usage in documentation
- Performance issues: Use React DevTools Profiler to identify slow components

## Known Limitations

- File uploads limited to 10MB
- Excel import limited to specific formats
- Token refresh not implemented (requires re-login after 30 min)
- Some advanced KPI calculations may require optimization for large datasets
