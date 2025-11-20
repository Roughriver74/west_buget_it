# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IT Budget Manager** - Enterprise-grade full-stack web application for comprehensive financial management with expense/revenue tracking, forecasting, payroll, KPI system, credit portfolio management, AI-powered automation, and 1C integration. Written in Russian for Russian-speaking organizations.

**Stack**: FastAPI + React/TypeScript + PostgreSQL + Docker + Redis + APScheduler

**Key Features**:
- 💰 Budget planning & expense management (OPEX/CAPEX)
- 📈 Revenue budget with seasonality & customer LTV
- 🏦 AI bank transaction classification & matching
- 💼 Credit portfolio management with FTP auto-import
- 🧾 AI invoice OCR processing (Tesseract + GPT-4o)
- 👔 Founder dashboard with cross-department KPIs
- 🔄 1C OData integration (expenses, catalogs, transactions)
- ⏰ Background automation (APScheduler)
- 👥 Payroll & KPI-based bonuses
- 🔐 Multi-tenancy & role-based access (5 roles)
- 📊 Advanced analytics & forecasting
- 🎛️ **Modular architecture** with license-level feature control (NEW)

## 🎛️ Module System - Feature Access Control

**Module System** - централизованная система управления доступом к функциям приложения на уровне организации.

### Архитектура

```
Backend API Protection ──┐
                         ├──> Module Access Control
Frontend UI Hiding   ────┘
```

### Доступные модули

| Code | Name | Description |
|------|------|-------------|
| `BUDGET_CORE` | Базовый модуль | Основной функционал (всегда включен) |
| `AI_FORECAST` | AI прогнозирование | Bank transactions + AI classification |
| `CREDIT_PORTFOLIO` | Кредитный портфель | Финансовый портфель + FTP import |
| `REVENUE_BUDGET` | Бюджет доходов | Планирование доходов + LTV метрики |
| `PAYROLL_KPI` | KPI и бонусы | Система KPI для сотрудников |
| `INTEGRATIONS_1C` | Интеграция с 1С | OData синхронизация |
| `FOUNDER_DASHBOARD` | Дашборд учредителя | Executive dashboard |
| `ADVANCED_ANALYTICS` | Расширенная аналитика | Продвинутые отчеты |
| `MULTI_DEPARTMENT` | Мультиотдельность | Управление отделами |

### Backend: Защита API

```python
from app.core.module_guard import require_module

@router.get("/credit-portfolio/contracts")
def get_contracts(
    module_access = Depends(require_module("CREDIT_PORTFOLIO")),  # ← Module check
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()
```

### Frontend: Условный рендеринг

```typescript
import { useModules } from '@/contexts/ModulesContext'
import { ModuleGate } from '@/components/common/ModuleGate'

// Вариант 1: Hook
const { hasModule } = useModules()
if (hasModule('CREDIT_PORTFOLIO')) {
  return <CreditPortfolioWidget />
}

// Вариант 2: Component
<ModuleGate moduleCode="AI_FORECAST">
  <AiForecastFeature />
</ModuleGate>

// Вариант 3: HOC
export default ModuleGuard(CreditPortfolioPage, 'CREDIT_PORTFOLIO')
```

### API для управления модулями (ADMIN только)

```bash
# Включить модуль для организации
POST /api/v1/modules/enable
{
  "module_code": "CREDIT_PORTFOLIO",
  "organization_id": 1,
  "expires_at": "2026-12-31T23:59:59Z",
  "limits": { "max_contracts": 100 }
}

# Отключить модуль
POST /api/v1/modules/disable
{
  "module_code": "CREDIT_PORTFOLIO",
  "organization_id": 1
}

# Получить включенные модули
GET /api/v1/modules/enabled/my
```

### Быстрый старт

```bash
# 1. Загрузить модули в БД
cd backend
python scripts/seed_modules.py

# 2. Включить модуль для организации (через SQL)
INSERT INTO organization_modules (organization_id, module_id, is_active)
SELECT 1, id, true FROM modules WHERE code = 'AI_FORECAST';

# 3. Frontend автоматически скроет/покажет элементы
# 4. Backend автоматически защитит API endpoints
```

**Полная документация**: [docs/MODULES.md](docs/MODULES.md)

**Ключевые файлы**:
- Backend: `backend/app/services/module_service.py`, `backend/app/core/module_guard.py`
- Frontend: `frontend/src/contexts/ModulesContext.tsx`, `frontend/src/components/common/ModuleGate.tsx`
- DB Models: `backend/app/db/models.py` (Module, OrganizationModule, ModuleEvent, FeatureLimit)
- Seed: `backend/scripts/seed_modules.py`

---

## Development Commands

### Deploy server

```bash
ssh root@31.129.107.178
```


**Troubleshooting deployment issues**:

Для решения проблем с деплоем обращайтесь к логам и используйте стандартные инструменты диагностики.

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
python scripts/import_plan_fact_2025.py  # Import plan/fact data for 2025
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

Five roles with different access levels:

- **USER**: Full access to all features, but **only sees their own department data** (auto-filtered by backend)
- **MANAGER**: Full access to all features, **can view and filter all departments**
- **ACCOUNTANT**: Access to reference data (categories, contractors, organizations), NDFL calculator
- **FOUNDER**: Executive dashboard with cross-department KPIs and high-level financial metrics (read-only access to all departments)
- **ADMIN**: Full system access + user management + department management

**Access Control Flow:**
1. Frontend routes check if user has required role (via `requiredRoles` in `ProtectedRoute`)
2. Backend API filters data by `department_id` based on user role:
   - **USER**: queries automatically filtered to `user.department_id`
   - **MANAGER/ADMIN/FOUNDER**: can specify `department_id` parameter to filter or see all departments
3. All data entities have `department_id` for multi-tenancy isolation

Check roles on both backend (API endpoints) and frontend (UI components).

## High-Level Architecture

### Backend Structure (`backend/app/`)
```
api/v1/              # API endpoints (40 modules)
├── auth.py          # Authentication & JWT
├── expenses.py      # Expense management
├── budget.py        # Budget planning & tracking
├── budget_plan_details.py  # Budget plan versioning & approval
├── forecast.py      # Forecasting & predictions
├── payroll.py       # Payroll & employee management
├── kpi.py           # KPI system for performance bonuses
├── analytics.py     # Analytics & reporting
├── bank_transactions.py  # Bank transactions (NEW v0.6.0) 🏦
├── credit_portfolio.py  # Credit portfolio management (NEW v0.8.0) 💰
├── revenue_*.py     # Revenue budget modules (8 files, NEW v0.8.0) 📈
├── invoice_processing.py  # AI invoice OCR & processing (NEW) 🧾
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
pages/               # 56 page components
├── DashboardPage.tsx
├── ExpensesPage.tsx
├── BudgetPlanPage.tsx
├── PayrollPlanPage.tsx
├── KpiManagementPage.tsx
├── CreditPortfolioPage.tsx  # Credit portfolio (NEW v0.8.0) 💰
├── RevenueStreamsPage.tsx   # Revenue budget (NEW v0.8.0) 📈
├── FounderDashboardPage.tsx # Founder dashboard (NEW) 👔
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
- `bank_transactions` - Bank statement operations (v0.6.0) 🏦
- `business_operation_mappings` - AI classification rules (v0.7.0) ⚙️
- `audit_logs` - Audit trail (department_id nullable)
- `attachments` - File attachments (linked via expense_id)

**Credit Portfolio entities** (NEW v0.8.0) 💰:
- `fin_organizations` - Financial organizations
- `fin_bank_accounts` - Bank accounts
- `fin_contracts` - Credit contracts
- `fin_receipts` - Receipts
- `fin_expenses` - Financial expenses
- `fin_expense_details` - Expense line items
- `fin_import_logs` - FTP import logs

**Revenue Budget entities** (NEW v0.8.0) 📈:
- `revenue_streams` - Revenue sources (products/services)
- `revenue_categories` - Revenue categories
- `revenue_plans` - Revenue planning (main table)
- `revenue_plan_versions` - Version control with approval
- `revenue_plan_details` - Monthly revenue details
- `revenue_actuals` - Actual revenue records
- `customer_metrics` - Customer LTV and churn risk
- `seasonality_coefficients` - Seasonal adjustments

**Invoice Processing entities** (NEW) 🧾:
- `processed_invoices` - OCR + AI parsed invoices

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

# Пример: все транзакции организации "ООО Демо"
org = db.query(Organization).filter_by(short_name="Демо").first()
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

### ⚙️ Business Operation Mappings - Визуальное управление маппингами

**UI для управления маппингами хозяйственных операций** (NEW v0.7.0)

**Доступ**: ADMIN и MANAGER только

**Путь**: `/business-operation-mappings`

**Меню**: Справочники → Маппинг операций

**Ключевые возможности:**
- ✅ Визуальное создание/редактирование/удаление маппингов
- ✅ Фильтрация и поиск по операциям
- ✅ Массовые операции (активация/деактивация/удаление)
- ✅ Настройка приоритетов и уверенности через UI
- ✅ Выбор категорий из dropdown с поиском
- ✅ Статистика и пагинация
- ✅ Интеграция с AI-классификатором

**Структура UI:**
```
┌────────────────────────────────────────────────────────┐
│  📊 Статистика                                         │
│  [Всего: 51] [Активных: 48] [Неактивных: 3]          │
│                                                        │
│  🔍 Фильтры                                           │
│  [Поиск...] [Статус ▼] [+ Создать маппинг]          │
│                                                        │
│  📋 Таблица маппингов                                 │
│  ┌──────────────┬──────────┬────────┬──────────┬───┐ │
│  │ Операция     │ Категория│ Приор. │ Уверен.  │ ✎ │ │
│  ├──────────────┼──────────┼────────┼──────────┼───┤ │
│  │ОплатаПоставщ │Закупки   │ 90     │ ████ 95% │ ✎ │ │
│  │ВыплатаЗарплат│Зарплата  │ 100    │ █████98% │ ✎ │ │
│  └──────────────┴──────────┴────────┴──────────┴───┘ │
└────────────────────────────────────────────────────────┘
```

**API эндпоинты:**
- `GET /api/v1/business-operation-mappings/` - Список
- `POST /api/v1/business-operation-mappings/` - Создать
- `PUT /api/v1/business-operation-mappings/{id}` - Обновить
- `DELETE /api/v1/business-operation-mappings/{id}` - Удалить
- `POST /api/v1/business-operation-mappings/bulk-activate` - Массовая активация
- `POST /api/v1/business-operation-mappings/bulk-deactivate` - Массовая деактивация
- `POST /api/v1/business-operation-mappings/bulk-delete` - Массовое удаление

**Компоненты:**
- `frontend/src/pages/BusinessOperationMappingsPage.tsx` - Основная страница
- `frontend/src/components/businessOperationMappings/BusinessOperationMappingFormModal.tsx` - Форма
- `frontend/src/api/businessOperationMappings.ts` - API клиент
- `backend/app/api/v1/business_operation_mappings.py` - API endpoints

**Документация:**
- 📖 [UI Руководство](docs/BUSINESS_OPERATION_MAPPING_UI.md) - Подробное руководство по использованию UI
- 📖 [Техническая документация](docs/BUSINESS_OPERATION_MAPPING.md) - Архитектура и API

**Пример использования:**
```bash
# 1. Открыть UI: http://localhost:5173/business-operation-mappings
# 2. Нажать "Создать маппинг"
# 3. Заполнить форму:
#    - Операция: ОплатаПоставщику
#    - Категория: Закупки у поставщиков
#    - Приоритет: 90
#    - Уверенность: 95%
# 4. Сохранить
# → Теперь все транзакции с этой операцией автоматически категоризируются
```

---

## 💼 Expense Requests - Синхронизация заявок на расход из 1С

### Обзор функционала

**Expense Requests Sync** - автоматическая синхронизация заявок на расходование денежных средств из 1С через OData API.

**Ключевые возможности:**
- ✅ Синхронизация заявок из 1С (Document_ЗаявкаНаРасходованиеДенежныхСредств)
- ✅ Автоматическое создание организаций и контрагентов из 1С
- ✅ Предотвращение дубликатов через external_id_1c
- ✅ Маппинг статусов документов 1С → IT Budget Manager
- ✅ Batch processing с пагинацией для больших объемов
- ✅ Поддержка фильтрации по проведенным/непроведенным документам

### Архитектура

```
1C OData API (Document_ЗаявкаНаРасходованиеДенежныхСредств)
    ↓
