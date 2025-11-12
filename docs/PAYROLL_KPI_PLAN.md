# План доработки: Модули ФОТ и KPI

## Обзор

Добавление в систему IT Budget Manager двух новых модулей:
1. **ФОТ (Фонд оплаты труда)** - планирование и учет зарплат сотрудников
2. **KPI (Key Performance Indicators)** - управление целями и премиями сотрудников

Оба модуля интегрируются с существующей multi-tenancy архитектурой (department-based) и системой бюджетирования.

---

## Источники данных

### Excel файлы для импорта:

1. **xls/Планфакт2025.xlsx**
   - Лист "ФОТ": помесячное планирование зарплат
   - Структура: ФИО, Янв-Дек (оклад + премия), Итого 2024, Ср. в месяц
   - Также есть раздел с окладами (контракт)

2. **xls/KPI_Manager_2025.xlsx**
   - Лист "УПРАВЛЕНИЕ КПИ": базовая информация по сотрудникам
   - Столбцы: Сотрудник, Оклад, Должность, ЗП Год, Базовая премия, Вариант премии, КПИ %
   - Таблица выплат по месяцам с датами отправки (например, "до 5.08")
   - Отдельные листы для каждого сотрудника с детализацией KPI

---

## Архитектура базы данных

### 1. Модель Employee (Сотрудники)

```python
class EmployeeStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    DISMISSED = "DISMISSED"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    # Personal info
    full_name = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Current salary info
    current_salary = Column(Numeric(15, 2), nullable=False)  # Текущий оклад
    base_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Базовая премия
    bonus_type = Column(String(50), nullable=True)  # Тип премии: результативный, фиксированный

    # Status
    status = Column(Enum(EmployeeStatusEnum), default=EmployeeStatusEnum.ACTIVE, nullable=False)
    hire_date = Column(Date, nullable=True)  # Дата найма
    dismiss_date = Column(Date, nullable=True)  # Дата увольнения

    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Link to User (optional - если сотрудник есть в системе как User)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="employees")
    user = relationship("User", backref="employee_profile")
    salary_history = relationship("SalaryHistory", back_populates="employee", cascade="all, delete-orphan")
    payroll_plans = relationship("PayrollPlan", back_populates="employee", cascade="all, delete-orphan")
    payroll_actuals = relationship("PayrollActual", back_populates="employee", cascade="all, delete-orphan")
    kpi_records = relationship("EmployeeKPI", back_populates="employee", cascade="all, delete-orphan")
```

### 2. Модель SalaryHistory (История изменений оклада)

```python
class SalaryHistory(Base):
    __tablename__ = "salary_history"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Salary change
    old_salary = Column(Numeric(15, 2), nullable=True)
    new_salary = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False, index=True)

    # Reason and notes
    change_reason = Column(String(255), nullable=True)  # Повышение, индексация, и т.д.
    notes = Column(Text, nullable=True)

    # Who made the change
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="salary_history")
    changed_by = relationship("User")
```

### 3. Модель PayrollPlan (План ФОТ)

```python
class PayrollPlan(Base):
    __tablename__ = "payroll_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Employee
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Planned amounts
    planned_salary = Column(Numeric(15, 2), nullable=False)  # Оклад
    planned_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Премия
    planned_total = Column(Numeric(15, 2), nullable=False)  # Итого = оклад + премия

    # Additional payments
    planned_vacation_pay = Column(Numeric(15, 2), default=0, nullable=False)  # Отпускные
    planned_sick_pay = Column(Numeric(15, 2), default=0, nullable=False)  # Больничные
    planned_other = Column(Numeric(15, 2), default=0, nullable=False)  # Прочее

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="payroll_plans")
    department_rel = relationship("Department")

    # Unique constraint: one plan per employee per month
    __table_args__ = (
        UniqueConstraint('employee_id', 'year', 'month', name='uq_payroll_plan_employee_month'),
    )
```

