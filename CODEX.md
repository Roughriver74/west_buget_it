# CODEX.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IT Budget Manager** - Full-stack web application for managing IT department budgets with expense tracking, forecasting, payroll management, and analytics. Written in Russian for Russian-speaking organizations.

**Stack**: FastAPI + React/TypeScript + PostgreSQL + Docker

## Development Commands

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
pytest                      # Run tests (when implemented)
```

### Frontend (React + Vite)
```bash
cd frontend

npm install                 # Install dependencies
npm run dev                 # Development server (port 5173)
npm run build               # Production build
npm run preview             # Preview production build
npm run lint                # Run ESLint
```

### Database Access
```bash
# PostgreSQL connection
docker exec -it it_budget_db psql -U budget_user -d it_budget_db

# Connection string
postgresql://budget_user:budget_pass@localhost:54329/it_budget_db
```

### Data Import
```bash
cd backend
python scripts/import_excel.py --file ../IT_Budget_Analysis_Full.xlsx
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

Three roles with different access levels:

- **USER**: Only sees their own department data
- **MANAGER**: Can view and filter all departments
- **ADMIN**: Full system access + user management

Check roles on both backend (API endpoints) and frontend (UI components).

## High-Level Architecture

### Backend Structure (`backend/app/`)
```
api/v1/              # API endpoints (17 modules)
├── auth.py          # Authentication & JWT
├── expenses.py      # Expense management
├── budget.py        # Budget planning & tracking
├── forecast.py      # Forecasting & predictions
├── payroll.py       # Payroll & employee management
├── analytics.py     # Analytics & reporting
├── departments.py   # Department management
├── audit.py         # Audit logging
└── ...              # Other endpoints

db/
├── models.py        # SQLAlchemy models (all entities)
└── session.py       # Database session management

core/
└── config.py        # Settings & configuration

schemas/             # Pydantic schemas (15+ files)
services/            # Business logic services
middleware/          # Custom middleware (rate limiting)
utils/               # Utilities & logging
```

### Frontend Structure (`frontend/src/`)
```
pages/               # 27 page components
├── DashboardPage.tsx
├── ExpensesPage.tsx
├── BudgetPlanPage.tsx
├── PayrollPlanPage.tsx
└── ...

components/          # Reusable components
├── common/          # Shared components (AppLayout, etc.)
├── budget/          # Budget-specific components
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
- `forecast_expenses` - Forecasted expenses
- `employees` - Employee records
- `payroll_plans` - Payroll planning
- `payroll_actuals` - Actual payroll payments
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

## Important Development Patterns

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

### Error Handling

**Backend**: All exceptions logged via `app/utils/logger.py`. Global exception handlers in `app/main.py`.
**Frontend**: ErrorBoundary component wraps app for React error catching.

### Rate Limiting

Backend has rate limiting: **100 requests/minute**, **1000 requests/hour** per IP.

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
```

### Frontend Environment Variables (`.env`)
```bash
VITE_API_URL=http://localhost:8000
```

## Testing Strategy

- USER role: Verify they only see their department
- MANAGER/ADMIN roles: Verify department filtering works
- Test department switching updates all data
- Verify JWT authentication on all protected routes

## Key Files to Reference

**Backend Examples**:
- `backend/app/api/v1/expenses.py` - Complete CRUD with roles & filtering
- `backend/app/api/v1/analytics.py` - Complex queries with aggregations
- `backend/app/db/models.py` - All database models

**Frontend Examples**:
- `frontend/src/pages/ExpensesPage.tsx` - Full page with useDepartment
- `frontend/src/components/common/AppLayout.tsx` - Layout & navigation
- `frontend/src/contexts/DepartmentContext.tsx` - Department selection

**Documentation**:
- `DEVELOPMENT_PRINCIPLES.md` - **CRITICAL**: Mandatory security & architecture rules
- `ROADMAP.md` - Project history and future plans
- `README.md` - Quick start guide

## Common Scripts

Located in `backend/scripts/`:
- `import_excel.py` - Import budget data from Excel
- `create_admin.py` - Create admin user
- Various utility scripts for data management

## Docker Services

Defined in `docker-compose.yml`:
- **db**: PostgreSQL 15 (port 54329)
- **backend**: FastAPI (port 8000)
- **frontend**: React/Vite (port 5173)

## Security Notes

⚠️ **PRODUCTION REQUIREMENTS**:
- Change `SECRET_KEY` to strong random value (min 32 chars)
- Set `DEBUG=False`
- Configure proper CORS origins
- Use HTTPS
- Review rate limiting settings
- Enable Redis for distributed rate limiting

## Debugging

**Backend logs**: `tail -f backend.log`
**Frontend logs**: `tail -f frontend.log`
**Process IDs**: Check `backend.pid`, `frontend.pid`

## Known Limitations

- Rate limiting is in-memory (use Redis for production)
- File uploads limited to 10MB
- Excel import limited to specific formats
- No email verification yet
- No password recovery yet
