"""API endpoints for tax rates"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import User, TaxRate, UserRoleEnum, TaxTypeEnum
from app.db.session import get_db
from app.utils.auth import get_current_active_user
from app.schemas.tax_rate import (
    TaxRateCreate,
    TaxRateUpdate,
    TaxRateInDB,
    TaxRateListItem,
    TaxCalculationRequest,
    TaxCalculationResult,
)

router = APIRouter()


def check_access(current_user: User):
    """Check if user has access to tax rates (ADMIN or ACCOUNTANT only)"""
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.ACCOUNTANT]:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Только администраторы и финансисты могут управлять ставками"
        )


@router.get("/", response_model=List[TaxRateListItem])
def get_tax_rates(
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    tax_type: Optional[str] = Query(None, description="Tax type filter"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    effective_date: Optional[date] = Query(None, description="Date to check effectiveness"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get list of tax rates (ADMIN/ACCOUNTANT only)"""
    check_access(current_user)

    query = db.query(TaxRate)

    # Apply filters
    if department_id is not None:
        query = query.filter(TaxRate.department_id == department_id)

    if tax_type:
        query = query.filter(TaxRate.tax_type == tax_type)

    if is_active is not None:
        query = query.filter(TaxRate.is_active == is_active)

    if effective_date:
        query = query.filter(
            and_(
                TaxRate.effective_from <= effective_date,
                or_(
                    TaxRate.effective_to.is_(None),
                    TaxRate.effective_to >= effective_date
                )
            )
        )

    # Order by effective_from descending
    query = query.order_by(TaxRate.effective_from.desc())

    # Pagination
    query = query.offset(skip).limit(limit)

    return query.all()


