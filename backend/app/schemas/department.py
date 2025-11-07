"""
Pydantic schemas for Department management
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Base Department schema
class DepartmentBase(BaseModel):
    """Base department schema with common fields"""
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    ftp_subdivision_name: Optional[str] = Field(None, max_length=255, description="Название подразделения из FTP для сопоставления")
    default_category_id: Optional[int] = Field(None, description="Категория по умолчанию для FTP импорта")
    manager_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


# Department creation schema
class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department"""
    is_active: bool = True


# Department update schema
class DepartmentUpdate(BaseModel):
    """Schema for updating department information"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    ftp_subdivision_name: Optional[str] = Field(None, max_length=255, description="Название подразделения из FTP для сопоставления")
    default_category_id: Optional[int] = Field(None, description="Категория по умолчанию для FTP импорта")
    manager_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None


# Department response schema
class Department(DepartmentBase):
    """Schema for department response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Department list item schema
class DepartmentListItem(BaseModel):
    """Schema for department in list view"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    ftp_subdivision_name: Optional[str] = None
    default_category_id: Optional[int] = None
    manager_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# Department with statistics
class DepartmentWithStats(Department):
    """Schema for department with statistics"""
    users_count: int = 0
    expenses_count: int = 0
    total_budget: float = 0.0

    class Config:
        from_attributes = True
