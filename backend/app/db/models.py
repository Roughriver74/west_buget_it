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
    func,
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
    DRAFT = "DRAFT"  # Черновик, редактируется
    IN_REVIEW = "IN_REVIEW"  # На согласовании
    REVISION_REQUESTED = "REVISION_REQUESTED"  # Возвращён на доработку
    APPROVED = "APPROVED"  # Утверждён
    REJECTED = "REJECTED"  # Отклонён
    ARCHIVED = "ARCHIVED"  # Старая версия (для истории)


class BudgetScenarioTypeEnum(str, enum.Enum):
    """Enum for budget scenario types"""
    BASE = "BASE"  # Базовый сценарий
    OPTIMISTIC = "OPTIMISTIC"  # Оптимистичный
    PESSIMISTIC = "PESSIMISTIC"  # Пессимистичный


class CalculationMethodEnum(str, enum.Enum):
    """Enum for budget calculation methods"""
    AVERAGE = "AVERAGE"  # Среднее за базовый год
    GROWTH = "GROWTH"  # Прогноз с трендом
    DRIVER_BASED = "DRIVER_BASED"  # Драйвер-базированный (headcount, projects, etc)
    SEASONAL = "SEASONAL"  # С учётом сезонности
    MANUAL = "MANUAL"  # Ручной ввод


class ApprovalActionEnum(str, enum.Enum):
    """Enum for approval actions"""
    SUBMITTED = "SUBMITTED"  # Отправлено на согласование
    APPROVED = "APPROVED"  # Утверждено
    REJECTED = "REJECTED"  # Отклонено
    REVISION_REQUESTED = "REVISION_REQUESTED"  # Запрошены правки


class UserRoleEnum(str, enum.Enum):
    """Enum for user roles in BDR (Budget Department Reporting)"""
    ADMIN = "ADMIN"  # Администратор - управление системой и пользователями
    FOUNDER = "FOUNDER"  # Учредитель - дашборд с ключевыми показателями по всем отделам
    MANAGER = "MANAGER"  # Руководитель - доступ ко всем отделам, сводная аналитика
    USER = "USER"  # Пользователь отдела - доступ только к своему отделу


class BonusTypeEnum(str, enum.Enum):
    """Enum for bonus calculation types"""
    PERFORMANCE_BASED = "PERFORMANCE_BASED"  # Результативный - зависит от КПИ%
    FIXED = "FIXED"  # Фиксированный - не зависит от КПИ
    MIXED = "MIXED"  # Смешанный - часть фиксированная, часть от КПИ


class KPIGoalStatusEnum(str, enum.Enum):
    """Enum for KPI goal statuses"""
    DRAFT = "DRAFT"  # Черновик
    ACTIVE = "ACTIVE"  # Активная цель
    ACHIEVED = "ACHIEVED"  # Достигнута
    NOT_ACHIEVED = "NOT_ACHIEVED"  # Не достигнута
    CANCELLED = "CANCELLED"  # Отменена


class RevenueStreamTypeEnum(str, enum.Enum):
    """Enum for revenue stream types"""
    REGIONAL = "REGIONAL"  # Региональные (СПБ, СЗФО, Регионы)
    CHANNEL = "CHANNEL"  # Каналы продаж (Опт, Тендеры, Интернет-магазин)
    PRODUCT = "PRODUCT"  # Продуктовые (Ортодонтия, Оборудование и т.д.)


class RevenueCategoryTypeEnum(str, enum.Enum):
    """Enum for revenue category types"""
    PRODUCT = "PRODUCT"  # Продукция
    SERVICE = "SERVICE"  # Услуги
    EQUIPMENT = "EQUIPMENT"  # Оборудование
    TENDER = "TENDER"  # Тендеры


class RevenuePlanStatusEnum(str, enum.Enum):
    """Enum for revenue plan statuses"""
    DRAFT = "DRAFT"  # Черновик
    PENDING_APPROVAL = "PENDING_APPROVAL"  # На согласовании
    APPROVED = "APPROVED"  # Утвержден
    ACTIVE = "ACTIVE"  # Активный
    ARCHIVED = "ARCHIVED"  # Архивный


