from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
import enum

from .session import Base


class ExpenseTypeEnum(str, enum.Enum):
    """Enum for expense types"""
    OPEX = "OPEX"
    CAPEX = "CAPEX"


class ExpenseStatusEnum(str, enum.Enum):
    """Enum for expense statuses"""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class BudgetStatusEnum(str, enum.Enum):
    """Enum for budget plan statuses"""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"


class BudgetVersionStatusEnum(str, enum.Enum):
    """Enum for budget version statuses (planning 2026 workflow)"""
    DRAFT = "draft"  # Черновик, редактируется
    IN_REVIEW = "in_review"  # На согласовании
    REVISION_REQUESTED = "revision_requested"  # Возвращён на доработку
    APPROVED = "approved"  # Утверждён
    REJECTED = "rejected"  # Отклонён
    ARCHIVED = "archived"  # Старая версия (для истории)


class BudgetScenarioTypeEnum(str, enum.Enum):
    """Enum for budget scenario types"""
    BASE = "base"  # Базовый сценарий
    OPTIMISTIC = "optimistic"  # Оптимистичный
    PESSIMISTIC = "pessimistic"  # Пессимистичный


class CalculationMethodEnum(str, enum.Enum):
    """Enum for budget calculation methods"""
    AVERAGE = "average"  # Среднее за базовый год
    GROWTH = "growth"  # Прогноз с трендом
    DRIVER_BASED = "driver_based"  # Драйвер-базированный (headcount, projects, etc)
    SEASONAL = "seasonal"  # С учётом сезонности
    MANUAL = "manual"  # Ручной ввод


class ApprovalActionEnum(str, enum.Enum):
    """Enum for approval actions"""
    APPROVED = "approved"  # Утверждено
    REJECTED = "rejected"  # Отклонено
    REVISION_REQUESTED = "revision_requested"  # Запрошены правки


class UserRoleEnum(str, enum.Enum):
    """Enum for user roles in BDR (Budget Department Reporting)"""
    ADMIN = "ADMIN"  # Администратор - управление системой и пользователями
    MANAGER = "MANAGER"  # Руководитель - доступ ко всем отделам, сводная аналитика
    USER = "USER"  # Пользователь отдела - доступ только к своему отделу