### 4. Модель PayrollActual (Факт выплат ФОТ)

```python
class PayrollActual(Base):
    __tablename__ = "payroll_actuals"

    id = Column(Integer, primary_key=True, index=True)

    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    payment_date = Column(Date, nullable=True)  # Фактическая дата выплаты

    # Employee
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Actual amounts
    actual_salary = Column(Numeric(15, 2), nullable=False)
    actual_bonus = Column(Numeric(15, 2), default=0, nullable=False)
    actual_total = Column(Numeric(15, 2), nullable=False)

    # Additional payments
    actual_vacation_pay = Column(Numeric(15, 2), default=0, nullable=False)
    actual_sick_pay = Column(Numeric(15, 2), default=0, nullable=False)
    actual_other = Column(Numeric(15, 2), default=0, nullable=False)

    # Link to expense (if salary is tracked as Expense)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True, index=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="payroll_actuals")
    department_rel = relationship("Department")
    expense = relationship("Expense")
```

### 5. Модель EmployeeKPI (KPI сотрудников)

```python
class EmployeeKPI(Base):
    __tablename__ = "employee_kpi"

    id = Column(Integer, primary_key=True, index=True)

    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)

    # Employee
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # KPI data
    base_bonus = Column(Numeric(15, 2), nullable=False)  # Базовая премия
    kpi_percentage = Column(Numeric(5, 2), default=100, nullable=False)  # КПИ в процентах (0-200)
    calculated_bonus = Column(Numeric(15, 2), nullable=False)  # Расчетная премия = base_bonus * (kpi_percentage / 100)

    # Bonus type
    bonus_type = Column(String(50), nullable=True)  # результативный, фиксированный, смешанный

    # Payment schedule
    payment_due_date = Column(Date, nullable=True)  # Когда выплатить (например, до 5-го числа)
    payment_status = Column(String(50), default="PLANNED", nullable=False)  # PLANNED, PAID, CANCELLED

    # Performance notes
    performance_notes = Column(Text, nullable=True)  # Заметки о производительности

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="kpi_records")
    department_rel = relationship("Department")
    goals = relationship("KPIGoalProgress", back_populates="kpi_record")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('employee_id', 'year', 'month', name='uq_employee_kpi_month'),
    )
```

### 6. Модель KPIGoal (Цели KPI)

```python
class KPIGoal(Base):
    __tablename__ = "kpi_goals"

    id = Column(Integer, primary_key=True, index=True)

    # Goal info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Measurement
    weight = Column(Numeric(5, 2), nullable=False)  # Вес цели в общем KPI (сумма должна быть 100%)
    target_value = Column(Numeric(15, 2), nullable=True)  # Целевое значение
    measurement_unit = Column(String(50), nullable=True)  # Единица измерения

    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department")
    progress_records = relationship("KPIGoalProgress", back_populates="goal")
```

### 7. Модель KPIGoalProgress (Прогресс по целям)

```python
class KPIGoalProgress(Base):
    __tablename__ = "kpi_goal_progress"

    id = Column(Integer, primary_key=True, index=True)

    # Links
    kpi_record_id = Column(Integer, ForeignKey("employee_kpi.id"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("kpi_goals.id"), nullable=False, index=True)

    # Progress data
    actual_value = Column(Numeric(15, 2), nullable=True)  # Фактическое значение
    achievement_percentage = Column(Numeric(5, 2), nullable=False)  # % выполнения (0-100+)
    weighted_score = Column(Numeric(5, 2), nullable=False)  # Взвешенная оценка = achievement_percentage * (goal.weight / 100)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    kpi_record = relationship("EmployeeKPI", back_populates="goals")
    goal = relationship("KPIGoal", back_populates="progress_records")
```

---

## API Endpoints

### Employees