class RevenueVersionStatusEnum(str, enum.Enum):
    """Enum for revenue plan version statuses"""
    DRAFT = "DRAFT"  # Черновик
    IN_REVIEW = "IN_REVIEW"  # На согласовании
    REVISION_REQUESTED = "REVISION_REQUESTED"  # Возвращён на доработку
    APPROVED = "APPROVED"  # Утверждён
    REJECTED = "REJECTED"  # Отклонён
    ARCHIVED = "ARCHIVED"  # Архивный


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
    default_category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True)  # Категория по умолчанию для импорта

    # Contact info
    manager_name = Column(String(255), nullable=True)  # Имя руководителя
    contact_email = Column(String(255), nullable=True)  # Email отдела
    contact_phone = Column(String(50), nullable=True)  # Телефон

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="department_rel")
    budget_categories = relationship("BudgetCategory", foreign_keys="BudgetCategory.department_id", back_populates="department_rel")
    default_category = relationship("BudgetCategory", foreign_keys=[default_category_id])
    contractors = relationship("Contractor", back_populates="department_rel")
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
    department_rel = relationship("Department", foreign_keys=[department_id], back_populates="budget_categories")
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
    """Organizations (ВЕСТ ООО, ВЕСТ ГРУПП ООО) - SHARED across all departments"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)  # Unique constraint restored - shared entity
    legal_name = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
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
    quarterly_bonus_base = Column(Numeric(15, 2), default=None, nullable=True)  # Базовая квартальная премия (опционально)
    annual_bonus_base = Column(Numeric(15, 2), default=None, nullable=True)  # Базовая годовая премия (опционально)

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
    total_paid = Column(Numeric(15, 2), nullable=False)  # Итого факт (gross amount, до вычета налогов)

    # Tax calculations (расчет налогов)
    income_tax_rate = Column(Numeric(5, 4), default=0.13, nullable=False)  # Ставка НДФЛ (по умолчанию 13%)
    income_tax_amount = Column(Numeric(15, 2), default=0, nullable=False)  # Сумма НДФЛ (вычисляется: total_paid * income_tax_rate)
    social_tax_amount = Column(Numeric(15, 2), default=0, nullable=False)  # Социальные отчисления (опционально)
    # net_amount = total_paid - income_tax_amount - social_tax_amount (вычисляется в приложении)

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

    # Baseline flag (only one approved version per year can be baseline)
    is_baseline = Column(Boolean, default=False, nullable=False, index=True)

    # Метаданные
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)  # Когда отправлен на согласование
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)

    # Custom approval checkboxes for presentation
    manager_approved = Column(Boolean, default=False, nullable=False)
    manager_approved_at = Column(DateTime, nullable=True)
    cfo_approved = Column(Boolean, default=False, nullable=False)
    cfo_approved_at = Column(DateTime, nullable=True)
    founder1_approved = Column(Boolean, default=False, nullable=False)
    founder1_approved_at = Column(DateTime, nullable=True)
    founder2_approved = Column(Boolean, default=False, nullable=False)
    founder2_approved_at = Column(DateTime, nullable=True)
    founder3_approved = Column(Boolean, default=False, nullable=False)
    founder3_approved_at = Column(DateTime, nullable=True)

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


class KPIGoal(Base):
    """KPI Goals (цели и метрики для оценки производительности)"""
    __tablename__ = "kpi_goals"
    __table_args__ = (
        Index('idx_kpi_goal_dept_status', 'department_id', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Goal information
    name = Column(String(255), nullable=False, index=True)  # Название цели
    description = Column(Text, nullable=True)  # Описание
    category = Column(String(100), nullable=True, index=True)  # Категория (Продажи, Качество, Эффективность и т.д.)

    # Measurement
    metric_name = Column(String(255), nullable=True)  # Название метрики
    metric_unit = Column(String(50), nullable=True)  # Единица измерения (%, шт, руб и т.д.)
    target_value = Column(Numeric(15, 2), nullable=True)  # Целевое значение
    weight = Column(Numeric(5, 2), nullable=False, default=100)  # Вес цели (для расчета общего КПИ%)

    # Period
    year = Column(Integer, nullable=False, index=True)  # Год
    is_annual = Column(Boolean, default=True, nullable=False)  # Годовая цель или ежемесячная

    # Status
    status = Column(Enum(KPIGoalStatusEnum), nullable=False, default=KPIGoalStatusEnum.DRAFT, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department_rel = relationship("Department")
    employee_goals = relationship("EmployeeKPIGoal", back_populates="goal")

    def __repr__(self):
        return f"<KPIGoal {self.name} (weight={self.weight})>"


class EmployeeKPI(Base):
    """Employee KPI (КПИ сотрудника по периодам с расчетом премий)"""
    __tablename__ = "employee_kpis"
    __table_args__ = (
        Index('idx_employee_kpi_period', 'employee_id', 'year', 'month'),
        Index('idx_employee_kpi_dept', 'department_id', 'year', 'month'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Employee and period
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # Месяц (1-12)

    # KPI percentage (процент выполнения КПИ)
    kpi_percentage = Column(Numeric(5, 2), nullable=True)  # КПИ% (0-200%, обычно 0-100%)

    # Bonus type and calculation
    monthly_bonus_type = Column(Enum(BonusTypeEnum), nullable=False, default=BonusTypeEnum.PERFORMANCE_BASED)
    quarterly_bonus_type = Column(Enum(BonusTypeEnum), nullable=False, default=BonusTypeEnum.PERFORMANCE_BASED)
    annual_bonus_type = Column(Enum(BonusTypeEnum), nullable=False, default=BonusTypeEnum.PERFORMANCE_BASED)

    # Base bonuses (базовые ставки - копируются из Employee или задаются вручную)
    monthly_bonus_base = Column(Numeric(15, 2), nullable=False, default=0)
    quarterly_bonus_base = Column(Numeric(15, 2), nullable=False, default=0)
    annual_bonus_base = Column(Numeric(15, 2), nullable=False, default=0)

    # Calculated bonuses (рассчитанные премии с учетом КПИ%)
    monthly_bonus_calculated = Column(Numeric(15, 2), nullable=True)  # = base * (kpi_percentage / 100) для PERFORMANCE_BASED
    quarterly_bonus_calculated = Column(Numeric(15, 2), nullable=True)
    annual_bonus_calculated = Column(Numeric(15, 2), nullable=True)

    # Fixed part for MIXED bonus type
    monthly_bonus_fixed_part = Column(Numeric(5, 2), nullable=True)  # % фиксированной части (0-100%)
    quarterly_bonus_fixed_part = Column(Numeric(5, 2), nullable=True)
    annual_bonus_fixed_part = Column(Numeric(5, 2), nullable=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Additional information
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee")
    department_rel = relationship("Department")
    goal_achievements = relationship("EmployeeKPIGoal", back_populates="employee_kpi")

    def __repr__(self):
        return f"<EmployeeKPI Employee#{self.employee_id} {self.year}-{self.month:02d} KPI={self.kpi_percentage}%>"


class EmployeeKPIGoal(Base):
    """Employee KPI Goal (связь сотрудников с целями и отслеживание выполнения)"""
    __tablename__ = "employee_kpi_goals"
    __table_args__ = (
        Index('idx_emp_kpi_goal_period', 'employee_id', 'goal_id', 'year', 'month'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Relations
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("kpi_goals.id"), nullable=False, index=True)
    employee_kpi_id = Column(Integer, ForeignKey("employee_kpis.id"), nullable=True, index=True)  # Связь с периодом

    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True, index=True)  # Null для годовых целей

    # Achievement tracking
    target_value = Column(Numeric(15, 2), nullable=True)  # Целевое значение (может отличаться от goal.target_value)
    actual_value = Column(Numeric(15, 2), nullable=True)  # Фактическое значение
    achievement_percentage = Column(Numeric(5, 2), nullable=True)  # % выполнения цели (actual/target * 100)

    # Weight for this employee (может отличаться от веса цели)
    weight = Column(Numeric(5, 2), nullable=True)  # Вес для расчета общего КПИ%

    # Status
    status = Column(Enum(KPIGoalStatusEnum), nullable=False, default=KPIGoalStatusEnum.ACTIVE)

    # Additional information
    notes = Column(Text, nullable=True)  # Комментарии

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee")
    goal = relationship("KPIGoal", back_populates="employee_goals")
    employee_kpi = relationship("EmployeeKPI", back_populates="goal_achievements")

    def __repr__(self):
        return f"<EmployeeKPIGoal Employee#{self.employee_id} Goal#{self.goal_id} {self.achievement_percentage}%>"


# ============================================================================
# REVENUE BUDGET MODULE - Модуль бюджета доходов
# ============================================================================


class RevenueStream(Base):
    """Revenue Stream (Поток доходов) - основная классификация источников дохода"""
    __tablename__ = "revenue_streams"
    __table_args__ = (
        Index('idx_revenue_stream_dept_active', 'department_id', 'is_active'),
        Index('idx_revenue_stream_type', 'stream_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # "СПБ и ЛО", "СЗФО", "Регионы" и т.д.
    code = Column(String(50), nullable=True, index=True)  # Код потока для идентификации
    stream_type = Column(Enum(RevenueStreamTypeEnum), nullable=False)
    # REGIONAL (региональные), CHANNEL (каналы продаж), PRODUCT (продуктовые)

    parent_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    parent = relationship("RevenueStream", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<RevenueStream {self.name} ({self.stream_type})>"


class RevenueCategory(Base):
    """Revenue Category (Категория доходов) - продуктовые и сервисные категории"""
    __tablename__ = "revenue_categories"
    __table_args__ = (
        Index('idx_revenue_category_dept_active', 'department_id', 'is_active'),
        Index('idx_revenue_category_type', 'category_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # "Брекеты", "Дуги", "Оборудование"
    code = Column(String(50), unique=True, nullable=True, index=True)
    category_type = Column(Enum(RevenueCategoryTypeEnum), nullable=False)
    # PRODUCT (продукция), SERVICE (услуги), EQUIPMENT (оборудование), TENDER (тендеры)

    parent_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Специфичные поля
    default_margin = Column(Numeric(5, 2), nullable=True)  # Наценка в %
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    parent = relationship("RevenueCategory", remote_side=[id], backref="subcategories")

    def __repr__(self):
        return f"<RevenueCategory {self.name} ({self.category_type})>"


class RevenuePlan(Base):
    """Revenue Plan (План доходов) - годовой план доходов с версионированием"""
    __tablename__ = "revenue_plans"
    __table_args__ = (
        Index('idx_revenue_plan_year_dept', 'year', 'department_id'),
        Index('idx_revenue_plan_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # "План доходов 2025"
    year = Column(Integer, nullable=False, index=True)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)
    revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    status = Column(Enum(RevenuePlanStatusEnum), default=RevenuePlanStatusEnum.DRAFT, nullable=False)
    # DRAFT, PENDING_APPROVAL, APPROVED, ACTIVE, ARCHIVED

    total_planned_revenue = Column(Numeric(15, 2), nullable=True)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    revenue_stream = relationship("RevenueStream")
    revenue_category = relationship("RevenueCategory")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    versions = relationship("RevenuePlanVersion", back_populates="plan")

    def __repr__(self):
        return f"<RevenuePlan {self.name} {self.year} ({self.status})>"

class RevenuePlanVersion(Base):
    """Revenue Plan Version (Версия плана доходов) - версионирование плана"""
    __tablename__ = "revenue_plan_versions"
    __table_args__ = (
        Index('idx_revenue_version_plan', 'plan_id'),
        Index('idx_revenue_version_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("revenue_plans.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(255), nullable=True)

    status = Column(Enum(RevenueVersionStatusEnum), default=RevenueVersionStatusEnum.DRAFT, nullable=False)
    description = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    plan = relationship("RevenuePlan", back_populates="versions")
    details = relationship("RevenuePlanDetail", back_populates="version")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<RevenuePlanVersion #{self.version_number} for Plan#{self.plan_id} ({self.status})>"


class RevenuePlanDetail(Base):
    """Revenue Plan Detail (Детали плана доходов) - детализация плана по месяцам и категориям"""
    __tablename__ = "revenue_plan_details"
    __table_args__ = (
        Index('idx_revenue_detail_version', 'version_id'),
        Index('idx_revenue_detail_stream', 'revenue_stream_id'),
        Index('idx_revenue_detail_category', 'revenue_category_id'),
        Index('idx_revenue_detail_dept', 'department_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("revenue_plan_versions.id"), nullable=False)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)
    revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

    # Месячные планы (12 колонок)
    month_01 = Column(Numeric(15, 2), default=0)
    month_02 = Column(Numeric(15, 2), default=0)
    month_03 = Column(Numeric(15, 2), default=0)
    month_04 = Column(Numeric(15, 2), default=0)
    month_05 = Column(Numeric(15, 2), default=0)
    month_06 = Column(Numeric(15, 2), default=0)
    month_07 = Column(Numeric(15, 2), default=0)
    month_08 = Column(Numeric(15, 2), default=0)
    month_09 = Column(Numeric(15, 2), default=0)
    month_10 = Column(Numeric(15, 2), default=0)
    month_11 = Column(Numeric(15, 2), default=0)
    month_12 = Column(Numeric(15, 2), default=0)

    # Итого
    total = Column(Numeric(15, 2), nullable=True)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    version = relationship("RevenuePlanVersion", back_populates="details")
    revenue_stream = relationship("RevenueStream")
    revenue_category = relationship("RevenueCategory")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<RevenuePlanDetail Version#{self.version_id} Stream#{self.revenue_stream_id} Total={self.total}>"


class RevenueActual(Base):
    """Revenue Actual (Фактические доходы) - фактическая выручка за месяц"""
    __tablename__ = "revenue_actuals"
    __table_args__ = (
        Index('idx_revenue_actual_year_month', 'year', 'month'),
        Index('idx_revenue_actual_dept', 'department_id'),
        Index('idx_revenue_actual_stream', 'revenue_stream_id'),
        Index('idx_revenue_actual_category', 'revenue_category_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)
    revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    planned_amount = Column(Numeric(15, 2), nullable=True)  # Из плана
    actual_amount = Column(Numeric(15, 2), nullable=False)  # Факт
    variance = Column(Numeric(15, 2), nullable=True)  # Отклонение
    variance_percent = Column(Numeric(5, 2), nullable=True)  # % отклонения

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Метаданные
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    revenue_stream = relationship("RevenueStream")
    revenue_category = relationship("RevenueCategory")
    department_rel = relationship("Department")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<RevenueActual {self.year}-{self.month:02d} Actual={self.actual_amount}>"


class CustomerMetrics(Base):
    """Customer Metrics (Клиентские метрики) - метрики клиентской базы по регионам"""
    __tablename__ = "customer_metrics"
    __table_args__ = (
        Index('idx_customer_metrics_year_month', 'year', 'month'),
        Index('idx_customer_metrics_dept', 'department_id'),
        Index('idx_customer_metrics_stream', 'revenue_stream_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)

    # Клиентские метрики
    total_customer_base = Column(Integer, nullable=True)  # ОКБ (Общая клиентская база)
    active_customer_base = Column(Integer, nullable=True)  # АКБ (Активная клиентская база)
    coverage_rate = Column(Numeric(5, 4), nullable=True)  # Покрытие (АКБ/ОКБ)

    # Сегменты клиентов
    regular_clinics = Column(Integer, nullable=True)  # Обычные клиники
    network_clinics = Column(Integer, nullable=True)  # Сетевые клиники
    new_clinics = Column(Integer, nullable=True)  # Новые клиники

    # Средний чек
    avg_order_value = Column(Numeric(12, 2), nullable=True)
    avg_order_value_regular = Column(Numeric(12, 2), nullable=True)
    avg_order_value_network = Column(Numeric(12, 2), nullable=True)
    avg_order_value_new = Column(Numeric(12, 2), nullable=True)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    revenue_stream = relationship("RevenueStream")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<CustomerMetrics {self.year}-{self.month:02d} Stream#{self.revenue_stream_id} АКБ={self.active_customer_base}>"


class SeasonalityCoefficient(Base):
    """Seasonality Coefficient (Коэффициенты сезонности) - исторические коэффициенты для прогнозирования"""
    __tablename__ = "seasonality_coefficients"
    __table_args__ = (
        Index('idx_seasonality_year', 'year'),
        Index('idx_seasonality_dept', 'department_id'),
        Index('idx_seasonality_stream', 'revenue_stream_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=False)
    year = Column(Integer, nullable=False, index=True)  # Исторический год

    # Коэффициенты по месяцам (относительно среднего = 1.0)
    coef_01 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_02 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_03 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_04 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_05 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_06 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_07 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_08 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_09 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_10 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_11 = Column(Numeric(5, 4), nullable=False, default=1.0)
    coef_12 = Column(Numeric(5, 4), nullable=False, default=1.0)

    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    revenue_stream = relationship("RevenueStream")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<SeasonalityCoefficient {self.year} Stream#{self.revenue_stream_id}>"


class APITokenScopeEnum(str, enum.Enum):
    """Enum for API token scopes"""
    READ = "READ"  # Read-only access
    WRITE = "WRITE"  # Write access (create, update)
    DELETE = "DELETE"  # Delete access
    ADMIN = "ADMIN"  # Full admin access


class APITokenStatusEnum(str, enum.Enum):
    """Enum for API token status"""
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class InvoiceProcessingStatusEnum(str, enum.Enum):
    """Enum for invoice processing statuses"""
    PENDING = "PENDING"  # Загружен, ожидает обработки
    PROCESSING = "PROCESSING"  # В процессе обработки (OCR + AI)
    PROCESSED = "PROCESSED"  # Успешно распознан
    ERROR = "ERROR"  # Ошибка обработки
    MANUAL_REVIEW = "MANUAL_REVIEW"  # Требует ручной проверки
    EXPENSE_CREATED = "EXPENSE_CREATED"  # Расход создан


class RevenueForecast(Base):
    """Revenue Forecast (Прогноз доходов) - ML-прогнозы на основе исторических данных"""
    __tablename__ = "revenue_forecasts"
    __table_args__ = (
        Index('idx_revenue_forecast_year_month', 'forecast_year', 'forecast_month'),
        Index('idx_revenue_forecast_dept', 'department_id'),
        Index('idx_revenue_forecast_stream', 'revenue_stream_id'),
        Index('idx_revenue_forecast_category', 'revenue_category_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)
    revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

    forecast_year = Column(Integer, nullable=False, index=True)
    forecast_month = Column(Integer, nullable=False, index=True)

    forecast_amount = Column(Numeric(15, 2), nullable=False)
    confidence_level = Column(Numeric(5, 2), nullable=True)  # Уровень доверия (0-100%)

    model_type = Column(String(50), nullable=True)  # "LINEAR", "ARIMA", "ML" и т.д.
    model_params = Column(JSON, nullable=True)  # Параметры модели

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Relationships
    revenue_stream = relationship("RevenueStream")
    revenue_category = relationship("RevenueCategory")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<RevenueForecast {self.forecast_year}-{self.forecast_month:02d} Amount={self.forecast_amount}>"


class APIToken(Base):
    """
    API Token (API Токены) - токены для внешней интеграции

    Используется для авторизации внешних систем для доступа к API.
    Поддерживает различные scope'ы доступа и привязку к департаменту.
    """
    __tablename__ = "api_tokens"
    __table_args__ = (
        Index('idx_api_token_key', 'token_key'),
        Index('idx_api_token_dept', 'department_id'),
        Index('idx_api_token_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Token identification
    name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)
    token_key = Column(String(255), nullable=False, unique=True, index=True)  # Actual token

    # Access control
    scopes = Column(JSON, nullable=False, default=[])  # List of APITokenScopeEnum
    status = Column(Enum(APITokenStatusEnum), nullable=False, default=APITokenStatusEnum.ACTIVE)

    # Department isolation (nullable for system-wide tokens)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Token lifecycle
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Null = never expires
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Usage tracking
    request_count = Column(Integer, nullable=False, default=0)

    # Relationships
    department_rel = relationship("Department")
    creator = relationship("User", foreign_keys=[created_by])
    revoker = relationship("User", foreign_keys=[revoked_by])

    def __repr__(self):
        return f"<APIToken {self.name} ({self.status})>"


class ProcessedInvoice(Base):
    """
    Processed Invoice (Обработанные счета) - история AI-обработки счетов на оплату

    Хранит результаты автоматического распознавания счетов через OCR и AI-парсинг.
    Используется для создания заявок на расходование (Expenses).
    """
    __tablename__ = "processed_invoices"
    __table_args__ = (
        Index('idx_processed_invoice_dept', 'department_id'),
        Index('idx_processed_invoice_status', 'status'),
        Index('idx_processed_invoice_number', 'invoice_number'),
        Index('idx_processed_invoice_inn', 'supplier_inn'),
        Index('idx_processed_invoice_date', 'invoice_date'),
        Index('idx_processed_invoice_uploaded_at', 'uploaded_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Метаданные файла
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Путь к файлу в хранилище
    file_size_kb = Column(Integer, nullable=True)  # Размер файла в КБ
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)

    # OCR результаты
    ocr_text = Column(Text, nullable=True)  # Полный текст из OCR
    ocr_confidence = Column(Numeric(5, 2), nullable=True)  # Уверенность OCR (0-100%)
    ocr_processing_time_sec = Column(Numeric(10, 2), nullable=True)  # Время обработки OCR

    # Распознанные данные счета
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_date = Column(Date, nullable=True)

    # Данные поставщика
    supplier_name = Column(String(500), nullable=True)
    supplier_inn = Column(String(12), nullable=True, index=True)
    supplier_kpp = Column(String(9), nullable=True)
    supplier_bank_name = Column(String(255), nullable=True)
    supplier_bik = Column(String(9), nullable=True)
    supplier_account = Column(String(20), nullable=True)

    # Суммы
    amount_without_vat = Column(Numeric(15, 2), nullable=True)
    vat_amount = Column(Numeric(15, 2), nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=True)

    # Дополнительные данные
    payment_purpose = Column(Text, nullable=True)
    contract_number = Column(String(100), nullable=True)
    contract_date = Column(Date, nullable=True)

    # Статус обработки
    status = Column(
        Enum(InvoiceProcessingStatusEnum),
        nullable=False,
        default=InvoiceProcessingStatusEnum.PENDING,
        index=True
    )

    # Связь с созданным расходом, контрагентом и категорией
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)  # Категория бюджета для 1С

    # 1C Integration tracking
    external_id_1c = Column(String(100), nullable=True, index=True)  # ID документа в 1С
    created_in_1c_at = Column(DateTime, nullable=True, index=True)  # Когда создан документ в 1С

    # AI данные (полный JSON с табличной частью и всеми деталями)
    parsed_data = Column(JSON, nullable=True)
    ai_processing_time_sec = Column(Numeric(10, 2), nullable=True)  # Время обработки AI
    ai_model_used = Column(String(100), nullable=True)  # Модель AI (например "gpt-5-mini")

    # Ошибки и предупреждения
    errors = Column(JSON, nullable=True)  # Список ошибок: [{"field": "inn", "message": "..."}]
    warnings = Column(JSON, nullable=True)  # Список предупреждений

    # Аудит
    processed_at = Column(DateTime, nullable=True)  # Когда завершена обработка
    expense_created_at = Column(DateTime, nullable=True)  # Когда создан expense

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    uploaded_by_rel = relationship("User", foreign_keys=[uploaded_by])
    expense_rel = relationship("Expense", foreign_keys=[expense_id])
    contractor_rel = relationship("Contractor", foreign_keys=[contractor_id])
    category_rel = relationship("BudgetCategory", foreign_keys=[category_id])

    def __repr__(self):
        return f"<ProcessedInvoice {self.invoice_number or self.original_filename} ({self.status})>"
