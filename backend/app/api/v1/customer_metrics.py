"""
API endpoints for Customer Metrics
Handles customer base metrics (ОКБ, АКБ, покрытие, средний чек)
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
    CustomerMetrics,
)
from app.schemas import (
    CustomerMetricsCreate,
    CustomerMetricsUpdate,
    CustomerMetricsInDB,
)
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_metrics_access(db: Session, metrics_id: int, user: User) -> CustomerMetrics:
    """
    Check if user has access to customer metrics based on department.
    Raises 404 if metrics not found or user lacks access.
    """
    metrics = db.query(CustomerMetrics).filter(CustomerMetrics.id == metrics_id).first()

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer metrics with id {metrics_id} not found"
        )

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if metrics.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access customer metrics from your department"
            )

    return metrics


# ============================================================================
# Customer Metrics Endpoints
# ============================================================================


@router.get("/", response_model=List[CustomerMetricsInDB])
def get_customer_metrics(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month"),
    region: Optional[str] = Query(None, description="Filter by region"),
    department_id: Optional[int] = Query(None, description="Filter by department (MANAGER/ADMIN only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customer metrics with filtering

    - USER: Can only see metrics from their own department
    - MANAGER/ADMIN: Can see metrics from all departments or filter by department
    """
    query = db.query(CustomerMetrics)

    # Apply filters
    if year:
        query = query.filter(CustomerMetrics.year == year)
    if month:
        query = query.filter(CustomerMetrics.month == month)
    if region:
        query = query.filter(CustomerMetrics.region.ilike(f"%{region}%"))

    # SECURITY: Multi-tenancy filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(CustomerMetrics.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(CustomerMetrics.department_id == department_id)

    total = query.count()
    metrics = query.order_by(
        CustomerMetrics.year.desc(),
        CustomerMetrics.month.desc(),
        CustomerMetrics.region
    ).offset(skip).limit(limit).all()

    log_info(
        f"Get customer metrics list - user_id: {current_user.id}, year: {year}, month: {month}, "
        f"region: {region}, department_id: {department_id}, total: {total}",
        "customer_metrics"
    )

    return metrics


@router.get("/{metrics_id}", response_model=CustomerMetricsInDB)
def get_customer_metrics_by_id(
    metrics_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer metrics by ID"""
    metrics = check_metrics_access(db, metrics_id, current_user)

    log_info(f"Get customer metrics - user_id: {current_user.id}, metrics_id: {metrics_id}", "customer_metrics")

    return metrics


@router.post("/", response_model=CustomerMetricsInDB, status_code=status.HTTP_201_CREATED)
def create_customer_metrics(
    metrics_data: CustomerMetricsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new customer metrics

    - Department is auto-assigned from current_user (USER role)
    - MANAGER/ADMIN can specify department_id
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
        if metrics_data.department_id:
            department_id = metrics_data.department_id
        else:
            department_id = current_user.department_id

    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Check for duplicate (same year + month + region + department)
    existing = (
        db.query(CustomerMetrics)
        .filter(
            CustomerMetrics.year == metrics_data.year,
            CustomerMetrics.month == metrics_data.month,
            CustomerMetrics.region == metrics_data.region,
            CustomerMetrics.department_id == department_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer metrics for {metrics_data.year}-{metrics_data.month} in region '{metrics_data.region}' already exist"
        )

    # Calculate coverage if both ОКБ and АКБ are provided
    coverage_percent = None
    if metrics_data.total_customer_base and metrics_data.active_customer_base:
        if metrics_data.total_customer_base > 0:
            coverage_percent = Decimal(str(
                round((float(metrics_data.active_customer_base) / float(metrics_data.total_customer_base)) * 100, 2)
            ))

    # Create metrics
    new_metrics = CustomerMetrics(
        year=metrics_data.year,
        month=metrics_data.month,
        region=metrics_data.region,
        department_id=department_id,
        total_customer_base=metrics_data.total_customer_base,
        active_customer_base=metrics_data.active_customer_base,
        coverage_percent=coverage_percent,
        avg_check_regular=metrics_data.avg_check_regular,
        avg_check_network=metrics_data.avg_check_network,
        avg_check_new_clinics=metrics_data.avg_check_new_clinics,
        notes=metrics_data.notes,
        created_at=datetime.now()
    )

    db.add(new_metrics)
    db.commit()
    db.refresh(new_metrics)

    log_info(
        f"Create customer metrics - user_id: {current_user.id}, metrics_id: {new_metrics.id}, "
        f"year: {metrics_data.year}, month: {metrics_data.month}, region: {metrics_data.region}",
        "customer_metrics"
    )

    return new_metrics


@router.put("/{metrics_id}", response_model=CustomerMetricsInDB)
def update_customer_metrics(
    metrics_id: int,
    metrics_data: CustomerMetricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update customer metrics"""
    metrics = check_metrics_access(db, metrics_id, current_user)

    # Update fields
    update_fields = metrics_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(metrics, field, value)

    # Recalculate coverage if needed
    if metrics.total_customer_base and metrics.active_customer_base:
        if metrics.total_customer_base > 0:
            metrics.coverage_percent = Decimal(str(
                round((float(metrics.active_customer_base) / float(metrics.total_customer_base)) * 100, 2)
            ))

    metrics.updated_at = datetime.now()

    db.commit()
    db.refresh(metrics)

    log_info(
        f"Update customer metrics - user_id: {current_user.id}, metrics_id: {metrics_id}, updates: {update_fields}",
        "customer_metrics"
    )

    return metrics


@router.delete("/{metrics_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_metrics(
    metrics_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete customer metrics (ADMIN only)"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete customer metrics"
        )

    metrics = check_metrics_access(db, metrics_id, current_user)

    db.delete(metrics)
    db.commit()

    log_info(f"Delete customer metrics - user_id: {current_user.id}, metrics_id: {metrics_id}", "customer_metrics")
