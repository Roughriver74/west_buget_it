# План интеграции Acme Fin DWH в IT Budget Manager

## 🎯 Цель интеграции

Интегрировать модуль управления кредитным портфелем **Acme Fin DWH** в основную систему **IT Budget Manager** как новый раздел в меню "Финансы".

---

## 📊 Что интегрируем

### Источник: Acme Fin DWH
- **Путь**: `/Users/evgenijsikunov/projects/acme/acme_fin/acme-acme_fin`
- **Функционал**: Управление кредитным портфелем с автоматическим ETL из 1С
- **Технологии**: FastAPI + React + PostgreSQL + Redis

### Целевая система: IT Budget Manager
- **Путь**: `/Users/evgenijsikunov/projects/acme/acme_buget_it`
- **Архитектура**: Multi-tenancy с JWT auth и RBAC

---

## 🔧 Ключевые изменения

### 1. Адаптация под Multi-Tenancy

**КРИТИЧЕСКИ ВАЖНО:** Все таблицы Acme Fin должны получить `department_id`

```python
# ДО (acme_fin)
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

# ПОСЛЕ (acme_buget_it integration)
class FinOrganization(Base):
    __tablename__ = "fin_organizations"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)  # ДОБАВЛЕНО
    name = Column(String(255))

    department_rel = relationship("Department")
```

### 2. Переименование таблиц

Чтобы избежать конфликтов с существующими таблицами:

| Acme Fin | IT Budget Manager |
|----------|-------------------|
| `organizations` | `fin_organizations` |
| `bank_accounts` | `fin_bank_accounts` |
| `contracts` | `fin_contracts` |
| `receipts` | `fin_receipts` |
| `expenses` | `fin_expenses` |
| `expense_details` | `fin_expense_details` |
| `import_logs` | `fin_import_logs` |

### 3. Адаптация API Endpoints

```python
# Acme Fin имеет endpoints:
/api/receipts
/api/expenses
/api/analytics
/api/kpi

# В IT Budget Manager станут:
/api/v1/credit-portfolio/receipts
/api/v1/credit-portfolio/expenses
/api/v1/credit-portfolio/analytics
/api/v1/credit-portfolio/kpi
```

---

## 📝 Пошаговый план

### Этап 1: Backend - Модели данных

**Файл**: `backend/app/db/models.py`

1. Скопировать модели из acme_fin:
   - Organization → FinOrganization
   - BankAccount → FinBankAccount
   - Contract → FinContract
   - Receipt → FinReceipt
   - Expense → FinExpense
   - ExpenseDetail → FinExpenseDetail
   - ImportLog → FinImportLog

2. Добавить во все модели:
   ```python
   department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
   department_rel = relationship("Department")
   ```

3. Обновить relationships (переименовать модели)

### Этап 2: Backend - Pydantic Schemas

**Файл**: `backend/app/schemas/credit_portfolio.py` (создать новый)

1. Скопировать schemas из acme_fin
2. Добавить `department_id` в Create schemas (опционально для ADMIN/MANAGER)
3. Добавить `department_id` в InDB schemas (обязательно)

### Этап 3: Backend - Миграции

**Создать миграцию**:

```bash
cd backend
alembic revision --autogenerate -m "add credit portfolio tables from acme_fin"
alembic upgrade head
```

### Этап 4: Backend - API Endpoints

**Файл**: `backend/app/api/v1/credit_portfolio.py` (создать новый)

1. Скопировать endpoints из acme_fin/backend/app/api/:
   - `receipts.py` → `credit_portfolio/receipts` routes
   - `expenses.py` → `credit_portfolio/expenses` routes
   - `analytics.py` → `credit_portfolio/analytics` routes
   - `kpi.py` → `credit_portfolio/kpi` routes
   - `references.py` → `credit_portfolio/references` routes

2. Добавить во все endpoints:
   ```python
   @router.get("/receipts")
   async def get_receipts(
       department_id: Optional[int] = None,  # ДОБАВЛЕНО
       current_user: User = Depends(get_current_active_user),  # ДОБАВЛЕНО
       db: Session = Depends(get_db)
   ):
       query = db.query(FinReceipt)

       # Multi-tenancy filtering
       if current_user.role == UserRoleEnum.USER:
           query = query.filter(FinReceipt.department_id == current_user.department_id)
       elif department_id:
           query = query.filter(FinReceipt.department_id == department_id)

       return query.all()
   ```

3. Зарегистрировать router в `backend/app/api/v1/__init__.py`

### Этап 5: Backend - FTP Import Service

**Файл**: `backend/app/services/credit_portfolio_import.py` (создать новый)

