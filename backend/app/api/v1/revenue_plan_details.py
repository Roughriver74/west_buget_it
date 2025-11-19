"""
API endpoints for Revenue Plan Details Module
Handles monthly revenue planning details with bulk operations
"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.db import get_db
from app.db.models import (
    User,
    UserRoleEnum,
    RevenuePlan,
    RevenuePlanVersion,
    RevenuePlanDetail,
    RevenueStream,
    RevenueCategory,
    RevenueVersionStatusEnum,
    SeasonalityCoefficient,
)
from app.schemas import (
    RevenuePlanDetailCreate,
    RevenuePlanDetailUpdate,
    RevenuePlanDetailInDB,
    RevenuePlanDetailBulkUpdate,
)
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info
from app.services.cache import cache_service
from app.core.config import settings

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "revenue_plan_details"


class BulkCreateRequest(BaseModel):
    """Request for bulk creating revenue plan details"""
    details: List[RevenuePlanDetailCreate]


class BulkUpdateRequest(BaseModel):
    """Request for bulk updating revenue plan details"""
    updates: List[RevenuePlanDetailBulkUpdate]


def check_version_access(db: Session, version_id: int, user: User) -> RevenuePlanVersion:
    """
    Check if user has access to revenue plan version based on department.
    Raises 404 if version not found or user lacks access.
    """
    version = (
        db.query(RevenuePlanVersion)
        .join(RevenuePlan, RevenuePlanVersion.plan_id == RevenuePlan.id)
        .filter(RevenuePlanVersion.id == version_id)
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan version with id {version_id} not found"
        )

    # Get plan to check department
    plan = version.plan_rel

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if plan.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access revenue plan details from your department"
            )

    return version


def recalculate_detail_total(detail: RevenuePlanDetail) -> None:
    """Calculate total for a revenue plan detail (sum of all months)"""
    total = (
        detail.month_01 + detail.month_02 + detail.month_03 + detail.month_04 +
        detail.month_05 + detail.month_06 + detail.month_07 + detail.month_08 +
        detail.month_09 + detail.month_10 + detail.month_11 + detail.month_12
    )
    detail.total = total


# ============================================================================
# Revenue Plan Details Endpoints
# ============================================================================


@router.get("/", response_model=List[RevenuePlanDetailInDB])
def get_revenue_plan_details(
    version_id: int = Query(..., description="Version ID to get details for"),
    revenue_stream_id: Optional[int] = Query(None, description="Filter by revenue stream"),
    revenue_category_id: Optional[int] = Query(None, description="Filter by revenue category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.REVENUE_PLAN_DETAILS_PAGE_SIZE, ge=1, le=settings.MAX_REVENUE_PLAN_DETAILS_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get revenue plan details for a specific version

    - USER: Can only see details from their own department
    - MANAGER/ADMIN: Can see details from all departments
    """
    version = check_version_access(db, version_id, current_user)

    query = db.query(RevenuePlanDetail).filter(RevenuePlanDetail.version_id == version_id)

    # Apply filters
    if revenue_stream_id:
        query = query.filter(RevenuePlanDetail.revenue_stream_id == revenue_stream_id)
    if revenue_category_id:
        query = query.filter(RevenuePlanDetail.revenue_category_id == revenue_category_id)

    total = query.count()
    details = query.order_by(
        RevenuePlanDetail.revenue_stream_id,
        RevenuePlanDetail.revenue_category_id
    ).offset(skip).limit(limit).all()

    log_info(
        f"Get revenue plan details list - user_id: {current_user.id}, version_id: {version_id}, total: {total}",
        "revenue_plan_details"
    )

    return details


