from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class BudgetPlanBase(BaseModel):
    """Base schema for budget plan"""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    category_id: int
    planned_amount: Decimal = Field(..., ge=0)
    capex_planned: Decimal = Field(default=0, ge=0)
    opex_planned: Decimal = Field(default=0, ge=0)


class BudgetPlanCreate(BudgetPlanBase):
    """Schema for creating budget plan"""
    pass


class BudgetPlanUpdate(BaseModel):
    """Schema for updating budget plan"""
    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    category_id: Optional[int] = None
    planned_amount: Optional[Decimal] = Field(None, ge=0)
    capex_planned: Optional[Decimal] = Field(None, ge=0)
    opex_planned: Optional[Decimal] = Field(None, ge=0)


class BudgetPlanInDB(BudgetPlanBase):
    """Schema for budget plan from database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
