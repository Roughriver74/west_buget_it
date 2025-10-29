"""
Budget Validation Schemas
"""
from typing import List, Optional
from pydantic import BaseModel


class BudgetInfo(BaseModel):
    """Budget information for validation context"""
    baseline_version_id: int
    baseline_version_name: Optional[str]
    monthly_budget: float
    monthly_actual: float
    monthly_new_total: float
    monthly_percent: float
    annual_budget: float
    annual_actual: float
    annual_new_total: float
    annual_percent: float


class ExpenseValidationResponse(BaseModel):
    """Response for expense validation"""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    budget_info: Optional[BudgetInfo] = None


class CategoryBudgetAlert(BaseModel):
    """Budget alert for a specific category and month"""
    category_id: int
    month: int
    planned: float
    actual: float
    percent: float


class BudgetStatusResponse(BaseModel):
    """Response for budget status check"""
    has_baseline: bool
    baseline_version_id: Optional[int] = None
    baseline_version_name: Optional[str] = None
    categories_over_budget: List[CategoryBudgetAlert]
    categories_at_risk: List[CategoryBudgetAlert]
    total_over_budget: int
    total_at_risk: int
    message: Optional[str] = None
