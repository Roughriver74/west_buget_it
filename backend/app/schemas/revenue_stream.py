from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import RevenueStreamTypeEnum


class RevenueStreamBase(BaseModel):
    """Base schema for revenue stream"""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    stream_type: RevenueStreamTypeEnum
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class RevenueStreamCreate(RevenueStreamBase):
    """Schema for creating revenue stream"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenueStreamUpdate(BaseModel):
    """Schema for updating revenue stream"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    stream_type: Optional[RevenueStreamTypeEnum] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RevenueStreamInDB(RevenueStreamBase):
    """Schema for revenue stream from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RevenueStreamTree(RevenueStreamInDB):
    """Schema for revenue stream with children (tree structure)"""
    children: List['RevenueStreamTree'] = []

    class Config:
        from_attributes = True


# For nested tree structure
RevenueStreamTree.model_rebuild()
