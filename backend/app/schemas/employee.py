from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.db.models import EmployeeStatusEnum, PositionLevelEnum


class EmployeeBase(BaseModel):
    """Base schema for employee"""
    full_name: str = Field(..., max_length=500)
    position: str = Field(..., max_length=255)
    position_level: Optional[PositionLevelEnum] = None
    base_salary: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal('30.0'), ge=0, le=100)
    hire_date: date
    organization_id: Optional[int] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Schema for creating employee"""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating employee"""
    full_name: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=255)
    position_level: Optional[PositionLevelEnum] = None
    base_salary: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    status: Optional[EmployeeStatusEnum] = None
    organization_id: Optional[int] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class EmployeeInDB(EmployeeBase):
    """Schema for employee from database"""
    id: int
    status: EmployeeStatusEnum
    termination_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeList(BaseModel):
    """Schema for employee list with pagination"""
    total: int
    items: list[EmployeeInDB]
    page: int
    page_size: int
    pages: int


# Payroll schemas

class PayrollBase(BaseModel):
    """Base schema for payroll"""
    employee_id: int
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    base_salary: Decimal = Field(..., ge=0)
    bonus: Decimal = Field(default=Decimal('0'), ge=0)
    other_payments: Decimal = Field(default=Decimal('0'), ge=0)
    worked_days: Optional[int] = Field(None, ge=0, le=31)
    notes: Optional[str] = None


class PayrollCreate(PayrollBase):
    """Schema for creating payroll (автоматический расчет налогов)"""
    pass


class PayrollUpdate(BaseModel):
    """Schema for updating payroll"""
    base_salary: Optional[Decimal] = Field(None, ge=0)
    bonus: Optional[Decimal] = Field(None, ge=0)
    other_payments: Optional[Decimal] = Field(None, ge=0)
    worked_days: Optional[int] = Field(None, ge=0, le=31)
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class PayrollInDB(PayrollBase):
    """Schema for payroll from database"""
    id: int
    gross_salary: Decimal  # Начислено (до налогов)
    taxes: Decimal  # Налоги с сотрудника
    net_salary: Decimal  # К выплате
    employer_taxes: Decimal  # Налоги работодателя
    total_cost: Decimal  # Полная стоимость
    payment_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollList(BaseModel):
    """Schema for payroll list"""
    total: int
    items: list[PayrollInDB]
    page: int
    page_size: int
    pages: int


class PayrollSummary(BaseModel):
    """Summary statistics for payroll"""
    year: int
    month: Optional[int] = None
    total_employees: int
    total_base_salary: Decimal
    total_bonuses: Decimal
    total_gross_salary: Decimal
    total_taxes: Decimal
    total_net_salary: Decimal
    total_employer_taxes: Decimal
    total_cost: Decimal  # Полная стоимость ФОТ для компании
    average_salary: Decimal


class EmployeeWithPayrolls(EmployeeInDB):
    """Employee with payroll history"""
    recent_payrolls: list[PayrollInDB] = []
    total_earned_ytd: Decimal = Decimal('0')  # Year-to-date


class FOTBudgetComparison(BaseModel):
    """Сравнение ФОТ с бюджетом"""
    year: int
    month: int
    planned_fot: Decimal  # Плановый ФОТ из бюджета
    actual_fot: Decimal  # Фактический ФОТ
    difference: Decimal  # Разница
    execution_percent: float  # Процент исполнения