OData1CClient.get_expense_requests()
    ↓
Expense1CSync.sync_expenses()
    ↓
    ├─ Маппинг полей 1С → Expense
    ├─ Auto-create Organizations
    ├─ Auto-create Contractors
    └─ Create/Update Expenses
    ↓
Database (expenses, organizations, contractors)
```

### Модель данных

**Поле external_id_1c в Expense**:
- Хранит `Ref_Key` из 1С (уникальный GUID документа)
- Используется для предотвращения дубликатов
- Indexed для быстрого поиска

### API Endpoint

**POST /api/v1/expenses/sync/1c** (ADMIN/MANAGER only)

```bash
# Синхронизация заявок за ноябрь 2025
curl -X POST "http://localhost:8000/api/v1/expenses/sync/1c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-11-01T00:00:00",
    "date_to": "2025-11-30T23:59:59",
    "department_id": 1,
    "only_posted": true
  }'

# Response
{
  "success": true,
  "message": "Sync completed",
  "statistics": {
    "total_fetched": 150,
    "total_processed": 148,
    "total_created": 120,
    "total_updated": 28,
    "total_skipped": 0,
    "errors": [],
    "success": true
  },
  "department": {
    "id": 1,
    "name": "IT Department"
  }
}
```

### Маппинг полей 1С → IT Budget Manager

| 1C Field                | Expense Field      | Описание                                      |
|-------------------------|--------------------|-----------------------------------------------|
| `Ref_Key`               | `external_id_1c`   | Уникальный GUID документа                     |
| `Number`                | `number`           | Номер документа (например: "ВЛ0В-000203")    |
| `Date`                  | `request_date`     | Дата документа                                |
| `ДатаПлатежа`           | `payment_date`     | Дата платежа                                  |
| `СуммаДокумента`        | `amount`           | Сумма документа                               |
| `Организация_Key`       | `organization_id`  | GUID организации (auto-create)                |
| `Контрагент_Key`        | `contractor_id`    | GUID контрагента (auto-create)                |
| `НазначениеПлатежа`     | `comment`          | Полное назначение платежа                     |
| `Posted` + `Статус`     | `status`           | См. маппинг статусов ниже                     |

### Маппинг статусов

| 1C Статус      | 1C Posted | IT Budget Status | is_paid | is_closed |
|----------------|-----------|------------------|---------|-----------|
| `вс_Оплачена`  | Any       | `PAID`           | `true`  | `true`    |
| Any            | `true`    | `PENDING`        | `false` | `false`   |
| Any            | `false`   | `DRAFT`          | `false` | `false`   |

### Сервисы

**OData1CClient** (`backend/app/services/odata_1c_client.py`):
```python
# Получить заявки на расход из 1С
expense_docs = client.get_expense_requests(
    date_from=date(2025, 11, 1),
    date_to=date(2025, 11, 30),
    top=100,
    skip=0,
    only_posted=True
)

# Получить организацию по GUID
org_data = client.get_organization_by_key(org_guid)

# Получить контрагента по GUID
contractor_data = client.get_counterparty_by_key(contractor_guid)
```

**Expense1CSync** (`backend/app/services/expense_1c_sync.py`):
```python
from app.services.expense_1c_sync import Expense1CSync

# Create sync service
sync_service = Expense1CSync(
    db=db,
    odata_client=odata_client,
    department_id=1
)

# Run sync
result = sync_service.sync_expenses(
    date_from=date(2025, 11, 1),
    date_to=date(2025, 11, 30),
    batch_size=100,
    only_posted=True
)

print(result.to_dict())
```

### Тестирование

**Тестовый скрипт** (`backend/scripts/test_1c_expense_sync.py`):
```bash
cd backend
python scripts/test_1c_expense_sync.py
```

Выполняет:
1. ✅ Проверку подключения к 1С OData
2. ✅ Получение образцов документов (5 шт)
3. ✅ Вывод структуры полей для проверки маппинга
4. ✅ Валидацию обязательных полей
5. ✅ Тест получения организаций/контрагентов из 1С

### Environment Variables

```bash
# 1C OData Configuration (в .env)
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28
```

### Производительность

**Batch Processing**:
- Батчи по 100 документов (настраивается)
- Коммит после каждого батча
- Снижение нагрузки на память

**Pagination**:
- OData limit: max 1000 записей
- Автоматическая пагинация через `$skip`
- Защита от бесконечного цикла

**Duplicate Prevention**:
```sql
-- Проверка по external_id_1c
SELECT * FROM expenses
WHERE external_id_1c = 'a1810a57-b6eb-11f0-ad7f-74563c634acb'
  AND department_id = 1;
```

### Database Migration

```bash
# Migration file: 2025_11_16_1531-158ce187a936_add_external_id_1c_to_expenses_for_1c_.py
cd backend
alembic upgrade head
```

```sql
-- Add external_id_1c field to expenses
ALTER TABLE expenses ADD COLUMN external_id_1c VARCHAR(100);
CREATE INDEX ix_expenses_external_id_1c ON expenses(external_id_1c);
```

### Workflow синхронизации

```
1. ПОДКЛЮЧЕНИЕ К 1С
   ↓
   OData1CClient → test_connection()

2. ПОЛУЧЕНИЕ ДОКУМЕНТОВ
   ↓
   get_expense_requests(date_from, date_to, batch_size)
   ↓
   Пагинация (skip += batch_size)

3. ОБРАБОТКА ДОКУМЕНТА
   ↓
   Проверка external_id_1c → existing_expense?
   ↓
   ├─ Нет → Создать новый
   │   ├─ Get/Create Organization
   │   ├─ Get/Create Contractor
   │   └─ Create Expense
   │
   └─ Да → Обновить существующий
       └─ Update fields if changed

4. КОММИТ БАТЧА
   ↓
   db.commit() после каждых 100 документов

5. СТАТИСТИКА
   ↓
   Return Expense1CSyncResult
```

### Логирование

```python
import logging

# Enable debug logging
logging.getLogger("app.services.expense_1c_sync").setLevel(logging.DEBUG)
logging.getLogger("app.services.odata_1c_client").setLevel(logging.DEBUG)
```

### Частые сценарии

#### 1. Первичная синхронизация за год
```bash
curl -X POST "http://localhost:8000/api/v1/expenses/sync/1c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-01-01T00:00:00",
    "date_to": "2025-12-31T23:59:59",
    "department_id": 1,
    "only_posted": true
  }'
```

#### 2. Регулярная синхронизация (за текущий месяц)
```bash
# Можно настроить через cron
curl -X POST "http://localhost:8000/api/v1/expenses/sync/1c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-11-01T00:00:00",
    "date_to": "2025-11-30T23:59:59",
    "department_id": 1,
    "only_posted": false
  }'
```

#### 3. Проверка синхронизированных заявок
```sql
-- Проверить синхронизированные заявки
SELECT
  id,
  number,
  request_date,
  amount,
  status,
  external_id_1c,
  created_at
FROM expenses
WHERE external_id_1c IS NOT NULL
ORDER BY created_at DESC
LIMIT 100;

-- Проверить созданные организации
SELECT id, short_name, inn, external_id_1c
FROM organizations
WHERE external_id_1c IS NOT NULL;

