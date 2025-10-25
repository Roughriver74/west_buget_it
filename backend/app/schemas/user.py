"""
Pydantic schemas for User authentication and management
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator

from app.db.models import UserRoleEnum


# Base User schema
class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None


# User registration schema
class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRoleEnum = UserRoleEnum.REQUESTER

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        return v


# User update schema
class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRoleEnum] = None


# User password change schema
class UserPasswordChange(BaseModel):
    """Schema for changing user password"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        return v


# User response schema
class User(UserBase):
    """Schema for user response (without password)"""
    id: int
    role: UserRoleEnum
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User list item schema (minimal info)
class UserListItem(BaseModel):
    """Schema for user in list view"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRoleEnum
    is_active: bool
    department: Optional[str] = None
    position: Optional[str] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # Can be username or email
    password: str


class UserLoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    user: User
