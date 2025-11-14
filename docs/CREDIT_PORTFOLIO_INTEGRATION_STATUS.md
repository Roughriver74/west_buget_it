# Статус интеграции Credit Portfolio

## ✅ Выполнено

### 1. Backend Models (models.py)
**Файл**: `backend/app/db/models.py`

Добавлено 7 новых моделей с multi-tenancy:
- ✅ `FinOrganization` - организации холдинга
- ✅ `FinBankAccount` - банковские счета
- ✅ `FinContract` - кредитные договоры
- ✅ `FinReceipt` - поступления кредитов
- ✅ `FinExpense` - списания по кредитам
- ✅ `FinExpenseDetail` - расшифровка платежей (тело/проценты)
- ✅ `FinImportLog` - журнал импорта из 1С

**Ключевые особенности**:
- Все таблицы с префиксом `fin_` (избежать конфликтов)
- Все таблицы имеют `department_id` для multi-tenancy
- Unique constraints на key fields + department_id
- Relationships настроены корректно

---

## 🔄 В процессе / Требуется выполнить

### 2. Pydantic Schemas

**Создать файл**: `backend/app/schemas/credit_portfolio.py`

<details>
<summary>Готовый код для schemas</summary>

```python
"""
Pydantic schemas for Credit Portfolio
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ==================== FinOrganization ====================

class FinOrganizationBase(BaseModel):
    name: str = Field(..., description="Название организации")
    inn: Optional[str] = Field(None, description="ИНН")
    is_active: bool = Field(True, description="Активность")


class FinOrganizationCreate(FinOrganizationBase):
    department_id: Optional[int] = Field(None, description="ID отдела (опционально для ADMIN/MANAGER)")


class FinOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    is_active: Optional[bool] = None


class FinOrganizationInDB(FinOrganizationBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinBankAccount ====================

class FinBankAccountBase(BaseModel):
    account_number: str = Field(..., description="Номер счета")
    bank_name: Optional[str] = Field(None, description="Название банка")
    is_active: bool = Field(True, description="Активность")


class FinBankAccountCreate(FinBankAccountBase):
    department_id: Optional[int] = Field(None)


class FinBankAccountUpdate(BaseModel):
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = None


class FinBankAccountInDB(FinBankAccountBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinContract ====================

class FinContractBase(BaseModel):
    contract_number: str = Field(..., description="Номер договора")
    contract_date: Optional[date] = Field(None, description="Дата договора")
    contract_type: Optional[str] = Field(None, description="Тип договора (Кредит, Заем)")
    counterparty: Optional[str] = Field(None, description="Контрагент")
    is_active: bool = Field(True, description="Активность")


class FinContractCreate(FinContractBase):
    department_id: Optional[int] = None


class FinContractUpdate(BaseModel):
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    contract_type: Optional[str] = None
    counterparty: Optional[str] = None
    is_active: Optional[bool] = None


class FinContractInDB(FinContractBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinReceipt ====================

class FinReceiptBase(BaseModel):
    operation_id: str
    organization_id: int
    bank_account_id: Optional[int] = None
    contract_id: Optional[int] = None
    operation_type: Optional[str] = None
    accounting_account: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    payer: Optional[str] = None
    payer_account: Optional[str] = None
    settlement_account: Optional[str] = None
    contract_date: Optional[date] = None
    currency: str = "RUB"
    amount: Decimal
    commission: Optional[Decimal] = None
    payment_purpose: Optional[str] = None
    responsible_person: Optional[str] = None
    comment: Optional[str] = None


class FinReceiptCreate(FinReceiptBase):
    department_id: Optional[int] = None


class FinReceiptInDB(FinReceiptBase):
    id: int
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinExpense ====================

class FinExpenseBase(BaseModel):
    operation_id: str
    organization_id: int
    bank_account_id: Optional[int] = None
    contract_id: Optional[int] = None
    operation_type: Optional[str] = None
    accounting_account: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    recipient: Optional[str] = None
    recipient_account: Optional[str] = None
    debit_account: Optional[str] = None
    contract_date: Optional[date] = None
    currency: str = "RUB"
    amount: Decimal
    expense_article: Optional[str] = None
    payment_purpose: Optional[str] = None
    responsible_person: Optional[str] = None
    comment: Optional[str] = None
    tax_period: Optional[str] = None
    unconfirmed_by_bank: bool = False


class FinExpenseCreate(FinExpenseBase):
    department_id: Optional[int] = None


class FinExpenseInDB(FinExpenseBase):
    id: int
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinExpenseDetail ====================

class FinExpenseDetailBase(BaseModel):
    expense_operation_id: str
    contract_number: Optional[str] = None
    repayment_type: Optional[str] = None
    settlement_account: Optional[str] = None
    advance_account: Optional[str] = None
    payment_type: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    settlement_rate: Decimal = Decimal("1.0")
    settlement_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    expense_amount: Optional[Decimal] = None
    vat_in_expense: Optional[Decimal] = None


class FinExpenseDetailCreate(FinExpenseDetailBase):
    department_id: Optional[int] = None


class FinExpenseDetailInDB(FinExpenseDetailBase):
    id: int
    department_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== FinImportLog ====================

class FinImportLogInDB(BaseModel):
    id: int
    import_date: datetime
    source_file: Optional[str]
    table_name: Optional[str]
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_failed: int = 0
    status: Optional[str]
    error_message: Optional[str]
    processed_by: Optional[str]
    processing_time_seconds: Optional[Decimal]
    department_id: int

    class Config:
        from_attributes = True
```

