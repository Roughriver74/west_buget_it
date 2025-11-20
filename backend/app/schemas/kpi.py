from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import BonusTypeEnum, KPIGoalStatusEnum, EmployeeKPIStatusEnum


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

    # Depremium threshold
    depremium_threshold: Optional[Decimal] = Field(None, ge=0, le=100, description="Порог депремирования (%)")
    depremium_applied: bool = False

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

    # Task complexity bonus component (NEW in Task 3.2)
    task_complexity_avg: Optional[Decimal] = Field(None, ge=1, le=10, description="Средняя сложность задач (1-10)")
    task_complexity_multiplier: Optional[Decimal] = Field(None, ge=0.5, le=2.0, description="Множитель премии по сложности")
    task_complexity_weight: Optional[Decimal] = Field(None, ge=0, le=100, description="Вес компонента сложности в премии (%)")

    # Complexity bonus components
    monthly_bonus_complexity: Optional[Decimal] = Field(None, ge=0, description="Компонент месячной премии по сложности")
    quarterly_bonus_complexity: Optional[Decimal] = Field(None, ge=0, description="Компонент квартальной премии по сложности")
    annual_bonus_complexity: Optional[Decimal] = Field(None, ge=0, description="Компонент годовой премии по сложности")

    # Workflow status
    status: EmployeeKPIStatusEnum = EmployeeKPIStatusEnum.DRAFT

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

    # Depremium threshold
    depremium_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    depremium_applied: Optional[bool] = None

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

    # Task complexity bonus component (NEW in Task 3.2)
    task_complexity_avg: Optional[Decimal] = Field(None, ge=1, le=10)
    task_complexity_multiplier: Optional[Decimal] = Field(None, ge=0.5, le=2.0)
    task_complexity_weight: Optional[Decimal] = Field(None, ge=0, le=100)

    # Complexity bonus components
    monthly_bonus_complexity: Optional[Decimal] = Field(None, ge=0)
    quarterly_bonus_complexity: Optional[Decimal] = Field(None, ge=0)
    annual_bonus_complexity: Optional[Decimal] = Field(None, ge=0)

    # Workflow status
    status: Optional[EmployeeKPIStatusEnum] = None

    department_id: Optional[int] = None
    notes: Optional[str] = None


class EmployeeKPIInDB(EmployeeKPIBase):
    """Schema for employee KPI in database"""
    id: int
    created_at: datetime
    updated_at: datetime

    # Approval tracking
    submitted_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

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


# ============ KPI Goal Template Schemas ============

class KPIGoalTemplateItemBase(BaseModel):
    """Base schema for KPI goal template item"""
    goal_id: int
    weight: Decimal = Field(..., ge=0, le=100, description="Вес цели в шаблоне (0-100)")
    default_target_value: Optional[Decimal] = Field(None, ge=0)
    display_order: int = Field(0, ge=0)


class KPIGoalTemplateItemCreate(KPIGoalTemplateItemBase):
    """Schema for creating KPI goal template item"""
    pass


class KPIGoalTemplateItemUpdate(BaseModel):
    """Schema for updating KPI goal template item"""
    goal_id: Optional[int] = None
    weight: Optional[Decimal] = Field(None, ge=0, le=100)
    default_target_value: Optional[Decimal] = Field(None, ge=0)
    display_order: Optional[int] = Field(None, ge=0)


class KPIGoalTemplateItemInDB(KPIGoalTemplateItemBase):
    """Schema for KPI goal template item in database"""
    id: int
    template_id: int

    class Config:
        from_attributes = True


class KPIGoalTemplateItemWithGoal(KPIGoalTemplateItemInDB):
    """Schema for KPI goal template item with goal details"""
    goal: KPIGoalInDB

    class Config:
        from_attributes = True


class KPIGoalTemplateBase(BaseModel):
    """Base schema for KPI goal template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: int
    is_active: bool = True


class KPIGoalTemplateCreate(KPIGoalTemplateBase):
    """Schema for creating KPI goal template with items"""
    template_goals: List[KPIGoalTemplateItemCreate] = Field(..., min_items=1)


class KPIGoalTemplateUpdate(BaseModel):
    """Schema for updating KPI goal template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    template_goals: Optional[List[KPIGoalTemplateItemCreate]] = None


class KPIGoalTemplateInDB(KPIGoalTemplateBase):
    """Schema for KPI goal template in database"""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


class KPIGoalTemplateWithGoals(KPIGoalTemplateInDB):
    """Schema for KPI goal template with all goals"""
    template_goals: List[KPIGoalTemplateItemWithGoal]

    class Config:
        from_attributes = True


class ApplyTemplateRequest(BaseModel):
    """Schema for applying template to employees"""
    employee_ids: List[int] = Field(..., min_items=1)
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)


class ApplyTemplateResponse(BaseModel):
    """Schema for template application response"""
    success: bool
    message: str
    employees_updated: int
    goals_created: int
    errors: List[str] = []


# ============ Bulk Operations Schemas ============

class BulkAssignGoalsRequest(BaseModel):
    """Request для массового назначения целей сотрудникам"""
    employee_ids: List[int] = Field(..., min_items=1, description="Список ID сотрудников")
    goal_id: int = Field(..., description="ID цели для назначения")
    year: int = Field(..., ge=2020, le=2100, description="Год")
    month: int = Field(..., ge=1, le=12, description="Месяц")
    weight: Decimal = Field(..., ge=0, le=100, description="Вес цели (0-100%)")
    target_value: Optional[Decimal] = Field(None, ge=0, description="Целевое значение")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [1, 2, 3],
                "goal_id": 5,
                "year": 2025,
                "month": 11,
                "weight": 30.0,
                "target_value": 100.0
            }
        }


class BulkAssignGoalsResponse(BaseModel):
    """Response для массового назначения целей"""
    success: bool
    message: str
    total_employees: int
    assigned_count: int
    skipped_count: int
    error_count: int
    details: List[Dict[str, Any]] = []
    errors: List[str] = []
