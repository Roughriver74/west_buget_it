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
    Integer,
    Numeric,
    String,
    Text,
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


class EmployeeStatusEnum(str, enum.Enum):
    """Enum for employee statuses"""
    ACTIVE = "ACTIVE"
    VACATION = "VACATION"
    SICK_LEAVE = "SICK_LEAVE"
    DISMISSED = "DISMISSED"


class PositionLevelEnum(str, enum.Enum):
    """Enum for employee position levels"""
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    MANAGER = "MANAGER"


class BudgetCategory(Base):
    """Budget categories (статьи расходов)"""
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(Enum(ExpenseTypeEnum), nullable=False)  # OPEX or CAPEX
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Подкатегории (hierarchical structure)
    parent_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="category")
    budget_plans = relationship("BudgetPlan", back_populates="category")

    # Self-referential relationship for subcategories
    parent = relationship("BudgetCategory", remote_side=[id], backref="subcategories")

    def __repr__(self):
        return f"<BudgetCategory {self.name} ({self.type})>"


class Contractor(Base):
    """Contractors (контрагенты/получатели)"""
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    short_name = Column(String(255), nullable=True)
    inn = Column(String(20), unique=True, nullable=True, index=True)
    contact_info = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="contractor")

    def __repr__(self):
        return f"<Contractor {self.name}>"


class Organization(Base):
    """Organizations (ВЕСТ ООО, ВЕСТ ГРУПП ООО)"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    legal_name = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"


class Expense(Base):
    """Expenses (заявки на расходы)"""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, nullable=False, index=True)  # 0В0В-001627

    # Foreign keys
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Amount and dates
    amount = Column(Numeric(15, 2), nullable=False)
    request_date = Column(DateTime, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=True)

    # Status
    status = Column(Enum(ExpenseStatusEnum), nullable=False, default=ExpenseStatusEnum.DRAFT, index=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)

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
    category = relationship("BudgetCategory", back_populates="expenses")
    contractor = relationship("Contractor", back_populates="expenses")
    organization = relationship("Organization", back_populates="expenses")
    attachments = relationship("ExpenseAttachment", back_populates="expense", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Expense {self.number} - {self.amount}>"


class ForecastExpense(Base):
    """Forecast expenses (прогнозные расходы на следующий месяц)"""
    __tablename__ = "forecast_expenses"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

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
    category = relationship("BudgetCategory")
    contractor = relationship("Contractor")
    organization = relationship("Organization")
    based_on_expense = relationship("Expense", foreign_keys=[based_on_expense_id])

    def __repr__(self):
        return f"<ForecastExpense {self.id} on {self.forecast_date}>"


class ExpenseAttachment(Base):
    """Expense attachments (вложения к заявкам: счета, договора, накладные)"""
    __tablename__ = "expense_attachments"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)

    # File info
    filename = Column(String(500), nullable=False)  # Оригинальное имя файла
    file_path = Column(String(1000), nullable=False)  # Путь к файлу на диске
    file_size = Column(Integer, nullable=False)  # Размер в байтах
    mime_type = Column(String(100), nullable=True)  # MIME тип файла

    # File type (invoice, contract, etc.)
    file_type = Column(String(50), nullable=True)  # invoice, contract, receipt, other

    # Additional info
    description = Column(Text, nullable=True)
    uploaded_by = Column(String(255), nullable=True)  # Кто загрузил

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="attachments")

    def __repr__(self):
        return f"<ExpenseAttachment {self.filename}>"


class BudgetPlan(Base):
    """Budget plans (планы бюджета)"""
    __tablename__ = "budget_plans"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Foreign key
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False)

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
    category = relationship("BudgetCategory", back_populates="budget_plans")

    def __repr__(self):
        return f"<BudgetPlan {self.year}-{self.month:02d} - {self.planned_amount}>"


class Employee(Base):
    """IT Department employees (сотрудники IT-отдела)"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    # Personal info
    full_name = Column(String(500), nullable=False, index=True)
    position = Column(String(255), nullable=False)  # Должность
    position_level = Column(Enum(PositionLevelEnum), nullable=True)  # Уровень позиции

    # Employment info
    hire_date = Column(Date, nullable=False)  # Дата приема на работу
    termination_date = Column(Date, nullable=True)  # Дата увольнения
    status = Column(Enum(EmployeeStatusEnum), default=EmployeeStatusEnum.ACTIVE, nullable=False, index=True)

    # Salary info
    base_salary = Column(Numeric(12, 2), nullable=False)  # Оклад (в месяц)
    tax_rate = Column(Numeric(5, 2), default=30.0, nullable=False)  # Ставка налогов (%)

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Additional info
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization")
    payrolls = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.full_name} - {self.position}>"


class Payroll(Base):
    """Payroll records (записи о начислениях зарплаты)"""
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)

    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Amounts
    base_salary = Column(Numeric(12, 2), nullable=False)  # Оклад
    bonus = Column(Numeric(12, 2), default=0, nullable=False)  # Премия
    other_payments = Column(Numeric(12, 2), default=0, nullable=False)  # Прочие выплаты

    # Calculated fields
    gross_salary = Column(Numeric(12, 2), nullable=False)  # Начислено (до налогов)
    taxes = Column(Numeric(12, 2), nullable=False)  # Налоги
    net_salary = Column(Numeric(12, 2), nullable=False)  # К выплате (на руки)

    # Total cost for employer
    employer_taxes = Column(Numeric(12, 2), nullable=False)  # Налоги работодателя (ЕСН и др.)
    total_cost = Column(Numeric(12, 2), nullable=False)  # Полная стоимость для работодателя

    # Additional info
    worked_days = Column(Integer, nullable=True)  # Отработано дней
    payment_date = Column(Date, nullable=True)  # Дата выплаты
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="payrolls")

    def __repr__(self):
        return f"<Payroll {self.employee_id} - {self.year}-{self.month:02d} - {self.total_cost}>"
