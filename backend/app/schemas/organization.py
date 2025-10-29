from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """Base schema for organization"""
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization (SHARED - no department_id)"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class OrganizationInDB(OrganizationBase):
    """Schema for organization from database (SHARED - no department_id)"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
