from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
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
    DRAFT = "Черновик"
    PENDING = "К оплате"
    PAID = "Оплачена"
    REJECTED = "Отклонена"
    CLOSED = "Закрыта"


class BudgetStatusEnum(str, enum.Enum):
    """Enum for budget plan statuses"""
    DRAFT = "Черновик"
    APPROVED = "Утвержден"


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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    category = relationship("BudgetCategory", back_populates="expenses")
    contractor = relationship("Contractor", back_populates="expenses")
    organization = relationship("Organization", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.number} - {self.amount}>"


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
