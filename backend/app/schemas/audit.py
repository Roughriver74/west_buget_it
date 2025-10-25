"""
Pydantic schemas for Audit Logs
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.db.models import AuditActionEnum


class AuditLogBase(BaseModel):
    """Base schema for audit log"""
    action: AuditActionEnum
    entity_type: str
    entity_id: Optional[int] = None
    description: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log"""
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    department_id: Optional[int] = None


class AuditLogInDB(AuditLogBase):
    """Schema for audit log in database"""
    id: int
    user_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    department_id: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogWithUser(AuditLogInDB):
    """Schema for audit log with user information"""
    username: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        from_attributes = True
