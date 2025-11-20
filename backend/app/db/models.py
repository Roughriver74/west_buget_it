from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
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
    TypeDecorator,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .session import Base


class FlexibleEnumType(TypeDecorator):
    """
    Custom enum type that handles legacy values from database.
    Automatically converts old Russian values and other legacy formats to current enum values.
    """
    impl = Enum
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        # Map legacy values to current enum values
        self.legacy_mapping = self._get_legacy_mapping(enum_class)
        super().__init__(enum_class, *args, **kwargs)

    def _get_legacy_mapping(self, enum_class):
        """Get mapping of legacy values to current enum values"""
        if enum_class == ExpenseStatusEnum:
            return {
                'Черновик': 'DRAFT',
                'ЧЕРНОВИК': 'DRAFT',
                'На согласовании': 'PENDING',
                'НА СОГЛАСОВАНИИ': 'PENDING',
                'К оплате': 'PENDING',
                'К ОПЛАТЕ': 'PENDING',
                'Оплачена': 'PAID',
                'ОПЛАЧЕНА': 'PAID',
                'Оплачено': 'PAID',
                'ОПЛАЧЕНО': 'PAID',
                'Отклонена': 'REJECTED',
                'ОТКЛОНЕНА': 'REJECTED',
                'Закрыта': 'CLOSED',
                'ЗАКРЫТА': 'CLOSED',
                'PAID': 'PAID',  # Sometimes stored as uppercase
            }
        elif enum_class == BudgetStatusEnum:
            return {
                'Черновик': 'DRAFT',
                'ЧЕРНОВИК': 'DRAFT',
                'Утверждено': 'APPROVED',
                'УТВЕРЖДЕНО': 'APPROVED',
            }
        return {}

    def process_result_value(self, value, dialect):
        """Convert legacy values from database to current enum values"""
        if value is None:
            return None
        
        # If it's already a valid enum value, return it
        try:
            return self.enum_class(value)
        except ValueError:
            pass
        
        # Try to convert legacy value
        value_str = str(value).strip()
        
        # Check legacy mapping
        if value_str in self.legacy_mapping:
            mapped_value = self.legacy_mapping[value_str]
            try:
                return self.enum_class(mapped_value)
            except ValueError:
                pass
        
        # Try case-insensitive match
        value_upper = value_str.upper()
        for legacy_val, enum_val in self.legacy_mapping.items():
            if legacy_val.upper() == value_upper:
                try:
                    return self.enum_class(enum_val)
                except ValueError:
                    pass
        
        # If still not found, try direct enum lookup (case-insensitive)
        for enum_val in self.enum_class:
            if enum_val.value.upper() == value_upper:
                return enum_val
        
        # Last resort: return default or raise error
        # For backward compatibility, try to return a sensible default
        if self.enum_class == ExpenseStatusEnum:
            return ExpenseStatusEnum.DRAFT
        elif self.enum_class == BudgetStatusEnum:
            return BudgetStatusEnum.DRAFT
        
        # If no default available, log and return first enum value
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unknown enum value '{value}' for {self.enum_class.__name__}, using default")
        return list(self.enum_class)[0]


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
    ACCOUNTANT = "ACCOUNTANT"  # Финансист - справочники и НДФЛ, доступ ко всем отделам
    HR = "HR"  # Сотрудник отдела кадров - доступ к модулю HR_DEPARTMENT для всех отделов
    USER = "USER"  # Пользователь отдела - доступ только к своему отделу
    REQUESTER = "REQUESTER"  # Запросчик заявок/расходов (ограниченные права)


class BonusTypeEnum(str, enum.Enum):
    """Enum for bonus calculation types"""
    PERFORMANCE_BASED = "PERFORMANCE_BASED"  # Результативный - зависит от КПИ%
    FIXED = "FIXED"  # Фиксированный - не зависит от КПИ
    MIXED = "MIXED"  # Смешанный - часть фиксированная, часть от КПИ


class TaxTypeEnum(str, enum.Enum):
    """Enum for tax and social contribution types"""
    INCOME_TAX = "INCOME_TAX"  # НДФЛ
    PENSION_FUND = "PENSION_FUND"  # ПФР (пенсионный фонд)
    MEDICAL_INSURANCE = "MEDICAL_INSURANCE"  # ФОМС (медицинское страхование)
    SOCIAL_INSURANCE = "SOCIAL_INSURANCE"  # ФСС (социальное страхование)
    INJURY_INSURANCE = "INJURY_INSURANCE"  # Страхование от несчастных случаев


class KPIGoalStatusEnum(str, enum.Enum):
    """Enum for KPI goal statuses"""
    DRAFT = "DRAFT"  # Черновик
    ACTIVE = "ACTIVE"  # Активная цель
    ACHIEVED = "ACHIEVED"  # Достигнута
    NOT_ACHIEVED = "NOT_ACHIEVED"  # Не достигнута
    CANCELLED = "CANCELLED"  # Отменена


class EmployeeKPIStatusEnum(str, enum.Enum):
    """Enum for EmployeeKPI workflow statuses (simplified workflow)"""
    DRAFT = "DRAFT"  # Черновик - цели установлены, сотрудник работает над ними
    UNDER_REVIEW = "UNDER_REVIEW"  # На проверке - результаты введены, ждет оценки руководителя
    APPROVED = "APPROVED"  # Утверждено - руководитель утвердил, премии рассчитаны
    REJECTED = "REJECTED"  # Отклонено - требуется доработка


# KPITaskStatusEnum and KPITaskPriorityEnum removed - Tasks feature deprecated


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


class BankTransactionTypeEnum(str, enum.Enum):
    """Enum for bank transaction types"""
    DEBIT = "DEBIT"  # Списание (расход)
    CREDIT = "CREDIT"  # Поступление (доход)


class BankTransactionStatusEnum(str, enum.Enum):
    """Enum for bank transaction processing statuses"""
    NEW = "NEW"  # Новая, не обработана
    CATEGORIZED = "CATEGORIZED"  # Категория назначена
    MATCHED = "MATCHED"  # Связана с заявкой
    APPROVED = "APPROVED"  # Проверена и одобрена
    NEEDS_REVIEW = "NEEDS_REVIEW"  # Требует ручной проверки
    IGNORED = "IGNORED"  # Проигнорирована (не относится к учету)


class PaymentSourceEnum(str, enum.Enum):
    """Enum for payment source (bank or cash)"""
    BANK = "BANK"  # Банк
    CASH = "CASH"  # Касса


class RegionEnum(str, enum.Enum):
    """Enum for regions"""
    MOSCOW = "MOSCOW"  # Москва
    SPB = "SPB"  # Санкт-Петербург
    REGIONS = "REGIONS"  # Регионы
    FOREIGN = "FOREIGN"  # Зарубеж