-- Проверить созданных контрагентов
SELECT id, name, inn, external_id_1c
FROM contractors
WHERE external_id_1c IS NOT NULL;
```

### Troubleshooting

**Connection Error**:
```
Failed to connect to 1C OData service
```
→ Проверьте URL, credentials, сетевой доступ

**Missing Required Fields**:
```
Missing or invalid Ref_Key
```
→ Документ в 1С имеет некорректную структуру

**Organization/Contractor Not Found**:
```
Organization {guid} not found in 1C
```
→ GUID есть в документе, но не найден в справочнике 1С

### Future Enhancements

- [ ] Scheduled sync (ежедневная/ежечасная через cron)
- [ ] Webhook от 1С при изменении документов
- [ ] Двусторонняя синхронизация (обновление статуса в 1С при оплате)
- [ ] Синхронизация табличной части (РасшифровкаПлатежа)
- [ ] Авто-категоризация на основе СтатьяРасходов из 1С
- [ ] Связывание с банковскими транзакциями для auto-matching

**Полная документация**: [1C Expense Requests Sync Guide](docs/1C_EXPENSE_REQUESTS_SYNC.md)

### 🔄 1C Catalog Synchronization - Синхронизация справочников

Помимо синхронизации заявок, система также поддерживает **автоматическую синхронизацию справочников** из 1С.

**Синхронизируемые сущности:**

#### 1. Organizations (Справочник_Организации)
```bash
POST /api/v1/sync-1c/organizations/sync
```
- Автоматическое создание/обновление организаций
- Поля: наименование, ИНН, КПП, юридический адрес
- external_id_1c для предотвращения дубликатов

#### 2. Budget Categories (Справочник_СтатьиРасходов)
```bash
POST /api/v1/sync-1c/categories/sync
```
- Синхронизация категорий бюджета
- Иерархическая структура (родитель-потомок)
- Типы: OPEX, CAPEX, Tax

#### 3. Contractors (Справочник_Контрагенты)
```bash
POST /api/v1/sync-1c/contractors/sync
```
- Контрагенты (поставщики, подрядчики)
- ИНН, КПП, банковские реквизиты

#### 4. Bank Transactions (Документ_ОперацииПоСчету)
```bash
POST /api/v1/sync-1c/bank-transactions/sync
```
- Банковские операции из 1С
- Автоматическая категоризация
- Связывание с expense requests

**Сервисы:**
- `Catalog1CSync` (`backend/app/services/catalog_1c_sync.py`)
- `Category1CSync` (`backend/app/services/category_1c_sync.py`)
- `Organization1CSync` (`backend/app/services/organization_1c_sync.py`)

**Автоматизация через APScheduler:**
```python
# Daily sync (midnight)
@scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
async def sync_1c_catalogs_daily():
    await catalog_sync.sync_organizations()
    await catalog_sync.sync_categories()
    await catalog_sync.sync_contractors()
```

**Документация:**
- 📖 [1C Catalog Sync Guide](docs/1C_CATALOG_SYNC.md)
- 📖 [1C Catalog Sync Cron](docs/1C_CATALOG_SYNC_CRON.md)
- 📖 [1C OData Integration](docs/1C_ODATA_INTEGRATION.md)

---

## 💰 Credit Portfolio Management - Финансовый портфель для ФИН отдела

### Обзор функционала

**Credit Portfolio** - модуль для управления финансовым портфелем компании: организации, банковские счета, кредитные договоры, поступления и расходы.

**Ключевые возможности:**
- ✅ Управление организациями и банковскими счетами
- ✅ Кредитные договоры с параметрами (сумма, ставка, срок)
- ✅ Учет поступлений и расходов по договорам
- ✅ Автоматический импорт данных из Excel через FTP
- ✅ Ежемесячная аналитика и KPI
- ✅ Сравнение договоров и cash flow анализ
- ✅ Интеграция с основными бюджетами

### Модели данных (7 моделей)

```python
# 1. FinOrganization - Финансовые организации
class FinOrganization(Base):
    __tablename__ = "fin_organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # Наименование
    inn = Column(String(12))                     # ИНН
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 2. FinBankAccount - Банковские счета
class FinBankAccount(Base):
    __tablename__ = "fin_bank_accounts"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("fin_organizations.id"))
    account_number = Column(String(20), nullable=False)
    bank_name = Column(String(255))
    currency = Column(String(3), default="RUB")  # RUB, USD, EUR
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 3. FinContract - Кредитные договоры
class FinContract(Base):
    __tablename__ = "fin_contracts"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("fin_organizations.id"))
    contract_number = Column(String(50))
    contract_date = Column(Date)
    contract_amount = Column(Numeric(15, 2))     # Сумма договора
    interest_rate = Column(Numeric(5, 2))        # Процентная ставка
    start_date = Column(Date)                    # Дата начала
    end_date = Column(Date)                      # Дата окончания
    status = Column(String(50))                  # ACTIVE/CLOSED
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 4. FinReceipt - Поступления
class FinReceipt(Base):
    __tablename__ = "fin_receipts"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("fin_contracts.id"))
    receipt_date = Column(Date)
    amount = Column(Numeric(15, 2))
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 5. FinExpense - Расходы по договорам
class FinExpense(Base):
    __tablename__ = "fin_expenses"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("fin_contracts.id"))
    expense_date = Column(Date)
    amount = Column(Numeric(15, 2))
    category = Column(String(100))               # INTEREST/PRINCIPAL/FEE
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 6. FinExpenseDetail - Детализация расходов
class FinExpenseDetail(Base):
    __tablename__ = "fin_expense_details"

    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey("fin_expenses.id"))
    item_name = Column(String(255))
    amount = Column(Numeric(15, 2))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 7. FinImportLog - Логи импорта из FTP
class FinImportLog(Base):
    __tablename__ = "fin_import_logs"

    id = Column(Integer, primary_key=True)
    import_date = Column(DateTime, default=func.now())
    file_name = Column(String(255))
    status = Column(String(50))                  # SUCCESS/ERROR
    records_imported = Column(Integer, default=0)
    error_message = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
```

### API Endpoints

**Base path**: `/api/v1/credit-portfolio`

```bash
# Organizations
GET    /api/v1/credit-portfolio/organizations
POST   /api/v1/credit-portfolio/organizations
PUT    /api/v1/credit-portfolio/organizations/{id}
DELETE /api/v1/credit-portfolio/organizations/{id}

# Bank Accounts
GET    /api/v1/credit-portfolio/bank-accounts
POST   /api/v1/credit-portfolio/bank-accounts
PUT    /api/v1/credit-portfolio/bank-accounts/{id}
DELETE /api/v1/credit-portfolio/bank-accounts/{id}

# Contracts
GET    /api/v1/credit-portfolio/contracts
POST   /api/v1/credit-portfolio/contracts
PUT    /api/v1/credit-portfolio/contracts/{id}
DELETE /api/v1/credit-portfolio/contracts/{id}
GET    /api/v1/credit-portfolio/contracts/{id}/details  # Детали договора

# Receipts & Expenses
GET    /api/v1/credit-portfolio/receipts
POST   /api/v1/credit-portfolio/receipts
GET    /api/v1/credit-portfolio/expenses
POST   /api/v1/credit-portfolio/expenses

# Analytics & KPI
GET    /api/v1/credit-portfolio/analytics/monthly
GET    /api/v1/credit-portfolio/analytics/kpi
GET    /api/v1/credit-portfolio/analytics/cash-flow
GET    /api/v1/credit-portfolio/analytics/contract-comparison

# FTP Import
POST   /api/v1/credit-portfolio/import/ftp  # Trigger FTP import
GET    /api/v1/credit-portfolio/import/logs  # Import history
```

### FTP Автоматический импорт

**Сервисы:**
- `FTPImportService` (`backend/app/services/ftp_import_service.py`)
- `CreditPortfolioParser` (`backend/app/services/credit_portfolio_parser.py`)
- `ImportConfigManager` (`backend/app/services/import_config_manager.py`)

**Workflow:**
```
1. ПОДКЛЮЧЕНИЕ К FTP
   ↓
   FTP сервер → проверка новых файлов Excel

2. ЗАГРУЗКА ФАЙЛА
   ↓
   Download → /tmp/credit_portfolio_import_{date}.xlsx

3. ПАРСИНГ
   ↓
   CreditPortfolioParser.parse_excel(file_path)
   ↓
   Определение структуры:
   - Organizations sheet
   - BankAccounts sheet
   - Contracts sheet
   - Receipts sheet
   - Expenses sheet

4. ВАЛИДАЦИЯ
   ↓
   Проверка обязательных полей
   Проверка корректности данных

5. ИМПОРТ
   ↓
   Batch insert/update (по 100 записей)
   Create FinImportLog

6. УВЕДОМЛЕНИЕ
   ↓
   Email notification (success/error)
   Update dashboard statistics
```

**Конфигурация FTP** (`.env`):
```bash
# FTP Settings
FTP_HOST=ftp.example.com
FTP_PORT=21
FTP_USERNAME=import_user
FTP_PASSWORD=secure_password
FTP_DIRECTORY=/credit_portfolio/import
FTP_IMPORT_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Import Settings
CREDIT_PORTFOLIO_AUTO_IMPORT=true
CREDIT_PORTFOLIO_NOTIFY_EMAIL=finance@company.com
```

**Запуск импорта вручную:**
```bash
cd backend
python scripts/run_credit_portfolio_import.py

# Или через API
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/ftp" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"department_id": 1}'
```

### Frontend страницы

**5 основных страниц:**

1. **CreditPortfolioPage.tsx** - Главная страница
   - Список организаций, счетов, договоров
   - Фильтры и поиск
   - CRUD операции

2. **CreditPortfolioContractsPage.tsx** - Управление договорами
   - Таблица договоров с детализацией
   - Статусы (ACTIVE/CLOSED)
   - Сроки и суммы

3. **CreditPortfolioComparePage.tsx** - Сравнение договоров
   - Side-by-side сравнение
   - Процентные ставки
   - Сроки и условия

4. **CreditPortfolioCashFlowPage.tsx** - Cash Flow анализ
   - График поступлений/расходов
   - Прогноз платежей
   - Остатки по счетам

5. **CreditPortfolioKPIPage.tsx** - KPI и аналитика
   - Ежемесячная статистика
   - Ключевые показатели
   - Тренды

### Интеграция с основным бюджетом

```python
# Связь с Expenses через category
expense = Expense(
    category_id=credit_portfolio_category_id,  # "Кредитные платежи"
    amount=fin_expense.amount,
    contractor_id=fin_contract.organization_id,
    comment=f"Платеж по договору {fin_contract.contract_number}",
    department_id=fin_expense.department_id
)

# Автоматическое создание expense при импорте
if auto_create_expenses:
    create_expense_from_fin_expense(fin_expense)
