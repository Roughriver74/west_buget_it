from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class DashboardConfigBase(BaseModel):
    """Base schema for dashboard configuration"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    user_id: Optional[str] = Field(None, max_length=255)
    is_default: bool = False
    is_public: bool = False
    config: Dict[str, Any] = Field(..., description="Dashboard layout and widgets configuration")


class DashboardConfigCreate(DashboardConfigBase):
    """Schema for creating dashboard configuration"""
    pass


class DashboardConfigUpdate(BaseModel):
    """Schema for updating dashboard configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class DashboardConfigInDB(DashboardConfigBase):
    """Schema for dashboard configuration from database"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardConfigList(BaseModel):
    """Schema for dashboard configuration list"""
    items: list[DashboardConfigInDB]
    total: int
