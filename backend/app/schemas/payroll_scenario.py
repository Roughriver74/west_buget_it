"""
Pydantic schemas for insurance rates and payroll scenarios

Модели для учета изменений в страховых взносах и сценарного планирования ФОТ
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.db.models import TaxTypeEnum, PayrollScenarioTypeEnum


# ==================== Insurance Rate Schemas ====================

class InsuranceRateBase(BaseModel):
    """Base schema for insurance rate"""
    year: int = Field(..., ge=2020, le=2030, description="Год действия ставки")
    rate_type: TaxTypeEnum = Field(..., description="Тип страхового взноса")
    rate_percentage: Decimal = Field(..., ge=0, le=100, description="Ставка в процентах")
    threshold_amount: Optional[Decimal] = Field(None, ge=0, description="Порог для прогрессивной шкалы")
    rate_above_threshold: Optional[Decimal] = Field(None, ge=0, le=100, description="Ставка выше порога")
    description: Optional[str] = Field(None, description="Описание изменений")
    legal_basis: Optional[str] = Field(None, max_length=255, description="Ссылка на ФЗ/приказ")
    total_employer_burden: Optional[Decimal] = Field(None, ge=0, le=100, description="Общая нагрузка работодателя")


class InsuranceRateCreate(InsuranceRateBase):
    """Schema for creating insurance rate

    department_id is auto-assigned from user's department for USER role
    """
    department_id: Optional[int] = Field(None, description="Department ID (optional for ADMIN/MANAGER)")


class InsuranceRateUpdate(BaseModel):
    """Schema for updating insurance rate"""
    rate_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    threshold_amount: Optional[Decimal] = Field(None, ge=0)
    rate_above_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    legal_basis: Optional[str] = Field(None, max_length=255)
    total_employer_burden: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class InsuranceRateInDB(InsuranceRateBase):
    """Schema for insurance rate in database"""
    id: int
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]

    class Config:
        from_attributes = True


# ==================== Payroll Scenario Schemas ====================

class PayrollScenarioBase(BaseModel):
    """Base schema for payroll scenario"""
    name: str = Field(..., min_length=1, max_length=255, description="Название сценария")
    description: Optional[str] = Field(None, description="Описание сценария")
    scenario_type: PayrollScenarioTypeEnum = Field(..., description="Тип сценария")
    target_year: int = Field(..., ge=2024, le=2030, description="Год планирования")
    base_year: int = Field(..., ge=2020, le=2030, description="Базовый год для сравнения")
    headcount_change_percent: Decimal = Field(0, ge=-100, le=100, description="Изменение штата в %")
    salary_change_percent: Decimal = Field(0, ge=-100, le=100, description="Изменение з/п в %")


class PayrollScenarioCreate(PayrollScenarioBase):
    """Schema for creating payroll scenario"""
    department_id: Optional[int] = Field(None, description="Department ID (optional for ADMIN/MANAGER)")


class PayrollScenarioUpdate(BaseModel):
    """Schema for updating payroll scenario"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scenario_type: Optional[PayrollScenarioTypeEnum] = None
    headcount_change_percent: Optional[Decimal] = Field(None, ge=-100, le=100)
    salary_change_percent: Optional[Decimal] = Field(None, ge=-100, le=100)
    is_active: Optional[bool] = None


class PayrollScenarioInDB(PayrollScenarioBase):
    """Schema for payroll scenario in database"""
    id: int
    department_id: int
    total_headcount: Optional[int]
    total_base_salary: Optional[Decimal]
    total_insurance_cost: Optional[Decimal]
    total_payroll_cost: Optional[Decimal]
    base_year_total_cost: Optional[Decimal]
    cost_difference: Optional[Decimal]
    cost_difference_percent: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]

    class Config:
        from_attributes = True


# ==================== Payroll Scenario Detail Schemas ====================

class PayrollScenarioDetailBase(BaseModel):
    """Base schema for payroll scenario detail"""
    employee_name: str = Field(..., min_length=1, max_length=255, description="ФИО сотрудника")
    position: Optional[str] = Field(None, max_length=255, description="Должность")
    is_new_hire: bool = Field(False, description="Новый сотрудник")
    is_terminated: bool = Field(False, description="Увольнение")
    termination_month: Optional[int] = Field(None, ge=1, le=12, description="Месяц увольнения")
    base_salary: Decimal = Field(..., ge=0, description="Плановый оклад")
    monthly_bonus: Decimal = Field(0, ge=0, description="Месячная премия")
    notes: Optional[str] = None


