from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, Field
from app.db.models import RevenuePlanStatusEnum, RevenueVersionStatusEnum


class RevenuePlanBase(BaseModel):
    """Base schema for revenue plan"""
    name: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=2020, le=2100)
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    description: Optional[str] = None


class RevenuePlanCreate(RevenuePlanBase):
    """Schema for creating revenue plan"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenuePlanUpdate(BaseModel):
    """Schema for updating revenue plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[RevenuePlanStatusEnum] = None
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    description: Optional[str] = None


class RevenuePlanInDB(RevenuePlanBase):
    """Schema for revenue plan from database"""
    id: int
    department_id: int
    status: RevenuePlanStatusEnum
    total_planned_revenue: Optional[Decimal] = None
    created_by: int
    created_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Revenue Plan Version ====================


class RevenuePlanVersionBase(BaseModel):
    """Base schema for revenue plan version"""
    version_number: int
    version_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class RevenuePlanVersionCreate(RevenuePlanVersionBase):
    """Schema for creating revenue plan version"""
    plan_id: int


class RevenuePlanVersionUpdate(BaseModel):
    """Schema for updating revenue plan version"""
    version_name: Optional[str] = Field(None, max_length=255)
    status: Optional[RevenueVersionStatusEnum] = None
    description: Optional[str] = None


class RevenuePlanVersionInDB(RevenuePlanVersionBase):
    """Schema for revenue plan version from database"""
    id: int
    plan_id: int
    status: RevenueVersionStatusEnum
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Revenue Plan Detail ====================


class RevenuePlanDetailBase(BaseModel):
    """Base schema for revenue plan detail"""
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    month_01: Decimal = Field(default=Decimal("0.00"))
    month_02: Decimal = Field(default=Decimal("0.00"))
    month_03: Decimal = Field(default=Decimal("0.00"))
    month_04: Decimal = Field(default=Decimal("0.00"))
    month_05: Decimal = Field(default=Decimal("0.00"))
    month_06: Decimal = Field(default=Decimal("0.00"))
    month_07: Decimal = Field(default=Decimal("0.00"))
    month_08: Decimal = Field(default=Decimal("0.00"))
    month_09: Decimal = Field(default=Decimal("0.00"))
    month_10: Decimal = Field(default=Decimal("0.00"))
    month_11: Decimal = Field(default=Decimal("0.00"))
    month_12: Decimal = Field(default=Decimal("0.00"))


class RevenuePlanDetailCreate(RevenuePlanDetailBase):
    """Schema for creating revenue plan detail"""
    version_id: int
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenuePlanDetailUpdate(BaseModel):
    """Schema for updating revenue plan detail"""
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    month_01: Optional[Decimal] = None
    month_02: Optional[Decimal] = None
    month_03: Optional[Decimal] = None
    month_04: Optional[Decimal] = None
    month_05: Optional[Decimal] = None
    month_06: Optional[Decimal] = None
    month_07: Optional[Decimal] = None
    month_08: Optional[Decimal] = None
    month_09: Optional[Decimal] = None
    month_10: Optional[Decimal] = None
    month_11: Optional[Decimal] = None
    month_12: Optional[Decimal] = None


class RevenuePlanDetailInDB(RevenuePlanDetailBase):
    """Schema for revenue plan detail from database"""
    id: int
    version_id: int
    department_id: int
    total: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RevenuePlanDetailBulkUpdate(BaseModel):
    """Schema for bulk updating revenue plan details"""
    id: int
    updates: Dict[str, Decimal]  # e.g., {"month_01": 1000.00, "month_02": 1500.00}