```
GET    /api/v1/employees                    # Список сотрудников (с фильтрами)
POST   /api/v1/employees                    # Создать сотрудника
GET    /api/v1/employees/{id}               # Получить сотрудника
PUT    /api/v1/employees/{id}               # Обновить сотрудника
DELETE /api/v1/employees/{id}               # Удалить сотрудника
PATCH  /api/v1/employees/{id}/status        # Изменить статус
GET    /api/v1/employees/{id}/salary-history # История изменений оклада
POST   /api/v1/employees/{id}/salary-history # Добавить изменение оклада

# Bulk operations
POST   /api/v1/employees/bulk-activate      # Массовая активация
POST   /api/v1/employees/bulk-deactivate    # Массовая деактивация
GET    /api/v1/employees/export             # Экспорт в Excel
POST   /api/v1/employees/import             # Импорт из Excel
```

### Payroll Planning

```
GET    /api/v1/payroll/plans                # Список планов ФОТ (фильтры: year, month, employee_id, department_id)
POST   /api/v1/payroll/plans                # Создать план
GET    /api/v1/payroll/plans/{id}           # Получить план
PUT    /api/v1/payroll/plans/{id}           # Обновить план
DELETE /api/v1/payroll/plans/{id}           # Удалить план

# Bulk operations
POST   /api/v1/payroll/plans/bulk-create    # Создать планы для всех сотрудников на месяц
POST   /api/v1/payroll/plans/copy-from-previous # Скопировать из предыдущего месяца

# Analytics
GET    /api/v1/payroll/plans/summary        # Сводка по планам (year, month, department_id)
GET    /api/v1/payroll/plans/by-employee/{employee_id} # План по сотруднику за год

# Import/Export
GET    /api/v1/payroll/plans/export         # Экспорт в Excel
POST   /api/v1/payroll/plans/import         # Импорт из Excel (лист "ФОТ")
```

### Payroll Actuals

```
GET    /api/v1/payroll/actuals              # Список факт выплат
POST   /api/v1/payroll/actuals              # Создать факт выплаты
GET    /api/v1/payroll/actuals/{id}         # Получить факт
PUT    /api/v1/payroll/actuals/{id}         # Обновить факт
DELETE /api/v1/payroll/actuals/{id}         # Удалить факт

# Comparison
GET    /api/v1/payroll/actuals/plan-vs-actual # Сравнение план/факт (year, month, department_id)

# Auto-generation
POST   /api/v1/payroll/actuals/generate-from-plan # Создать факт на основе плана
POST   /api/v1/payroll/actuals/link-to-expense    # Связать с заявкой (Expense)
```

### KPI Management

```
GET    /api/v1/kpi/records                  # Список KPI записей
POST   /api/v1/kpi/records                  # Создать KPI запись
GET    /api/v1/kpi/records/{id}             # Получить KPI
PUT    /api/v1/kpi/records/{id}             # Обновить KPI
DELETE /api/v1/kpi/records/{id}             # Удалить KPI
PATCH  /api/v1/kpi/records/{id}/percentage  # Обновить только KPI%

# Bulk operations
POST   /api/v1/kpi/records/bulk-create      # Создать KPI для всех сотрудников на месяц
POST   /api/v1/kpi/records/bulk-update-percentage # Массовое обновление KPI%

# Analytics
GET    /api/v1/kpi/records/summary          # Сводка по KPI (year, month, department_id)
GET    /api/v1/kpi/records/by-employee/{employee_id} # KPI сотрудника за год
GET    /api/v1/kpi/records/leaderboard      # Рейтинг сотрудников по KPI

# Import/Export
GET    /api/v1/kpi/records/export           # Экспорт в Excel
POST   /api/v1/kpi/records/import           # Импорт из Excel (KPI_Manager_2025.xlsx)
```

### KPI Goals

```
GET    /api/v1/kpi/goals                    # Список целей
POST   /api/v1/kpi/goals                    # Создать цель
GET    /api/v1/kpi/goals/{id}               # Получить цель
PUT    /api/v1/kpi/goals/{id}               # Обновить цель
DELETE /api/v1/kpi/goals/{id}               # Удалить цель

# Progress tracking
GET    /api/v1/kpi/goals/{id}/progress      # Прогресс по цели
POST   /api/v1/kpi/records/{kpi_id}/goals/{goal_id}/progress # Обновить прогресс
```

