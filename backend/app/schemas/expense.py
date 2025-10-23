from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.db.models import ExpenseStatusEnum
from .category import BudgetCategoryInDB
from .contractor import ContractorInDB
from .organization import OrganizationInDB


class ExpenseBase(BaseModel):
    """Base schema for expense"""
    number: str = Field(..., min_length=1, max_length=50)
    category_id: int
    contractor_id: Optional[int] = None
    organization_id: int
    amount: Decimal = Field(..., ge=0)
    request_date: datetime
    payment_date: Optional[datetime] = None
    status: ExpenseStatusEnum = ExpenseStatusEnum.DRAFT
    is_paid: bool = False
    is_closed: bool = False
    comment: Optional[str] = None
    requester: Optional[str] = Field(None, max_length=255)


class ExpenseCreate(ExpenseBase):
    """Schema for creating expense"""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating expense"""
    number: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[int] = None
    contractor_id: Optional[int] = None
    organization_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    request_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    status: Optional[ExpenseStatusEnum] = None
    is_paid: Optional[bool] = None
    is_closed: Optional[bool] = None
    comment: Optional[str] = None
    requester: Optional[str] = Field(None, max_length=255)


class ExpenseStatusUpdate(BaseModel):
    """Schema for updating expense status"""
    status: ExpenseStatusEnum


class ExpenseInDB(ExpenseBase):
    """Schema for expense from database with relationships"""
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[BudgetCategoryInDB] = None
    contractor: Optional[ContractorInDB] = None
    organization: Optional[OrganizationInDB] = None

    class Config:
        from_attributes = True


class ExpenseList(BaseModel):
    """Schema for expense list with pagination"""
    total: int
    items: list[ExpenseInDB]
    page: int
    page_size: int
    pages: int
