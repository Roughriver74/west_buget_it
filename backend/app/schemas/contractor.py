from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContractorBase(BaseModel):
    """Base schema for contractor"""
    name: str = Field(..., min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=255)
    inn: Optional[str] = Field(None, max_length=20)
    contact_info: Optional[str] = None
    is_active: bool = True


class ContractorCreate(ContractorBase):
    """Schema for creating contractor"""
    department_id: Optional[int] = None  # Optional - auto-assigned if not provided


class ContractorUpdate(BaseModel):
    """Schema for updating contractor"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=255)
    inn: Optional[str] = Field(None, max_length=20)
    contact_info: Optional[str] = None
    is_active: Optional[bool] = None


class ContractorInDB(ContractorBase):
    """Schema for contractor from database"""
    id: int
    department_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