```

### Документация

- 📖 [Credit Portfolio Overview](docs/CREDIT_PORTFOLIO_OVERVIEW.md)
- 📖 [FTP Auto Import Guide](docs/CREDIT_PORTFOLIO_AUTO_IMPORT.md)
- 📖 [Debug Guide](docs/CREDIT_PORTFOLIO_DEBUG.md)
- 📖 [Final Status](docs/CREDIT_PORTFOLIO_FINAL_STATUS.md)
- 📖 [Migration Notes](docs/CREDIT_PORTFOLIO_MIGRATION.md)

### Типичные сценарии

#### 1. Создание нового договора
```bash
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": 1,
    "contract_number": "КД-2025-001",
    "contract_date": "2025-01-15",
    "contract_amount": 5000000.00,
    "interest_rate": 12.5,
    "start_date": "2025-02-01",
    "end_date": "2026-02-01",
    "status": "ACTIVE",
    "department_id": 1
  }'
```

#### 2. Просмотр аналитики за месяц
```bash
curl "http://localhost:8000/api/v1/credit-portfolio/analytics/monthly?year=2025&month=11&department_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. Импорт из FTP
```bash
# Автоматический (через cron)
0 2 * * * cd /app/backend && python scripts/run_credit_portfolio_import.py

# Ручной
curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/ftp" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📈 Revenue Budget Management - Управление бюджетом доходов

### Обзор функционала

**Revenue Budget** - полноценный модуль для планирования и учета доходов с версионированием, customer metrics, и сезонностью.

**Ключевые возможности:**
- ✅ Источники доходов (Revenue Streams) и категории
- ✅ Планирование доходов с версионированием (как в expenses budget)
- ✅ Учет фактических доходов (Revenue Actuals)
- ✅ Customer Lifetime Value (LTV) и метрики клиентов
- ✅ Коэффициенты сезонности для прогнозирования
- ✅ Аналитика и сравнение plan vs actual
- ✅ Интеграция с expense budget для P&L

### Модели данных (8 основных)

```python
# 1. RevenueStream - Источники дохода
class RevenueStream(Base):
    __tablename__ = "revenue_streams"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)   # Продукт/Услуга
    code = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 2. RevenueCategory - Категории доходов
class RevenueCategory(Base):
    __tablename__ = "revenue_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)   # Прямые продажи, Подписки, Лицензии
    code = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 3. RevenuePlan - План доходов (главная таблица)
class RevenuePlan(Base):
    __tablename__ = "revenue_plans"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    name = Column(String(255))
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 4. RevenuePlanVersion - Версии плана (для approval workflow)
class RevenuePlanVersion(Base):
    __tablename__ = "revenue_plan_versions"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("revenue_plans.id"))
    version_number = Column(Integer, nullable=False)
    status = Column(String(50))  # DRAFT/PENDING/APPROVED/REJECTED
    created_by_id = Column(Integer, ForeignKey("users.id"))
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 5. RevenuePlanDetail - Детали плана (по месяцам и источникам)
class RevenuePlanDetail(Base):
    __tablename__ = "revenue_plan_details"

    id = Column(Integer, primary_key=True)
    plan_version_id = Column(Integer, ForeignKey("revenue_plan_versions.id"))
    stream_id = Column(Integer, ForeignKey("revenue_streams.id"))
    category_id = Column(Integer, ForeignKey("revenue_categories.id"))
    month = Column(Integer)  # 1-12
    planned_amount = Column(Numeric(15, 2))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 6. RevenueActual - Фактические доходы
class RevenueActual(Base):
    __tablename__ = "revenue_actuals"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("revenue_streams.id"))
    category_id = Column(Integer, ForeignKey("revenue_categories.id"))
    actual_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))  # Опционально
    invoice_number = Column(String(50))
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 7. CustomerMetrics - Метрики клиентов
class CustomerMetrics(Base):
    __tablename__ = "customer_metrics"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    month = Column(Date)
    revenue = Column(Numeric(15, 2))
    ltv = Column(Numeric(15, 2))          # Customer Lifetime Value
    churn_risk = Column(Numeric(5, 2))    # Риск оттока (0-100%)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

# 8. SeasonalityCoefficient - Коэффициенты сезонности
class SeasonalityCoefficient(Base):
    __tablename__ = "seasonality_coefficients"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("revenue_streams.id"))
    month = Column(Integer)  # 1-12
    coefficient = Column(Numeric(5, 4))  # 0.5 = -50%, 1.5 = +50%
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
```

### API Endpoints (8 модулей)

**Base path**: `/api/v1/revenue`

```bash
# Revenue Streams
GET    /api/v1/revenue/streams
POST   /api/v1/revenue/streams
PUT    /api/v1/revenue/streams/{id}
DELETE /api/v1/revenue/streams/{id}

# Revenue Categories
GET    /api/v1/revenue/categories
POST   /api/v1/revenue/categories
PUT    /api/v1/revenue/categories/{id}
DELETE /api/v1/revenue/categories/{id}

# Revenue Plans (главный план)
GET    /api/v1/revenue/plans
POST   /api/v1/revenue/plans
PUT    /api/v1/revenue/plans/{id}
DELETE /api/v1/revenue/plans/{id}

# Revenue Plan Versions (версионирование)
GET    /api/v1/revenue/plan-versions
POST   /api/v1/revenue/plan-versions/{id}/approve
POST   /api/v1/revenue/plan-versions/{id}/reject

# Revenue Plan Details (детали по месяцам)
GET    /api/v1/revenue/plan-details?plan_version_id=1
POST   /api/v1/revenue/plan-details
PUT    /api/v1/revenue/plan-details/{id}
POST   /api/v1/revenue/plan-details/bulk-update  # Массовое обновление

# Revenue Actuals (фактические доходы)
GET    /api/v1/revenue/actuals
POST   /api/v1/revenue/actuals
PUT    /api/v1/revenue/actuals/{id}
DELETE /api/v1/revenue/actuals/{id}

# Customer Metrics (метрики клиентов)
GET    /api/v1/revenue/customer-metrics
POST   /api/v1/revenue/customer-metrics
GET    /api/v1/revenue/customer-metrics/ltv  # LTV аналитика

# Seasonality (сезонность)
GET    /api/v1/revenue/seasonality
POST   /api/v1/revenue/seasonality
PUT    /api/v1/revenue/seasonality/{id}
GET    /api/v1/revenue/seasonality/forecast  # Прогноз с учетом сезонности

# Analytics (аналитика)
GET    /api/v1/revenue/analytics/plan-vs-actual
GET    /api/v1/revenue/analytics/by-stream
GET    /api/v1/revenue/analytics/by-category
GET    /api/v1/revenue/analytics/trends
GET    /api/v1/revenue/analytics/forecast  # Прогноз доходов
```

### Frontend страницы (8 страниц)

1. **RevenueStreamsPage.tsx** - Управление источниками доходов
2. **RevenueCategoriesPage.tsx** - Управление категориями
3. **RevenuePlanPage.tsx** - Планирование доходов (главная)
4. **RevenuePlanDetailsPage.tsx** - Детали плана по месяцам (как BudgetPlanDetailsTable)
5. **RevenueActualsPage.tsx** - Учет фактических доходов
6. **RevenueAnalyticsPage.tsx** - Аналитика plan vs actual
7. **CustomerMetricsPage.tsx** - Метрики клиентов и LTV
8. **SeasonalityPage.tsx** - Настройка коэффициентов сезонности

### Workflow планирования

```
1. СОЗДАНИЕ ПЛАНА
   ↓
   Create RevenuePlan for year 2025
   Create RevenuePlanVersion (v1, status=DRAFT)

2. ЗАПОЛНЕНИЕ ДЕТАЛЕЙ
   ↓
   Add RevenuePlanDetail records:
   - Stream: "Продукт А", Month: 1, Amount: 500000
   - Stream: "Продукт Б", Month: 1, Amount: 300000
   - ...для всех 12 месяцев

3. APPROVAL WORKFLOW
   ↓
   Submit for approval → status=PENDING
   Manager reviews
   Approve → status=APPROVED

4. ВЕРСИИ
   ↓
   При изменениях создается новая версия
   Старые версии сохраняются для истории
   Можно сравнивать версии side-by-side

5. СРАВНЕНИЕ ПЛАН vs ФАКТ
   ↓
   RevenueActual records сравниваются с планом
   Отклонения по месяцам, источникам, категориям
   Тренды и forecast
```

### Интеграция с Expense Budget

```python
# Сводный P&L (Profit & Loss)
def get_profit_loss_report(year: int, month: int, department_id: int):
    # Доходы
    revenue = db.query(func.sum(RevenueActual.amount)).filter(
        extract('year', RevenueActual.actual_date) == year,
        extract('month', RevenueActual.actual_date) == month,
        RevenueActual.department_id == department_id
    ).scalar() or 0

    # Расходы
    expenses = db.query(func.sum(Expense.amount)).filter(
        extract('year', Expense.request_date) == year,
        extract('month', Expense.request_date) == month,
        Expense.department_id == department_id,
        Expense.status == 'PAID'
    ).scalar() or 0

    # Прибыль
    profit = revenue - expenses
    margin = (profit / revenue * 100) if revenue > 0 else 0

    return {
        "revenue": float(revenue),
        "expenses": float(expenses),
        "profit": float(profit),
        "margin_percent": float(margin)
    }
```

### Сезонность и прогнозирование

```python
# Применение сезонных коэффициентов
def forecast_with_seasonality(stream_id: int, base_amount: float, month: int):
    coeff = db.query(SeasonalityCoefficient).filter_by(
        stream_id=stream_id,
        month=month
    ).first()

    if coeff:
        return base_amount * float(coeff.coefficient)
    else:
        return base_amount  # Default: без изменений

# Пример: зимний месяц (коэфф 1.3) → +30% к доходам
# Летний месяц (коэфф 0.7) → -30% к доходам
```

### Документация

- 📖 [Revenue Budget Guide](docs/REVENUE_BUDGET_GUIDE.md)
- 📖 [Revenue Planning Workflow](docs/REVENUE_PLANNING_WORKFLOW.md)
- 📖 [Customer LTV Calculations](docs/CUSTOMER_LTV.md)
- 📖 [Seasonality Setup](docs/REVENUE_SEASONALITY.md)

---

## 🧾 AI Invoice Processing - Автоматическое распознавание счетов

### Обзор функционала

**Invoice Processing** - AI-powered модуль для автоматического распознавания и обработки счетов (invoices) с использованием OCR и GPT-4o.

**Ключевые возможности:**
- ✅ OCR распознавание PDF и изображений счетов (Tesseract)
- ✅ AI парсинг через VseGPT API (GPT-4o-mini)
- ✅ Автоматическое извлечение: сумма, дата, контрагент, позиции
- ✅ **Интеграция с 1С: создание заявок на расход** (NEW v0.9.0) 🏢
- ✅ Workflow: Upload → OCR → AI Parse → Review → **Create 1C Expense Request**
- ✅ Ручная коррекция распознанных данных

### Зависимости

```bash
# OCR
pip install pytesseract pdf2image Pillow