</details>

### 3. Database Migration

**Шаг 1**: Исправить .env файл:
```bash
cd backend
# Изменить DEBUG=WARN на DEBUG=True в .env
```

**Шаг 2**: Создать и применить миграцию:
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "add credit portfolio tables"
alembic upgrade head
```

### 4. Backend API Endpoints

**Создать файл**: `backend/app/api/v1/credit_portfolio.py`

Этот файл будет содержать все API endpoints. Рекомендуется:
1. Скопировать endpoints из west_fin
2. Адаптировать под multi-tenancy
3. Добавить проверку ролей (MANAGER, ADMIN, ACCOUNTANT)

**Затем зарегистрировать** в `backend/app/api/v1/__init__.py`:
```python
from app.api.v1 import credit_portfolio

# В функции include_api_routes():
app.include_router(
    credit_portfolio.router,
    prefix="/api/v1/credit-portfolio",
    tags=["Credit Portfolio"]
)
```

### 5. FTP Import Service

**Создать файлы**:
- `backend/app/services/credit_portfolio_ftp.py` - FTP клиент
- `backend/app/services/credit_portfolio_parser.py` - парсер XLSX
- `backend/app/services/credit_portfolio_importer.py` - импорт в БД

**Скопировать из**: `/Users/evgenijsikunov/projects/west/west_fin/west-west_fin/backend/app/services/`

### 6. Scheduler для автоматического импорта

**Если scheduler уже есть**, добавить задачу:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def import_credit_data():
    # Вызвать FTP import service
    pass

scheduler.add_job(
    import_credit_data,
    'cron',
    hour=8,
    minute=0,
    timezone='Europe/Moscow'
)
```

### 7. Frontend - Меню навигации

**Файл**: `frontend/src/components/common/AppLayout.tsx`

**Создать раздел "Финансы"**:

```typescript
// Найти существующий код меню и добавить:
{
  key: 'finance',
  icon: <DollarOutlined />,
  label: 'Финансы',
  children: [
    {
      key: '/bank-transactions',
      label: 'Банковские операции',
      icon: <BankOutlined />,
    },
    {
      key: 'credit-portfolio',
      label: 'Кредитный портфель',
      icon: <CreditCardOutlined />,
      children: [
        {
          key: '/credit-portfolio',
          label: 'Аналитика',
        },
        {
          key: '/credit-portfolio/kpi',
          label: 'KPI метрики',
        },
        {
          key: '/credit-portfolio/cash-flow',
          label: 'Денежные потоки',
        },
        {
          key: '/credit-portfolio/contracts',
          label: 'Договоры',
        },
      ],
    },
  ],
},
```

### 8. Frontend - Страницы

**Скопировать страницы** из west_fin:
```bash
cp -r /Users/evgenijsikunov/projects/west/west_fin/west-west_fin/frontend/src/pages/* \
      frontend/src/pages/
```

**Адаптировать каждую страницу**:
1. Добавить `import { useDepartment } from '@/contexts/DepartmentContext'`
2. Добавить `const { selectedDepartment } = useDepartment()`
3. Передавать `department_id: selectedDepartment?.id` в API вызовы