1. Скопировать из acme_fin:
   - `services/ftp_client.py`
   - `services/parser.py`
   - `services/importer.py`

2. Адаптировать под multi-tenancy:
   ```python
   class CreditPortfolioImporter:
       def __init__(self, db: Session, department_id: int):
           self.db = db
           self.department_id = department_id  # ДОБАВЛЕНО

       def import_receipts(self, data: List[dict]):
           for item in data:
               item['department_id'] = self.department_id  # ДОБАВЛЕНО
               # ... остальная логика
   ```

### Этап 6: Backend - Scheduler (Опционально)

**Файл**: `backend/app/scheduler/credit_portfolio_scheduler.py`

1. Скопировать scheduler logic из acme_fin
2. Настроить для каждого department (если нужно)

### Этап 7: Frontend - API Client

**Файл**: `frontend/src/api/creditPortfolio.ts` (создать новый)

```typescript
import apiClient from './client'

export interface FinReceipt {
  id: number
  operation_id: string
  organization_id: number
  amount: number
  document_date: string
  department_id: number  // ДОБАВЛЕНО
  // ... остальные поля
}

export const creditPortfolioAPI = {
  // Receipts
  getReceipts: (params?: { department_id?: number }) =>
    apiClient.get<FinReceipt[]>('/api/v1/credit-portfolio/receipts', { params }),

  // Expenses
  getExpenses: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/expenses', { params }),

  // Analytics
  getAnalytics: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/analytics', { params }),

  // KPI
  getKPI: (params?: { department_id?: number }) =>
    apiClient.get('/api/v1/credit-portfolio/kpi', { params }),
}
```

### Этап 8: Frontend - Страницы

**Скопировать страницы** из `acme_fin/frontend/src/pages`:

1. `CreditPortfolioPage.tsx` (Dashboard)
2. `CreditPortfolioKPIPage.tsx` (KPI метрики)
3. `CreditPortfolioCashFlowPage.tsx` (Cash Flow)
4. `CreditPortfolioContractsPage.tsx` (Contracts)
5. `CreditPortfolioCalendarPage.tsx` (Calendar)

**Адаптировать под IT Budget Manager**:

```typescript
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioAPI } from '@/api/creditPortfolio'

const CreditPortfolioPage = () => {
  const { selectedDepartment } = useDepartment()  // ДОБАВЛЕНО

  const { data } = useQuery({
    queryKey: ['credit-receipts', selectedDepartment?.id],  // ДОБАВЛЕНО
    queryFn: () => creditPortfolioAPI.getReceipts({
      department_id: selectedDepartment?.id  // ДОБАВЛЕНО
    })
  })

  // ... остальная логика
}
```

### Этап 9: Frontend - Компоненты

**Скопировать компоненты** из `acme_fin/frontend/src/components`:

1. Скопировать все компоненты в `frontend/src/components/creditPortfolio/`
2. Адаптировать импорты
3. Добавить поддержку `useDepartment` hook

### Этап 10: Frontend - Маршрутизация

**Файл**: `frontend/src/App.tsx`

Добавить новые routes:

```typescript
import CreditPortfolioPage from '@/pages/CreditPortfolioPage'
import CreditPortfolioKPIPage from '@/pages/CreditPortfolioKPIPage'
// ... остальные импорты

// В Routes:
<Route
  path="/credit-portfolio"
  element={
    <ProtectedRoute requiredRoles={['USER', 'MANAGER', 'ADMIN']}>
      <CreditPortfolioPage />
    </ProtectedRoute>
  }
/>
<Route
  path="/credit-portfolio/kpi"
  element={
    <ProtectedRoute requiredRoles={['USER', 'MANAGER', 'ADMIN']}>
      <CreditPortfolioKPIPage />
    </ProtectedRoute>
  }
/>
```

### Этап 11: Frontend - Меню навигации

**Файл**: `frontend/src/components/common/AppLayout.tsx`

Добавить подраздел "Кредитный портфель" в раздел "Финансы":

```typescript
{
  key: 'finance',
  icon: <DollarOutlined />,
  label: 'Финансы',
  children: [
    {
      key: '/bank-transactions',
      label: 'Банковские операции',
    },
    // ДОБАВЛЕНО:
    {
      key: 'credit-portfolio-group',
      label: 'Кредитный портфель',
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
        {
          key: '/credit-portfolio/calendar',
          label: 'Календарь платежей',
        },
      ],
    },
  ],
},
```

### Этап 12: Права доступа (RBAC)

**По умолчанию** все роли имеют доступ к кредитному портфелю:

- **USER**: Видит только свой отдел (`department_id`)
- **MANAGER**: Видит все отделы (может фильтровать)
- **ADMIN**: Полный доступ
- **ACCOUNTANT**: Только просмотр (без редактирования)

