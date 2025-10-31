from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class CustomerMetricsBase(BaseModel):
    """Base schema for customer metrics"""
    revenue_stream_id: int
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    total_customer_base: Optional[int] = None  # ОКБ
    active_customer_base: Optional[int] = None  # АКБ
    coverage_rate: Optional[Decimal] = None  # Покрытие (АКБ/ОКБ)
    regular_clinics: Optional[int] = None
    network_clinics: Optional[int] = None
    new_clinics: Optional[int] = None
    avg_order_value: Optional[Decimal] = None
    avg_order_value_regular: Optional[Decimal] = None
    avg_order_value_network: Optional[Decimal] = None
    avg_order_value_new: Optional[Decimal] = None


class CustomerMetricsCreate(CustomerMetricsBase):
    """Schema for creating customer metrics"""
    department_id: Optional[int] = None  # Optional - auto-assigned from current_user


class CustomerMetricsUpdate(BaseModel):
    """Schema for updating customer metrics"""
    total_customer_base: Optional[int] = None
    active_customer_base: Optional[int] = None
    coverage_rate: Optional[Decimal] = None
    regular_clinics: Optional[int] = None
    network_clinics: Optional[int] = None
    new_clinics: Optional[int] = None
    avg_order_value: Optional[Decimal] = None
    avg_order_value_regular: Optional[Decimal] = None
    avg_order_value_network: Optional[Decimal] = None
    avg_order_value_new: Optional[Decimal] = None


class CustomerMetricsInDB(CustomerMetricsBase):
    """Schema for customer metrics from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
