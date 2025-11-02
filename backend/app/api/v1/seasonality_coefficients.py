"""
API endpoints for Seasonality Coefficients
Handles seasonality coefficients for revenue forecasting (12 months)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from decimal import Decimal

from app.db import get_db
from app.db.models import (
    User,
    UserRoleEnum,
    SeasonalityCoefficient,
)
from app.schemas import (
    SeasonalityCoefficientCreate,
    SeasonalityCoefficientUpdate,
    SeasonalityCoefficientInDB,
)
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_coefficient_access(db: Session, coefficient_id: int, user: User) -> SeasonalityCoefficient:
    """
    Check if user has access to seasonality coefficient based on department.
    Raises 404 if coefficient not found or user lacks access.
    """
    coefficient = db.query(SeasonalityCoefficient).filter(SeasonalityCoefficient.id == coefficient_id).first()

    if not coefficient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seasonality coefficient with id {coefficient_id} not found"
        )

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if coefficient.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access seasonality coefficients from your department"
            )

    return coefficient


# ============================================================================
# Seasonality Coefficients Endpoints
# ============================================================================


@router.get("/", response_model=List[SeasonalityCoefficientInDB])
def get_seasonality_coefficients(
    year: Optional[int] = Query(None, description="Filter by year"),
    category: Optional[str] = Query(None, description="Filter by category"),
    department_id: Optional[int] = Query(None, description="Filter by department (MANAGER/ADMIN only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get seasonality coefficients with filtering

    - USER: Can only see coefficients from their own department
    - MANAGER/ADMIN: Can see coefficients from all departments or filter by department
    """
    query = db.query(SeasonalityCoefficient)

    # Apply filters
    if year:
        query = query.filter(SeasonalityCoefficient.year == year)
    if category:
        query = query.filter(SeasonalityCoefficient.category.ilike(f"%{category}%"))

    # SECURITY: Multi-tenancy filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(SeasonalityCoefficient.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(SeasonalityCoefficient.department_id == department_id)

    total = query.count()
    coefficients = query.order_by(
        SeasonalityCoefficient.year.desc(),
        SeasonalityCoefficient.category
    ).offset(skip).limit(limit).all()

    log_info(
        f"Get seasonality coefficients list - user_id: {current_user.id}, year: {year}, "
        f"category: {category}, department_id: {department_id}, total: {total}",
        "seasonality_coefficients"
    )

    return coefficients


