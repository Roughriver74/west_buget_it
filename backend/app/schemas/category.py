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


class BudgetCategoryCreate(BudgetCategoryBase):
    """Schema for creating budget category"""
    pass


class BudgetCategoryUpdate(BaseModel):
    """Schema for updating budget category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ExpenseTypeEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BudgetCategoryInDB(BudgetCategoryBase):
    """Schema for budget category from database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