# System dependencies (macOS)
brew install tesseract
brew install poppler  # For PDF support

# System dependencies (Ubuntu/Debian)
apt-get install tesseract-ocr tesseract-ocr-rus poppler-utils

# AI API
# VseGPT API (GPT-4o-mini) через credentials
```

### Модель данных

```python
class ProcessedInvoice(Base):
    __tablename__ = "processed_invoices"

    id = Column(Integer, primary_key=True)

    # Файл
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(String(50))  # PDF/PNG/JPG

    # OCR результаты
    ocr_text = Column(Text)                  # Полный текст из OCR
    ocr_confidence = Column(Numeric(5, 2))   # Уверенность OCR (0-100%)
    ocr_status = Column(String(50))          # SUCCESS/ERROR

    # AI парсинг
    ai_parsed_data = Column(JSON)            # Структурированные данные
    ai_confidence = Column(Numeric(5, 2))    # Уверенность AI (0-100%)

    # Извлеченные поля
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    total_amount = Column(Numeric(15, 2))
    vat_amount = Column(Numeric(15, 2))
    contractor_name = Column(String(255))
    contractor_inn = Column(String(12))

    # Позиции счета (JSON array)
    line_items = Column(JSON)  # [{"name": "...", "qty": 1, "price": 1000, "total": 1000}]

    # Статус обработки
    status = Column(String(50))  # NEW/OCR_COMPLETED/AI_PARSED/REVIEWED/APPROVED/ERROR

    # Связь с 1С
    external_id_1c = Column(String(100))
    synced_to_1c = Column(Boolean, default=False)
    synced_at = Column(DateTime)

    # Ручная коррекция
    manually_corrected = Column(Boolean, default=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
```

### Сервисы

#### 1. InvoiceOCRService (OCR распознавание)
**Файл**: `backend/app/services/invoice_ocr_service.py`

```python
from app.services.invoice_ocr_service import InvoiceOCRService

# Create service
ocr_service = InvoiceOCRService()

# Process PDF or image
result = ocr_service.process_file(
    file_path="/tmp/invoice.pdf",
    language="rus+eng"  # Tesseract languages
)

# Result:
# {
#     "text": "...полный распознанный текст...",
#     "confidence": 85.5,
#     "status": "SUCCESS",
#     "page_count": 2
# }
```

#### 2. InvoiceAIParser (AI парсинг)
**Файл**: `backend/app/services/invoice_ai_parser.py`

```python
from app.services.invoice_ai_parser import InvoiceAIParser

# Create parser
parser = InvoiceAIParser(vsegpt_api_key=settings.VSEGPT_API_KEY)

# Parse OCR text
parsed_data = parser.parse_invoice_text(ocr_text)

# Result:
# {
#     "invoice_number": "СФ-2025-001",
#     "invoice_date": "2025-11-17",
#     "total_amount": 120000.00,
#     "vat_amount": 20000.00,
#     "contractor": {
#         "name": "ООО Поставщик",
#         "inn": "7701234567"
#     },
#     "line_items": [
#         {"name": "Товар 1", "qty": 10, "price": 1000, "total": 10000},
#         {"name": "Товар 2", "qty": 5, "price": 2000, "total": 10000}
#     ],
#     "confidence": 92.5
# }
```

#### 3. InvoiceProcessorService (Главный сервис)
**Файл**: `backend/app/services/invoice_processor_service.py`

```python
from app.services.invoice_processor_service import InvoiceProcessorService

# Create processor
processor = InvoiceProcessorService(db=db, department_id=1)

# Full pipeline: Upload → OCR → AI Parse
result = await processor.process_invoice_file(
    file=uploaded_file,
    auto_sync_to_1c=True
)

# Result:
# ProcessedInvoice object with all fields populated
```

### API Endpoints

**Base path**: `/api/v1/invoices`

```bash
# Upload and process invoice
POST   /api/v1/invoices/upload
  -F "file=@invoice.pdf"
  -F "department_id=1"
  -F "auto_parse=true"

# Get processed invoices
GET    /api/v1/invoices
  ?status=AI_PARSED
  &department_id=1

# Get single invoice
GET    /api/v1/invoices/{id}

# Manual correction
PUT    /api/v1/invoices/{id}/correct
{
  "invoice_number": "СФ-2025-001",
  "total_amount": 120000.00,
  "contractor_name": "ООО Поставщик"
}

# Approve invoice
POST   /api/v1/invoices/{id}/approve

# Sync to 1C
POST   /api/v1/invoices/{id}/sync-to-1c

# Re-process with AI
POST   /api/v1/invoices/{id}/reprocess

# ==================== 1C Integration (NEW v0.9.0) ====================

# Get cash flow categories (статьи ДДС)
GET    /api/v1/invoice-processing/cash-flow-categories
  ?department_id=1

# AI-suggest category
POST   /api/v1/invoice-processing/{id}/suggest-category

# Set category
PUT    /api/v1/invoice-processing/{id}/category
{
  "category_id": 15
}

# Validate before sending to 1C
POST   /api/v1/invoice-processing/{id}/validate-for-1c

# Create expense request in 1C
POST   /api/v1/invoice-processing/{id}/create-1c-expense-request
{
  "upload_attachment": true
}
```

### Workflow обработки

```
1. UPLOAD
   ↓
   User uploads PDF/Image → /tmp/invoices/{uuid}.pdf

2. OCR RECOGNITION
   ↓
   InvoiceOCRService.process_file()
   ↓
   Tesseract OCR → extracted text
   ↓
   Save to ProcessedInvoice.ocr_text
   Status → OCR_COMPLETED

3. AI PARSING
   ↓
   InvoiceAIParser.parse_invoice_text()
   ↓
   VseGPT API (GPT-4o-mini)
   Prompt: "Extract structured data from this invoice: {ocr_text}"
   ↓
   Parse JSON response
   ↓
   Save to ProcessedInvoice.ai_parsed_data
   Status → AI_PARSED

4. REVIEW (Optional)
   ↓
   User reviews extracted data
   ↓
   Manual corrections if needed
   ↓
   Status → REVIEWED

5. APPROVAL
   ↓
   User approves
   ↓
   Status → APPROVED

6. SYNC TO 1C (Optional)
   ↓
   Create Document_СчетНаОплату in 1C via OData
   ↓
   synced_to_1c = true
   external_id_1c = Ref_Key from 1C
```

### Environment Variables

```bash
# .env
VSEGPT_API_KEY=your_vsegpt_api_key
VSEGPT_API_URL=https://api.vsegpt.ru/v1/chat/completions
VSEGPT_MODEL=openai/gpt-4o-mini

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract
TESSERACT_LANGUAGES=rus+eng
OCR_DPI=300  # Higher DPI = better quality, slower

# File Storage
INVOICE_STORAGE_PATH=/app/storage/invoices
INVOICE_MAX_FILE_SIZE=10485760  # 10MB
```

### Frontend интеграция

**Страница**: `frontend/src/pages/InvoiceProcessingPage.tsx`

```typescript
const InvoiceProcessingPage = () => {
  const { selectedDepartment } = useDepartment()

  // Upload invoice
  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('department_id', selectedDepartment.id)
    formData.append('auto_parse', 'true')

    await api.uploadInvoice(formData)
  }

  // Review and correct
  const handleCorrect = async (invoiceId: number, data: any) => {
    await api.correctInvoice(invoiceId, data)
  }

  // Approve
  const handleApprove = async (invoiceId: number) => {
    await api.approveInvoice(invoiceId)
  }
}
```

### Интеграция с 1С

```python
# Sync invoice to 1C
def sync_invoice_to_1c(invoice: ProcessedInvoice):
    odata_client = OData1CClient()

    # Create Document_СчетНаОплату
    invoice_data = {
        "Номер": invoice.invoice_number,
        "Дата": invoice.invoice_date.isoformat(),
        "Сумма": float(invoice.total_amount),
        "Контрагент_Key": get_contractor_guid_by_inn(invoice.contractor_inn),
        "ТабличнаяЧасть": [
            {
                "Номенклатура": item["name"],
                "Количество": item["qty"],
                "Цена": item["price"],
                "Сумма": item["total"]
            }
            for item in invoice.line_items
        ]
    }

    response = odata_client.create_document("Document_СчетНаОплату", invoice_data)

    # Update invoice
    invoice.external_id_1c = response["Ref_Key"]
    invoice.synced_to_1c = True
    invoice.synced_at = datetime.utcnow()
```

### Типичные сценарии

#### 1. Загрузка и автоматическая обработка
```bash
curl -X POST "http://localhost:8000/api/v1/invoices/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice_001.pdf" \
  -F "department_id=1" \
  -F "auto_parse=true"
```

#### 2. Ручная коррекция
```bash
curl -X PUT "http://localhost:8000/api/v1/invoices/123/correct" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "СФ-2025-001",
    "total_amount": 125000.00,
    "contractor_inn": "7701234567"
  }'
```

#### 3. Синхронизация с 1С
```bash
curl -X POST "http://localhost:8000/api/v1/invoices/123/sync-to-1c" \
  -H "Authorization: Bearer $TOKEN"
```

### Troubleshooting

**OCR Quality Issues:**
```python
# Increase DPI for better quality
OCR_DPI=600  # Default: 300

# Add preprocessing
from PIL import Image, ImageEnhance

def preprocess_image(image_path):
    img = Image.open(image_path)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Convert to grayscale
    img = img.convert('L')

    return img
```

**AI Parsing Errors:**
```python
# Check API response
logging.getLogger("app.services.invoice_ai_parser").setLevel(logging.DEBUG)

# Fallback to manual parsing
if ai_confidence < 80:
    # Flag for manual review
    invoice.status = "NEEDS_REVIEW"
