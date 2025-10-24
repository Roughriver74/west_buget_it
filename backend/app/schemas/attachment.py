from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AttachmentBase(BaseModel):
    """Base schema for attachment"""
    expense_id: int
    filename: str = Field(..., max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    uploaded_by: Optional[str] = Field(None, max_length=255)


class AttachmentCreate(BaseModel):
    """Schema for creating attachment (file upload)"""
    expense_id: int
    file_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    uploaded_by: Optional[str] = Field(None, max_length=255)


class AttachmentUpdate(BaseModel):
    """Schema for updating attachment metadata"""
    file_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class AttachmentInDB(AttachmentBase):
    """Schema for attachment from database"""
    id: int
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentList(BaseModel):
    """Schema for attachment list"""
    total: int
    items: list[AttachmentInDB]