@router.get("/{tax_rate_id}", response_model=TaxRateInDB)
def get_tax_rate(
    tax_rate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get tax rate by ID (ADMIN/ACCOUNTANT only)"""
    check_access(current_user)

    tax_rate = db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    return tax_rate


@router.post("/", response_model=TaxRateInDB)
def create_tax_rate(
    tax_rate_data: TaxRateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create new tax rate (ADMIN/ACCOUNTANT only)"""
    check_access(current_user)

    # Validate tax_type enum
    try:
        TaxTypeEnum(tax_rate_data.tax_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tax_type. Must be one of: {[e.value for e in TaxTypeEnum]}"
        )

    # Validate effective dates
    if tax_rate_data.effective_to and tax_rate_data.effective_to < tax_rate_data.effective_from:
        raise HTTPException(
            status_code=400,
            detail="effective_to must be >= effective_from"
        )

    # Create tax rate
    tax_rate = TaxRate(
        **tax_rate_data.model_dump(),
        created_by_id=current_user.id
    )
    db.add(tax_rate)
    db.commit()
    db.refresh(tax_rate)

    return tax_rate


@router.put("/{tax_rate_id}", response_model=TaxRateInDB)
def update_tax_rate(
    tax_rate_id: int,
    tax_rate_data: TaxRateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update tax rate (ADMIN/ACCOUNTANT only)"""
    check_access(current_user)

    tax_rate = db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    # Update fields
    update_data = tax_rate_data.model_dump(exclude_unset=True)

    # Validate tax_type if provided
    if "tax_type" in update_data:
        try:
            TaxTypeEnum(update_data["tax_type"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tax_type. Must be one of: {[e.value for e in TaxTypeEnum]}"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(tax_rate, field, value)

    # Validate effective dates
    if tax_rate.effective_to and tax_rate.effective_to < tax_rate.effective_from:
        raise HTTPException(
            status_code=400,
            detail="effective_to must be >= effective_from"
        )

    db.commit()
    db.refresh(tax_rate)

    return tax_rate


@router.delete("/{tax_rate_id}")
def delete_tax_rate(
    tax_rate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete tax rate (ADMIN/ACCOUNTANT only)"""
    check_access(current_user)

    tax_rate = db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    db.delete(tax_rate)
    db.commit()

    return {"message": "Tax rate deleted successfully"}


@router.post("/calculate", response_model=TaxCalculationResult)
def calculate_taxes(
    calc_data: TaxCalculationRequest,
    department_id: Optional[int] = Query(None, description="Department ID (optional)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Calculate all taxes and social contributions for a given salary amount"""

    check_access(current_user)

    gross_amount = calc_data.gross_amount
    calc_date = date(calc_data.year, calc_data.month, 1)

    # Get active tax rates for the specified date
    tax_rates_query = db.query(TaxRate).filter(
        TaxRate.is_active == True,
        TaxRate.effective_from <= calc_date,
        or_(
            TaxRate.effective_to.is_(None),
            TaxRate.effective_to >= calc_date
        )
    )

    if department_id is not None:
        tax_rates_query = tax_rates_query.filter(
            or_(
                TaxRate.department_id == department_id,
                TaxRate.department_id.is_(None)
            )
        )
    else:
        tax_rates_query = tax_rates_query.filter(TaxRate.department_id.is_(None))

    selected_rates = merge_tax_rates_with_defaults(tax_rates_query.all())

    # Initialize result
    income_tax = Decimal(0)
    income_tax_rate = Decimal(0)
    pension_fund = Decimal(0)
    pension_fund_rate = Decimal(0)
    medical_insurance = Decimal(0)
    medical_insurance_rate = Decimal(0)
    social_insurance = Decimal(0)
    social_insurance_rate = Decimal(0)

    breakdown = {}

    # Calculate taxes
    for tax_rate in selected_rates.values():
        if tax_rate.tax_type == TaxTypeEnum.INCOME_TAX:
            # НДФЛ (13% or 15% if above threshold)
            if tax_rate.threshold_amount and gross_amount > tax_rate.threshold_amount:
                # Progressive rate
                amount_below = tax_rate.threshold_amount
                amount_above = gross_amount - tax_rate.threshold_amount
                income_tax = (amount_below * tax_rate.rate) + (amount_above * (tax_rate.rate_above_threshold or tax_rate.rate))
                income_tax_rate = tax_rate.rate_above_threshold or tax_rate.rate
            else:
                income_tax = gross_amount * tax_rate.rate
                income_tax_rate = tax_rate.rate

            breakdown["income_tax"] = {
                "rate": float(income_tax_rate),
                "amount": float(income_tax),
                "description": tax_rate.name
            }

        elif tax_rate.tax_type == TaxTypeEnum.PENSION_FUND:
            # ПФР (22% до предела, 10% выше)
            if tax_rate.threshold_amount and gross_amount > tax_rate.threshold_amount:
                amount_below = tax_rate.threshold_amount
                amount_above = gross_amount - tax_rate.threshold_amount
                pension_fund = (amount_below * tax_rate.rate) + (amount_above * (tax_rate.rate_above_threshold or Decimal(0)))
                pension_fund_rate = tax_rate.rate
            else:
                pension_fund = gross_amount * tax_rate.rate
                pension_fund_rate = tax_rate.rate

            breakdown["pension_fund"] = {
                "rate": float(pension_fund_rate),
                "amount": float(pension_fund),
                "description": tax_rate.name
            }

        elif tax_rate.tax_type == TaxTypeEnum.MEDICAL_INSURANCE:
            # ФОМС (5.1%)
            medical_insurance = gross_amount * tax_rate.rate
            medical_insurance_rate = tax_rate.rate

            breakdown["medical_insurance"] = {
                "rate": float(medical_insurance_rate),
                "amount": float(medical_insurance),
                "description": tax_rate.name
            }

        elif tax_rate.tax_type == TaxTypeEnum.SOCIAL_INSURANCE:
            # ФСС (2.9%)
            social_insurance = gross_amount * tax_rate.rate
            social_insurance_rate = tax_rate.rate

            breakdown["social_insurance"] = {
                "rate": float(social_insurance_rate),
                "amount": float(social_insurance),
                "description": tax_rate.name
            }

    # Calculate totals
    total_social_contributions = pension_fund + medical_insurance + social_insurance
    net_amount = gross_amount - income_tax
    employer_cost = gross_amount + total_social_contributions

    return TaxCalculationResult(
        gross_amount=gross_amount,
        income_tax=income_tax,
        income_tax_rate=income_tax_rate,
        pension_fund=pension_fund,
        pension_fund_rate=pension_fund_rate,
        medical_insurance=medical_insurance,
        medical_insurance_rate=medical_insurance_rate,
        social_insurance=social_insurance,
        social_insurance_rate=social_insurance_rate,
        total_social_contributions=total_social_contributions,
        net_amount=net_amount,
        employer_cost=employer_cost,
        breakdown=breakdown
    )


@router.post("/initialize-default")
def initialize_default_tax_rates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Initialize default Russian tax rates for 2025 (ADMIN/ACCOUNTANT only, global)"""
    check_access(current_user)

    # Check if already initialized globally
    existing = db.query(TaxRate).filter(
        TaxRate.department_id.is_(None)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Tax rates already exist globally"
        )

    # Default tax rates for Russia 2025
    default_rates = [
        {
            "tax_type": TaxTypeEnum.INCOME_TAX,
            "name": "НДФЛ (13%)",
            "description": "Налог на доходы физических лиц до 5 млн руб в год",
            "rate": Decimal("0.13"),
            "threshold_amount": Decimal("5000000"),
            "rate_above_threshold": Decimal("0.15"),
            "effective_from": date(2025, 1, 1),
            "effective_to": None,
        },
        {
            "tax_type": TaxTypeEnum.PENSION_FUND,
            "name": "ПФР (22%)",
            "description": "Пенсионный фонд РФ (22% до предела взносов, 10% выше)",
            "rate": Decimal("0.22"),
            "threshold_amount": Decimal("1917000"),  # Предел взносов 2025
            "rate_above_threshold": Decimal("0.10"),
            "effective_from": date(2025, 1, 1),
            "effective_to": None,
        },
        {
            "tax_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "name": "ФОМС (5.1%)",
            "description": "Федеральный фонд обязательного медицинского страхования",
            "rate": Decimal("0.051"),
            "threshold_amount": None,
            "rate_above_threshold": None,
            "effective_from": date(2025, 1, 1),
            "effective_to": None,
        },
        {
            "tax_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "name": "ФСС (2.9%)",
            "description": "Фонд социального страхования",
            "rate": Decimal("0.029"),
            "threshold_amount": None,
            "rate_above_threshold": None,
            "effective_from": date(2025, 1, 1),
            "effective_to": None,
        },
    ]

    # Create tax rates
    for rate_data in default_rates:
        tax_rate = TaxRate(
            **rate_data,
            department_id=None,
            is_active=True,
            created_by_id=current_user.id
        )
        db.add(tax_rate)

    db.commit()

    return {
        "message": "Default tax rates initialized successfully",
        "count": len(default_rates)
    }
