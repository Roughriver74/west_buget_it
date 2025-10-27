from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import EmployeeStatusEnum


# ============ Employee Schemas ============

class EmployeeBase(BaseModel):
    """Base schema for employee"""
    full_name: str = Field(..., min_length=1, max_length=255)
    position: str = Field(..., min_length=1, max_length=255)
    employee_number: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    fire_date: Optional[date] = None
    status: EmployeeStatusEnum = EmployeeStatusEnum.ACTIVE
    base_salary: Decimal = Field(..., ge=0)
    # Bonus base rates (базовые ставки премий)
    monthly_bonus_base: Decimal = Field(0, ge=0, description="Базовая месячная премия")
    quarterly_bonus_base: Decimal = Field(0, ge=0, description="Базовая квартальная премия")
    annual_bonus_base: Decimal = Field(0, ge=0, description="Базовая годовая премия")
    department_id: int
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Schema for creating employee"""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating employee"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, min_length=1, max_length=255)
    employee_number: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    fire_date: Optional[date] = None
    status: Optional[EmployeeStatusEnum] = None
    base_salary: Optional[Decimal] = Field(None, ge=0)
    # Bonus base rates (optional for update)
    monthly_bonus_base: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_base: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_base: Optional[Decimal] = Field(None, ge=0)
    department_id: Optional[int] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class EmployeeInDB(EmployeeBase):
    """Schema for employee in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeWithSalaryHistory(EmployeeInDB):
    """Employee with salary history"""
    salary_history: List['SalaryHistoryInDB'] = []

    class Config:
        from_attributes = True


# ============ Salary History Schemas ============

class SalaryHistoryBase(BaseModel):
    """Base schema for salary history"""
    employee_id: int
    old_salary: Optional[Decimal] = Field(None, ge=0)
    new_salary: Decimal = Field(..., ge=0)
    effective_date: date
    reason: Optional[str] = None
    notes: Optional[str] = None


class SalaryHistoryCreate(SalaryHistoryBase):
    """Schema for creating salary history"""
    pass


class SalaryHistoryInDB(SalaryHistoryBase):
    """Schema for salary history in database"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Payroll Plan Schemas ============

class PayrollPlanBase(BaseModel):
    """Base schema for payroll plan"""
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    employee_id: int
    department_id: int
    base_salary: Decimal = Field(..., ge=0)
    # Bonuses by type (премии по типам)
    monthly_bonus: Decimal = Field(0, ge=0, description="Месячная премия")
    quarterly_bonus: Decimal = Field(0, ge=0, description="Квартальная премия")
    annual_bonus: Decimal = Field(0, ge=0, description="Годовая премия")
    other_payments: Decimal = Field(0, ge=0)
    total_planned: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class PayrollPlanCreate(BaseModel):
    """Schema for creating payroll plan"""
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    employee_id: int
    base_salary: Decimal = Field(..., ge=0)
    # Bonuses by type
    monthly_bonus: Decimal = Field(0, ge=0)
    quarterly_bonus: Decimal = Field(0, ge=0)
    annual_bonus: Decimal = Field(0, ge=0)
    other_payments: Decimal = Field(0, ge=0)
    notes: Optional[str] = None


class PayrollPlanUpdate(BaseModel):
    """Schema for updating payroll plan"""
    base_salary: Optional[Decimal] = Field(None, ge=0)
    # Bonuses by type (optional for update)
    monthly_bonus: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus: Optional[Decimal] = Field(None, ge=0)
    annual_bonus: Optional[Decimal] = Field(None, ge=0)
    other_payments: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class PayrollPlanInDB(PayrollPlanBase):
    """Schema for payroll plan in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollPlanWithEmployee(PayrollPlanInDB):
    """Payroll plan with employee details"""
    employee: EmployeeInDB

    class Config:
        from_attributes = True


# ============ Payroll Actual Schemas ============

class PayrollActualBase(BaseModel):
    """Base schema for payroll actual"""
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    employee_id: int
    department_id: int
    base_salary_paid: Decimal = Field(..., ge=0)
    # Actual bonuses by type (фактические премии по типам)
    monthly_bonus_paid: Decimal = Field(0, ge=0, description="Месячная премия (факт)")
    quarterly_bonus_paid: Decimal = Field(0, ge=0, description="Квартальная премия (факт)")
    annual_bonus_paid: Decimal = Field(0, ge=0, description="Годовая премия (факт)")
    other_payments_paid: Decimal = Field(0, ge=0)
    total_paid: Decimal = Field(..., ge=0)
    payment_date: Optional[date] = None
    expense_id: Optional[int] = None
    notes: Optional[str] = None