```

### Документация 1С интеграции

- 📖 **[Invoice to 1C Integration Guide](docs/INVOICE_TO_1C_INTEGRATION.md)** - Полная документация по созданию заявок на расход в 1С
- 📖 **[Implementation Summary](docs/INVOICE_TO_1C_IMPLEMENTATION_SUMMARY.md)** - Техническая документация реализации

**Workflow создания заявки в 1С:**
1. Upload invoice → OCR → AI Parse
2. **Выбор статьи ДДС** (cash flow category)
3. **Валидация** (контрагент/организация найдены в 1С)
4. **Создание заявки** через OData API
5. Автоматическая синхронизация обратно как Expense

**Требования:**
- Контрагент должен существовать в 1С (по ИНН)
- Организация должна существовать в 1С (buyer INN)
- Статья ДДС должна быть синхронизирована (`external_id_1c` заполнен)

**Пример:**
```bash
# 1. Suggest category
POST /api/v1/invoice-processing/123/suggest-category

# 2. Set category
PUT /api/v1/invoice-processing/123/category {"category_id": 15}

# 3. Validate
POST /api/v1/invoice-processing/123/validate-for-1c

# 4. Create in 1C
POST /api/v1/invoice-processing/123/create-1c-expense-request
```

---

## ⏰ Background Automation - Планировщик задач

### Обзор функционала

**Background Jobs** - автоматизация фоновых задач через APScheduler для регулярных операций.

**Ключевые возможности:**
- ✅ Автоматическая синхронизация с 1С (hourly/daily)
- ✅ FTP мониторинг и импорт (credit portfolio)
- ✅ Scheduled reports (email отчеты)
- ✅ Bank transaction processing
- ✅ Data cleanup tasks

### Зависимости

```python
# requirements.txt
APScheduler==3.10.4
```

### Scheduler Service

**Файл**: `backend/app/services/scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Create scheduler
scheduler = AsyncIOScheduler()

# Job: Sync 1C expense requests (hourly)
@scheduler.scheduled_job(CronTrigger(hour='*', minute=0))
async def sync_1c_expenses():
    logger.info("Starting 1C expense sync job")
    # Run sync for all departments
    for dept in departments:
        await expense_1c_sync.sync_expenses(
            department_id=dept.id,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today()
        )

# Job: FTP import (daily at 2 AM)
@scheduler.scheduled_job(CronTrigger(hour=2, minute=0))
async def ftp_import_credit_portfolio():
    logger.info("Starting FTP import job")
    await ftp_service.import_from_ftp()

# Job: Send daily reports (daily at 8 AM)
@scheduler.scheduled_job(CronTrigger(hour=8, minute=0))
async def send_daily_reports():
    logger.info("Sending daily reports")
    await report_service.send_daily_summary()

# Start scheduler
scheduler.start()
```

### Интеграция с FastAPI

**Файл**: `backend/app/main.py`

```python
from app.services.scheduler import scheduler

