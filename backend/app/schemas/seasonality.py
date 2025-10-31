from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class SeasonalityCoefficientBase(BaseModel):
    """Base schema for seasonality coefficient"""
    revenue_stream_id: int
    year: int = Field(..., ge=2020, le=2100)
    coef_01: Decimal = Field(default=Decimal("1.0"))
    coef_02: Decimal = Field(default=Decimal("1.0"))
    coef_03: Decimal = Field(default=Decimal("1.0"))
    coef_04: Decimal = Field(default=Decimal("1.0"))
    coef_05: Decimal = Field(default=Decimal("1.0"))
    coef_06: Decimal = Field(default=Decimal("1.0"))
    coef_07: Decimal = Field(default=Decimal("1.0"))
    coef_08: Decimal = Field(default=Decimal("1.0"))
    coef_09: Decimal = Field(default=Decimal("1.0"))
    coef_10: Decimal = Field(default=Decimal("1.0"))
    coef_11: Decimal = Field(default=Decimal("1.0"))
    coef_12: Decimal = Field(default=Decimal("1.0"))
    description: Optional[str] = None


class SeasonalityCoefficientCreate(SeasonalityCoefficientBase):
    """Schema for creating seasonality coefficient"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class SeasonalityCoefficientUpdate(BaseModel):
    """Schema for updating seasonality coefficient"""
    coef_01: Optional[Decimal] = None
    coef_02: Optional[Decimal] = None
    coef_03: Optional[Decimal] = None
    coef_04: Optional[Decimal] = None
    coef_05: Optional[Decimal] = None
    coef_06: Optional[Decimal] = None
    coef_07: Optional[Decimal] = None
    coef_08: Optional[Decimal] = None
    coef_09: Optional[Decimal] = None
    coef_10: Optional[Decimal] = None
    coef_11: Optional[Decimal] = None
    coef_12: Optional[Decimal] = None
    description: Optional[str] = None


class SeasonalityCoefficientInDB(SeasonalityCoefficientBase):
    """Schema for seasonality coefficient from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