class Department(Base):
    """Departments (отделы компании) - основа multi-tenancy"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)  # Название отдела
    code = Column(String(50), unique=True, nullable=False, index=True)  # Код отдела
    description = Column(Text, nullable=True)  # Описание
    is_active = Column(Boolean, default=True, nullable=False)  # Активен ли отдел

    # FTP import mapping
    ftp_subdivision_name = Column(String(255), nullable=True, index=True)  # Название подразделения из FTP для сопоставления

    # Contact info
    manager_name = Column(String(255), nullable=True)  # Имя руководителя
    contact_email = Column(String(255), nullable=True)  # Email отдела
    contact_phone = Column(String(50), nullable=True)  # Телефон

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="department_rel")
    budget_categories = relationship("BudgetCategory", back_populates="department_rel")
    contractors = relationship("Contractor", back_populates="department_rel")
    organizations = relationship("Organization", back_populates="department_rel")
    expenses = relationship("Expense", back_populates="department_rel")
    budget_plans = relationship("BudgetPlan", back_populates="department_rel")
    forecast_expenses = relationship("ForecastExpense", back_populates="department_rel")
    employees = relationship("Employee", back_populates="department_rel")
    payroll_plans = relationship("PayrollPlan", back_populates="department_rel")
    payroll_actuals = relationship("PayrollActual", back_populates="department_rel")

    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"


class BudgetCategory(Base):
    """Budget categories (статьи расходов)"""
    __tablename__ = "budget_categories"
    __table_args__ = (
        Index('idx_budget_category_dept_active', 'department_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(Enum(ExpenseTypeEnum), nullable=False)  # OPEX or CAPEX
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Подкатегории (hierarchical structure)
    parent_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="budget_categories")
    expenses = relationship("Expense", back_populates="category")
    budget_plans = relationship("BudgetPlan", back_populates="category")

    # Self-referential relationship for subcategories
    parent = relationship("BudgetCategory", remote_side=[id], backref="subcategories")

    def __repr__(self):
        return f"<BudgetCategory {self.name} ({self.type})>"


class Contractor(Base):
    """Contractors (контрагенты/получатели)"""
    __tablename__ = "contractors"
    __table_args__ = (
        Index('idx_contractor_dept_active', 'department_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    short_name = Column(String(255), nullable=True)
    inn = Column(String(20), nullable=True, index=True)  # Removed unique constraint for multi-tenancy
    contact_info = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="contractors")
    expenses = relationship("Expense", back_populates="contractor")

    def __repr__(self):
        return f"<Contractor {self.name}>"


class Organization(Base):
    """Organizations (ВЕСТ ООО, ВЕСТ ГРУПП ООО)"""
    __tablename__ = "organizations"
    __table_args__ = (
        Index('idx_organization_dept_active', 'department_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Removed unique constraint for multi-tenancy
    legal_name = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="organizations")
    expenses = relationship("Expense", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"


class Expense(Base):
    """Expenses (заявки на расходы)"""
    __tablename__ = "expenses"
    __table_args__ = (
        Index('idx_expense_dept_status', 'department_id', 'status'),
        Index('idx_expense_dept_date', 'department_id', 'request_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), nullable=False, index=True)  # Removed unique constraint for multi-tenancy

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Foreign keys
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Amount and dates
    amount = Column(Numeric(15, 2), nullable=False)
    request_date = Column(DateTime, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=True)

    # Status
    status = Column(Enum(ExpenseStatusEnum), nullable=False, default=ExpenseStatusEnum.DRAFT, index=True)
    is_paid = Column(Boolean, default=False, nullable=False, index=True)
    is_closed = Column(Boolean, default=False, nullable=False, index=True)

    # Additional info
    comment = Column(Text, nullable=True)
    requester = Column(String(255), nullable=True)  # Заявитель

    # Import tracking
    imported_from_ftp = Column(Boolean, default=False, nullable=False)  # Загружена из FTP
    needs_review = Column(Boolean, default=False, nullable=False)  # Требует проверки категории

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="expenses")
    category = relationship("BudgetCategory", back_populates="expenses")
    contractor = relationship("Contractor", back_populates="expenses")
    organization = relationship("Organization", back_populates="expenses")
    attachments = relationship("Attachment", back_populates="expense", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Expense {self.number} - {self.amount}>"


class ForecastExpense(Base):
    """Forecast expenses (прогнозные расходы на следующий месяц)"""
    __tablename__ = "forecast_expenses"

    id = Column(Integer, primary_key=True, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Foreign keys
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False, index=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Date and amount
    forecast_date = Column(Date, nullable=False, index=True)  # Прогнозная дата платежа
    amount = Column(Numeric(15, 2), nullable=False)

    # Additional info
    comment = Column(Text, nullable=True)
    is_regular = Column(Boolean, default=False, nullable=False)  # Регулярный расход

    # Source tracking
    based_on_expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)  # На основе какой заявки

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="forecast_expenses")
    category = relationship("BudgetCategory")
    contractor = relationship("Contractor")
    organization = relationship("Organization")
    based_on_expense = relationship("Expense", foreign_keys=[based_on_expense_id])

    def __repr__(self):
        return f"<ForecastExpense {self.id} on {self.forecast_date}>"


class BudgetPlan(Base):
    """Budget plans (планы бюджета)"""
    __tablename__ = "budget_plans"
    __table_args__ = (
        Index('idx_budget_plan_dept_year_month', 'department_id', 'year', 'month'),
    )

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Foreign key
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False, index=True)

    # Planned amounts
    planned_amount = Column(Numeric(15, 2), nullable=False)
    capex_planned = Column(Numeric(15, 2), default=0, nullable=False)
    opex_planned = Column(Numeric(15, 2), default=0, nullable=False)

    # Status (для всего года - все записи одного года имеют одинаковый статус)
    status = Column(Enum(BudgetStatusEnum), default=BudgetStatusEnum.DRAFT, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="budget_plans")
    category = relationship("BudgetCategory", back_populates="budget_plans")

    def __repr__(self):
        return f"<BudgetPlan {self.year}-{self.month:02d} - {self.planned_amount}>"


class Attachment(Base):
    """Attachments (приложения к заявкам: счета, договора, акты)"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)

    # File information
    filename = Column(String(500), nullable=False)  # Оригинальное имя файла
    file_path = Column(String(1000), nullable=False)  # Путь к файлу в хранилище
    file_size = Column(Integer, nullable=False)  # Размер файла в байтах
    mime_type = Column(String(100), nullable=True)  # MIME тип файла
    file_type = Column(String(50), nullable=True)  # Тип документа: invoice, contract, act, other

    # Upload information
    uploaded_by = Column(String(255), nullable=True)  # Кто загрузил

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.filename} for Expense {self.expense_id}>"


