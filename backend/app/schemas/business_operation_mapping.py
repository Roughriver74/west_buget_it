"""
Pydantic schemas for Business Operation Mappings
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class BusinessOperationMappingBase(BaseModel):
    """Base schema for business operation mapping"""
    business_operation: str = Field(..., description="Business operation name from 1C", max_length=100)
    category_id: Optional[int] = Field(None, description="Budget category ID (nullable for auto-created stubs)")
    priority: int = Field(default=10, ge=1, le=100, description="Priority (higher = more important)")
    confidence: Decimal = Field(default=Decimal("0.98"), ge=0, le=1, description="Confidence level (0-1)")
    notes: Optional[str] = Field(None, description="Optional notes")

    @field_validator('confidence', mode='before')
    @classmethod
    def validate_confidence(cls, v):
        if isinstance(v, str):
            return Decimal(v)
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class BusinessOperationMappingCreate(BusinessOperationMappingBase):
    """Schema for creating business operation mapping"""
    department_id: int = Field(..., description="Department ID")


class BusinessOperationMappingUpdate(BaseModel):
    """Schema for updating business operation mapping"""
    category_id: Optional[int] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('confidence', mode='before')
    @classmethod
    def validate_confidence(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return Decimal(v)
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class BusinessOperationMappingInDB(BaseModel):
    """Schema for business operation mapping in database"""
    id: int
    business_operation: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_type: Optional[str] = None
    priority: int
    confidence: float
    notes: Optional[str] = None
    department_id: int
    department_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BusinessOperationMappingList(BaseModel):
    """Schema for paginated list of mappings"""
    items: List[BusinessOperationMappingInDB]
    total: int
    skip: int
    limit: int