@app.on_event("startup")
async def startup_event():
    # Start background scheduler
    scheduler.start()
    logger.info("Background scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop scheduler gracefully
    scheduler.shutdown()
    logger.info("Background scheduler stopped")
```

### Конфигурация задач

**Environment Variables**:
```bash
# .env
SCHEDULER_ENABLED=true

# 1C Sync
SYNC_1C_EXPENSES_ENABLED=true
SYNC_1C_EXPENSES_SCHEDULE=0 * * * *  # Hourly

SYNC_1C_CATALOGS_ENABLED=true
SYNC_1C_CATALOGS_SCHEDULE=0 0 * * *  # Daily at midnight

# FTP Import
FTP_IMPORT_ENABLED=true
FTP_IMPORT_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Reports
DAILY_REPORT_ENABLED=true
DAILY_REPORT_SCHEDULE=0 8 * * *  # Daily at 8 AM
DAILY_REPORT_RECIPIENTS=finance@company.com,cfo@company.com
```

### Доступные задачи

```python
# 1C Synchronization Jobs
sync_1c_expenses()           # Hourly - заявки на расход
sync_1c_catalogs()           # Daily - справочники
sync_1c_organizations()      # Daily - организации
sync_1c_categories()         # Daily - категории

# FTP Import Jobs
ftp_import_credit_portfolio() # Daily - кредитный портфель
ftp_import_bank_statements()  # Daily - банковские выписки

# Processing Jobs
process_bank_transactions()   # Hourly - классификация транзакций
detect_regular_patterns()     # Weekly - определение регулярных платежей

# Reporting Jobs
send_daily_reports()          # Daily - ежедневные отчеты
send_weekly_summary()         # Weekly - еженедельная сводка
send_monthly_closing()        # Monthly - закрытие месяца

# Maintenance Jobs
cleanup_old_logs()            # Daily - очистка старых логов
cleanup_temp_files()          # Daily - очистка временных файлов
vacuum_database()             # Weekly - оптимизация БД
```

### Мониторинг задач

**API для управления задачами**:
```bash
# Get all scheduled jobs
GET /api/v1/scheduler/jobs

# Get job details
GET /api/v1/scheduler/jobs/{job_id}

# Trigger job manually
POST /api/v1/scheduler/jobs/{job_id}/trigger

# Pause job
POST /api/v1/scheduler/jobs/{job_id}/pause

# Resume job
POST /api/v1/scheduler/jobs/{job_id}/resume
```

### Логирование

```python
import logging

# Configure scheduler logging
logging.getLogger('apscheduler').setLevel(logging.INFO)

# Job execution logs
@scheduler.scheduled_job(...)
async def my_job():
    logger.info(f"Job {my_job.__name__} started")
    try:
        # Job logic
        logger.info(f"Job {my_job.__name__} completed successfully")
    except Exception as e:
        logger.error(f"Job {my_job.__name__} failed: {e}", exc_info=True)
```

### Документация

- 📖 [APScheduler Auto Import](docs/APSCHEDULER_AUTO_IMPORT.md)
- 📖 [1C Catalog Sync Cron](docs/1C_CATALOG_SYNC_CRON.md)

---

## 👔 Founder Dashboard - Панель руководителя

### Обзор функционала

**Founder Dashboard** - специальная панель для руководителя (FOUNDER role) с высокоуровневыми KPI и кросс-департментской аналитикой.

**Ключевые возможности:**
- ✅ Сводная финансовая информация по всем отделам
- ✅ Ключевые KPI компании
- ✅ Revenue vs Expenses (P&L)
- ✅ Cash Flow прогноз
- ✅ Top contractors и expenses
- ✅ Тренды и отклонения от плана

### FOUNDER Role

```python
class UserRoleEnum(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    FOUNDER = "FOUNDER"  # Executive read-only access
    ADMIN = "ADMIN"
```

**Права доступа:**
- Просмотр всех департаментов (read-only)
- Доступ ко всем отчетам и аналитике
- НЕ может редактировать данные (только просмотр)
- Специальная dashboard страница

### API Endpoints

**Base path**: `/api/v1/founder`

```bash
# Executive summary
GET /api/v1/founder/dashboard/summary

# Cross-department KPIs
GET /api/v1/founder/dashboard/kpis

# P&L report (all departments)
GET /api/v1/founder/dashboard/profit-loss?year=2025&month=11

# Cash flow forecast
GET /api/v1/founder/dashboard/cash-flow-forecast

# Top metrics
GET /api/v1/founder/dashboard/top-contractors
GET /api/v1/founder/dashboard/top-expenses
GET /api/v1/founder/dashboard/budget-execution
```

### Frontend

**Страница**: `frontend/src/pages/FounderDashboardPage.tsx`

**Компоненты:**
- Executive summary cards (revenue, expenses, profit, margin)
- Multi-department comparison charts
- Budget execution gauge (plan vs actual)
- Cash flow timeline
- Top contractors table
- Alerts and notifications

**Доступ**: Только для пользователей с ролью FOUNDER

---

## ⏱️ Timesheet Module - Табель учета рабочего времени

### Обзор функционала

**Timesheet Module** (HR_DEPARTMENT) - модуль для учета рабочего времени сотрудников с автоматическим расчетом и Excel экспортом.

**Ключевые возможности:**
- ✅ Табель учета времени по дням месяца
- ✅ Автоматическая подсветка выходных и праздников РФ
- ✅ Поддержка темной темы
- ✅ Статусы: DRAFT, APPROVED, PAID
- ✅ Excel экспорт/импорт табелей
- ✅ Шаблоны для ручного заполнения
- ✅ Аналитика по отделам
- ✅ Учет сверхурочных и перерывов

### Модели данных (2 основные)

```python
# 1. WorkTimesheet - Табель сотрудника за месяц
class WorkTimesheet(Base):
    __tablename__ = "work_timesheets"

    id = Column(UUID, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    status = Column(Enum(TimesheetStatusEnum), default=TimesheetStatusEnum.DRAFT)

    # Итоги
    total_days_worked = Column(Integer, default=0)
    total_hours_worked = Column(Numeric(10, 2), default=0)

    # Утверждение
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Оплата
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime)

# 2. DailyWorkRecord - Ежедневная запись
class DailyWorkRecord(Base):
    __tablename__ = "daily_work_records"

    id = Column(UUID, primary_key=True)
    timesheet_id = Column(UUID, ForeignKey("work_timesheets.id"), nullable=False)
    work_date = Column(Date, nullable=False)
    is_working_day = Column(Boolean, default=True)

    # Часы
    hours_worked = Column(Numeric(5, 2), nullable=False)
    break_hours = Column(Numeric(5, 2), default=0)
    overtime_hours = Column(Numeric(5, 2), default=0)

    # Вычисляемое поле
    @property
    def net_hours_worked(self):
        return self.hours_worked - (self.break_hours or Decimal("0")) + (self.overtime_hours or Decimal("0"))

    notes = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
```

### Статусы табеля (TimesheetStatusEnum)

```python
DRAFT = "DRAFT"          # 📝 Черновик - можно редактировать
APPROVED = "APPROVED"    # ✅ Утвержден - только чтение
PAID = "PAID"           # 💰 Оплачен - архив
```

### API Endpoints

**Base path**: `/api/v1/timesheets`

```bash
# ============ WorkTimesheet CRUD ============

# Получить список табелей (с фильтрами)
GET    /api/v1/timesheets
  ?year=2025
  &month=11
  &department_id=1
  &employee_id=5
  &status=DRAFT

# Получить табель по ID
GET    /api/v1/timesheets/{timesheet_id}

# Создать табель
POST   /api/v1/timesheets
{
  "employee_id": 5,
  "year": 2025,
  "month": 11
}

# Обновить табель
PUT    /api/v1/timesheets/{timesheet_id}
{
  "status": "APPROVED"
}

# Утвердить табель (HR/MANAGER)
POST   /api/v1/timesheets/{timesheet_id}/approve
{
  "notes": "Утверждено"
}

# Удалить табель
DELETE /api/v1/timesheets/{timesheet_id}

# ============ DailyWorkRecord CRUD ============

# Получить записи табеля
GET    /api/v1/timesheets/{timesheet_id}/records

# Создать запись
POST   /api/v1/timesheets/{timesheet_id}/records
{
  "work_date": "2025-11-15",
  "hours_worked": 8,
  "break_hours": 1,
  "is_working_day": true
}

# Обновить запись
PUT    /api/v1/timesheets/records/{record_id}
{
  "hours_worked": 7.5
}

# Удалить запись
DELETE /api/v1/timesheets/records/{record_id}

# Массовое создание/обновление
POST   /api/v1/timesheets/records/bulk
{
  "timesheet_id": "uuid",
  "records": [
    {"work_date": "2025-11-01", "hours_worked": 8},
    {"work_date": "2025-11-02", "hours_worked": 8}
  ]
}

# ============ Grid View (Главная функция) ============

# Получить табель в виде сетки (все сотрудники + все дни месяца)
GET    /api/v1/timesheets/grid/{year}/{month}?department_id=1

Response:
{
  "year": 2025,
  "month": 11,
  "department_id": 1,
  "department_name": "IT Department",
  "working_days_in_month": 20,
  "calendar_days_in_month": 30,
  "employees": [
    {
      "employee_id": 5,
      "employee_full_name": "Иванов Иван Иванович",
      "employee_position": "Разработчик",
      "employee_number": "EMP-001",
      "timesheet_id": "uuid",
      "timesheet_status": "DRAFT",
      "total_days_worked": 18,
      "total_hours_worked": 144.0,
      "can_edit": true,
      "days": [
        {
          "date": "2025-11-01",
          "day_of_week": 6,  // 6=Saturday
          "is_working_day": false,
          "hours_worked": 0,
          "break_hours": null,
          "overtime_hours": null,
          "net_hours_worked": 0,
          "notes": null,
          "record_id": null
        },
        {
          "date": "2025-11-04",
          "day_of_week": 2,  // 2=Tuesday
          "is_working_day": true,
          "hours_worked": 8.0,
          "break_hours": 1.0,
          "overtime_hours": 0,
          "net_hours_worked": 7.0,
          "notes": null,
          "record_id": "uuid"
        }
        // ... all 30 days
      ]
    }
    // ... all employees
  ]
}

# ============ Analytics ============

# Сводная статистика
GET    /api/v1/timesheets/analytics/summary
  ?year=2025
  &month=11
  &department_id=1

Response:
{
  "year": 2025,
  "month": 11,
  "department_id": 1,
  "total_employees": 8,
  "employees_with_timesheets": 8,
  "total_days_worked": 160,
  "total_hours_worked": 1280.0,
  "average_hours_per_employee": 160.0,
  "draft_count": 5,
  "approved_count": 2,
  "paid_count": 1
}

# ============ Excel Export/Import ============

# Экспорт табеля в Excel
GET    /api/v1/timesheets/export/excel
  ?year=2025
  &month=11
  &department_id=1

Returns: Excel file (timesheet_2025_11_Department.xlsx)

# Скачать шаблон для заполнения
GET    /api/v1/timesheets/export/template
  ?year=2025
  &month=11
  &department_id=1
  &language=ru  # ru или en

Returns: Excel template with employee list
```

### Роли и доступ

**HR Role** (NEW):
- Полный доступ ко всем табелям всех отделов
- Может утверждать табели
- Может редактировать любые черновики

**MANAGER Role**:
- Доступ к табелям своего отдела
- Может утверждать табели своего отдела

**USER Role**:
- Видит только свой отдел
- Может редактировать только свои черновики

**ADMIN/FOUNDER**:
- Полный доступ ко всем табелям (read-only для FOUNDER)

### Frontend компоненты

**Страницы:**
1. `TimesheetsGridPage.tsx` - Главная страница с календарной сеткой

**Компоненты:**
1. `TimesheetGrid.tsx` - Календарная сетка с:
   - Все сотрудники по строкам
   - Все дни месяца по колонкам
   - Автоматическая подсветка выходных (красный)
   - Подсветка отработанных дней (зеленый)
   - Tooltips с названиями праздников
   - Предупреждения о перенесенных рабочих днях
   - Итоговая строка с суммами
   - Sticky header и controls
   - Поддержка темной темы

**Утилиты:**
- `frontend/src/utils/holidays.ts` - Российский календарь праздников
  - Фиксированные праздники (Новый год, 23 февраля, 8 марта, и т.д.)
  - Переносы выходных по годам (2024, 2025)
  - Проверка выходных и праздников
  - Определение перенесенных рабочих дней

**Роут**: `/timesheets` (доступен для ролей: ADMIN, MANAGER, USER, HR)

**Меню**: Раздел "Справочники" → "Табель"

### Excel сервис

**Файл**: `backend/app/services/timesheet_excel_service.py`

**Функции:**

1. **export_timesheet_grid()** - Экспорт заполненного табеля
   - Все сотрудники с табельными номерами
   - Дни месяца в колонках
   - Подсветка выходных (красный фон)
   - Подсветка отработанных дней (зеленый фон)
   - Итоговые строки с суммами
   - Freeze panes для удобной прокрутки

2. **generate_timesheet_template()** - Генерация шаблона
   - Список сотрудников
   - Пустые ячейки для заполнения
   - Подсветка выходных
   - Инструкции по заполнению
   - Многоязычность (RU/EN)

### Workflow использования

```
1. СОЗДАНИЕ ТАБЕЛЯ
   ↓
   POST /api/v1/timesheets (employee_id, year, month)
   Status = DRAFT

2. ЗАПОЛНЕНИЕ ДАННЫХ
   ↓
   Option A: Через UI (TimesheetGrid)
   - Inline editing (будущая функция)

   Option B: Массовая загрузка
   - POST /timesheets/records/bulk

   Option C: Excel импорт (будущая функция)
   - Скачать template
   - Заполнить в Excel
   - Загрузить обратно

3. АВТОМАТИЧЕСКИЙ РАСЧЕТ
   ↓
   После каждого изменения:
   - Пересчет total_days_worked
   - Пересчет total_hours_worked
   - Обновление timesheet

4. УТВЕРЖДЕНИЕ (HR/MANAGER)
   ↓
   POST /timesheets/{id}/approve
   Status = APPROVED
   Can no longer edit

5. ОПЛАТА (HR)
   ↓
   Update: is_paid = true
   Status = PAID
   Архив

6. ЭКСПОРТ
   ↓
   GET /timesheets/export/excel
   - Для отчетности
   - Для передачи в бухгалтерию
```

### База данных

**Таблицы:**
- `work_timesheets` - Табели сотрудников
- `daily_work_records` - Ежедневные записи

**Индексы:**
```sql
CREATE INDEX idx_work_timesheets_employee_year_month
ON work_timesheets(employee_id, year, month);

CREATE INDEX idx_work_timesheets_department
ON work_timesheets(department_id);

CREATE INDEX idx_work_timesheets_status
ON work_timesheets(status);

CREATE INDEX idx_daily_work_records_timesheet
ON daily_work_records(timesheet_id);

CREATE INDEX idx_daily_work_records_date
ON daily_work_records(work_date);

-- Unique constraint: один табель на сотрудника/месяц
CREATE UNIQUE INDEX idx_work_timesheets_unique
ON work_timesheets(employee_id, year, month)
WHERE is_active = true;
```

### Seed данные

**Скрипт**: `backend/scripts/seed_timesheets.py`

```bash
# Создать тестовые табели
cd backend
python scripts/seed_timesheets.py 2025 11

# Параметры:
# - year: год (default: 2025)
# - month: месяц (default: 11)

# Создаст:
# - Табели для всех активных сотрудников
# - Записи только для рабочих дней (Пн-Пт)
# - Случайные часы (7-9 часов/день)
# - Случайные сверхурочные (10% вероятность)
# - Смешанные статусы (больше DRAFT, меньше APPROVED)
```

### Типичные сценарии

#### 1. Просмотр табеля отдела за месяц
```bash
# Frontend: Выбрать месяц и год в UI
# API вызов:
GET /api/v1/timesheets/grid/2025/11?department_id=1

# Результат: Календарная сетка со всеми сотрудниками и днями
```

#### 2. Создание табеля для сотрудника
```bash
curl -X POST "http://localhost:8000/api/v1/timesheets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 5,
    "year": 2025,
    "month": 11
  }'
```

#### 3. Массовое заполнение табеля
```bash
curl -X POST "http://localhost:8000/api/v1/timesheets/records/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timesheet_id": "uuid",
    "records": [
      {"work_date": "2025-11-01", "hours_worked": 8, "break_hours": 1},
      {"work_date": "2025-11-02", "hours_worked": 8, "break_hours": 1},
      ...
    ]
  }'
```

#### 4. Утверждение табеля
```bash
curl -X POST "http://localhost:8000/api/v1/timesheets/{id}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Табель проверен и утвержден"
  }'
```

#### 5. Экспорт в Excel
```bash
# Через UI: кнопка "Экспорт в Excel"
# API:
curl -X GET "http://localhost:8000/api/v1/timesheets/export/excel?year=2025&month=11&department_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o timesheet_2025_11.xlsx
```

### Интеграция с другими модулями

**Payroll (Зарплата)**:
```python
# Табель используется для расчета зарплаты
timesheet = db.query(WorkTimesheet).filter_by(
    employee_id=employee_id,
    year=year,
    month=month,
    status=TimesheetStatusEnum.APPROVED
).first()

# Расчет оплаты
base_salary = employee.base_salary
hourly_rate = base_salary / 160  # Среднее: 160 часов/месяц
actual_pay = hourly_rate * float(timesheet.total_hours_worked)
```

**Employees (Сотрудники)**:
- Табель создается для каждого активного сотрудника
- При увольнении сотрудника его табели остаются в архиве

**Departments (Отделы)**:
- Табели группируются по отделам
- Multi-tenancy через department_id

### Российский календарь праздников

**Утилита**: `frontend/src/utils/holidays.ts`

**Функции:**
```typescript
// Проверка выходного/праздника
isWeekendOrHoliday(year: number, month: number, day: number): boolean