**Если нужны специальные права** - добавить проверки в endpoints:

```python
if current_user.role == UserRoleEnum.ACCOUNTANT:
    # Только чтение, запретить POST/PUT/DELETE
    if request.method in ['POST', 'PUT', 'DELETE']:
        raise HTTPException(status_code=403, detail="Read-only access")
```

### Этап 13: Тестирование

1. **Backend тесты**:
   ```bash
   cd backend
   pytest tests/test_credit_portfolio.py -v
   ```

2. **Frontend тесты**:
   - Проверить загрузку всех страниц
   - Проверить фильтрацию по department_id
   - Проверить роли доступа

3. **Integration тесты**:
   - FTP импорт с department_id
   - API endpoints с multi-tenancy
   - Frontend с department selector

---

## 🔄 Процесс работы после интеграции

```
1. FTP → Автозагрузка XLSX (1С → FTP)
   ↓
2. Scheduler → Каждый день в 8:00 импорт
   ↓
3. Parser → Разбор XLSX файлов
   ↓
4. Importer → UPSERT в БД (с department_id)
   ↓
5. API → REST endpoints для фронтенда
   ↓
6. Frontend → Дашборды с фильтрацией по отделу
```

---

## 🎨 Новые страницы в меню

```
Финансы
├── Банковские операции
└── Кредитный портфель
    ├── Аналитика (Dashboard)
    ├── KPI метрики
    ├── Денежные потоки (Cash Flow)
    ├── Договоры (Contracts)
    └── Календарь платежей
```

---

## ⚠️ Важные моменты

### 1. Конфликты с существующими таблицами

В IT Budget Manager уже есть:
- `organizations` - для поставщиков/организаций
- `expenses` - для заявок на расход

В Acme Fin тоже есть:
- `organizations` - для организаций холдинга
- `expenses` - для списаний по кредитам

**Решение**: Переименовать все таблицы Acme Fin с префиксом `fin_`

### 2. Multi-tenancy обязателен

**КРИТИЧЕСКИ ВАЖНО**: Добавить `department_id` во ВСЕ таблицы и ВСЕ API endpoints.

### 3. FTP credentials

FTP учетные данные из Acme Fin:
```env
FTP_HOST=floppisw.beget.tech
FTP_USER=floppisw_fin
FTP_PASSWORD=G!5zb1FiL8!d
```

**Не хардкодить!** Добавить в `.env`:
```env
CREDIT_PORTFOLIO_FTP_HOST=...
CREDIT_PORTFOLIO_FTP_USER=...
CREDIT_PORTFOLIO_FTP_PASSWORD=...
```

### 4. Redis для кэширования

Acme Fin использует Redis для кэширования KPI метрик.

**Опция 1**: Использовать тот же Redis что и основная система
**Опция 2**: Отказаться от Redis (простые запросы с pagination)

### 5. Scheduler

Acme Fin использует APScheduler для автоматического импорта.

**Рекомендация**: Интегрировать в существующий scheduler (если есть) или создать отдельный background task.

---

## 📊 Ожидаемые результаты

### Backend
- ✅ 7 новых таблиц с `department_id`
- ✅ ~30 новых API endpoints
- ✅ FTP import service с multi-tenancy
- ✅ Scheduler для автоматического импорта

### Frontend
- ✅ 5 новых страниц с аналитикой
- ✅ ~20 новых компонентов
- ✅ Интеграция с `useDepartment` hook
- ✅ Подраздел "Кредитный портфель" в меню

### Database
- ✅ ~10,000+ записей (поступления + списания)
- ✅ Справочники (организации, счета, договоры)
- ✅ История импортов

---

## 🚀 Следующие шаги

1. ✅ Изучить структуру Acme Fin (DONE)
2. ✅ Создать план интеграции (DONE)
3. ⏳ Адаптировать модели под multi-tenancy
4. ⏳ Скопировать и адаптировать backend
5. ⏳ Создать миграции
6. ⏳ Скопировать и адаптировать frontend
7. ⏳ Добавить в меню
8. ⏳ Протестировать

---

## 📞 Вопросы для уточнения

1. **FTP доступ**: Нужен ли автоматический импорт или достаточно ручной загрузки?
2. **Роли**: Все роли имеют доступ или только MANAGER/ADMIN?
3. **Redis**: Использовать Redis для кэширования или обойтись без него?
4. **Scheduler**: Создать отдельный или интегрировать в существующий?
5. **Multi-tenancy**: Каждый отдел свой FTP или общий?

---

**Готов начать интеграцию!** 🚀
