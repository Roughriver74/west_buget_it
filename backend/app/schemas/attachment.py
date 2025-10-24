from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AttachmentBase(BaseModel):
    """Base schema for attachment"""
    filename: str = Field(..., min_length=1, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)  # invoice, contract, act, other
    uploaded_by: Optional[str] = Field(None, max_length=255)


class AttachmentCreate(AttachmentBase):
    """Schema for creating attachment"""
    expense_id: int
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_size: int = Field(..., ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)


class AttachmentUpdate(BaseModel):
    """Schema for updating attachment"""
    filename: Optional[str] = Field(None, min_length=1, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)


class AttachmentInDB(AttachmentBase):
    """Schema for attachment from database"""
    id: int
    expense_id: int
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachmentList(BaseModel):
    """Schema for attachment list"""
    items: list[AttachmentInDB]
    total: int