@router.get("/{detail_id}", response_model=RevenuePlanDetailInDB)
def get_revenue_plan_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get revenue plan detail by ID"""
    detail = (
        db.query(RevenuePlanDetail)
        .join(RevenuePlanVersion, RevenuePlanDetail.version_id == RevenuePlanVersion.id)
        .join(RevenuePlan, RevenuePlanVersion.plan_id == RevenuePlan.id)
        .filter(RevenuePlanDetail.id == detail_id)
        .first()
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan detail with id {detail_id} not found"
        )

    # Check access
    version = detail.version_rel
    plan = version.plan_rel

    if current_user.role == UserRoleEnum.USER:
        if plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access revenue plan details from your department"
            )

    log_info(f"Get revenue plan detail - user_id: {current_user.id}, detail_id: {detail_id}", "revenue_plan_details")

    return detail


@router.post("/", response_model=RevenuePlanDetailInDB, status_code=status.HTTP_201_CREATED)
def create_revenue_plan_detail(
    detail_data: RevenuePlanDetailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new revenue plan detail

    - Department is auto-assigned from plan
    - Validates that version exists and is editable (DRAFT)
    """
    version = check_version_access(db, detail_data.version_id, current_user)

    # Check if version is editable
    if version.status != RevenueVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit revenue plan details in {version.status} status. Only DRAFT versions are editable."
        )

    # Get department from plan
    plan = version.plan_rel
    department_id = plan.department_id

    # Validate revenue stream/category belong to same department
    if detail_data.revenue_stream_id:
        stream = db.query(RevenueStream).filter(RevenueStream.id == detail_data.revenue_stream_id).first()
        if not stream or stream.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revenue stream not found or belongs to different department"
            )

    if detail_data.revenue_category_id:
        category = db.query(RevenueCategory).filter(RevenueCategory.id == detail_data.revenue_category_id).first()
        if not category or category.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revenue category not found or belongs to different department"
            )

    # Check for duplicate (same version + stream + category)
    existing = (
        db.query(RevenuePlanDetail)
        .filter(
            RevenuePlanDetail.version_id == detail_data.version_id,
            RevenuePlanDetail.revenue_stream_id == detail_data.revenue_stream_id,
            RevenuePlanDetail.revenue_category_id == detail_data.revenue_category_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Revenue plan detail already exists for this stream/category combination"
        )

    # Create detail
    new_detail = RevenuePlanDetail(
        version_id=detail_data.version_id,
        department_id=department_id,
        revenue_stream_id=detail_data.revenue_stream_id,
        revenue_category_id=detail_data.revenue_category_id,
        month_01=detail_data.month_01,
        month_02=detail_data.month_02,
        month_03=detail_data.month_03,
        month_04=detail_data.month_04,
        month_05=detail_data.month_05,
        month_06=detail_data.month_06,
        month_07=detail_data.month_07,
        month_08=detail_data.month_08,
        month_09=detail_data.month_09,
        month_10=detail_data.month_10,
        month_11=detail_data.month_11,
        month_12=detail_data.month_12,
        created_at=datetime.now()
    )

    # Calculate total
    recalculate_detail_total(new_detail)

    db.add(new_detail)
    db.commit()
    db.refresh(new_detail)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(f"Create revenue plan detail - user_id: {current_user.id}, detail_id: {new_detail.id}", "revenue_plan_details")

    return new_detail


@router.post("/bulk", response_model=List[RevenuePlanDetailInDB], status_code=status.HTTP_201_CREATED)
def bulk_create_revenue_plan_details(
    request: BulkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk create revenue plan details
    Useful for importing data or creating initial plan structure
    """
    if not request.details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one detail is required"
        )

    # Validate all details belong to same version
    version_ids = set(detail.version_id for detail in request.details)
    if len(version_ids) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All details must belong to the same version"
        )

    version_id = list(version_ids)[0]
    version = check_version_access(db, version_id, current_user)

    # Check if version is editable
    if version.status != RevenueVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit revenue plan details in {version.status} status. Only DRAFT versions are editable."
        )

    plan = version.plan_rel
    department_id = plan.department_id

    created_details = []

    for detail_data in request.details:
        # Check for duplicate
        existing = (
            db.query(RevenuePlanDetail)
            .filter(
                RevenuePlanDetail.version_id == version_id,
                RevenuePlanDetail.revenue_stream_id == detail_data.revenue_stream_id,
                RevenuePlanDetail.revenue_category_id == detail_data.revenue_category_id
            )
            .first()
        )

        if existing:
            # Skip duplicates
            continue

        # Create detail
        new_detail = RevenuePlanDetail(
            version_id=version_id,
            department_id=department_id,
            revenue_stream_id=detail_data.revenue_stream_id,
            revenue_category_id=detail_data.revenue_category_id,
            month_01=detail_data.month_01,
            month_02=detail_data.month_02,
            month_03=detail_data.month_03,
            month_04=detail_data.month_04,
            month_05=detail_data.month_05,
            month_06=detail_data.month_06,
            month_07=detail_data.month_07,
            month_08=detail_data.month_08,
            month_09=detail_data.month_09,
            month_10=detail_data.month_10,
            month_11=detail_data.month_11,
            month_12=detail_data.month_12,
            created_at=datetime.now()
        )

        recalculate_detail_total(new_detail)
        db.add(new_detail)
        created_details.append(new_detail)

    db.commit()

    # Refresh all created details
    for detail in created_details:
        db.refresh(detail)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(f"Bulk create revenue plan details - user_id: {current_user.id}, count: {len(created_details)}", "revenue_plan_details")

    return created_details


@router.put("/{detail_id}", response_model=RevenuePlanDetailInDB)
def update_revenue_plan_detail(
    detail_id: int,
    detail_data: RevenuePlanDetailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update revenue plan detail"""
    detail = (
        db.query(RevenuePlanDetail)
        .join(RevenuePlanVersion, RevenuePlanDetail.version_id == RevenuePlanVersion.id)
        .join(RevenuePlan, RevenuePlanVersion.plan_id == RevenuePlan.id)
        .filter(RevenuePlanDetail.id == detail_id)
        .first()
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan detail with id {detail_id} not found"
        )

    # Check access
    version = detail.version_rel
    plan = version.plan_rel

    if current_user.role == UserRoleEnum.USER:
        if plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update revenue plan details from your department"
            )

    # Check if version is editable
    if version.status != RevenueVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit revenue plan details in {version.status} status. Only DRAFT versions are editable."
        )

    # Update fields
    update_fields = detail_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        if value is not None:
            setattr(detail, field, value)

    # Recalculate total
    recalculate_detail_total(detail)
    detail.updated_at = datetime.now()

    db.commit()
    db.refresh(detail)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(f"Update revenue plan detail - user_id: {current_user.id}, detail_id: {detail_id}", "revenue_plan_details")

    return detail


