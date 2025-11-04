from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import APITokenScopeEnum, APITokenStatusEnum


class APITokenBase(BaseModel):
    """Base schema for API token"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: List[APITokenScopeEnum] = Field(default=[APITokenScopeEnum.READ])
    department_id: Optional[int] = None  # None = system-wide token
    expires_at: Optional[datetime] = None  # None = never expires


class APITokenCreate(APITokenBase):
    """Schema for creating API token"""
    pass


class APITokenUpdate(BaseModel):
    """Schema for updating API token"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: Optional[List[APITokenScopeEnum]] = None
    status: Optional[APITokenStatusEnum] = None
    expires_at: Optional[datetime] = None


class APITokenInDB(APITokenBase):
    """Schema for API token from database (without token_key for security)"""
    id: int
    status: APITokenStatusEnum
    created_by: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[int] = None
    request_count: int

    class Config:
        from_attributes = True


class APITokenWithKey(APITokenInDB):
    """Schema for API token with key (only returned on creation)"""
    token_key: str


class APITokenRevoke(BaseModel):
    """Schema for revoking API token"""
    reason: Optional[str] = None