class PayrollActualCreate(BaseModel):
    """Schema for creating payroll actual"""
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    employee_id: int
    base_salary_paid: Decimal = Field(..., ge=0)
    # Actual bonuses by type
    monthly_bonus_paid: Decimal = Field(0, ge=0)
    quarterly_bonus_paid: Decimal = Field(0, ge=0)
    annual_bonus_paid: Decimal = Field(0, ge=0)
    other_payments_paid: Decimal = Field(0, ge=0)
    payment_date: Optional[date] = None
    expense_id: Optional[int] = None
    notes: Optional[str] = None


class PayrollActualUpdate(BaseModel):
    """Schema for updating payroll actual"""
    base_salary_paid: Optional[Decimal] = Field(None, ge=0)
    # Actual bonuses by type (optional for update)
    monthly_bonus_paid: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_paid: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_paid: Optional[Decimal] = Field(None, ge=0)
    other_payments_paid: Optional[Decimal] = Field(None, ge=0)
    payment_date: Optional[date] = None
    expense_id: Optional[int] = None
    notes: Optional[str] = None


class PayrollActualInDB(PayrollActualBase):
    """Schema for payroll actual in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollActualWithEmployee(PayrollActualInDB):
    """Payroll actual with employee details"""
    employee: EmployeeInDB

    class Config:
        from_attributes = True


# ============ Analytics Schemas ============

class PayrollSummary(BaseModel):
    """Payroll summary for analytics"""
    year: int
    month: int
    total_employees: int
    total_planned: Decimal
    total_paid: Decimal
    variance: Decimal
    variance_percent: float


class EmployeePayrollStats(BaseModel):
    """Employee payroll statistics"""
    employee_id: int
    employee_name: str
    position: str
    department_id: int
    total_planned: Decimal
    total_paid: Decimal
    months_worked: int
    average_monthly_pay: Decimal


class DepartmentPayrollStats(BaseModel):
    """Department payroll statistics"""
    department_id: int
    department_name: str
    total_employees: int
    total_planned: Decimal
    total_paid: Decimal
    variance: Decimal
    average_salary: Decimal


class SalaryStatistics(BaseModel):
    """Salary distribution statistics"""
    total_employees: int
    active_employees: int
    min_salary: Decimal
    max_salary: Decimal
    average_salary: Decimal
    median_salary: Decimal
    percentile_25: Decimal
    percentile_75: Decimal
    percentile_90: Decimal
    total_payroll: Decimal


class PayrollStructureMonth(BaseModel):
    """Payroll structure breakdown for a single month"""
    year: int
    month: int
    total_base_salary: Decimal
    # Bonuses by type (разбивка премий по типам)
    total_monthly_bonus: Decimal = Field(default=0, description="Месячные премии")
    total_quarterly_bonus: Decimal = Field(default=0, description="Квартальные премии")
    total_annual_bonus: Decimal = Field(default=0, description="Годовые премии")
    total_bonus: Decimal = Field(default=0, description="Всего премий (сумма всех типов)")
    total_other_payments: Decimal
    total_amount: Decimal
    employee_count: int


class PayrollDynamics(BaseModel):
    """Payroll dynamics over time"""
    year: int
    month: int
    planned_base_salary: Decimal
    # Planned bonuses by type
    planned_monthly_bonus: Decimal = 0
    planned_quarterly_bonus: Decimal = 0
    planned_annual_bonus: Decimal = 0
    planned_bonus: Decimal  # Total planned bonuses
    planned_other: Decimal
    planned_total: Decimal
    actual_base_salary: Decimal
    # Actual bonuses by type
    actual_monthly_bonus: Decimal = 0
    actual_quarterly_bonus: Decimal = 0
    actual_annual_bonus: Decimal = 0
    actual_bonus: Decimal  # Total actual bonuses
    actual_other: Decimal
    actual_total: Decimal
    employee_count: int


class PayrollForecast(BaseModel):
    """Payroll forecast for future months"""
    year: int
    month: int
    forecasted_total: Decimal
    forecasted_base_salary: Decimal
    # Forecasted bonuses by type
    forecasted_monthly_bonus: Decimal = 0
    forecasted_quarterly_bonus: Decimal = 0
    forecasted_annual_bonus: Decimal = 0
    forecasted_bonus: Decimal  # Total forecasted bonuses
    forecasted_other: Decimal
    employee_count: int
    confidence: str  # "high", "medium", "low"
    based_on_months: int  # How many historical months used for forecast
