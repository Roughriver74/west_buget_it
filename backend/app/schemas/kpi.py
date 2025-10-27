from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import BonusTypeEnum, KPIGoalStatusEnum


# ============ KPI Goal Schemas ============

class KPIGoalBase(BaseModel):
    """Base schema for KPI goal"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    metric_name: Optional[str] = Field(None, max_length=255)
    metric_unit: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = Field(None, ge=0)
    weight: Decimal = Field(100, ge=0, le=100, description="Вес цели (0-100)")
    year: int = Field(..., ge=2020, le=2100)
    is_annual: bool = True
    status: KPIGoalStatusEnum = KPIGoalStatusEnum.DRAFT
    department_id: int


class KPIGoalCreate(KPIGoalBase):
    """Schema for creating KPI goal"""
    pass


class KPIGoalUpdate(BaseModel):
    """Schema for updating KPI goal"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    metric_name: Optional[str] = Field(None, max_length=255)
    metric_unit: Optional[str] = Field(None, max_length=50)
    target_value: Optional[Decimal] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    year: Optional[int] = Field(None, ge=2020, le=2100)
    is_annual: Optional[bool] = None
    status: Optional[KPIGoalStatusEnum] = None
    department_id: Optional[int] = None


class KPIGoalInDB(KPIGoalBase):
    """Schema for KPI goal in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Employee KPI Schemas ============

class EmployeeKPIBase(BaseModel):
    """Base schema for employee KPI"""
    employee_id: int
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    kpi_percentage: Optional[Decimal] = Field(None, ge=0, le=200, description="КПИ% (0-200)")

    # Bonus types
    monthly_bonus_type: BonusTypeEnum = BonusTypeEnum.PERFORMANCE_BASED
    quarterly_bonus_type: BonusTypeEnum = BonusTypeEnum.PERFORMANCE_BASED
    annual_bonus_type: BonusTypeEnum = BonusTypeEnum.PERFORMANCE_BASED

    # Base bonuses
    monthly_bonus_base: Decimal = Field(0, ge=0)
    quarterly_bonus_base: Decimal = Field(0, ge=0)
    annual_bonus_base: Decimal = Field(0, ge=0)

    # Calculated bonuses (optional - may be auto-calculated)
    monthly_bonus_calculated: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_calculated: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_calculated: Optional[Decimal] = Field(None, ge=0)

    # Fixed part for MIXED bonus type (0-100%)
    monthly_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)
    quarterly_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)
    annual_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)

    department_id: int
    notes: Optional[str] = None


class EmployeeKPICreate(EmployeeKPIBase):
    """Schema for creating employee KPI"""
    pass


class EmployeeKPIUpdate(BaseModel):
    """Schema for updating employee KPI"""
    employee_id: Optional[int] = None
    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    kpi_percentage: Optional[Decimal] = Field(None, ge=0, le=200)

    # Bonus types
    monthly_bonus_type: Optional[BonusTypeEnum] = None
    quarterly_bonus_type: Optional[BonusTypeEnum] = None
    annual_bonus_type: Optional[BonusTypeEnum] = None

    # Base bonuses
    monthly_bonus_base: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_base: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_base: Optional[Decimal] = Field(None, ge=0)

    # Calculated bonuses
    monthly_bonus_calculated: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_calculated: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_calculated: Optional[Decimal] = Field(None, ge=0)

    # Fixed part for MIXED bonus type
    monthly_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)
    quarterly_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)
    annual_bonus_fixed_part: Optional[Decimal] = Field(None, ge=0, le=100)

    department_id: Optional[int] = None
    notes: Optional[str] = None


class EmployeeKPIInDB(EmployeeKPIBase):
    """Schema for employee KPI in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeKPIWithGoals(EmployeeKPIInDB):
    """Employee KPI with related goals"""
    goal_achievements: List['EmployeeKPIGoalInDB'] = []

    class Config:
        from_attributes = True


# ============ Employee KPI Goal Schemas ============

class EmployeeKPIGoalBase(BaseModel):
    """Base schema for employee KPI goal assignment"""
    employee_id: int
    goal_id: int
    employee_kpi_id: Optional[int] = None
    year: int = Field(..., ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12, description="Null для годовых целей")
    target_value: Optional[Decimal] = Field(None, ge=0)
    actual_value: Optional[Decimal] = Field(None, ge=0)
    achievement_percentage: Optional[Decimal] = Field(None, ge=0, le=200, description="% выполнения")
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    status: KPIGoalStatusEnum = KPIGoalStatusEnum.ACTIVE
    notes: Optional[str] = None


class EmployeeKPIGoalCreate(EmployeeKPIGoalBase):
    """Schema for creating employee KPI goal"""
    pass


class EmployeeKPIGoalUpdate(BaseModel):
    """Schema for updating employee KPI goal"""
    employee_id: Optional[int] = None
    goal_id: Optional[int] = None
    employee_kpi_id: Optional[int] = None
    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    target_value: Optional[Decimal] = Field(None, ge=0)
    actual_value: Optional[Decimal] = Field(None, ge=0)
    achievement_percentage: Optional[Decimal] = Field(None, ge=0, le=200)
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[KPIGoalStatusEnum] = None
    notes: Optional[str] = None


class EmployeeKPIGoalInDB(EmployeeKPIGoalBase):
    """Schema for employee KPI goal in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeKPIGoalWithDetails(EmployeeKPIGoalInDB):
    """Employee KPI goal with goal details"""
    goal: Optional[KPIGoalInDB] = None

    class Config:
        from_attributes = True


# ============ KPI Analytics Schemas ============

class KPIEmployeeSummary(BaseModel):
    """Summary of employee KPI performance"""
    employee_id: int
    employee_name: str
    position: str
    year: int
    month: Optional[int] = None
    kpi_percentage: Optional[Decimal]
    total_bonus_calculated: Decimal
    monthly_bonus_calculated: Decimal
    quarterly_bonus_calculated: Decimal
    annual_bonus_calculated: Decimal
    goals_count: int
    goals_achieved: int


class KPIDepartmentSummary(BaseModel):
    """Summary of department KPI performance"""
    department_id: int
    department_name: str
    year: int
    month: Optional[int] = None
    avg_kpi_percentage: Decimal
    total_employees: int
    total_bonus_calculated: Decimal
    goals_count: int
    goals_achieved: int


class KPIGoalProgress(BaseModel):
    """Progress tracking for a specific goal"""
    goal_id: int
    goal_name: str
    category: Optional[str]
    target_value: Optional[Decimal]
    metric_unit: Optional[str]
    employees_assigned: int
    employees_achieved: int
    avg_achievement_percentage: Decimal
    total_weight: Decimal