class DocumentTypeEnum(str, enum.Enum):
    """Enum for document types"""
    PAYMENT_ORDER = "PAYMENT_ORDER"  # Платежное поручение
    CASH_ORDER = "CASH_ORDER"  # Кассовый ордер
    INVOICE = "INVOICE"  # Счет
    ACT = "ACT"  # Акт
    CONTRACT = "CONTRACT"  # Договор
    OTHER = "OTHER"  # Другое


class ModuleEventTypeEnum(str, enum.Enum):
    """Enum for module event types"""
    MODULE_ENABLED = "MODULE_ENABLED"  # Модуль включен
    MODULE_DISABLED = "MODULE_DISABLED"  # Модуль отключен
    MODULE_EXPIRED = "MODULE_EXPIRED"  # Срок действия модуля истек
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"  # Превышен лимит
    LIMIT_WARNING = "LIMIT_WARNING"  # Предупреждение о приближении к лимиту
    ACCESS_DENIED = "ACCESS_DENIED"  # Отказ в доступе
    MODULE_UPDATED = "MODULE_UPDATED"  # Модуль обновлен


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
        Index('idx_budget_category_external_id_1c_dept', 'external_id_1c', 'department_id', unique=True),  # Composite unique for 1C sync
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(Enum(ExpenseTypeEnum), nullable=False)  # OPEX or CAPEX
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Подкатегории (hierarchical structure)
    parent_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)

    # 1C Integration (Catalog_СтатьиДвиженияДенежныхСредств)
    external_id_1c = Column(String(100), nullable=True, index=True)  # Ref_Key из 1С
    code_1c = Column(String(50), nullable=True)  # Code из 1С (например: "01-000021")
    is_folder = Column(Boolean, default=False, nullable=False)  # Папка (группа) или элемент
    order_index = Column(Integer, nullable=True)  # РеквизитДопУпорядочивания из 1С

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
        Index('idx_contractor_external_id_1c_dept', 'external_id_1c', 'department_id', unique=True),  # Composite unique for 1C sync
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    short_name = Column(String(255), nullable=True)
    inn = Column(String(20), nullable=True, index=True)  # Removed unique constraint for multi-tenancy
    kpp = Column(String(20), nullable=True)  # КПП для 1С интеграции
    contact_info = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # 1C Integration
    external_id_1c = Column(String(100), nullable=True, index=True)  # ID в 1С (unique per department)

    # Bitrix24 integration
    bitrix_company_id = Column(Integer, nullable=True, index=True)  # ID компании в Битрикс24

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
    """Organizations (ДЕМО ООО, ДЕМО ГРУПП ООО) - SHARED across all departments"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)  # Unique constraint restored - shared entity
    legal_name = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # 1C Integration (Organizations are shared, so external_id_1c should be unique globally)
    external_id_1c = Column(String(100), nullable=True, unique=True, index=True)  # ID в 1С (уникален глобально)
    full_name = Column(String(500), nullable=True)  # Полное наименование из 1С (НаименованиеПолное)
    short_name = Column(String(255), nullable=True)  # Краткое наименование из 1С (НаименованиеСокращенное)
    inn = Column(String(20), nullable=True, index=True)  # ИНН
    kpp = Column(String(20), nullable=True)  # КПП
    ogrn = Column(String(20), nullable=True)  # ОГРН
    prefix = Column(String(10), nullable=True)  # Префикс (например: "ВА", "Демо")
    okpo = Column(String(20), nullable=True)  # Код по ОКПО
    status_1c = Column(String(50), nullable=True)  # Статус из 1С ("Действует", "Ликвидирована")

    # Department for tracking which department imported (optional for shared entities)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="organization")
    department_rel = relationship("Department", foreign_keys=[department_id])

    def __repr__(self):
        return f"<Organization {self.name}>"


class Expense(Base):
    """Expenses (заявки на расходы)"""
    __tablename__ = "expenses"
    __table_args__ = (
        Index('idx_expense_dept_status', 'department_id', 'status'),
        Index('idx_expense_dept_date', 'department_id', 'request_date'),
        Index('idx_expense_external_id_1c_dept', 'external_id_1c', 'department_id', unique=True),  # Composite unique for 1C sync
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
    status = Column(FlexibleEnumType(ExpenseStatusEnum), nullable=False, default=ExpenseStatusEnum.DRAFT, index=True)
    is_paid = Column(Boolean, default=False, nullable=False, index=True)
    is_closed = Column(Boolean, default=False, nullable=False, index=True)

    # Additional info
    comment = Column(Text, nullable=True)
    requester = Column(String(255), nullable=True)  # Заявитель

    # Import tracking
    imported_from_ftp = Column(Boolean, default=False, nullable=False)  # Загружена из FTP
    needs_review = Column(Boolean, default=False, nullable=False)  # Требует проверки категории
    external_id_1c = Column(String(100), nullable=True, index=True)  # ID документа в 1С (для синхронизации)

    # Bitrix24 integration
    bitrix_task_id = Column(Integer, nullable=True, index=True)  # ID задачи в Битрикс24
    bitrix_task_url = Column(String(500), nullable=True)  # URL задачи в Битрикс24
    bitrix_sync_at = Column(DateTime, nullable=True)  # Когда синхронизировано с Битрикс24

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
    status = Column(FlexibleEnumType(BudgetStatusEnum), default=BudgetStatusEnum.DRAFT, nullable=False, index=True)

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


class SalaryTypeEnum(str, enum.Enum):
    """Enum for salary type - how salary is entered"""
    GROSS = "GROSS"  # Брутто (до вычета НДФЛ) - начисление
    NET = "NET"      # Нетто (на руки) - желаемая сумма к выплате


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
    birth_date = Column(Date, nullable=True)  # Дата рождения (для различения полных тёзок)

    # Employment details
    hire_date = Column(Date, nullable=True)  # Дата приема на работу
    fire_date = Column(Date, nullable=True)  # Дата увольнения
    status = Column(Enum(EmployeeStatusEnum), nullable=False, default=EmployeeStatusEnum.ACTIVE, index=True)

    # Salary information (NEW in Task 1.4: Брутто ↔ Нетто расчет)
    salary_type = Column(Enum(SalaryTypeEnum), nullable=False, default=SalaryTypeEnum.GROSS, index=True)  # Тип ввода оклада
    base_salary = Column(Numeric(15, 2), nullable=False)  # Оклад (значение которое ввели)

    # Calculated salary fields (auto-calculated based on salary_type)
    base_salary_gross = Column(Numeric(15, 2), nullable=True)  # Оклад брутто (до вычета НДФЛ)
    base_salary_net = Column(Numeric(15, 2), nullable=True)    # Оклад нетто (на руки после НДФЛ)
    ndfl_amount = Column(Numeric(15, 2), nullable=True)        # Сумма НДФЛ
    ndfl_rate = Column(Numeric(5, 4), nullable=False, default=0.13)  # Ставка НДФЛ (по умолчанию 13%)

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
    timesheets = relationship("WorkTimesheet", back_populates="employee")

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


class TaxRate(Base):
    """Tax rates and social contributions (налоговые ставки и страховые взносы)"""
    __tablename__ = "tax_rates"
    __table_args__ = (
        Index('idx_tax_rate_type_active', 'tax_type', 'is_active'),
        Index('idx_tax_rate_effective_date', 'effective_from', 'effective_to'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Tax type
    tax_type = Column(Enum(TaxTypeEnum), nullable=False, index=True)
    name = Column(String(200), nullable=False)  # Название налога/взноса
    description = Column(Text, nullable=True)  # Описание

    # Rate details
    rate = Column(Numeric(5, 4), nullable=False)  # Ставка (например, 0.13 для 13%)
    threshold_amount = Column(Numeric(15, 2), nullable=True)  # Порог дохода (если применимо)
    rate_above_threshold = Column(Numeric(5, 4), nullable=True)  # Ставка выше порога (например, 0.15 для НДФЛ > 5 млн)

    # Effective period
    effective_from = Column(Date, nullable=False, index=True)  # Дата начала действия
    effective_to = Column(Date, nullable=True, index=True)  # Дата окончания действия (null = бессрочно)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)  # Примечания, основание (например, "Закон 123-ФЗ")

    # Relationships
    department_rel = relationship("Department")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<TaxRate {self.tax_type.value}: {self.rate*100}%>"


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
    template_items = relationship("KPIGoalTemplateItem", back_populates="goal")

    def __repr__(self):
        return f"<KPIGoal {self.name} (weight={self.weight})>"


class KPIGoalTemplate(Base):
    """KPI Goal Template (шаблон набора целей для быстрого назначения сотрудникам)

    Позволяет менеджерам создавать повторно используемые наборы целей (например, "Продажи Q1", "IT Стандарт")
    и быстро применять их к сотрудникам, сокращая ручную работу.
    """
    __tablename__ = "kpi_goal_templates"
    __table_args__ = (
        Index('idx_kpi_template_dept_active', 'department_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Template information
    name = Column(String(255), nullable=False, index=True)  # Название шаблона
    description = Column(Text, nullable=True)  # Описание

    # Department association (multi-tenancy)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Active status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    department_rel = relationship("Department")
    created_by = relationship("User")
    template_goals = relationship("KPIGoalTemplateItem", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KPIGoalTemplate {self.name} ({len(self.template_goals)} goals)>"


class KPIGoalTemplateItem(Base):
    """KPI Goal Template Item (цель в шаблоне с весом)

    Связывает KPIGoal с шаблоном и задает вес для этой цели.
    При применении шаблона создаются EmployeeKPIGoal записи с этими весами.
    """
    __tablename__ = "kpi_goal_template_items"
    __table_args__ = (
        Index('idx_template_item_template', 'template_id'),
        Index('idx_template_item_goal', 'goal_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Relations
    template_id = Column(Integer, ForeignKey("kpi_goal_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("kpi_goals.id"), nullable=False, index=True)

    # Weight for this goal in the template (0-100%)
    weight = Column(Numeric(5, 2), nullable=False)  # Вес цели в шаблоне

    # Default target value (optional, can override goal's default target_value)
    default_target_value = Column(Numeric(15, 2), nullable=True)

    # Order in template (for UI display)
    display_order = Column(Integer, nullable=False, default=0)

    # Relationships
    template = relationship("KPIGoalTemplate", back_populates="template_goals")
    goal = relationship("KPIGoal", back_populates="template_items")

    def __repr__(self):
        return f"<KPIGoalTemplateItem Template#{self.template_id} Goal#{self.goal_id} weight={self.weight}%>"


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

    # Depremium threshold (порог депремирования)
    depremium_threshold = Column(Numeric(5, 2), nullable=True, default=10.00)  # Минимальный порог KPI% (по умолчанию 10%)
    depremium_applied = Column(Boolean, nullable=False, default=False)  # Флаг: было ли применено депремирование

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

    # Task complexity bonus removed - Tasks feature deprecated

    # Workflow status
    status = Column(
        Enum(EmployeeKPIStatusEnum),
        default=EmployeeKPIStatusEnum.DRAFT,
        nullable=False,
        index=True
    )

    # Approval tracking
    submitted_at = Column(DateTime, nullable=True)  # Когда отправлено на проверку
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто проверил
    reviewed_at = Column(DateTime, nullable=True)  # Когда проверено
    rejection_reason = Column(Text, nullable=True)  # Причина отклонения (если REJECTED)

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
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

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


# KPITask model removed - Tasks feature deprecated in favor of simplified KPI Goals workflow


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


class TimesheetStatusEnum(str, enum.Enum):
    """Enum for timesheet statuses (Статусы табеля учета рабочего времени)"""
    DRAFT = "DRAFT"  # Черновик (можно редактировать)
    APPROVED = "APPROVED"  # Утвержден (редактирование запрещено)
    PAID = "PAID"  # Оплачен (финальный статус)


class DayTypeEnum(str, enum.Enum):
    """Enum for day types (Типы дней в табеле)"""
    WORK = "WORK"  # Рабочий день (оплачиваемый)
    UNPAID_LEAVE = "UNPAID_LEAVE"  # День за свой счет (неоплачиваемый отпуск)
    SICK_LEAVE = "SICK_LEAVE"  # Больничный
    VACATION = "VACATION"  # Оплачиваемый отпуск
    WEEKEND = "WEEKEND"  # Выходной
    HOLIDAY = "HOLIDAY"  # Праздник


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
    desired_payment_date = Column(Date, nullable=True)  # Желаемая дата оплаты (ЖелательнаяДатаПлатежа) - устанавливается пользователем для отправки в 1С

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


class BankTransaction(Base):
    """
    Bank Transactions (Банковские операции)
    Списания и поступления из банковских выписок
    """
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Основная информация о транзакции
    transaction_date = Column(Date, nullable=False, index=True)  # Дата операции
    amount = Column(Numeric(15, 2), nullable=False)  # Сумма
    transaction_type = Column(
        Enum(BankTransactionTypeEnum),
        nullable=False,
        default=BankTransactionTypeEnum.DEBIT,
        index=True
    )  # Тип операции: списание или поступление

    # Контрагент
    counterparty_name = Column(String(500), nullable=True, index=True)  # Наименование контрагента
    counterparty_inn = Column(String(12), nullable=True, index=True)  # ИНН контрагента
    counterparty_kpp = Column(String(9), nullable=True)  # КПП контрагента
    counterparty_account = Column(String(20), nullable=True)  # Счет контрагента
    counterparty_bank = Column(String(500), nullable=True)  # Банк контрагента
    counterparty_bik = Column(String(20), nullable=True)  # БИК банка контрагента (SWIFT/BIC code)

    # Назначение платежа
    payment_purpose = Column(Text, nullable=True)  # Назначение платежа (основа для AI классификации)
    business_operation = Column(String(100), nullable=True, index=True)  # ХозяйственнаяОперация из 1С (для авто-категоризации)

    # Источник платежа
    payment_source = Column(
        Enum(PaymentSourceEnum),
        nullable=True,
        default=PaymentSourceEnum.BANK,
        index=True
    )  # Источник: банк или касса

    # Наша организация
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    account_number = Column(String(20), nullable=True)  # Наш счет

    # Банковские реквизиты документа
    document_number = Column(String(50), nullable=True, index=True)  # Номер платежного документа
    document_date = Column(Date, nullable=True)  # Дата платежного документа

    # Классификация (AI и ручная)
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)  # Статья расходов
    category_confidence = Column(Numeric(5, 4), nullable=True)  # Уверенность AI в категории (0-1)
    suggested_category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True)  # Предложенная AI категория

    # Связь с заявками
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True, index=True)  # Связанная заявка
    matching_score = Column(Numeric(5, 2), nullable=True)  # Степень совпадения с заявкой (0-100)
    suggested_expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)  # Предложенная заявка

    # Статус обработки
    status = Column(
        Enum(BankTransactionStatusEnum),
        nullable=False,
        default=BankTransactionStatusEnum.NEW,
        index=True
    )

    # Дополнительные данные
    notes = Column(Text, nullable=True)  # Примечания финансиста
    is_regular_payment = Column(Boolean, default=False, nullable=False, index=True)  # Регулярный платеж
    regular_payment_pattern_id = Column(Integer, nullable=True)  # ID паттерна регулярного платежа

    # Расширенные поля (для детализации операций)
    region = Column(Enum(RegionEnum), nullable=True, index=True)  # Регион
    exhibition = Column(String(255), nullable=True)  # Выставка/мероприятие
    document_type = Column(Enum(DocumentTypeEnum), nullable=True)  # Тип документа

    # Детализация сумм по валютам и типам
    amount_rub_credit = Column(Numeric(15, 2), nullable=True)  # Приход в рублях
    amount_eur_credit = Column(Numeric(15, 2), nullable=True)  # Приход в евро
    amount_rub_debit = Column(Numeric(15, 2), nullable=True)  # Расход в рублях
    amount_eur_debit = Column(Numeric(15, 2), nullable=True)  # Расход в евро

    # Временные метки
    transaction_month = Column(Integer, nullable=True, index=True)  # Месяц операции (1-12)
    transaction_year = Column(Integer, nullable=True, index=True)  # Год операции
    expense_acceptance_month = Column(Integer, nullable=True)  # Месяц принятия к расходу (1-12)
    expense_acceptance_year = Column(Integer, nullable=True)  # Год принятия к расходу

    # Обработка и аудит
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто проверил
    reviewed_at = Column(DateTime, nullable=True)  # Когда проверено

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Импорт
    import_source = Column(String(50), nullable=True)  # Источник: "FTP", "MANUAL_UPLOAD", "API"
    import_file_name = Column(String(255), nullable=True)  # Имя файла импорта
    imported_at = Column(DateTime, nullable=True)  # Когда импортировано

    # External ID (для связи с 1С)
    external_id_1c = Column(String(100), nullable=True, index=True, unique=True)  # ID в 1С

    # Системные поля
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    organization_rel = relationship("Organization", foreign_keys=[organization_id])
    category_rel = relationship("BudgetCategory", foreign_keys=[category_id])
    suggested_category_rel = relationship("BudgetCategory", foreign_keys=[suggested_category_id])
    expense_rel = relationship("Expense", foreign_keys=[expense_id])
    suggested_expense_rel = relationship("Expense", foreign_keys=[suggested_expense_id])
    reviewed_by_rel = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<BankTransaction {self.transaction_date} {self.counterparty_name} {self.amount}>"


# ==================== Credit Portfolio Models (from Acme Fin DWH) ====================

class FinOrganization(Base):
    """Model for credit portfolio organizations (Организации холдинга)"""
    __tablename__ = "fin_organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    inn = Column(String(20))

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    receipts = relationship("FinReceipt", back_populates="org")
    expenses_fin = relationship("FinExpense", back_populates="org")
    contracts = relationship("FinContract", back_populates="organization")

    # Unique constraint на name + department_id
    __table_args__ = (
        Index('ix_fin_organizations_name_dept', 'name', 'department_id', unique=True),
    )

    def __repr__(self):
        return f"<FinOrganization(id={self.id}, name='{self.name}')>"


class FinBankAccount(Base):
    """Model for bank accounts for credit portfolio (Банковские счета)"""
    __tablename__ = "fin_bank_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(255), nullable=False, index=True)
    bank_name = Column(String(255))

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    receipts = relationship("FinReceipt", back_populates="bank")
    expenses_fin = relationship("FinExpense", back_populates="bank")

    # Unique constraint на account_number + department_id
    __table_args__ = (
        Index('ix_fin_bank_accounts_number_dept', 'account_number', 'department_id', unique=True),
    )

    def __repr__(self):
        return f"<FinBankAccount(id={self.id}, account='{self.account_number}')>"


class FinContract(Base):
    """Model for credit contracts (Кредитные договоры)"""
    __tablename__ = "fin_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_number = Column(String(255), nullable=False, index=True)
    contract_date = Column(Date, index=True)
    contract_type = Column(String(100))  # Кредит, Заем, и т.д.
    counterparty = Column(String(255))

    # Foreign keys
    organization_id = Column(Integer, ForeignKey("fin_organizations.id"), nullable=True, index=True)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    organization = relationship("FinOrganization", back_populates="contracts")
    receipts = relationship("FinReceipt", back_populates="contract")
    expenses_fin = relationship("FinExpense", back_populates="contract")

    # Unique constraint на contract_number + department_id
    __table_args__ = (
        Index('ix_fin_contracts_number_dept', 'contract_number', 'department_id', unique=True),
    )

    def __repr__(self):
        return f"<FinContract(id={self.id}, number='{self.contract_number}')>"


class FinReceipt(Base):
    """Model for credit receipts / поступления кредитов"""
    __tablename__ = "fin_receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(String(255), unique=True, nullable=False, index=True)

    # Foreign keys
    organization_id = Column(Integer, ForeignKey("fin_organizations.id"), index=True, nullable=False)
    bank_account_id = Column(Integer, ForeignKey("fin_bank_accounts.id"), index=True)
    contract_id = Column(Integer, ForeignKey("fin_contracts.id"), index=True)

    # Transaction details
    operation_type = Column(String(255))
    accounting_account = Column(String(50))
    document_number = Column(String(255))
    document_date = Column(Date, index=True)
    payer = Column(String(255), index=True)
    payer_account = Column(String(255))
    settlement_account = Column(String(100))
    contract_date = Column(Date)
    currency = Column(String(10), default="RUB")
    amount = Column(Numeric(15, 2), nullable=False)
    commission = Column(Numeric(15, 2))
    payment_purpose = Column(Text)
    responsible_person = Column(String(255))
    comment = Column(Text)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    org = relationship("FinOrganization", back_populates="receipts")
    bank = relationship("FinBankAccount", back_populates="receipts")
    contract = relationship("FinContract", back_populates="receipts")

    # Unique constraint на operation_id + department_id
    __table_args__ = (
        Index('ix_fin_receipts_operation_dept', 'operation_id', 'department_id', unique=True),
    )

    def __repr__(self):
        return f"<FinReceipt(id={self.id}, operation_id='{self.operation_id}', amount={self.amount})>"


class FinExpense(Base):
    """Model for credit expenses / списания по кредитам"""
    __tablename__ = "fin_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(String(255), unique=True, nullable=False, index=True)

    # Foreign keys
    organization_id = Column(Integer, ForeignKey("fin_organizations.id"), index=True, nullable=False)
    bank_account_id = Column(Integer, ForeignKey("fin_bank_accounts.id"), index=True)
    contract_id = Column(Integer, ForeignKey("fin_contracts.id"), index=True)

    # Transaction details
    operation_type = Column(String(255))
    accounting_account = Column(String(50))
    document_number = Column(String(255))
    document_date = Column(Date, index=True)
    recipient = Column(String(255), index=True)
    recipient_account = Column(String(255))
    debit_account = Column(String(100))
    contract_date = Column(Date)
    currency = Column(String(10), default="RUB")
    amount = Column(Numeric(15, 2), nullable=False)
    expense_article = Column(String(255), index=True)
    payment_purpose = Column(Text)
    responsible_person = Column(String(255))
    comment = Column(Text)
    tax_period = Column(String(10))
    unconfirmed_by_bank = Column(Boolean, default=False)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    department_rel = relationship("Department")
    org = relationship("FinOrganization", back_populates="expenses_fin")
    bank = relationship("FinBankAccount", back_populates="expenses_fin")
    contract = relationship("FinContract", back_populates="expenses_fin")
    details = relationship("FinExpenseDetail", back_populates="expense", cascade="all, delete-orphan")

    # Unique constraint на operation_id + department_id
    __table_args__ = (
        Index('ix_fin_expenses_operation_dept', 'operation_id', 'department_id', unique=True),
    )

    def __repr__(self):
        return f"<FinExpense(id={self.id}, operation_id='{self.operation_id}', amount={self.amount})>"


class FinExpenseDetail(Base):
    """Model for expense details / расшифровка платежей (тело/проценты)"""
    __tablename__ = "fin_expense_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_operation_id = Column(
        String(255),
        ForeignKey("fin_expenses.operation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contract_number = Column(String(255), index=True)
    repayment_type = Column(String(100))
    settlement_account = Column(String(100), index=True)
    advance_account = Column(String(100))
    payment_type = Column(String(255), index=True)  # Тело кредита / Проценты
    payment_amount = Column(Numeric(15, 2))
    settlement_rate = Column(Numeric(15, 6), default=1)
    settlement_amount = Column(Numeric(15, 2))
    vat_amount = Column(Numeric(15, 2))
    expense_amount = Column(Numeric(15, 2))
    vat_in_expense = Column(Numeric(15, 2))

    # Multi-tenancy (наследуется от родительского expense)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    department_rel = relationship("Department")
    expense = relationship("FinExpense", back_populates="details")

    def __repr__(self):
        return f"<FinExpenseDetail(id={self.id}, expense_operation_id='{self.expense_operation_id}')>"


class FinImportLog(Base):
    """Model for import logs / журнал импорта из 1С"""
    __tablename__ = "fin_import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_date = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    source_file = Column(String(255), index=True)
    table_name = Column(String(50), index=True)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    status = Column(String(50), index=True)  # SUCCESS, FAILED, PARTIAL
    error_message = Column(Text)
    processed_by = Column(String(100))
    processing_time_seconds = Column(Numeric(10, 2))

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Relationships
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<FinImportLog(id={self.id}, source_file='{self.source_file}', status='{self.status}')>"


class BusinessOperationMapping(Base):
    """
    Model for mapping 1C Business Operations (ХозяйственнаяОперация) to Budget Categories

    Гибкая таблица для настройки соответствия хозяйственных операций из 1С
    и категорий бюджета. Позволяет настраивать маппинг для каждого отдела отдельно.
    """
    __tablename__ = "business_operation_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # Хозяйственная операция из 1С
    business_operation = Column(String(100), nullable=False, index=True)

    # Связь с категорией бюджета (nullable для авто-созданных stub записей)
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)

    # Приоритет (чем выше - тем важнее, для случаев когда одна операция может быть в нескольких категориях)
    priority = Column(Integer, default=10, nullable=False)

    # Уверенность маппинга (0.0-1.0)
    confidence = Column(Numeric(5, 4), default=0.98, nullable=False)

    # Комментарий (зачем этот маппинг)
    notes = Column(Text, nullable=True)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    department_rel = relationship("Department")
    category_rel = relationship("BudgetCategory")
    created_by_user = relationship("User", foreign_keys=[created_by])

    # Unique constraint: одна операция -> одна категория в рамках отдела
    __table_args__ = (
        Index('ix_business_operation_mapping_unique',
              'business_operation', 'department_id', 'category_id', unique=True),
    )

    def __repr__(self):
        return f"<BusinessOperationMapping(id={self.id}, operation='{self.business_operation}', category_id={self.category_id})>"


# ==================== Insurance & Payroll Scenario Models ====================


class InsuranceRate(Base):
    """
    Справочник ставок страховых взносов по годам

    Хранит исторические и планируемые ставки для:
    - Пенсионного фонда (ПФР)
    - Медицинского страхования (ФОМС)
    - Социального страхования (ФСС)
    - Страхования от несчастных случаев

    Позволяет отслеживать изменения законодательства и их влияние на ФОТ
    """
    __tablename__ = "insurance_rates"
    __table_args__ = (
        Index('ix_insurance_rate_year_type', 'year', 'rate_type'),
        Index('ix_insurance_rate_dept_year', 'department_id', 'year'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Период действия
    year = Column(Integer, nullable=False, index=True)

    # Тип страхового взноса
    rate_type = Column(Enum(TaxTypeEnum), nullable=False, index=True)

    # Ставка в процентах (например, 22.0 для 22%)
    rate_percentage = Column(Numeric(5, 2), nullable=False)

    # Пороговые значения для прогрессивной шкалы (опционально)
    threshold_amount = Column(Numeric(15, 2), nullable=True)  # Порог для повышенной ставки
    rate_above_threshold = Column(Numeric(5, 2), nullable=True)  # Ставка выше порога

    # Описание изменений
    description = Column(Text, nullable=True)  # Например: "Повышение с 22% до 30%"
    legal_basis = Column(String(255), nullable=True)  # Ссылка на ФЗ/приказ

    # Расчетные поля (для быстрого доступа)
    total_employer_burden = Column(Numeric(5, 2), nullable=True)  # Общая нагрузка работодателя (сумма всех взносов)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    department_rel = relationship("Department")
    created_by_user = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<InsuranceRate {self.year} {self.rate_type.value}: {self.rate_percentage}%>"


class PayrollScenarioTypeEnum(str, enum.Enum):
    """Enum for payroll scenario types"""
    BASE = "BASE"  # Базовый сценарий (текущее состояние)
    OPTIMISTIC = "OPTIMISTIC"  # Оптимистичный (рост, расширение штата)
    PESSIMISTIC = "PESSIMISTIC"  # Пессимистичный (сокращение, оптимизация)
    CUSTOM = "CUSTOM"  # Кастомный сценарий


class PayrollDataSourceEnum(str, enum.Enum):
    """Enum for payroll scenario data source"""
    EMPLOYEES = "EMPLOYEES"  # Текущие сотрудники (employees table)
    ACTUAL = "ACTUAL"  # Фактические выплаты (payroll_actuals)
    PLAN = "PLAN"  # Плановые данные (payroll_plans)


class PayrollScenario(Base):
    """
    Сценарии планирования ФОТ с учетом изменений в законодательстве

    Позволяет моделировать различные варианты:
    - Базовый: текущий штат + новые ставки
    - Оптимистичный: расширение штата
    - Пессимистичный: сокращение штата/зарплат для компенсации роста взносов
    """
    __tablename__ = "payroll_scenarios"
    __table_args__ = (
        Index('ix_payroll_scenario_dept_year', 'department_id', 'target_year'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Основная информация
    name = Column(String(255), nullable=False)  # Название сценария
    description = Column(Text, nullable=True)  # Описание
    scenario_type = Column(Enum(PayrollScenarioTypeEnum), nullable=False, default=PayrollScenarioTypeEnum.BASE)

    # Источник данных для расчета
    data_source = Column(Enum(PayrollDataSourceEnum), nullable=False, default=PayrollDataSourceEnum.EMPLOYEES)

    # Год планирования
    target_year = Column(Integer, nullable=False, index=True)  # Год, на который строится сценарий
    base_year = Column(Integer, nullable=False)  # Базовый год для сравнения

    # Параметры сценария
    headcount_change_percent = Column(Numeric(5, 2), default=0, nullable=False)  # Изменение штата в %
    salary_change_percent = Column(Numeric(5, 2), default=0, nullable=False)  # Изменение з/п в %

    # Расчетные итоги (вычисляются автоматически)
    total_headcount = Column(Integer, nullable=True)  # Итоговая численность
    total_base_salary = Column(Numeric(15, 2), nullable=True)  # Итого оклады
    total_insurance_cost = Column(Numeric(15, 2), nullable=True)  # Итого страховые взносы
    total_payroll_cost = Column(Numeric(15, 2), nullable=True)  # Итого ФОТ (оклады + взносы + НДФЛ)

    # Сравнение с базовым годом
    base_year_total_cost = Column(Numeric(15, 2), nullable=True)  # ФОТ базового года
    cost_difference = Column(Numeric(15, 2), nullable=True)  # Разница в рублях
    cost_difference_percent = Column(Numeric(5, 2), nullable=True)  # Разница в %

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    department_rel = relationship("Department")
    created_by_user = relationship("User", foreign_keys=[created_by])
    scenario_details = relationship("PayrollScenarioDetail", back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PayrollScenario {self.name} ({self.target_year})>"


class PayrollScenarioDetail(Base):
    """
    Детали сценария ФОТ по сотрудникам

    Хранит планируемые изменения для каждого сотрудника в рамках сценария:
    - Изменение оклада
    - Статус (работает/уволен/новый)
    - Расчет страховых взносов
    """
    __tablename__ = "payroll_scenario_details"
    __table_args__ = (
        Index('ix_payroll_scenario_detail_scenario', 'scenario_id'),
        Index('ix_payroll_scenario_detail_employee', 'employee_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Связи
    scenario_id = Column(Integer, ForeignKey("payroll_scenarios.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)  # NULL для новых позиций

    # Данные сотрудника
    employee_name = Column(String(255), nullable=False)  # ФИО (для новых или архивных)
    position = Column(String(255), nullable=True)  # Должность

    # Статус в сценарии
    is_new_hire = Column(Boolean, default=False, nullable=False)  # Новый сотрудник
    is_terminated = Column(Boolean, default=False, nullable=False)  # Увольнение
    termination_month = Column(Integer, nullable=True)  # Месяц увольнения (1-12)

    # Плановый оклад и премии
    base_salary = Column(Numeric(15, 2), nullable=False)
    monthly_bonus = Column(Numeric(15, 2), default=0, nullable=False)
    quarterly_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Квартальная премия
    annual_bonus = Column(Numeric(15, 2), default=0, nullable=False)  # Годовая премия

    # Расчет страховых взносов (по новым ставкам)
    pension_contribution = Column(Numeric(15, 2), nullable=True)  # ПФР
    medical_contribution = Column(Numeric(15, 2), nullable=True)  # ФОМС
    social_contribution = Column(Numeric(15, 2), nullable=True)  # ФСС
    injury_contribution = Column(Numeric(15, 2), nullable=True)  # НС
    total_insurance = Column(Numeric(15, 2), nullable=True)  # Итого взносы

    # НДФЛ
    income_tax = Column(Numeric(15, 2), nullable=True)

    # Итоговая стоимость сотрудника (оклад + взносы)
    total_employee_cost = Column(Numeric(15, 2), nullable=True)

    # Сравнение с базовым годом
    base_year_salary = Column(Numeric(15, 2), nullable=True)  # Оклад в базовом году
    base_year_insurance = Column(Numeric(15, 2), nullable=True)  # Взносы в базовом году
    cost_increase = Column(Numeric(15, 2), nullable=True)  # Рост стоимости

    # Примечания
    notes = Column(Text, nullable=True)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scenario = relationship("PayrollScenario", back_populates="scenario_details")
    employee = relationship("Employee")
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<PayrollScenarioDetail {self.employee_name}: {self.base_salary}>"


class PayrollYearlyComparison(Base):
    """
    Сравнительный анализ ФОТ между годами с учетом изменений в законодательстве

    Автоматически рассчитываемая таблица для быстрого доступа к аналитике:
    - Изменение ставок страховых взносов
    - Влияние на общий ФОТ
    - Рекомендации по оптимизации
    """
    __tablename__ = "payroll_yearly_comparisons"
    __table_args__ = (
        Index('ix_payroll_comparison_dept_years', 'department_id', 'base_year', 'target_year'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Сравниваемые годы
    base_year = Column(Integer, nullable=False, index=True)  # Базовый год (например, 2025)
    target_year = Column(Integer, nullable=False, index=True)  # Целевой год (например, 2026)

    # Данные базового года
    base_year_headcount = Column(Integer, nullable=True)
    base_year_total_salary = Column(Numeric(15, 2), nullable=True)
    base_year_total_insurance = Column(Numeric(15, 2), nullable=True)
    base_year_total_cost = Column(Numeric(15, 2), nullable=True)

    # Данные целевого года (при текущем штате)
    target_year_headcount = Column(Integer, nullable=True)
    target_year_total_salary = Column(Numeric(15, 2), nullable=True)  # Без изменений
    target_year_total_insurance = Column(Numeric(15, 2), nullable=True)  # С новыми ставками
    target_year_total_cost = Column(Numeric(15, 2), nullable=True)

    # Анализ изменений
    insurance_rate_change = Column(JSON, nullable=True)  # {"PENSION_FUND": {"from": 22, "to": 30}, ...}
    total_cost_increase = Column(Numeric(15, 2), nullable=True)  # Рост в рублях
    total_cost_increase_percent = Column(Numeric(5, 2), nullable=True)  # Рост в %

    # Разбивка по типам взносов
    pension_increase = Column(Numeric(15, 2), nullable=True)
    medical_increase = Column(Numeric(15, 2), nullable=True)
    social_increase = Column(Numeric(15, 2), nullable=True)

    # Рекомендации (автоматически генерируемые)
    recommendations = Column(JSON, nullable=True)  # [{"type": "headcount_reduction", "value": 5, "impact": -500000}]

    # Расчетная дата
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Multi-tenancy
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # System fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department_rel = relationship("Department")

    def __repr__(self):
        return f"<PayrollYearlyComparison {self.base_year} vs {self.target_year}>"


# ============================================================================
# MODULE SYSTEM - Feature enablement and licensing
# ============================================================================


class Module(Base):
    """Modules - каталог доступных модулей системы"""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # AI_FORECAST, CREDIT_PORTFOLIO, etc.
    name = Column(String(255), nullable=False)  # "AI & Forecasting", "Credit Portfolio Management"
    description = Column(Text, nullable=True)  # Подробное описание модуля
    version = Column(String(20), nullable=True)  # "1.0.0"

    # Зависимости от других модулей
    dependencies = Column(JSON, nullable=True)  # ["BUDGET_CORE", "INTEGRATIONS_1C"]

    # Активность
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Метаданные
    icon = Column(String(50), nullable=True)  # Иконка для UI
    sort_order = Column(Integer, nullable=True)  # Порядок отображения

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization_modules = relationship("OrganizationModule", back_populates="module_rel")
    module_events = relationship("ModuleEvent", back_populates="module_rel")

    def __repr__(self):
        return f"<Module {self.code}: {self.name}>"


class OrganizationModule(Base):
    """OrganizationModule - связь организаций с включенными модулями"""
    __tablename__ = "organization_modules"
    __table_args__ = (
        Index('idx_org_module_org_module', 'organization_id', 'module_id', unique=True),
        Index('idx_org_module_active', 'organization_id', 'is_active'),
        Index('idx_org_module_expires', 'expires_at'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Связи
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True)

    # Сроки действия
    enabled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # NULL = без срока истечения

    # Лимиты (JSON для гибкости)
    limits = Column(JSON, nullable=True)  # {"max_users": 10, "max_departments": 3, "max_api_calls_per_day": 1000}

    # Активность
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Кто включил/обновил
    enabled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization_rel = relationship("Organization")
    module_rel = relationship("Module", back_populates="organization_modules")
    enabled_by_rel = relationship("User", foreign_keys=[enabled_by_id])
    updated_by_rel = relationship("User", foreign_keys=[updated_by_id])
    feature_limits = relationship("FeatureLimit", back_populates="organization_module_rel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrganizationModule org={self.organization_id} module={self.module_id}>"


class FeatureLimit(Base):
    """FeatureLimit - детальные лимиты для модулей организации"""
    __tablename__ = "feature_limits"
    __table_args__ = (
        Index('idx_feature_limit_org_module', 'organization_module_id', 'limit_type'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Связь с organization_module
    organization_module_id = Column(Integer, ForeignKey("organization_modules.id"), nullable=False, index=True)

    # Тип лимита
    limit_type = Column(String(50), nullable=False, index=True)  # "users", "departments", "api_calls", "storage_gb"

    # Значения
    limit_value = Column(Integer, nullable=False)  # Максимальное значение
    current_usage = Column(Integer, default=0, nullable=False)  # Текущее использование

    # Предупреждения
    warning_threshold = Column(Integer, nullable=True)  # Порог предупреждения (например, 80% от лимита)
    warning_sent = Column(Boolean, default=False, nullable=False)  # Было ли отправлено предупреждение

    # Метаданные
    notes = Column(Text, nullable=True)  # Примечания

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)  # Когда последний раз проверяли

    # Relationships
    organization_module_rel = relationship("OrganizationModule", back_populates="feature_limits")

    def __repr__(self):
        return f"<FeatureLimit {self.limit_type}: {self.current_usage}/{self.limit_value}>"

    @property
    def usage_percent(self) -> float:
        """Процент использования лимита"""
        if self.limit_value == 0:
            return 0.0
        return (self.current_usage / self.limit_value) * 100

    @property
    def is_exceeded(self) -> bool:
        """Превышен ли лимит"""
        return self.current_usage >= self.limit_value

    @property
    def is_warning_threshold_reached(self) -> bool:
        """Достигнут ли порог предупреждения"""
        if not self.warning_threshold:
            return False
        return self.current_usage >= self.warning_threshold


class ModuleEvent(Base):
    """ModuleEvent - события модулей для аудита и аналитики"""
    __tablename__ = "module_events"
    __table_args__ = (
        Index('idx_module_event_org_module', 'organization_id', 'module_id'),
        Index('idx_module_event_type', 'event_type'),
        Index('idx_module_event_created', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Связи
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True)

    # Тип события
    event_type = Column(Enum(ModuleEventTypeEnum), nullable=False, index=True)

    # Метаданные события
    event_metadata = Column(JSON, nullable=True)  # Дополнительная информация

    # Кто инициировал
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # IP и user agent для аудита
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    organization_rel = relationship("Organization")
    module_rel = relationship("Module", back_populates="module_events")
    created_by_rel = relationship("User")

    def __repr__(self):
        return f"<ModuleEvent {self.event_type} org={self.organization_id} module={self.module_id}>"


# ==================== Admin Settings (Singleton) ====================

class AdminSettings(Base):
    """
    Глобальные настройки администратора (singleton)
    Хранятся в БД и не теряются после перезапуска
    """
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True)  # Всегда = 1 (singleton)

    # Основные настройки
    app_name = Column(String(255), nullable=True)

    # 1C OData
    odata_url = Column(String(500), nullable=True)
    odata_username = Column(String(255), nullable=True)
    odata_password = Column(String(255), nullable=True)
    odata_custom_auth_token = Column(Text, nullable=True)

    # VseGPT (AI для обработки счетов)
    vsegpt_api_key = Column(String(500), nullable=True)
    vsegpt_base_url = Column(String(500), nullable=True)
    vsegpt_model = Column(String(255), nullable=True)

    # Credit Portfolio FTP
    credit_portfolio_ftp_host = Column(String(255), nullable=True)
    credit_portfolio_ftp_user = Column(String(255), nullable=True)
    credit_portfolio_ftp_password = Column(String(255), nullable=True)
    credit_portfolio_ftp_remote_dir = Column(String(500), nullable=True)
    credit_portfolio_ftp_local_dir = Column(String(500), nullable=True)

    # Scheduler настройки
    scheduler_enabled = Column(Boolean, default=True, nullable=False)
    credit_portfolio_import_enabled = Column(Boolean, default=False, nullable=False)
    credit_portfolio_import_hour = Column(Integer, default=2, nullable=False)
    credit_portfolio_import_minute = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    updated_by_rel = relationship("User")

    def __repr__(self):
        return f"<AdminSettings id={self.id}>"


# ==================== TIMESHEET MODELS (HR_DEPARTMENT) ====================

class WorkTimesheet(Base):
    """
    Табель учета рабочего времени (HR_DEPARTMENT module)
    Один табель на сотрудника за месяц
    """
    __tablename__ = "work_timesheets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Сотрудник
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)

    # Период
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)

    # Итоги
    total_days_worked = Column(Integer, default=0, nullable=False)
    total_hours_worked = Column(Numeric(6, 2), default=0, nullable=False)

    # Статус
    status = Column(Enum(TimesheetStatusEnum), default=TimesheetStatusEnum.DRAFT, nullable=False, index=True)

    # Утверждение
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(Date)

    # Примечания
    notes = Column(Text)

    # Кэш для быстрого доступа (JSON)
    daily_summary = Column(JSON)

    # Multi-tenancy (ОБЯЗАТЕЛЬНО)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", back_populates="timesheets")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    daily_records = relationship("DailyWorkRecord", back_populates="timesheet", cascade="all, delete-orphan")
    department_rel = relationship("Department")

    # Constraints
    __table_args__ = (
        UniqueConstraint('employee_id', 'department_id', 'year', 'month', name='uq_timesheet_employee_period'),
        CheckConstraint('year >= 2020 AND year <= 2100', name='ck_timesheet_year'),
        CheckConstraint('month >= 1 AND month <= 12', name='ck_timesheet_month'),
        CheckConstraint('total_days_worked >= 0 AND total_days_worked <= 31', name='ck_timesheet_days'),
        CheckConstraint('total_hours_worked >= 0', name='ck_timesheet_hours'),
        Index('ix_timesheet_employee_period', 'employee_id', 'year', 'month'),
        Index('ix_timesheet_period', 'year', 'month'),
        Index('ix_timesheet_department_period', 'department_id', 'year', 'month'),
    )

    @property
    def can_edit(self) -> bool:
        """Можно ли редактировать табель"""
        return self.status == TimesheetStatusEnum.DRAFT

    @property
    def period_display(self) -> str:
        """Отображение периода на русском"""
        months_ru = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return f"{months_ru[self.month - 1]} {self.year}"

    def __repr__(self):
        return f"<WorkTimesheet employee={self.employee_id} period={self.year}-{self.month:02d} status={self.status}>"


class DailyWorkRecord(Base):
    """
    Подневные записи табеля
    Одна запись на день для каждого табеля
    """
    __tablename__ = "daily_work_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Связь с табелем
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("work_timesheets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Дата
    work_date = Column(Date, nullable=False, index=True)

    # Работа
    is_working_day = Column(Boolean, default=False, nullable=False)
    hours_worked = Column(Numeric(4, 2), default=0, nullable=False)

    # Тип дня (NEW)
    day_type = Column(Enum(DayTypeEnum), default=DayTypeEnum.WORK, nullable=False)

    # Дополнительные часы
    break_hours = Column(Numeric(3, 2), default=0)
    overtime_hours = Column(Numeric(3, 2), default=0)

    # Примечания
    notes = Column(Text)

    # Multi-tenancy (ОБЯЗАТЕЛЬНО)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    timesheet = relationship("WorkTimesheet", back_populates="daily_records")
    department_rel = relationship("Department")

    # Constraints
    __table_args__ = (
        UniqueConstraint('timesheet_id', 'work_date', name='uq_daily_record_timesheet_date'),
        CheckConstraint('hours_worked >= 0 AND hours_worked <= 24', name='ck_daily_hours'),
        CheckConstraint('break_hours >= 0', name='ck_break_hours'),
        CheckConstraint('overtime_hours >= 0', name='ck_overtime_hours'),
        Index('ix_daily_record_timesheet_date', 'timesheet_id', 'work_date'),
        Index('ix_daily_record_date', 'work_date'),
        Index('ix_daily_record_department', 'department_id'),
    )

    @property
    def net_hours_worked(self) -> float:
        """Чистое время работы (без перерывов)"""
        return float(self.hours_worked) - float(self.break_hours or 0)

    def __repr__(self):
        return f"<DailyWorkRecord date={self.work_date} hours={self.hours_worked}>"
