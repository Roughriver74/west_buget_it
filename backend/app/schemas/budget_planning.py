"""
Pydantic schemas for Budget Planning 2026 Module
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.db.models import (
    BudgetVersionStatusEnum,
    BudgetScenarioTypeEnum,
    CalculationMethodEnum,
    ApprovalActionEnum,
    ExpenseTypeEnum,
)


# ============================================================================
# Budget Scenario Schemas
# ============================================================================


class BudgetScenarioBase(BaseModel):
    """Base schema for budget scenario"""
    year: int = Field(..., description="Planning year (e.g., 2026)")
    scenario_name: str = Field(..., max_length=100, description="Scenario name")
    scenario_type: BudgetScenarioTypeEnum
    global_growth_rate: Decimal = Field(default=Decimal("0"), description="Global growth rate %")
    inflation_rate: Decimal = Field(default=Decimal("0"), description="Inflation rate %")
    fx_rate: Optional[Decimal] = Field(None, description="FX rate for imports")
    assumptions: Optional[Dict[str, Any]] = Field(None, description="Business assumptions (JSON)")
    description: Optional[str] = None
    is_active: bool = True


class BudgetScenarioCreate(BudgetScenarioBase):
    """Schema for creating budget scenario - department_id auto-assigned from current_user"""
    pass


class BudgetScenarioUpdate(BaseModel):
    """Schema for updating budget scenario"""
    scenario_name: Optional[str] = Field(None, max_length=100)
    global_growth_rate: Optional[Decimal] = None
    inflation_rate: Optional[Decimal] = None
    fx_rate: Optional[Decimal] = None
    assumptions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BudgetScenarioInDB(BudgetScenarioBase):
    """Schema for budget scenario from database"""
    id: int
    department_id: int
    created_at: datetime
    created_by: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Budget Version Schemas
# ============================================================================


class BudgetVersionBase(BaseModel):
    """Base schema for budget version"""
    year: int = Field(..., description="Planning year (e.g., 2026)")
    version_name: Optional[str] = Field(None, max_length=100, description="Version name")
    scenario_id: Optional[int] = None
    status: BudgetVersionStatusEnum = BudgetVersionStatusEnum.DRAFT
    is_baseline: bool = Field(default=False, description="Is this the baseline version for the year")
    comments: Optional[str] = None
    change_log: Optional[str] = None


class BudgetVersionCreate(BudgetVersionBase):
    """Schema for creating budget version - department_id auto-assigned from current_user, version_number auto-incremented"""
    copy_from_version_id: Optional[int] = Field(None, description="Copy from existing version")
    auto_calculate: bool = Field(False, description="Auto-calculate from previous year")


class BudgetVersionUpdate(BaseModel):
    """Schema for updating budget version"""
    version_name: Optional[str] = Field(None, max_length=100)
    scenario_id: Optional[int] = None
    status: Optional[BudgetVersionStatusEnum] = None
    is_baseline: Optional[bool] = None
    comments: Optional[str] = None
    change_log: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class BudgetVersionInDB(BudgetVersionBase):
    """Schema for budget version from database"""
    id: int
    version_number: int
    department_id: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    total_amount: Decimal
    total_capex: Decimal
    total_opex: Decimal

    model_config = ConfigDict(from_attributes=True)


class BudgetVersionWithDetails(BudgetVersionInDB):
    """Schema for budget version with plan details"""
    plan_details: List["BudgetPlanDetailInDB"] = []
    scenario: Optional[BudgetScenarioInDB] = None
    approval_logs: List["BudgetApprovalLogInDB"] = []


# ============================================================================
# Budget Plan Detail Schemas
# ============================================================================


class BudgetPlanDetailBase(BaseModel):
    """Base schema for budget plan detail"""
    version_id: int
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    category_id: int
    subcategory: Optional[str] = Field(None, max_length=100)
    planned_amount: Decimal = Field(..., description="Planned amount")
    type: ExpenseTypeEnum
    calculation_method: Optional[CalculationMethodEnum] = None
    calculation_params: Optional[Dict[str, Any]] = None
    business_driver: Optional[str] = Field(None, max_length=100)
    justification: Optional[str] = None
    based_on_year: Optional[int] = None
    based_on_avg: Optional[Decimal] = None
    based_on_total: Optional[Decimal] = None
    growth_rate: Optional[Decimal] = None


class BudgetPlanDetailCreate(BudgetPlanDetailBase):
    """Schema for creating budget plan detail"""
    pass


class BudgetPlanDetailUpdate(BaseModel):
    """Schema for updating budget plan detail"""
    month: Optional[int] = Field(None, ge=1, le=12)
    category_id: Optional[int] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    planned_amount: Optional[Decimal] = None
    type: Optional[ExpenseTypeEnum] = None
    calculation_method: Optional[CalculationMethodEnum] = None
    calculation_params: Optional[Dict[str, Any]] = None
    business_driver: Optional[str] = Field(None, max_length=100)
    justification: Optional[str] = None
    based_on_year: Optional[int] = None
    based_on_avg: Optional[Decimal] = None
    based_on_total: Optional[Decimal] = None
    growth_rate: Optional[Decimal] = None


class BudgetPlanDetailInDB(BudgetPlanDetailBase):
    """Schema for budget plan detail from database"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Budget Approval Log Schemas
# ============================================================================


