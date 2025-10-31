from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from app.db.models import RevenueCategoryTypeEnum


class RevenueCategoryBase(BaseModel):
    """Base schema for revenue category"""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    category_type: RevenueCategoryTypeEnum
    parent_id: Optional[int] = None
    default_margin: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: bool = True


class RevenueCategoryCreate(RevenueCategoryBase):
    """Schema for creating revenue category"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenueCategoryUpdate(BaseModel):
    """Schema for updating revenue category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    category_type: Optional[RevenueCategoryTypeEnum] = None
    parent_id: Optional[int] = None
    default_margin: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RevenueCategoryInDB(RevenueCategoryBase):
    """Schema for revenue category from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RevenueCategoryTree(RevenueCategoryInDB):
    """Schema for revenue category with subcategories (tree structure)"""
    subcategories: List['RevenueCategoryTree'] = []

    class Config:
        from_attributes = True


# For nested tree structure
RevenueCategoryTree.model_rebuild()