### Analytics & Reports

```
GET    /api/v1/analytics/payroll            # Аналитика ФОТ
GET    /api/v1/analytics/kpi                # Аналитика KPI
GET    /api/v1/analytics/team-performance   # Производительность команды
GET    /api/v1/analytics/payroll-forecast   # Прогноз ФОТ
GET    /api/v1/analytics/roi-analysis       # ROI анализ (затраты на ФОТ vs результаты)
```

---

## Frontend Components

### Страницы

1. **Сотрудники** (`/employees`)
   - Таблица сотрудников с фильтрами
   - Карточки статистики (всего, активных, уволенных)
   - Кнопки: Добавить, Импорт, Экспорт
   - Массовые операции

2. **Детальная страница сотрудника** (`/employees/{id}`)
   - Основная информация
   - История изменений оклада
   - График ФОТ по месяцам
   - График KPI по месяцам
   - Вкладки: Планы ФОТ, Факт выплат, KPI записи

3. **Планирование ФОТ** (`/payroll/planning`)
   - Таблица планов по месяцам
   - Группировка по сотрудникам
   - Редактирование inline
   - Кнопки: Копировать из пред. месяца, Импорт, Экспорт
   - Сводка: итого по месяцам, по сотрудникам

4. **Факт выплат ФОТ** (`/payroll/actuals`)
   - Таблица фактических выплат
   - Сравнение с планом (отклонения)
   - Статусы выплат
   - Связь с заявками (Expenses)

5. **Управление KPI** (`/kpi/management`)
   - Таблица KPI по сотрудникам и месяцам
   - Редактирование KPI% inline
   - Автоматический расчет премий
   - Календарь выплат премий
   - Индикаторы производительности

6. **Цели KPI** (`/kpi/goals`)
   - Список целей
   - Создание/редактирование целей
   - Назначение целей сотрудникам
   - Отслеживание прогресса

7. **Аналитика ФОТ** (`/analytics/payroll`)
   - Дашборд с метриками ФОТ
   - Графики: план/факт, динамика, распределение
   - Прогноз расходов на ФОТ
   - Экспорт отчетов

8. **Аналитика KPI** (`/analytics/kpi`)
   - Дашборд производительности
   - Рейтинг сотрудников
   - Динамика KPI
   - Анализ выполнения целей
   - Корреляция КПИ и бизнес-результатов

### Компоненты

- `EmployeeCard` - карточка сотрудника
- `EmployeeForm` - форма создания/редактирования
- `SalaryHistoryTimeline` - timeline изменений оклада
- `PayrollPlanTable` - таблица планов ФОТ (editable)
- `PayrollActualTable` - таблица факт выплат
- `KPIRecordTable` - таблица KPI (editable KPI%)
- `KPIGoalForm` - форма создания/редактирования целей
- `KPIProgressTracker` - трекер прогресса по целям
- `PayrollChart` - графики ФОТ
- `KPIChart` - графики KPI
- `TeamPerformanceDashboard` - дашборд производительности команды
- `PayrollForecastChart` - прогноз ФОТ

---

## Этапы разработки

### Этап 1: Базовые модели и CRUD (2-3 дня)

- [ ] Создать модели Employee, SalaryHistory
- [ ] Миграция базы данных
- [ ] API endpoints для сотрудников (CRUD)
- [ ] Pydantic схемы для валидации
- [ ] Базовый UI: страница списка сотрудников
- [ ] Форма создания/редактирования сотрудника

### Этап 2: Планирование ФОТ (3-4 дня)