### 9. Frontend - API Client

**Создать файл**: `frontend/src/api/creditPortfolio.ts`

```typescript
import apiClient from './client'

export const creditPortfolioAPI = {
  // Organizations
  getOrganizations: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/organizations', { params }),

  // Receipts
  getReceipts: (params?: { department_id?: number; date_from?: string; date_to?: string }) =>
    apiClient.get('/api/v1/credit-portfolio/receipts', { params }),

  // Expenses
  getExpenses: (params?: { department_id?: number; date_from?: string; date_to?: string }) =>
    apiClient.get('/api/v1/credit-portfolio/expenses', { params }),

  // Analytics
  getAnalytics: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/analytics', { params }),

  // KPI
  getKPI: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/kpi', { params }),

  // Import
  triggerImport: () =>
    apiClient.post('/api/v1/credit-portfolio/import/trigger'),
}
```

### 10. Права доступа (RBAC)

**В каждом endpoint** добавить проверку:

```python
@router.get("/receipts")
async def get_receipts(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Проверка роли
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN, UserRoleEnum.ACCOUNTANT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only MANAGER, ADMIN, ACCOUNTANT roles allowed"
        )

    # Multi-tenancy filtering (ACCOUNTANT тоже может фильтровать)
    query = db.query(FinReceipt)
    if department_id:
        query = query.filter(FinReceipt.department_id == department_id)

    return query.all()
```

**На frontend** в ProtectedRoute:
```typescript
<Route
  path="/credit-portfolio"
  element={
    <ProtectedRoute requiredRoles={['MANAGER', 'ADMIN', 'ACCOUNTANT']}>
      <CreditPortfolioPage />
    </ProtectedRoute>
  }
/>
```

---

## 📊 Новая структура меню

```
Бюджет
├── Панель управления
├── Расходы
├── Бюджет
└── ...

Финансы (НОВЫЙ РАЗДЕЛ)
├── Банковские операции (переехал сюда)
└── Кредитный портфель (НОВЫЙ)
    ├── Аналитика
    ├── KPI метрики
    ├── Денежные потоки
    └── Договоры

Фонд оплаты труда
├── Сотрудники
└── ...

Аналитика
└── ...

Справочники
└── ...

Настройки
└── ...
```

---

## 🚀 Пошаговая инструкция для завершения

### Этап 1: Backend миграция
```bash
cd backend
# 1. Исправить .env: DEBUG=True
nano .env

# 2. Создать schemas
# Создать файл backend/app/schemas/credit_portfolio.py (код выше)

# 3. Создать миграцию
source venv/bin/activate
alembic revision --autogenerate -m "add credit portfolio tables"
alembic upgrade head
```

### Этап 2: Backend API (упрощенная версия)
```bash
# Скопировать сервисы из west_fin
cp /Users/evgenijsikunov/projects/west/west_fin/west-west_fin/backend/app/services/ftp_client.py \
   backend/app/services/credit_portfolio_ftp.py

# Создать базовый API endpoint (можно начать с простого)
# backend/app/api/v1/credit_portfolio.py
```

### Этап 3: Frontend меню и роутинг
```bash
# 1. Обновить меню (AppLayout.tsx)
# 2. Скопировать страницы из west_fin
# 3. Создать API client
# 4. Настроить маршрутизацию
```

### Этап 4: Тестирование
```bash
# Запустить систему
./run.sh

# Проверить:
# 1. Миграции применились
# 2. API endpoints доступны
# 3. Меню отображается
# 4. Права доступа работают
```

---

## ⚠️ Важные моменты

1. **Конфликт таблиц**: Все таблицы West Fin переименованы с префиксом `fin_`
2. **Multi-tenancy обязателен**: Все таблицы имеют `department_id`
3. **Роли доступа**: Только MANAGER, ADMIN, ACCOUNTANT (НЕТ USER)
4. **FTP credentials**: Добавить в .env (не хардкодить!)
5. **Redis**: Опционально, можно добавить позже

---

## 📞 Следующие шаги

Готов помочь с любым из этапов интеграции! Просто скажите:
- "Создай schemas"
- "Создай API endpoints"
- "Настрой frontend меню"
- "Добавь FTP import"
- И т.д.

**Интеграция готова к завершению!** 🚀