@router.put("/bulk/update", response_model=List[RevenuePlanDetailInDB])
def bulk_update_revenue_plan_details(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk update revenue plan details
    Useful for updating multiple months at once
    """
    if not request.updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one update is required"
        )

    updated_details = []

    for update_item in request.updates:
        detail = db.query(RevenuePlanDetail).filter(RevenuePlanDetail.id == update_item.id).first()

        if not detail:
            log_error(
                f"Bulk update: detail not found - user_id: {current_user.id}, detail_id: {update_item.id}",
                "revenue_plan_details"
            )
            continue

        # Check access
        version = detail.version_rel
        plan = version.plan_rel

        if current_user.role == UserRoleEnum.USER:
            if plan.department_id != current_user.department_id:
                log_error(
                    f"Bulk update: access denied - user_id: {current_user.id}, detail_id: {detail.id}",
                    "revenue_plan_details"
                )
                continue

        # Check if version is editable
        if version.status != RevenueVersionStatusEnum.DRAFT:
            log_error(
                f"Bulk update: version not editable - user_id: {current_user.id}, detail_id: {detail.id}, version_status: {version.status}",
                "revenue_plan_details"
            )
            continue

        # Apply updates
        for field, value in update_item.updates.items():
            if hasattr(detail, field):
                setattr(detail, field, value)

        # Recalculate total
        recalculate_detail_total(detail)
        detail.updated_at = datetime.now()

        updated_details.append(detail)

    db.commit()

    # Refresh all updated details
    for detail in updated_details:
        db.refresh(detail)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(f"Bulk update revenue plan details - user_id: {current_user.id}, count: {len(updated_details)}", "revenue_plan_details")

    return updated_details


@router.delete("/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue_plan_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete revenue plan detail"""
    detail = (
        db.query(RevenuePlanDetail)
        .join(RevenuePlanVersion, RevenuePlanDetail.version_id == RevenuePlanVersion.id)
        .join(RevenuePlan, RevenuePlanVersion.plan_id == RevenuePlan.id)
        .filter(RevenuePlanDetail.id == detail_id)
        .first()
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan detail with id {detail_id} not found"
        )

    # Check access
    version = detail.version_rel
    plan = version.plan_rel

    if current_user.role == UserRoleEnum.USER:
        if plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete revenue plan details from your department"
            )

    # Check if version is editable
    if version.status != RevenueVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete revenue plan details in {version.status} status. Only DRAFT versions are editable."
        )

    db.delete(detail)
    db.commit()

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(f"Delete revenue plan detail - user_id: {current_user.id}, detail_id: {detail_id}", "revenue_plan_details")