@router.get("/{coefficient_id}", response_model=SeasonalityCoefficientInDB)
def get_seasonality_coefficient(
    coefficient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get seasonality coefficient by ID"""
    coefficient = check_coefficient_access(db, coefficient_id, current_user)

    log_info(
        f"Get seasonality coefficient - user_id: {current_user.id}, coefficient_id: {coefficient_id}",
        "seasonality_coefficients"
    )

    return coefficient


@router.post("/", response_model=SeasonalityCoefficientInDB, status_code=status.HTTP_201_CREATED)
def create_seasonality_coefficient(
    coefficient_data: SeasonalityCoefficientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new seasonality coefficient

    - Department is auto-assigned from current_user (USER role)
    - MANAGER/ADMIN can specify department_id
    - All 12 monthly coefficients should average to 1.0
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    else:
        # MANAGER/ADMIN can specify department
        if coefficient_data.department_id:
            department_id = coefficient_data.department_id
        else:
            department_id = current_user.department_id

    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Check for duplicate (same year + category + department)
    existing = (
        db.query(SeasonalityCoefficient)
        .filter(
            SeasonalityCoefficient.year == coefficient_data.year,
            SeasonalityCoefficient.category == coefficient_data.category,
            SeasonalityCoefficient.department_id == department_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seasonality coefficient for year {coefficient_data.year} and category '{coefficient_data.category}' already exists"
        )

    # Validate that average is close to 1.0
    monthly_values = [
        float(coefficient_data.coeff_month_01 or 1.0),
        float(coefficient_data.coeff_month_02 or 1.0),
        float(coefficient_data.coeff_month_03 or 1.0),
        float(coefficient_data.coeff_month_04 or 1.0),
        float(coefficient_data.coeff_month_05 or 1.0),
        float(coefficient_data.coeff_month_06 or 1.0),
        float(coefficient_data.coeff_month_07 or 1.0),
        float(coefficient_data.coeff_month_08 or 1.0),
        float(coefficient_data.coeff_month_09 or 1.0),
        float(coefficient_data.coeff_month_10 or 1.0),
        float(coefficient_data.coeff_month_11 or 1.0),
        float(coefficient_data.coeff_month_12 or 1.0),
    ]
    avg = sum(monthly_values) / 12
    if abs(avg - 1.0) > 0.1:  # Allow 10% deviation
        log_info(
            f"Warning: Seasonality coefficients average is {avg:.3f}, which deviates from 1.0. "
            f"Consider normalizing the coefficients.",
            "seasonality_coefficients"
        )

    # Create coefficient
    new_coefficient = SeasonalityCoefficient(
        year=coefficient_data.year,
        category=coefficient_data.category,
        department_id=department_id,
        coeff_month_01=coefficient_data.coeff_month_01,
        coeff_month_02=coefficient_data.coeff_month_02,
        coeff_month_03=coefficient_data.coeff_month_03,
        coeff_month_04=coefficient_data.coeff_month_04,
        coeff_month_05=coefficient_data.coeff_month_05,
        coeff_month_06=coefficient_data.coeff_month_06,
        coeff_month_07=coefficient_data.coeff_month_07,
        coeff_month_08=coefficient_data.coeff_month_08,
        coeff_month_09=coefficient_data.coeff_month_09,
        coeff_month_10=coefficient_data.coeff_month_10,
        coeff_month_11=coefficient_data.coeff_month_11,
        coeff_month_12=coefficient_data.coeff_month_12,
        notes=coefficient_data.notes,
        created_at=datetime.now()
    )

    db.add(new_coefficient)
    db.commit()
    db.refresh(new_coefficient)

    log_info(
        f"Create seasonality coefficient - user_id: {current_user.id}, coefficient_id: {new_coefficient.id}, "
        f"year: {coefficient_data.year}, category: {coefficient_data.category}",
        "seasonality_coefficients"
    )

    return new_coefficient


@router.put("/{coefficient_id}", response_model=SeasonalityCoefficientInDB)
def update_seasonality_coefficient(
    coefficient_id: int,
    coefficient_data: SeasonalityCoefficientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update seasonality coefficient"""
    coefficient = check_coefficient_access(db, coefficient_id, current_user)

    # Update fields
    update_fields = coefficient_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(coefficient, field, value)

    coefficient.updated_at = datetime.now()

    db.commit()
    db.refresh(coefficient)

    log_info(
        f"Update seasonality coefficient - user_id: {current_user.id}, coefficient_id: {coefficient_id}, "
        f"updates: {update_fields}",
        "seasonality_coefficients"
    )

    return coefficient


@router.delete("/{coefficient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seasonality_coefficient(
    coefficient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete seasonality coefficient (ADMIN only)"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete seasonality coefficients"
        )

    coefficient = check_coefficient_access(db, coefficient_id, current_user)

    db.delete(coefficient)
    db.commit()

    log_info(
        f"Delete seasonality coefficient - user_id: {current_user.id}, coefficient_id: {coefficient_id}",
        "seasonality_coefficients"
    )


@router.post("/calculate-from-history")
def calculate_coefficients_from_history(
    year: int = Query(..., description="Target year for coefficients"),
    category: str = Query(..., description="Category to calculate"),
    lookback_years: int = Query(3, description="Number of years to look back", ge=1, le=5),
    department_id: Optional[int] = Query(None, description="Department ID (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate seasonality coefficients from historical revenue data

    - Analyzes last N years of revenue actuals
    - Computes average monthly distribution
    - Normalizes to average = 1.0
    """
    # Determine department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    else:
        target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # TODO: Implement historical analysis logic
    # This would query RevenueActuals table for past years and calculate averages

    log_info(
        f"Calculate seasonality coefficients - user_id: {current_user.id}, year: {year}, "
        f"category: {category}, lookback_years: {lookback_years}, department_id: {target_department_id}",
        "seasonality_coefficients"
    )

    return {
        "message": "Seasonality calculation from history is not yet implemented",
        "year": year,
        "category": category,
        "lookback_years": lookback_years,
        "department_id": target_department_id,
        "status": "pending_implementation"
    }
