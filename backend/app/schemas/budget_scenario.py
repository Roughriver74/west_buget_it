"""
Pydantic schemas for Budget Scenarios
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class BudgetCategoryType(str, Enum):
    """Budget category type"""
    OPEX = "OPEX"
    CAPEX = "CAPEX"


class BudgetPriority(str, Enum):
    """Budget priority levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Budget Scenario Item Schemas
class BudgetScenarioItemBase(BaseModel):
    """Base schema for budget scenario item"""
    category_type: BudgetCategoryType
    category_name: str = Field(..., max_length=255)
    percentage: Decimal = Field(..., ge=0, le=100, description="Процент от общего бюджета")
    priority: BudgetPriority = BudgetPriority.MEDIUM
    change_from_previous: Optional[Decimal] = Field(None, description="Изменение к предыдущему году (%)")
    notes: Optional[str] = None


class BudgetScenarioItemCreate(BudgetScenarioItemBase):
    """Schema for creating budget scenario item"""
    pass


class BudgetScenarioItemUpdate(BaseModel):
    """Schema for updating budget scenario item"""
    category_type: Optional[BudgetCategoryType] = None
    category_name: Optional[str] = Field(None, max_length=255)
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    priority: Optional[BudgetPriority] = None
    change_from_previous: Optional[Decimal] = None
    notes: Optional[str] = None


class BudgetScenarioItem(BudgetScenarioItemBase):
    """Schema for budget scenario item response"""
    id: int
    scenario_id: int
    amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Budget Scenario Schemas
class BudgetScenarioBase(BaseModel):
    """Base schema for budget scenario"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    year: int = Field(..., ge=2020, le=2100)
    total_budget: Decimal = Field(..., gt=0, description="Общий бюджет")
    budget_change_percent: Optional[Decimal] = Field(None, description="Изменение бюджета к предыдущему году (%)")
    is_active: bool = True
    notes: Optional[str] = None


class BudgetScenarioCreate(BudgetScenarioBase):
    """Schema for creating budget scenario"""
    items: Optional[List[BudgetScenarioItemCreate]] = []

    @field_validator('items')
    @classmethod
    def validate_items_percentages(cls, items: List[BudgetScenarioItemCreate]) -> List[BudgetScenarioItemCreate]:
        """Validate that total percentages don't exceed 100%"""
        if items:
            total_percentage = sum(item.percentage for item in items)
            if total_percentage > 100:
                raise ValueError(f"Сумма процентов ({total_percentage}%) превышает 100%")
        return items


class BudgetScenarioUpdate(BaseModel):
    """Schema for updating budget scenario"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=2020, le=2100)
    total_budget: Optional[Decimal] = Field(None, gt=0)
    budget_change_percent: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BudgetScenario(BudgetScenarioBase):
    """Schema for budget scenario response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetScenarioWithItems(BudgetScenario):
    """Schema for budget scenario with items"""
    items: List[BudgetScenarioItem] = []

    class Config:
        from_attributes = True


# Summary and Comparison Schemas
class BudgetScenarioSummary(BaseModel):
    """Summary of budget scenario by category type"""
    scenario_id: int
    scenario_name: str
    year: int
    total_budget: Decimal
    opex_total: Decimal
    opex_percentage: Decimal
    capex_total: Decimal
    capex_percentage: Decimal
    items_count: int


class BudgetScenarioComparison(BaseModel):
    """Comparison between multiple scenarios"""
    year: int
    scenarios: List[BudgetScenarioWithItems]

    class Config:
        from_attributes = True


class BudgetCategoryComparison(BaseModel):
    """Comparison of a specific category across scenarios"""
    category_name: str
    category_type: BudgetCategoryType
    scenarios_data: dict  # {scenario_name: {amount, percentage, priority}}
