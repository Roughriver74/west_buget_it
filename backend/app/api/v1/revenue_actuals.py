from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db import get_db
from app.db.models import RevenueActual, User, UserRoleEnum
from app.schemas import (
    RevenueActualCreate,
    RevenueActualUpdate,
    RevenueActualInDB,
)
from app.services.cache import cache_service
from app.utils.auth import get_current_active_user
from app.utils.logger import log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "revenue_actuals"


def check_department_access(db: Session, actual_id: int, user: User) -> RevenueActual:
    """Check if user has access to revenue actual based on department"""
    actual = db.query(RevenueActual).filter(RevenueActual.id == actual_id).first()

    if not actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue actual with id {actual_id} not found"
        )

    if user.role == UserRoleEnum.USER:
        if actual.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Revenue actual with id {actual_id} not found"
            )

    return actual


@router.get("/", response_model=List[RevenueActualInDB])
def get_revenue_actuals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    year: Optional[int] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    revenue_stream_id: Optional[int] = None,
    revenue_category_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all revenue actuals with filtering"""
    query = db.query(RevenueActual)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenueActual.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(RevenueActual.department_id == department_id)

    if year is not None:
        query = query.filter(RevenueActual.year == year)

    if month is not None:
        query = query.filter(RevenueActual.month == month)

    if revenue_stream_id is not None:
        query = query.filter(RevenueActual.revenue_stream_id == revenue_stream_id)

    if revenue_category_id is not None:
        query = query.filter(RevenueActual.revenue_category_id == revenue_category_id)

    actuals = query.order_by(
        RevenueActual.year.desc(),
        RevenueActual.month.desc()
    ).offset(skip).limit(limit).all()

    log_info(f"Retrieved {len(actuals)} revenue actuals", context=f"User {current_user.id}")
    return actuals


@router.get("/{actual_id}", response_model=RevenueActualInDB)
def get_revenue_actual(
    actual_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific revenue actual by ID"""
    actual = check_department_access(db, actual_id, current_user)
    log_info(f"Retrieved revenue actual {actual_id}", context=f"User {current_user.id}")
    return RevenueActualInDB.model_validate(actual)


@router.post("/", response_model=RevenueActualInDB, status_code=status.HTTP_201_CREATED)
def create_revenue_actual(
    actual: RevenueActualCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new revenue actual record"""

    # Validate department assignment
    if actual.department_id:
        if current_user.role == UserRoleEnum.USER:
            if actual.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create actuals for your own department"
                )
    else:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no assigned department"
            )
        actual.department_id = current_user.department_id

    # Create the actual record
    db_actual = RevenueActual(
        **actual.model_dump(),
        created_by=current_user.id
    )

    # Calculate variance if planned_amount is provided
    if db_actual.planned_amount is not None and db_actual.planned_amount != 0:
        db_actual.variance = db_actual.actual_amount - db_actual.planned_amount
        db_actual.variance_percent = (db_actual.variance / db_actual.planned_amount) * 100
    elif db_actual.planned_amount == 0:
        # If planned is 0, variance is the actual amount
        db_actual.variance = db_actual.actual_amount
        db_actual.variance_percent = None  # Cannot calculate percentage
    else:
        # If planned is None, no variance calculation
        db_actual.variance = None
        db_actual.variance_percent = None

    db.add(db_actual)
    db.commit()
    db.refresh(db_actual)

    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Created revenue actual {db_actual.id} for {db_actual.year}-{db_actual.month:02d}", context=f"User {current_user.id}")
    return RevenueActualInDB.model_validate(db_actual)


@router.put("/{actual_id}", response_model=RevenueActualInDB)
def update_revenue_actual(
    actual_id: int,
    actual_update: RevenueActualUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing revenue actual"""
    db_actual = check_department_access(db, actual_id, current_user)

    # Update fields
    update_data = actual_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_actual, field, value)

    # Recalculate variance
    if db_actual.planned_amount is not None and db_actual.planned_amount != 0:
        db_actual.variance = db_actual.actual_amount - db_actual.planned_amount
        db_actual.variance_percent = (db_actual.variance / db_actual.planned_amount) * 100
    elif db_actual.planned_amount == 0:
        # If planned is 0, variance is the actual amount
        db_actual.variance = db_actual.actual_amount
        db_actual.variance_percent = None  # Cannot calculate percentage
    else:
        # If planned is None, no variance calculation
        db_actual.variance = None
        db_actual.variance_percent = None

    db.commit()
    db.refresh(db_actual)

    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Updated revenue actual {actual_id}", context=f"User {current_user.id}")
    return RevenueActualInDB.model_validate(db_actual)


@router.delete("/{actual_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue_actual(
    actual_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a revenue actual record"""
    db_actual = check_department_access(db, actual_id, current_user)

    db.delete(db_actual)
    db.commit()

    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Deleted revenue actual {actual_id}", context=f"User {current_user.id}")
    return None
