from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class RevenueForecastBase(BaseModel):
    """Base schema for revenue forecast"""
    revenue_stream_id: Optional[int] = None
    revenue_category_id: Optional[int] = None
    forecast_year: int = Field(..., ge=2020, le=2100)
    forecast_month: int = Field(..., ge=1, le=12)
    forecast_amount: Decimal
    confidence_level: Optional[Decimal] = None  # 0-100%
    model_type: Optional[str] = Field(None, max_length=50)
    model_params: Optional[Dict[str, Any]] = None


class RevenueForecastCreate(RevenueForecastBase):
    """Schema for creating revenue forecast"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class RevenueForecastUpdate(BaseModel):
    """Schema for updating revenue forecast"""
    forecast_amount: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    model_type: Optional[str] = Field(None, max_length=50)
    model_params: Optional[Dict[str, Any]] = None


class RevenueForecastInDB(RevenueForecastBase):
    """Schema for revenue forecast from database"""
    id: int
    department_id: int
    created_at: datetime

    class Config:
        from_attributes = True