class PayrollScenarioDetailCreate(PayrollScenarioDetailBase):
    """Schema for creating payroll scenario detail"""
    scenario_id: int = Field(..., description="ID сценария")
    employee_id: Optional[int] = Field(None, description="ID сотрудника (NULL для новых)")
    department_id: Optional[int] = Field(None, description="Department ID (optional)")


class PayrollScenarioDetailUpdate(BaseModel):
    """Schema for updating payroll scenario detail"""
    employee_name: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    is_new_hire: Optional[bool] = None
    is_terminated: Optional[bool] = None
    termination_month: Optional[int] = Field(None, ge=1, le=12)
    base_salary: Optional[Decimal] = Field(None, ge=0)
    monthly_bonus: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class PayrollScenarioDetailInDB(PayrollScenarioDetailBase):
    """Schema for payroll scenario detail in database"""
    id: int
    scenario_id: int
    employee_id: Optional[int]
    department_id: int
    pension_contribution: Optional[Decimal]
    medical_contribution: Optional[Decimal]
    social_contribution: Optional[Decimal]
    injury_contribution: Optional[Decimal]
    total_insurance: Optional[Decimal]
    income_tax: Optional[Decimal]
    total_employee_cost: Optional[Decimal]
    base_year_salary: Optional[Decimal]
    base_year_insurance: Optional[Decimal]
    cost_increase: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PayrollScenarioWithDetails(PayrollScenarioInDB):
    """Payroll scenario with employee details"""
    scenario_details: List[PayrollScenarioDetailInDB] = []

    class Config:
        from_attributes = True


# ==================== Payroll Yearly Comparison Schemas ====================

class PayrollYearlyComparisonBase(BaseModel):
    """Base schema for payroll yearly comparison"""
    base_year: int = Field(..., ge=2020, le=2030, description="Базовый год")
    target_year: int = Field(..., ge=2020, le=2030, description="Целевой год")


class PayrollYearlyComparisonInDB(PayrollYearlyComparisonBase):
    """Schema for payroll yearly comparison in database"""
    id: int
    department_id: int
    base_year_headcount: Optional[int]
    base_year_total_salary: Optional[Decimal]
    base_year_total_insurance: Optional[Decimal]
    base_year_total_cost: Optional[Decimal]
    target_year_headcount: Optional[int]
    target_year_total_salary: Optional[Decimal]
    target_year_total_insurance: Optional[Decimal]
    target_year_total_cost: Optional[Decimal]
    insurance_rate_change: Optional[Dict[str, Any]]
    total_cost_increase: Optional[Decimal]
    total_cost_increase_percent: Optional[Decimal]
    pension_increase: Optional[Decimal]
    medical_increase: Optional[Decimal]
    social_increase: Optional[Decimal]
    recommendations: Optional[List[Dict[str, Any]]]
    calculated_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Request/Response Schemas ====================

class YearComparisonRequest(BaseModel):
    """Request schema for generating year comparison"""
    base_year: int = Field(..., ge=2020, le=2030)
    target_year: int = Field(..., ge=2020, le=2030)
    department_id: Optional[int] = None


class ScenarioCalculationRequest(BaseModel):
    """Request schema for calculating scenario"""
    scenario_id: int


class ScenarioCalculationResponse(BaseModel):
    """Response schema for scenario calculation"""
    scenario_id: int
    total_headcount: int
    total_base_salary: Decimal
    total_insurance_cost: Decimal
    total_payroll_cost: Decimal
    cost_difference: Decimal
    cost_difference_percent: Decimal
    breakdown_by_employee: List[PayrollScenarioDetailInDB]


class InsuranceImpactAnalysis(BaseModel):
    """Analysis of insurance rate changes impact"""
    base_year: int
    target_year: int
    rate_changes: Dict[str, Dict[str, Decimal]]  # {"PENSION_FUND": {"from": 22, "to": 30}}
    total_impact: Decimal  # Total cost increase in rubles
    impact_percent: Decimal  # Impact as percentage
    recommendations: List[Dict[str, Any]]  # Recommendations for optimization