// Получить название праздника
getHolidayName(year: number, month: number, day: number): string | null

// Проверить перенесенный рабочий день
isTransferredWorkday(year: number, month: number, day: number): boolean
```

**Фиксированные праздники:**
- 1-8 января: Новогодние каникулы
- 7 января: Рождество Христово
- 23 февраля: День защитника Отечества
- 8 марта: Международный женский день
- 1 мая: Праздник Весны и Труда
- 9 мая: День Победы
- 12 июня: День России
- 4 ноября: День народного единства

**Переносы выходных:**
- 2024: рабочие дни 27.04, 02.11, 28.12
- 2025: рабочие дни 03.01, 02.05
- Обновляются ежегодно по постановлению правительства

### Performance

**Оптимизации:**
- Joinedload для связей (employee, department)
- Index на (employee_id, year, month)
- Lazy loading для daily_records (только при необходимости)
- Batch operations для массового создания записей
- Мемоизация в React компонентах (useMemo, useCallback)

### Ключевые файлы

**Backend:**
- `backend/app/db/models.py` - WorkTimesheet, DailyWorkRecord models
- `backend/app/api/v1/timesheets.py` - API endpoints (943 lines)
- `backend/app/schemas/timesheet.py` - Pydantic schemas
- `backend/app/services/timesheet_excel_service.py` - Excel export/import
- `backend/scripts/seed_timesheets.py` - Test data seeder

**Frontend:**
- `frontend/src/pages/TimesheetsGridPage.tsx` - Main page
- `frontend/src/components/timesheet/TimesheetGrid.tsx` - Grid component
- `frontend/src/types/timesheet.ts` - TypeScript types
- `frontend/src/api/timesheets.ts` - API client
- `frontend/src/utils/holidays.ts` - Russian holiday calendar

**Миграции:**
- `backend/alembic/versions/2025_11_20_0734-*.py` - Add HR role
- `backend/alembic/versions/2025_11_20_0838-*.py` - Add timesheet tables

---

## 📝 Правила создания документации

### ⚠️ ВАЖНО: Документация только для новой функциональности

**НЕ создавайте документацию для:**
- ❌ Исправлений багов (bug fixes)
- ❌ Рефакторинга существующего кода
- ❌ Оптимизаций производительности
- ❌ Исправлений деплоя или конфигурации
- ❌ Отчетов о сессиях разработки
- ❌ Аудитов кода

**Создавайте документацию ТОЛЬКО для:**
- ✅ Новой функциональности (новые модули, фичи)
- ✅ Новых API endpoints
- ✅ Новых workflow и процессов
- ✅ Руководств пользователя для новых возможностей
- ✅ Архитектурных решений для новых компонентов

### Где размещать документацию

**Папка `docs/`** - только для документации реальной функциональности:
- Руководства по использованию (`*_GUIDE.md`)
- Описания интеграций (`*_INTEGRATION.md`)
- Планы развития (`*_PLAN.md`)
- Архитектурная документация (`ARCHITECTURE.md`, `MULTI_TENANCY_*.md`)

**НЕ размещайте в `docs/`:**
- Отчеты о фиксах (`*_FIX.md`, `*_DEBUG.md`)
- Сессионные отчеты (`SESSION_*.md`)
- Отчеты об аудите (`*_AUDIT.md`, `*_REPORT.md`)

### Примеры правильной документации

✅ **Хорошо:**
- `docs/BANK_TRANSACTIONS_IMPORT_GUIDE.md` - руководство по использованию функционала
- `docs/1C_INTEGRATION_GUIDE.md` - описание интеграции
- `docs/PAYROLL_KPI_PLAN.md` - план новой функциональности

❌ **Плохо:**
- `docs/MEMORY_FIX.md` - исправление бага
- `docs/SESSION_SUMMARY_2025-10-30.md` - отчет о сессии
- `docs/BUGFIX_REPORT.md` - отчет об исправлениях

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
- **Goal Templates** (NEW v0.9.0): Reusable templates with predefined goals and weights, bulk apply to employees
- **Auto-create EmployeeKPI** (NEW v0.9.0): Automated monthly KPI creation via scheduler (1st of month, 00:01 MSK)
- **Auto-sync with Payroll** (NEW v0.9.0): Automatic PayrollPlan sync on EmployeeKPI approval
- **Bulk Operations** (NEW v0.9.0): Mass assign goals to multiple employees with single API call, validation & error handling

### Payroll Enhancements
- **Bonus Types**: FIXED, PERFORMANCE_BASED, MIXED bonus types
- **KPI Integration**: Link bonuses to KPI achievements
- **Auto-sync from KPI** (NEW v0.9.0): Calculated bonuses automatically update PayrollPlan when KPI approved
- **Analytics**: Breakdown of salary components (base, bonuses, etc.)

### Bank Transactions (v0.6.0) 🏦
- **Import from Excel**: Upload bank statements with auto-column detection
- **AI Classification**: Automatic categorization using keyword matching and historical data
- **Smart Matching**: Find matching expenses with scoring algorithm
- **Auto-categorization**: High confidence (>90%) categories applied automatically
- **Regular Patterns**: Detect recurring payments (subscriptions, rent)
- **Multi-status workflow**: NEW → CATEGORIZED → MATCHED → APPROVED
- **Reduces manual work by 80-90%** for recurring transactions

### Business Operation Mappings (v0.7.0) ⚙️
- **Visual UI**: Create/edit/delete mappings through web interface
- **AI Integration**: Direct integration with bank transaction classifier
- **Priority & Confidence**: Configurable parameters per mapping
- **Mass Operations**: Bulk activate/deactivate/delete mappings

### Credit Portfolio Management (v0.8.0) 💰
- **Financial Organizations**: Manage organizations and bank accounts
- **Credit Contracts**: Track credit agreements with terms and rates
- **Receipts & Expenses**: Monitor financial flows
- **FTP Auto-Import**: Automated data import from Excel via FTP
- **Analytics & KPI**: Monthly analytics and contract comparison
- **Cash Flow Analysis**: Forecast and track cash flow

### Revenue Budget (v0.8.0) 📈
- **Revenue Streams & Categories**: Manage revenue sources
- **Planning with Versioning**: Full approval workflow like expense budget
- **Revenue Actuals**: Track actual revenue vs plan
- **Customer Metrics**: LTV calculations and churn risk analysis
- **Seasonality**: Seasonal coefficients for forecasting
- **P&L Integration**: Combined revenue-expense profit & loss reports

### AI Invoice Processing (NEW) 🧾
- **OCR Recognition**: Tesseract-based PDF/image text extraction
- **AI Parsing**: VseGPT (GPT-4o-mini) for structured data extraction
- **Auto-extraction**: Invoice number, date, amount, contractor, line items
- **1C Integration**: Sync invoices to 1C Document_СчетНаОплату
- **Manual Review**: Correction workflow for AI results

### Background Automation (NEW) ⏰
- **APScheduler**: Automated task scheduling
- **1C Sync Jobs**: Hourly expense sync, daily catalog sync
- **FTP Monitoring**: Automated file import from FTP
- **Reports**: Scheduled daily/weekly/monthly reports
- **Maintenance**: Auto-cleanup and database optimization

### Founder Dashboard (NEW) 👔
- **Executive KPIs**: Cross-department high-level metrics
- **P&L Reports**: Consolidated profit & loss
- **Cash Flow Forecast**: Company-wide cash flow projections
- **Read-only Access**: FOUNDER role with view-only permissions

### 1C OData Integration (Expanded)
- **Expense Requests**: Automatic sync of spending requests
- **Catalog Sync**: Organizations, categories, contractors
- **Bank Transactions**: Import bank operations from 1C
- **Scheduled Jobs**: Automated hourly/daily sync via APScheduler

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

# 1C OData Integration
ODATA_1C_URL=http://10.10.100.77/trade/odata/standard.odata
ODATA_1C_USERNAME=odata.user
ODATA_1C_PASSWORD=ak228Hu2hbs28

# FTP Settings (Credit Portfolio Import)
FTP_HOST=ftp.example.com
FTP_PORT=21
FTP_USERNAME=import_user
FTP_PASSWORD=secure_password
FTP_DIRECTORY=/credit_portfolio/import
FTP_IMPORT_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Credit Portfolio
CREDIT_PORTFOLIO_AUTO_IMPORT=true
CREDIT_PORTFOLIO_NOTIFY_EMAIL=finance@company.com

# Invoice Processing (AI & OCR)
VSEGPT_API_KEY=your_vsegpt_api_key
VSEGPT_API_URL=https://api.vsegpt.ru/v1/chat/completions
VSEGPT_MODEL=openai/gpt-4o-mini
TESSERACT_CMD=/usr/bin/tesseract
TESSERACT_LANGUAGES=rus+eng
OCR_DPI=300
INVOICE_STORAGE_PATH=/app/storage/invoices
INVOICE_MAX_FILE_SIZE=10485760  # 10MB

# Background Scheduler (APScheduler)
SCHEDULER_ENABLED=true
SYNC_1C_EXPENSES_ENABLED=true
SYNC_1C_EXPENSES_SCHEDULE=0 * * * *  # Hourly
SYNC_1C_CATALOGS_ENABLED=true
SYNC_1C_CATALOGS_SCHEDULE=0 0 * * *  # Daily at midnight
FTP_IMPORT_ENABLED=true
DAILY_REPORT_ENABLED=true
DAILY_REPORT_SCHEDULE=0 8 * * *  # Daily at 8 AM
DAILY_REPORT_RECIPIENTS=finance@company.com,cfo@company.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true

# Redis (for rate limiting)
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

Located in `backend/scripts/` (68+ scripts):
- `import_excel.py` - Import budget data from Excel
- `import_plan_fact_2025.py` - Import plan/fact data for specific year
- `import_ai_categories.py` - Import AI classifier categories into budget_categories table
- `create_admin.py` - Create admin user
- `test_1c_expense_sync.py` - Test 1C expense sync integration
- `run_credit_portfolio_import.py` - Manual FTP import trigger
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