class DashboardConfig(Base):
    """Dashboard configurations (конфигурации пользовательских дашбордов)"""
    __tablename__ = "dashboard_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Название дашборда
    description = Column(Text, nullable=True)  # Описание дашборда

    # User association
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Configuration
    is_default = Column(Boolean, default=False, nullable=False)  # Дефолтный дашборд
    is_public = Column(Boolean, default=False, nullable=False)  # Публичный (доступен всем)

    # Layout configuration stored as JSON
    # Structure: { "widgets": [{"id": "...", "type": "...", "config": {...}, "layout": {"x": 0, "y": 0, "w": 4, "h": 2}}] }
    config = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="dashboards")

    def __repr__(self):
        return f"<DashboardConfig {self.name}>"


class User(Base):
    """Users (пользователи BDR системы)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)  # Логин
    email = Column(String(255), unique=True, nullable=False, index=True)  # Email
    full_name = Column(String(255), nullable=True)  # Полное имя

    # Authentication
    hashed_password = Column(String(255), nullable=False)  # Хеш пароля

    # Role and permissions in BDR
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.USER)

    # Department association (USER and MANAGER belong to department, ADMIN can be without)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)  # Активен ли пользователь
    is_verified = Column(Boolean, default=False, nullable=False)  # Подтвержден ли email

    # Additional info
    position = Column(String(255), nullable=True)  # Должность
    phone = Column(String(50), nullable=True)  # Телефон

    # Last login tracking
    last_login = Column(DateTime, nullable=True)  # Последний вход

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department", back_populates="users")
    dashboards = relationship("DashboardConfig", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class EmployeeStatusEnum(str, enum.Enum):
    """Enum for employee statuses"""
    ACTIVE = "ACTIVE"  # Активный сотрудник
    ON_VACATION = "ON_VACATION"  # В отпуске
    ON_LEAVE = "ON_LEAVE"  # В отпуске по уходу за ребенком / больничный
    FIRED = "FIRED"  # Уволен


class AuditActionEnum(str, enum.Enum):
    """Enum for audit log actions"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class AuditLog(Base):
    """Audit log for tracking critical operations"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_log_user_action', 'user_id', 'action'),
        Index('idx_audit_log_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_log_timestamp', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Action performed
    action = Column(Enum(AuditActionEnum), nullable=False, index=True)

    # Entity affected
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., "Expense", "User", "Category"
    entity_id = Column(Integer, nullable=True, index=True)  # ID of the affected entity

    # Details
    description = Column(Text, nullable=True)  # Human-readable description
    changes = Column(JSON, nullable=True)  # Detailed changes in JSON format

    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client info

    # Department context
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}#{self.entity_id} by User#{self.user_id}>"


class Employee(Base):
    """Employees (сотрудники) - для управления ФОТ"""
    __tablename__ = "employees"
    __table_args__ = (
        Index('idx_employee_dept_status', 'department_id', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Personal information
    full_name = Column(String(255), nullable=False, index=True)  # ФИО
    position = Column(String(255), nullable=False)  # Должность
    employee_number = Column(String(50), nullable=True, index=True)  # Табельный номер

    # Employment details
    hire_date = Column(Date, nullable=True)  # Дата приема на работу
    fire_date = Column(Date, nullable=True)  # Дата увольнения
    status = Column(Enum(EmployeeStatusEnum), nullable=False, default=EmployeeStatusEnum.ACTIVE, index=True)

    # Salary information
    base_salary = Column(Numeric(15, 2), nullable=False)  # Оклад

    # Bonus base rates (базовые ставки премий)
    monthly_bonus_base = Column(Numeric(15, 2), default=0, nullable=False)  # Базовая месячная премия
    quarterly_bonus_base = Column(Numeric(15, 2), default=0, nullable=False)  # Базовая квартальная премия
    annual_bonus_base = Column(Numeric(15, 2), default=0, nullable=False)  # Базовая годовая премия

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department")
    payroll_plans = relationship("PayrollPlan", back_populates="employee")
    payroll_actuals = relationship("PayrollActual", back_populates="employee")
    salary_history = relationship("SalaryHistory", back_populates="employee", order_by="SalaryHistory.effective_date.desc()")

    def __repr__(self):
        return f"<Employee {self.full_name} ({self.position})>"


class SalaryHistory(Base):
    """Salary history (история изменений оклада)"""
    __tablename__ = "salary_history"
    __table_args__ = (
        Index('idx_salary_history_employee_date', 'employee_id', 'effective_date'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Salary change information
    old_salary = Column(Numeric(15, 2), nullable=True)  # Старый оклад (None для первой записи)
    new_salary = Column(Numeric(15, 2), nullable=False)  # Новый оклад
    effective_date = Column(Date, nullable=False)  # Дата вступления в силу

    # Additional information
    reason = Column(Text, nullable=True)  # Причина изменения (повышение, индексация, и т.д.)
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="salary_history")

    def __repr__(self):
        return f"<SalaryHistory Employee#{self.employee_id}: {self.old_salary} → {self.new_salary}>"


class PayrollPlan(Base):
    """Payroll planning (планирование ФОТ по месяцам)"""
    __tablename__ = "payroll_plans"
    __table_args__ = (
        Index('idx_payroll_plan_dept_year_month', 'department_id', 'year', 'month'),
        Index('idx_payroll_plan_employee_year_month', 'employee_id', 'year', 'month'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Foreign keys
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Planned amounts
    base_salary = Column(Numeric(15, 2), nullable=False)  # Плановый оклад

    # Planned bonuses by type (плановые премии по типам)
    monthly_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Месячная премия
    quarterly_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Квартальная премия (Q1-Q4)
    annual_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Годовая премия

    other_payments = Column(Numeric(15, 2), default=0, nullable=False)  # Прочие выплаты
    total_planned = Column(Numeric(15, 2), nullable=False)  # Итого план (вычисляется)

    # Additional information
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="payroll_plans")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<PayrollPlan {self.year}-{self.month:02d} Employee#{self.employee_id}: {self.total_planned}>"


class PayrollActual(Base):
    """Payroll actual (фактические выплаты ФОТ)"""
    __tablename__ = "payroll_actuals"
    __table_args__ = (
        Index('idx_payroll_actual_dept_year_month', 'department_id', 'year', 'month'),
        Index('idx_payroll_actual_employee_year_month', 'employee_id', 'year', 'month'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Foreign keys
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Actual amounts paid
    base_salary_paid = Column(Numeric(15, 2), nullable=False)  # Фактически выплаченный оклад

    # Actual bonuses by type (фактические премии по типам)
    monthly_bonus_paid = Column(Numeric(15, 2), default=0, nullable=False)  # Месячная премия (факт)
    quarterly_bonus_paid = Column(Numeric(15, 2), default=0, nullable=False)  # Квартальная премия (факт)
    annual_bonus_paid = Column(Numeric(15, 2), default=0, nullable=False)  # Годовая премия (факт)

    other_payments_paid = Column(Numeric(15, 2), default=0, nullable=False)  # Прочие фактические выплаты
    total_paid = Column(Numeric(15, 2), nullable=False)  # Итого факт (вычисляется)

    # Payment details
    payment_date = Column(Date, nullable=True)  # Дата выплаты

    # Link to expense (if payroll is tracked as expense)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True, index=True)

    # Additional information
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="payroll_actuals")
    department_rel = relationship("Department")
    expense = relationship("Expense")

    def __repr__(self):
        return f"<PayrollActual {self.year}-{self.month:02d} Employee#{self.employee_id}: {self.total_paid}>"


# ============================================================================
# Budget Planning 2026 Module
# ============================================================================


class BudgetScenario(Base):
    """Budget scenarios (сценарии бюджета: базовый, оптимистичный, пессимистичный)"""
    __tablename__ = "budget_scenarios"
    __table_args__ = (
        Index('idx_budget_scenario_year_type', 'year', 'scenario_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)  # 2026, 2027...
    scenario_name = Column(String(100), nullable=False)  # "Базовый", "Оптимистичный"
    scenario_type = Column(Enum(BudgetScenarioTypeEnum), nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Глобальные параметры сценария
    global_growth_rate = Column(Numeric(5, 2), default=0, nullable=False)  # % роста (например, +10%)
    inflation_rate = Column(Numeric(5, 2), default=0, nullable=False)  # Инфляция (например, +6%)
    fx_rate = Column(Numeric(10, 4), nullable=True)  # Курс валюты для импортных расходов

    # Предположения сценария (JSON)
    assumptions = Column(JSON, nullable=True)  # Бизнес-предположения

    # Описание
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)

    # Relationships
    department_rel = relationship("Department")
    budget_versions = relationship("BudgetVersion", back_populates="scenario")

    def __repr__(self):
        return f"<BudgetScenario {self.year} - {self.scenario_name}>"


class BudgetVersion(Base):
    """Budget versions (версии бюджета с историей изменений)"""
    __tablename__ = "budget_versions"
    __table_args__ = (
        Index('idx_budget_version_year_status', 'year', 'status'),
        Index('idx_budget_version_dept_year', 'department_id', 'year'),
    )

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)  # 2026
    version_number = Column(Integer, nullable=False)  # 1, 2, 3...
    version_name = Column(String(100), nullable=True)  # "Первоначальный", "После ревью CFO"

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Foreign key to scenario
    scenario_id = Column(Integer, ForeignKey("budget_scenarios.id"), nullable=True, index=True)

    # Status workflow
    status = Column(
        Enum(BudgetVersionStatusEnum),
        default=BudgetVersionStatusEnum.DRAFT,
        nullable=False,
        index=True
    )

    # Метаданные
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)  # Когда отправлен на согласование
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)

    # Комментарии процесса
    comments = Column(Text, nullable=True)
    change_log = Column(Text, nullable=True)  # Что изменилось от предыдущей версии

    # Итоговые суммы (денормализация для быстрого доступа)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total_capex = Column(Numeric(15, 2), default=0, nullable=False)
    total_opex = Column(Numeric(15, 2), default=0, nullable=False)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department")
    scenario = relationship("BudgetScenario", back_populates="budget_versions")
    plan_details = relationship("BudgetPlanDetail", back_populates="version", cascade="all, delete-orphan")
    approval_logs = relationship("BudgetApprovalLog", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BudgetVersion {self.year} v{self.version_number} - {self.status.value}>"


class BudgetPlanDetail(Base):
    """Budget plan details (детализация плана по месяцам и статьям)"""
    __tablename__ = "budget_plan_details"
    __table_args__ = (
        Index('idx_budget_detail_version_month_category', 'version_id', 'month', 'category_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to version
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Период и категория
    month = Column(Integer, nullable=False, index=True)  # 1-12 (январь-декабрь)
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)  # Подстатья (опционально)

    # Суммы
    planned_amount = Column(Numeric(15, 2), nullable=False)
    type = Column(Enum(ExpenseTypeEnum), nullable=False)  # CAPEX или OPEX

    # Обоснование и драйверы
    calculation_method = Column(
        Enum(CalculationMethodEnum),
        nullable=True,
        index=True
    )  # "average", "growth", "manual", "driver_based"
    calculation_params = Column(JSON, nullable=True)  # Параметры расчёта
    business_driver = Column(String(100), nullable=True)  # Что влияет (headcount, проекты и т.д.)
    justification = Column(Text, nullable=True)  # Обоснование

    # Связь с фактом базового года (обычно 2025)
    based_on_year = Column(Integer, nullable=True)  # Базовый год для расчёта
    based_on_avg = Column(Numeric(15, 2), nullable=True)  # Среднее за базовый год
    based_on_total = Column(Numeric(15, 2), nullable=True)  # Сумма за базовый год
    growth_rate = Column(Numeric(5, 2), nullable=True)  # % роста/снижения

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    version = relationship("BudgetVersion", back_populates="plan_details")
    category = relationship("BudgetCategory")

    def __repr__(self):
        return f"<BudgetPlanDetail {self.month}/{self.version_id} - {self.planned_amount}>"


class BudgetApprovalLog(Base):
    """Budget approval log (история согласования бюджета)"""
    __tablename__ = "budget_approval_log"
    __table_args__ = (
        Index('idx_approval_log_version_iteration', 'version_id', 'iteration_number'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to version
    version_id = Column(Integer, ForeignKey("budget_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Информация о согласующем
    iteration_number = Column(Integer, nullable=False)  # Раунд согласования (1, 2, 3)
    reviewer_name = Column(String(100), nullable=False)
    reviewer_role = Column(String(50), nullable=False)  # "CFO", "CEO", "Head of IT"

    # Решение
    action = Column(Enum(ApprovalActionEnum), nullable=False)
    decision_date = Column(DateTime, nullable=False, index=True)

    # Комментарии и изменения
    comments = Column(Text, nullable=True)
    requested_changes = Column(JSON, nullable=True)  # Конкретные запросы на изменение

    # Следующие шаги
    next_action = Column(String(100), nullable=True)
    deadline = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    version = relationship("BudgetVersion", back_populates="approval_logs")

    def __repr__(self):
        return f"<BudgetApprovalLog v{self.version_id} round {self.iteration_number} - {self.action.value}>"
