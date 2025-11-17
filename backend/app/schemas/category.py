from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.db.models import ExpenseTypeEnum


class BudgetCategoryBase(BaseModel):
    """Base schema for budget category"""
    name: str = Field(..., min_length=1, max_length=255)
    type: ExpenseTypeEnum
    description: Optional[str] = None
    is_active: bool = True
    parent_id: Optional[int] = None


class BudgetCategoryCreate(BudgetCategoryBase):
    """Schema for creating budget category"""
    department_id: Optional[int] = None  # Optional - auto-assigned if not provided


class BudgetCategoryUpdate(BaseModel):
    """Schema for updating budget category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ExpenseTypeEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None
    department_id: Optional[int] = None  # Only ADMIN/MANAGER can change this


class BudgetCategoryInDB(BudgetCategoryBase):
    """Schema for budget category from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