@router.get("/version/{version_id}/summary")
def get_version_summary(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary statistics for a revenue plan version
    Returns totals by month, stream, and category
    """
    version = check_version_access(db, version_id, current_user)

    # Get all details for this version
    details = (
        db.query(RevenuePlanDetail)
        .filter(RevenuePlanDetail.version_id == version_id)
        .all()
    )

    if not details:
        return {
            "version_id": version_id,
            "total_revenue": 0,
            "monthly_totals": {f"month_{i:02d}": 0 for i in range(1, 13)},
            "by_stream": [],
            "by_category": []
        }

    # Calculate monthly totals
    monthly_totals = {f"month_{i:02d}": Decimal("0") for i in range(1, 13)}
    for detail in details:
        for i in range(1, 13):
            month_field = f"month_{i:02d}"
            monthly_totals[month_field] += getattr(detail, month_field)

    # Calculate total revenue
    total_revenue = sum(monthly_totals.values())

    # Group by stream
    stream_totals = {}
    for detail in details:
        stream_id = detail.revenue_stream_id or 0
        if stream_id not in stream_totals:
            stream_totals[stream_id] = Decimal("0")
        stream_totals[stream_id] += detail.total or Decimal("0")

    # Group by category
    category_totals = {}
    for detail in details:
        category_id = detail.revenue_category_id or 0
        if category_id not in category_totals:
            category_totals[category_id] = Decimal("0")
        category_totals[category_id] += detail.total or Decimal("0")

    log_info(f"Get version summary - user_id: {current_user.id}, version_id: {version_id}", "revenue_plan_details")

    return {
        "version_id": version_id,
        "total_revenue": float(total_revenue),
        "monthly_totals": {k: float(v) for k, v in monthly_totals.items()},
        "by_stream": [{"stream_id": k, "total": float(v)} for k, v in stream_totals.items()],
        "by_category": [{"category_id": k, "total": float(v)} for k, v in category_totals.items()]
    }


class ApplySeasonalityRequest(BaseModel):
    """Request for applying seasonality coefficients to a plan detail"""
    detail_id: int
    seasonality_coefficient_id: int
    annual_target: Decimal


@router.post("/apply-seasonality", response_model=RevenuePlanDetailInDB)
def apply_seasonality_coefficients(
    request: ApplySeasonalityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Apply seasonality coefficients to distribute annual revenue target across 12 months

    **Algorithm:**
    - Get seasonality coefficients (12 monthly coefficients that average to ~1.0)
    - Calculate monthly values: month_value = annual_target * (coefficient / 12)
    - Update revenue plan detail with calculated monthly values

    **Example:**
    - Annual target: 120,000
    - Coefficient for January: 1.2 (20% above average)
    - January value: 120,000 * (1.2 / 12) = 12,000

    **Requirements:**
    - Plan detail must exist and be editable (DRAFT status)
    - Seasonality coefficient must exist and belong to same department
    - User must have access to the plan detail
    """
    # Get detail and check access
    detail = db.query(RevenuePlanDetail).filter(RevenuePlanDetail.id == request.detail_id).first()

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan detail with id {request.detail_id} not found"
        )

    # Check version access
    version = check_version_access(db, detail.version_id, current_user)

    # Check if version is editable
    if version.status != RevenueVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit revenue plan details in {version.status} status. Only DRAFT versions are editable."
        )

    # Get seasonality coefficient
    coefficient = db.query(SeasonalityCoefficient).filter(
        SeasonalityCoefficient.id == request.seasonality_coefficient_id
    ).first()

    if not coefficient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seasonality coefficient with id {request.seasonality_coefficient_id} not found"
        )

    # Check department match
    if coefficient.department_id != detail.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seasonality coefficient must belong to the same department as the plan detail"
        )

    # Validate annual target
    if request.annual_target <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Annual target must be greater than zero"
        )

    # Apply seasonality coefficients
    # Formula: monthly_value = annual_target * (coefficient / 12)
    detail.month_01 = request.annual_target * (coefficient.coeff_month_01 / Decimal("12"))
    detail.month_02 = request.annual_target * (coefficient.coeff_month_02 / Decimal("12"))
    detail.month_03 = request.annual_target * (coefficient.coeff_month_03 / Decimal("12"))
    detail.month_04 = request.annual_target * (coefficient.coeff_month_04 / Decimal("12"))
    detail.month_05 = request.annual_target * (coefficient.coeff_month_05 / Decimal("12"))
    detail.month_06 = request.annual_target * (coefficient.coeff_month_06 / Decimal("12"))
    detail.month_07 = request.annual_target * (coefficient.coeff_month_07 / Decimal("12"))
    detail.month_08 = request.annual_target * (coefficient.coeff_month_08 / Decimal("12"))
    detail.month_09 = request.annual_target * (coefficient.coeff_month_09 / Decimal("12"))
    detail.month_10 = request.annual_target * (coefficient.coeff_month_10 / Decimal("12"))
    detail.month_11 = request.annual_target * (coefficient.coeff_month_11 / Decimal("12"))
    detail.month_12 = request.annual_target * (coefficient.coeff_month_12 / Decimal("12"))

    # Recalculate total
    recalculate_detail_total(detail)

    detail.updated_at = datetime.now()

    db.commit()
    db.refresh(detail)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info(
        f"Apply seasonality coefficients - user_id: {current_user.id}, detail_id: {request.detail_id}, "
        f"coefficient_id: {request.seasonality_coefficient_id}, annual_target: {request.annual_target}",
        "revenue_plan_details"
    )

    return detail