- [ ] Модели PayrollPlan, PayrollActual
- [ ] Миграция базы данных
- [ ] API endpoints для планов ФОТ
- [ ] Импорт из Excel (лист "ФОТ")
- [ ] UI: страница планирования ФОТ
- [ ] Редактируемая таблица планов (inline edit)
- [ ] Копирование из предыдущего месяца
- [ ] Экспорт планов в Excel

### Этап 3: Факт выплат ФОТ (2-3 дня)

- [ ] API endpoints для факт выплат
- [ ] Генерация факта на основе плана
- [ ] Связь с заявками (Expense)
- [ ] UI: страница факт выплат
- [ ] Сравнение план/факт с визуализацией отклонений

### Этап 4: Система KPI (4-5 дней)

- [ ] Модели EmployeeKPI, KPIGoal, KPIGoalProgress
- [ ] Миграция базы данных
- [ ] API endpoints для KPI записей
- [ ] API endpoints для целей KPI
- [ ] Импорт из Excel (KPI_Manager_2025.xlsx)
- [ ] UI: страница управления KPI
- [ ] Редактирование KPI% inline
- [ ] Автоматический расчет премий
- [ ] Календарь выплат премий

### Этап 5: Цели и прогресс KPI (3-4 дня)

- [ ] API для управления целями
- [ ] API для отслеживания прогресса
- [ ] UI: страница целей KPI
- [ ] Назначение целей сотрудникам
- [ ] Трекер прогресса по целям
- [ ] Автоматический расчет KPI% на основе целей

### Этап 6: Интеграция с бюджетом (2-3 дня)

- [ ] Автогенерация заявок (Expense) для ЗП
- [ ] Категория "Заработная плата" в BudgetCategory
- [ ] Включение ФОТ в BudgetPlan
- [ ] Прогноз ФОТ в календаре оплат
- [ ] Учет ФОТ в общей аналитике бюджета

### Этап 7: Аналитика и отчеты (3-4 дня)

- [ ] Дашборд ФОТ: план/факт, динамика, распределение
- [ ] Графики изменения ФОТ по месяцам
- [ ] Прогноз расходов на ФОТ
- [ ] Дашборд KPI: производительность команды
- [ ] Рейтинг сотрудников по KPI
- [ ] Динамика изменения KPI
- [ ] Анализ выполнения целей
- [ ] Корреляция КПИ и бизнес-результатов
- [ ] Сводные отчеты: бюджет + ФОТ + KPI
- [ ] ROI анализ (затраты на ФОТ vs результаты)

### Этап 8: Детальные страницы и UX (2-3 дня)

- [ ] Детальная страница сотрудника
- [ ] Timeline истории изменений оклада
- [ ] Графики ФОТ и KPI по сотруднику
- [ ] Интеграция с существующими дашбордами
- [ ] Улучшение навигации
- [ ] Адаптивный дизайн
- [ ] Тесты и багфиксинг

---

## Итого

**Общая оценка времени**: 22-29 дней (4-6 недель)

**Технологический стек**:
- Backend: FastAPI, SQLAlchemy, Alembic, Pandas (для импорта Excel)
- Frontend: React, TypeScript, Ant Design, Recharts (графики)
- Database: PostgreSQL

**Зависимости**:
- Все модули интегрируются с multi-tenancy (department-based)
- Используется существующая система аутентификации (JWT + RBAC)
- Импорт Excel использует pandas + openpyxl (уже есть в requirements.txt)

---

## Примечания

1. **Multi-tenancy**: Все новые таблицы имеют `department_id` для изоляции данных по отделам
2. **Права доступа**:
   - `ADMIN` - полный доступ ко всем отделам
   - `MANAGER` - просмотр всех отделов, редактирование только своего
   - `USER` - только просмотр данных своего отдела
3. **Интеграция с Expense**: ФОТ можно учитывать как обычные заявки на расходы (категория "Заработная плата")
4. **Прогнозирование**: Система прогнозирования расходов будет учитывать ФОТ при генерации прогнозов
5. **Импорт**: Скрипты импорта должны обрабатывать ошибки и предоставлять детальные отчеты
