"""Pydantic schemas for tax rates"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TaxRateBase(BaseModel):
    """Base schema for tax rate"""
    tax_type: str = Field(..., description="Tax type (INCOME_TAX, PENSION_FUND, etc.)")
    name: str = Field(..., min_length=1, max_length=200, description="Tax name")
    description: Optional[str] = Field(None, description="Description")
    rate: Decimal = Field(..., ge=0, le=1, description="Tax rate (0-1, e.g., 0.13 for 13%)")
    threshold_amount: Optional[Decimal] = Field(None, ge=0, description="Threshold amount if applicable")
    rate_above_threshold: Optional[Decimal] = Field(None, ge=0, le=1, description="Rate above threshold")
    effective_from: date = Field(..., description="Effective from date")
    effective_to: Optional[date] = Field(None, description="Effective to date (null = indefinite)")
    is_active: bool = Field(True, description="Is active")
    notes: Optional[str] = Field(None, description="Notes")


class TaxRateCreate(TaxRateBase):
    """Schema for creating a tax rate"""
    department_id: Optional[int] = Field(None, gt=0, description="Department ID (optional)")


class TaxRateUpdate(BaseModel):
    """Schema for updating a tax rate"""
    tax_type: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rate: Optional[Decimal] = Field(None, ge=0, le=1)
    threshold_amount: Optional[Decimal] = Field(None, ge=0)
    rate_above_threshold: Optional[Decimal] = Field(None, ge=0, le=1)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    department_id: Optional[int] = Field(None, gt=0, description="Department ID (optional)")


class TaxRateInDB(TaxRateBase):
    """Schema for tax rate in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None


class TaxRateListItem(BaseModel):
    """Schema for tax rate list item (lightweight)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tax_type: str
    name: str
    rate: Decimal
    threshold_amount: Optional[Decimal] = None
    rate_above_threshold: Optional[Decimal] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool
    department_id: Optional[int] = None


class TaxCalculationRequest(BaseModel):
    """Schema for tax calculation request"""
    gross_amount: Decimal = Field(..., gt=0, description="Gross salary amount")
    year: int = Field(..., ge=2020, le=2030, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month")


class TaxCalculationResult(BaseModel):
    """Schema for tax calculation result"""
    gross_amount: Decimal
    income_tax: Decimal
    income_tax_rate: Decimal
    pension_fund: Decimal
    pension_fund_rate: Decimal
    medical_insurance: Decimal
    medical_insurance_rate: Decimal
    social_insurance: Decimal
    social_insurance_rate: Decimal
    total_social_contributions: Decimal
    net_amount: Decimal
    employer_cost: Decimal  # gross + social contributions
    breakdown: dict  # Детальная разбивка
