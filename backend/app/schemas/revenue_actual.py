from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class RevenueActualBase(BaseModel):
    """Base schema for revenue actual"""
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    planned_amount: Optional[Decimal] = Field(None, ge=0)
    actual_amount: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=5000)


class RevenueActualCreate(RevenueActualBase):
    """Schema for creating revenue actual"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenueActualUpdate(BaseModel):
    """Schema for updating revenue actual"""
    planned_amount: Optional[Decimal] = Field(None, ge=0)
    actual_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=5000)


class RevenueActualInDB(RevenueActualBase):
    """Schema for revenue actual from database"""
    id: int
    department_id: int
    variance: Optional[Decimal] = None
    variance_percent: Optional[Decimal] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RevenueActualWithPlan(RevenueActualInDB):
    """Schema for revenue actual with plan vs actual comparison"""
    execution_rate: Optional[Decimal] = None  # actual / planned * 100

    class Config:
        from_attributes = True