class BudgetApprovalLogBase(BaseModel):
    """Base schema for budget approval log"""
    version_id: int
    iteration_number: int = Field(..., ge=1, description="Approval round (1, 2, 3...)")
    reviewer_name: str = Field(..., max_length=100)
    reviewer_role: str = Field(..., max_length=50, description="CFO, CEO, Head of IT")
    action: ApprovalActionEnum
    decision_date: datetime
    comments: Optional[str] = None
    requested_changes: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = Field(None, max_length=100)
    deadline: Optional[date] = None


class BudgetApprovalLogCreate(BudgetApprovalLogBase):
    """Schema for creating budget approval log"""
    pass


class BudgetApprovalLogInDB(BudgetApprovalLogBase):
    """Schema for budget approval log from database"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Calculator Request/Response Schemas
# ============================================================================


class CalculateByAverageRequest(BaseModel):
    """Request schema for calculate by average method - department_id auto-assigned from current_user"""
    category_id: int
    base_year: int = Field(..., description="Base year for calculation (e.g., 2025)")
    adjustment_percent: Decimal = Field(default=Decimal("0"), description="Adjustment % (inflation, growth)")
    target_year: int = Field(..., description="Target year (e.g., 2026)")


class CalculateByGrowthRequest(BaseModel):
    """Request schema for calculate by growth method - department_id auto-assigned from current_user"""
    category_id: int
    base_year: int
    growth_rate: Decimal = Field(..., description="Growth rate %")
    inflation_rate: Decimal = Field(default=Decimal("0"), description="Inflation rate %")
    target_year: int


class CalculateByDriverRequest(BaseModel):
    """Request schema for calculate by driver method - department_id auto-assigned from current_user"""
    category_id: int
    base_year: int
    driver_type: str = Field(..., description="Driver type: headcount, projects, revenue, etc")
    base_driver_value: Decimal = Field(..., description="Driver value in base year")
    planned_driver_value: Decimal = Field(..., description="Planned driver value for target year")
    cost_per_unit: Optional[Decimal] = Field(None, description="Cost per driver unit (optional, will calculate if not provided)")
    adjustment_percent: Decimal = Field(default=Decimal("0"), description="Additional adjustment %")
    target_year: int


class CalculationResult(BaseModel):
    """Response schema for calculation results"""
    category_id: int
    annual_total: Decimal
    monthly_avg: Decimal
    growth_percent: Decimal
    monthly_breakdown: List[Dict[str, Any]] = Field(
        ...,
        description="Monthly breakdown: [{'month': 1, 'amount': 560000}, ...]"
    )
    calculation_method: CalculationMethodEnum
    calculation_params: Dict[str, Any]
    based_on_total: Decimal
    based_on_avg: Decimal


class BaselineSummary(BaseModel):
    """Summary of baseline year (e.g., 2025) expenses"""
    category_id: int
    category_name: str
    total_amount: Decimal
    monthly_avg: Decimal
    monthly_breakdown: List[Dict[str, Any]]
    capex_total: Decimal
    opex_total: Decimal


class VersionComparisonResult(BaseModel):
    """Result of comparing two versions"""
    category: str
    v1_amount: Decimal
    v2_amount: Decimal
    difference: Decimal
    difference_percent: Decimal


class VersionComparison(BaseModel):
    """Full version comparison"""
    version1: BudgetVersionInDB
    version2: BudgetVersionInDB
    category_comparisons: List[VersionComparisonResult]
    total_v1: Decimal
    total_v2: Decimal
    total_difference: Decimal
    total_difference_percent: Decimal


# ============================================================================
# Plan vs Actual Schemas
# ============================================================================


class CategoryPlanVsActual(BaseModel):
    """Plan vs Actual for a single category"""
    category_id: int
    category_name: str
    category_type: ExpenseTypeEnum
    planned_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal  # actual - planned
    variance_percent: Decimal  # (variance / planned) * 100
    execution_percent: Decimal  # (actual / planned) * 100
    is_over_budget: bool


class MonthlyPlanVsActual(BaseModel):
    """Plan vs Actual for a specific month"""
    month: int  # 1-12
    month_name: str  # "Январь", "Февраль", etc.
    planned_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    execution_percent: Decimal
    is_over_budget: bool
    categories: List[CategoryPlanVsActual]


class PlanVsActualSummary(BaseModel):
    """Overall summary of plan vs actual for a year"""
    year: int
    department_id: int
    department_name: Optional[str] = None
    baseline_version_id: Optional[int] = None
    baseline_version_name: Optional[str] = None

    # Totals
    total_planned: Decimal
    total_actual: Decimal
    total_variance: Decimal
    total_variance_percent: Decimal
    total_execution_percent: Decimal

    # CAPEX/OPEX breakdown
    capex_planned: Decimal
    capex_actual: Decimal
    opex_planned: Decimal
    opex_actual: Decimal

    # Monthly breakdown
    monthly_data: List[MonthlyPlanVsActual]

    # Category breakdown
    category_data: List[CategoryPlanVsActual]

    # Alerts
    over_budget_categories: List[str]  # List of category names
    over_budget_months: List[int]  # List of month numbers


class BudgetAlert(BaseModel):
    """Budget alert for overspending"""
    alert_type: str  # "category", "month", "total"
    severity: str  # "warning", "critical"
    entity_id: Optional[int] = None  # category_id or month number
    entity_name: str
    planned_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    message: str


# Update forward references
BudgetVersionWithDetails.model_rebuild()
