# KPI Admin Guide - Руководство администратора

**Версия**: 1.0
**Дата**: Ноябрь 2025
**Целевая аудитория**: Администраторы (роль ADMIN)

---

## 📚 Содержание

1. [Введение](#введение)
2. [Архитектура системы](#архитектура-системы)
3. [Backend API](#backend-api)
4. [Модели данных](#модели-данных)
5. [Workflow и статусы](#workflow-и-статусы)
6. [Автоматические процессы](#автоматические-процессы)
7. [Импорт и экспорт](#импорт-и-экспорт)
8. [Мониторинг и логирование](#мониторинг-и-логирование)
9. [Troubleshooting](#troubleshooting)

---

## Введение

Это руководство предназначено для администраторов системы KPI Management. Здесь описаны технические детали, API, модели данных, и процедуры обслуживания.

### Основные компоненты

**Backend**:
- FastAPI + SQLAlchemy
- PostgreSQL database
- Pydantic schemas для валидации

**Frontend**:
- React + TypeScript
- Ant Design UI library
- React Query для state management
- recharts для визуализации

**Интеграции**:
- PayrollPlan - автоматическая синхронизация бонусов
- Department-based multi-tenancy
- Role-based access control (USER/MANAGER/ADMIN)

---

## Архитектура системы

### Обзор компонентов

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                      │
│  ┌──────────────┬─────────────────┬──────────────────┐ │
│  │  Dashboard   │  Wizard         │  Tables & Forms  │ │
│  │  (charts)    │  (3 steps)      │  (CRUD)          │ │
│  └──────────────┴─────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ▼ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                Backend API (FastAPI)                    │
│  ┌──────────────┬─────────────────┬──────────────────┐ │
│  │  /kpi/*      │  /analytics/*   │  /recalculate/*  │ │
│  │  CRUD        │  Dashboard      │  Auto-calc       │ │
│  └──────────────┴─────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ▼ ORM
┌─────────────────────────────────────────────────────────┐
│               Database (PostgreSQL)                     │
│  ┌──────────────┬─────────────────┬──────────────────┐ │
│  │ employee_kpis│  kpi_goals      │  goal_achievements│
│  │ kpi_goals    │  payroll_plans  │  (multi-tenant)  │ │
│  └──────────────┴─────────────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Multi-Tenancy

**Все данные KPI привязаны к `department_id`**:

- `employee_kpis.department_id`
- `kpi_goals.department_id`
- `goal_achievements.department_id`

**Фильтрация по ролям**:

- **USER**: видит только свой отдел (`WHERE department_id = user.department_id`)
- **MANAGER**: может выбирать отдел (`WHERE department_id = ?` или все отделы)
- **ADMIN**: полный доступ ко всем отделам

---

## Backend API

### Base URL

```
http://localhost:8000/api/v1/kpi
```

### Authentication

Все endpoint требуют JWT-авторизации:

```bash
Authorization: Bearer <token>
```

### Основные endpoints

#### Employee KPI

```bash
# List employee KPIs
GET /api/v1/kpi/employee-kpis
  ?department_id=1
  &year=2025
  &month=11
  &status=APPROVED

# Get single KPI
GET /api/v1/kpi/employee-kpis/{id}

# Create KPI
POST /api/v1/kpi/employee-kpis
{
  "employee_id": 5,
  "year": 2025,
  "month": 11,
  "department_id": 1,
  "kpi_percentage": null,
  "monthly_bonus_base": 50000,
  "monthly_bonus_type": "PERFORMANCE_BASED",
  ...
}

# Update KPI
PUT /api/v1/kpi/employee-kpis/{id}
{
  "kpi_percentage": 95.5,
  "monthly_bonus_base": 60000
}

# Delete KPI
DELETE /api/v1/kpi/employee-kpis/{id}
```

#### Goals

```bash
# List goals
GET /api/v1/kpi/goals
  ?department_id=1
  &year=2025
  &status=ACTIVE

# Create goal
POST /api/v1/kpi/goals
{
  "name": "Выручка Q4",
  "description": "Достичь 5М выручки",
  "target_value": 5000000,
  "measurement_unit": "руб",
  "year": 2025,
  "month": null,
  "department_id": 1
}

# Update goal
PUT /api/v1/kpi/goals/{id}

# Delete goal
DELETE /api/v1/kpi/goals/{id}
```

#### Goal Assignments

```bash
# List assignments
GET /api/v1/kpi/assignments
  ?employee_kpi_id=42
  &department_id=1

# Create assignment
POST /api/v1/kpi/assignments
{
  "employee_kpi_id": 42,
  "goal_id": 5,
  "weight": 40,
  "target_value": 100,
  "status": "ACTIVE",
  "department_id": 1
}

# Update assignment
PUT /api/v1/kpi/assignments/{id}
{
  "actual_value": 95,
  "achievement_percentage": 95.0,
  "status": "ACHIEVED"
}

# Delete assignment
DELETE /api/v1/kpi/assignments/{id}
```

#### Recalculation

```bash
# Recalculate single employee KPI
POST /api/v1/kpi/recalculate/{employee_kpi_id}

# Response:
{
  "success": true,
  "data": {
    "kpi_percentage": 92.5,
    "goals_count": 3,
    "weighted_achievement": 92.5
  }
}

# Recalculate all KPIs for department
POST /api/v1/kpi/recalculate/department
{
  "department_id": 1,
  "year": 2025
}

# Response:
{
  "success": true,
  "statistics": {
    "total": 50,
    "success": 48,
    "errors": 2
  }
}
```

#### Analytics

```bash
# Dashboard data
GET /api/v1/kpi/analytics/dashboard
  ?year=2025
  &department_id=1

# Response:
{
  "overview": {
    "total_kpis": 50,
    "avg_kpi_percentage": 87.5,
    "total_bonuses": 2500000,
    "unique_employees": 25,
    "total_goals": 10,
    "active_goals": 8
  },
  "status_distribution": [...],
  "monthly_trends": [...],
  "top_employees": [...]
}

# KPI trends by employee
GET /api/v1/kpi/analytics/kpi-trends
  ?year=2025
  &employee_id=5

# Summary statistics
GET /api/v1/kpi/analytics/summary
  ?department_id=1
  &year=2025
```

---

## Модели данных

### EmployeeKPI (employee_kpis)

**Главная таблица** с записями KPI для сотрудников.

```python
class EmployeeKPI(Base):
    __tablename__ = "employee_kpis"

    id: int                          # PK
    employee_id: int                 # FK -> employees.id
    department_id: int               # FK -> departments.id (multi-tenancy)
    year: int                        # Год KPI
    month: int                       # Месяц KPI (1-12)

    # KPI calculation
    kpi_percentage: Decimal          # % выполнения (nullable, auto-calculated)

    # Status workflow
    status: Enum                     # DRAFT, UNDER_REVIEW, APPROVED, REJECTED

    # Monthly bonus
    monthly_bonus_base: Decimal      # База месячного бонуса
    monthly_bonus_type: Enum         # PERFORMANCE_BASED, FIXED, MIXED
    monthly_bonus_multiplier: Decimal # Множитель
    monthly_bonus_fixed_part: Decimal # Фиксированная часть (для MIXED)
    monthly_bonus_calculated: Decimal # Рассчитанный бонус (auto)

    # Quarterly bonus
    quarterly_bonus_base: Decimal
    quarterly_bonus_type: Enum
    quarterly_bonus_multiplier: Decimal
    quarterly_bonus_fixed_part: Decimal
    quarterly_bonus_calculated: Decimal

    # Annual bonus
    annual_bonus_base: Decimal
    annual_bonus_type: Enum
    annual_bonus_multiplier: Decimal
    annual_bonus_fixed_part: Decimal
    annual_bonus_calculated: Decimal

    # Depremium
    depremium_threshold: Decimal     # Порог KPI% для депремирования

    # Relations
    goal_achievements: List[GoalAchievement]
    payroll_plan: PayrollPlan        # Auto-synced

    # Metadata
    comment: str
    notes: str                       # System notes (approvals, etc.)
    created_at: DateTime
    updated_at: DateTime
```

### KPIGoal (kpi_goals)

**Таблица целей**.

```python
class KPIGoal(Base):
    __tablename__ = "kpi_goals"

    id: int
    name: str                        # Название цели
    description: str
    department_id: int               # FK -> departments.id

    # Target
    target_value: Decimal            # Целевое значение
    measurement_unit: str            # Единица измерения

    # Period
    year: int
    month: int                       # Null = годовая цель

    # Status
    status: Enum                     # DRAFT, ACTIVE, ACHIEVED, NOT_ACHIEVED, CANCELLED

    # Metadata
    created_at: DateTime
    updated_at: DateTime
```

### GoalAchievement (goal_achievements)

**Таблица связей** между EmployeeKPI и Goals (назначения целей).

```python
class GoalAchievement(Base):
    __tablename__ = "goal_achievements"

    id: int
    employee_kpi_id: int             # FK -> employee_kpis.id
    goal_id: int                     # FK -> kpi_goals.id
    department_id: int               # FK -> departments.id

    # Weight
    weight: Decimal                  # Вес цели (0-100%)

    # Achievement
    target_value: Decimal            # Целевое значение (override)
    actual_value: Decimal            # Фактическое значение
    achievement_percentage: Decimal  # % достижения (auto-calculated)

    # Status
    status: Enum                     # DRAFT, ACTIVE, ACHIEVED, NOT_ACHIEVED, CANCELLED

    # Metadata
    created_at: DateTime
    updated_at: DateTime
```

### Индексы

**Критичные индексы для производительности**:

```sql
-- employee_kpis
CREATE INDEX ix_employee_kpis_department_id ON employee_kpis(department_id);
CREATE INDEX ix_employee_kpis_employee_id ON employee_kpis(employee_id);
CREATE INDEX ix_employee_kpis_year ON employee_kpis(year);
CREATE INDEX ix_employee_kpis_status ON employee_kpis(status);
CREATE INDEX ix_employee_kpis_year_month ON employee_kpis(year, month);

-- kpi_goals
CREATE INDEX ix_kpi_goals_department_id ON kpi_goals(department_id);
CREATE INDEX ix_kpi_goals_year ON kpi_goals(year);
CREATE INDEX ix_kpi_goals_status ON kpi_goals(status);

-- goal_achievements
CREATE INDEX ix_goal_achievements_employee_kpi_id ON goal_achievements(employee_kpi_id);
CREATE INDEX ix_goal_achievements_goal_id ON goal_achievements(goal_id);
CREATE INDEX ix_goal_achievements_department_id ON goal_achievements(department_id);
```

---

## Workflow и статусы

### Enum: KPIStatus

```python
class KPIStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"                  # Черновик
    UNDER_REVIEW = "UNDER_REVIEW"    # На проверке
    APPROVED = "APPROVED"            # Утверждено
    REJECTED = "REJECTED"            # Отклонено
```

### Допустимые переходы

```
DRAFT → UNDER_REVIEW
UNDER_REVIEW → APPROVED
UNDER_REVIEW → REJECTED
UNDER_REVIEW → DRAFT (return for correction)
REJECTED → DRAFT (return for correction)
```

### Проверки при переходе UNDER_REVIEW → APPROVED

```python
def validate_for_approval(employee_kpi: EmployeeKPI) -> bool:
    # 1. Check sum(weights) = 100%
    assignments = employee_kpi.goal_achievements
    total_weight = sum([a.weight for a in assignments])
    if total_weight != 100:
        raise ValueError(f"Sum of weights must be 100%, got {total_weight}%")

    # 2. Check at least one goal assigned
    if len(assignments) == 0:
        raise ValueError("At least one goal must be assigned")

    # 3. Check all goals are ACTIVE
    for assignment in assignments:
        if assignment.status != KPIGoalStatus.ACTIVE:
            raise ValueError(f"Goal {assignment.goal_id} is not ACTIVE")

    return True
```

### Автоматические действия при APPROVED

```python
async def on_kpi_approved(employee_kpi: EmployeeKPI, db: Session):
    # 1. Recalculate KPI% if not set
    if employee_kpi.kpi_percentage is None:
        kpi_percentage = calculate_kpi_percentage(employee_kpi)
        employee_kpi.kpi_percentage = kpi_percentage

    # 2. Recalculate bonuses
    calculate_bonuses(employee_kpi)

    # 3. Sync to PayrollPlan
    sync_to_payroll_plan(employee_kpi, db)

    # 4. Log approval
    employee_kpi.notes += f"\n[{datetime.utcnow()}] Approved by {current_user.id}"

    db.commit()
```

---

## Автоматические процессы

### 1. Расчет KPI%

**Формула**:

```
KPI% = Σ (achievement_percentage × weight) / 100
```

**Пример**:

```python
# Assignments:
# - Goal 1: achievement = 95%, weight = 40%
# - Goal 2: achievement = 85%, weight = 30%
# - Goal 3: achievement = 100%, weight = 30%

kpi_percentage = (95 * 40 + 85 * 30 + 100 * 30) / 100
              = (3800 + 2550 + 3000) / 100
              = 92.5%
```

**Код**:

```python
def calculate_kpi_percentage(employee_kpi: EmployeeKPI) -> Decimal:
    assignments = employee_kpi.goal_achievements

    if not assignments:
        return Decimal(0)

    total_weight = sum([a.weight for a in assignments if a.status == "ACTIVE"])

    if total_weight == 0:
        return Decimal(0)

    weighted_sum = sum([
        a.achievement_percentage * a.weight
        for a in assignments
        if a.status == "ACTIVE"
    ])

    kpi_percentage = weighted_sum / total_weight

    return Decimal(kpi_percentage).quantize(Decimal("0.01"))
```

### 2. Расчет бонусов

**Типы бонусов**:

1. **PERFORMANCE_BASED**:
   ```
   bonus = base × (KPI% / 100) × multiplier
   ```

2. **FIXED**:
   ```
   bonus = base × multiplier
   ```

3. **MIXED**:
   ```
   fixed_part = base × (fixed_part_percent / 100) × multiplier
   performance_part = base × (1 - fixed_part_percent / 100) × (KPI% / 100) × multiplier
   bonus = fixed_part + performance_part
   ```

**Депремирование**:

```python
if kpi_percentage < depremium_threshold:
    bonus = 0
```

**Код**:

```python
def calculate_bonus(
    base: Decimal,
    bonus_type: BonusType,
    kpi_percentage: Decimal,
    multiplier: Decimal,
    fixed_part: Decimal,
    depremium_threshold: Decimal
) -> Decimal:
    # Check depremium
    if kpi_percentage < depremium_threshold:
        return Decimal(0)

    if bonus_type == BonusType.PERFORMANCE_BASED:
        return base * (kpi_percentage / 100) * multiplier

    elif bonus_type == BonusType.FIXED:
        return base * multiplier

    elif bonus_type == BonusType.MIXED:
        fixed = base * (fixed_part / 100) * multiplier
        performance = base * (1 - fixed_part / 100) * (kpi_percentage / 100) * multiplier
        return fixed + performance

    return Decimal(0)
```

### 3. Синхронизация с PayrollPlan

**При утверждении KPI (APPROVED)**:

```python
def sync_to_payroll_plan(employee_kpi: EmployeeKPI, db: Session):
    # Find or create PayrollPlan record
    payroll_plan = db.query(PayrollPlan).filter(
        PayrollPlan.employee_id == employee_kpi.employee_id,
        PayrollPlan.year == employee_kpi.year,
        PayrollPlan.month == employee_kpi.month,
        PayrollPlan.department_id == employee_kpi.department_id
    ).first()

    if not payroll_plan:
        payroll_plan = PayrollPlan(
            employee_id=employee_kpi.employee_id,
            year=employee_kpi.year,
            month=employee_kpi.month,
            department_id=employee_kpi.department_id
        )
        db.add(payroll_plan)

    # Update bonuses
    payroll_plan.monthly_bonus = employee_kpi.monthly_bonus_calculated
    payroll_plan.quarterly_bonus = employee_kpi.quarterly_bonus_calculated
    payroll_plan.annual_bonus = employee_kpi.annual_bonus_calculated

    # Log sync
    payroll_plan.notes += f"\n[{datetime.utcnow()}] Synced from EmployeeKPI #{employee_kpi.id}"

    db.commit()
```

---

## Импорт и экспорт

### Импорт из Excel

**Endpoint**:

```bash
POST /api/v1/kpi/import/employee-kpis
Content-Type: multipart/form-data

file: <excel_file>
department_id: 1
```

**Формат Excel**:

| employee_id | year | month | kpi_percentage | monthly_bonus_base | monthly_bonus_type | ... |
|-------------|------|-------|----------------|--------------------|--------------------|-----|
| 5           | 2025 | 11    | 95.0           | 50000              | PERFORMANCE_BASED  | ... |
| 6           | 2025 | 11    | 87.5           | 60000              | MIXED              | ... |

**Процесс**:

1. Парсинг Excel файла
2. Валидация данных (employee_id exists, sum(weights) = 100%, etc.)
3. Создание/обновление записей
4. Возврат статистики (created, updated, errors)

### Экспорт в Excel

**Endpoint**:

```bash
GET /api/v1/kpi/export/employee-kpis
  ?department_id=1
  &year=2025
  &format=xlsx

Response: <excel_file>
```

---

## Мониторинг и логирование

### Логи приложения

**Уровни логирования**:

```python
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("app.api.kpi")

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Аудит изменений

**Все изменения логируются в `notes`**:

```python
employee_kpi.notes += f"\n[{datetime.utcnow()}] Updated by user #{current_user.id}: kpi_percentage changed from {old_value} to {new_value}"
```

### Метрики производительности

**SQL запросы**:

```sql
-- Slow queries
SELECT * FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Проблема: KPI% не рассчитывается

**Причины**:

1. ❌ Нет назначенных целей (`goal_achievements` пустой)
2. ❌ Сумма весов ≠ 100%
3. ❌ Все цели в статусе DRAFT (не ACTIVE)
4. ❌ `achievement_percentage` = NULL

**Решение**:

```python
# 1. Check assignments
assignments = db.query(GoalAchievement).filter(
    GoalAchievement.employee_kpi_id == kpi_id
).all()

if not assignments:
    print("No goals assigned!")

# 2. Check weights
total_weight = sum([a.weight for a in assignments])
if total_weight != 100:
    print(f"Sum of weights = {total_weight}%, should be 100%")

# 3. Check status
active_count = sum([1 for a in assignments if a.status == "ACTIVE"])
if active_count == 0:
    print("No ACTIVE goals!")

# 4. Check achievement_percentage
null_achievements = [a for a in assignments if a.achievement_percentage is None]
if null_achievements:
    print(f"Found {len(null_achievements)} goals with NULL achievement_percentage")
```

### Проблема: Бонусы не синхронизируются с PayrollPlan

**Причины**:

1. ❌ KPI не в статусе APPROVED
2. ❌ Ошибка в sync_to_payroll_plan()
3. ❌ PayrollPlan запись заблокирована другим процессом

**Решение**:

```python
# 1. Check status
if employee_kpi.status != KPIStatusEnum.APPROVED:
    print(f"KPI status = {employee_kpi.status}, should be APPROVED")

# 2. Manually trigger sync
try:
    sync_to_payroll_plan(employee_kpi, db)
    print("Sync successful")
except Exception as e:
    print(f"Sync failed: {e}")

# 3. Check PayrollPlan
payroll_plan = db.query(PayrollPlan).filter(
    PayrollPlan.employee_id == employee_kpi.employee_id,
    PayrollPlan.year == employee_kpi.year,
    PayrollPlan.month == employee_kpi.month
).first()

if payroll_plan:
    print(f"PayrollPlan found: monthly_bonus = {payroll_plan.monthly_bonus}")
else:
    print("PayrollPlan not found!")
```

### Проблема: Медленные запросы

**Диагностика**:

```sql
-- Enable query logging
SET log_min_duration_statement = 1000; -- Log queries > 1s

-- Check missing indexes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND tablename IN ('employee_kpis', 'kpi_goals', 'goal_achievements')
ORDER BY correlation;
```

**Решение**:

```sql
-- Add indexes if missing
CREATE INDEX ix_employee_kpis_department_year ON employee_kpis(department_id, year);
CREATE INDEX ix_goal_achievements_status ON goal_achievements(status);

-- Analyze tables
ANALYZE employee_kpis;
ANALYZE kpi_goals;
ANALYZE goal_achievements;
```

### Проблема: Duplicate key error при импорте

**Причина**: Попытка создать дубликат записи (employee_id, year, month).

**Решение**:

```python
# Use upsert instead of insert
existing = db.query(EmployeeKPI).filter(
    EmployeeKPI.employee_id == data["employee_id"],
    EmployeeKPI.year == data["year"],
    EmployeeKPI.month == data["month"],
    EmployeeKPI.department_id == data["department_id"]
).first()

if existing:
    # Update
    for key, value in data.items():
        setattr(existing, key, value)
else:
    # Insert
    new_kpi = EmployeeKPI(**data)
    db.add(new_kpi)

db.commit()
```

---

## Maintenance Tasks

### Ежедневные задачи

```bash
# 1. Backup database
pg_dump it_budget_db > backups/kpi_$(date +%Y%m%d).sql

# 2. Check slow queries
psql -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. Vacuum database
psql -c "VACUUM ANALYZE employee_kpis, kpi_goals, goal_achievements;"
```

### Еженедельные задачи

```bash
# 1. Check disk space
df -h

# 2. Review error logs
grep ERROR backend/logs/app.log | tail -100

# 3. Check orphaned records
psql -c "SELECT COUNT(*) FROM goal_achievements WHERE employee_kpi_id NOT IN (SELECT id FROM employee_kpis);"
```

### Ежемесячные задачи

```bash
# 1. Archive old data (>2 years)
psql -c "DELETE FROM employee_kpis WHERE year < 2023;"

# 2. Re-index tables
psql -c "REINDEX TABLE employee_kpis;"
psql -c "REINDEX TABLE kpi_goals;"
psql -c "REINDEX TABLE goal_achievements;"

# 3. Update statistics
psql -c "ANALYZE;"
```

---

## API Reference

### Complete endpoint list

```
# Employee KPI
GET    /api/v1/kpi/employee-kpis
POST   /api/v1/kpi/employee-kpis
GET    /api/v1/kpi/employee-kpis/{id}
PUT    /api/v1/kpi/employee-kpis/{id}
DELETE /api/v1/kpi/employee-kpis/{id}

# Goals
GET    /api/v1/kpi/goals
POST   /api/v1/kpi/goals
GET    /api/v1/kpi/goals/{id}
PUT    /api/v1/kpi/goals/{id}
DELETE /api/v1/kpi/goals/{id}

# Assignments
GET    /api/v1/kpi/assignments
POST   /api/v1/kpi/assignments
GET    /api/v1/kpi/assignments/{id}
PUT    /api/v1/kpi/assignments/{id}
DELETE /api/v1/kpi/assignments/{id}

# Recalculation
POST   /api/v1/kpi/recalculate/{employee_kpi_id}
POST   /api/v1/kpi/recalculate/department

# Analytics
GET    /api/v1/kpi/analytics/dashboard
GET    /api/v1/kpi/analytics/kpi-trends
GET    /api/v1/kpi/analytics/summary

# Import/Export
POST   /api/v1/kpi/import/employee-kpis
GET    /api/v1/kpi/export/employee-kpis
```

---

## 🔐 Security Considerations

### Authentication

- **JWT tokens** - 30 min expiry
- **Role-based access** - ADMIN has full access
- **Department filtering** - Multi-tenant isolation

### Data Privacy

- **PII protection** - Employee data is sensitive
- **Audit logs** - All changes logged in `notes`
- **Backups** - Daily encrypted backups

### API Rate Limiting

```python
# Redis-based rate limiting
@limiter.limit("100/minute")
def create_employee_kpi():
    pass
```

---

## 📞 Support

For technical issues:

1. Check logs: `backend/logs/app.log`
2. Check database: `psql it_budget_db`
3. Check Sentry: https://sentry.io/...
4. Contact dev team: dev@company.com

---

**End of Admin Guide**
