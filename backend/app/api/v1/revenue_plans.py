"""
API endpoints for Revenue Planning Module
Handles revenue plans, versions, and workflow (Draft → In Review → Approved)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from decimal import Decimal

from app.db import get_db
from app.db.models import (
    User,
    UserRoleEnum,
    RevenuePlan,
    RevenuePlanVersion,
    RevenuePlanDetail,
    RevenuePlanStatusEnum,
    RevenueVersionStatusEnum,
)
from app.schemas import (
    RevenuePlanCreate,
    RevenuePlanUpdate,
    RevenuePlanInDB,
    RevenuePlanVersionCreate,
    RevenuePlanVersionUpdate,
    RevenuePlanVersionInDB,
)
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info
from app.services.cache import cache_service

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "revenue_plans"


def recalculate_plan_totals(db: Session, plan: RevenuePlan) -> None:
    """
    Recalculate total_planned_revenue for a revenue plan.
    Sums all approved version details.
    """
    # Get approved version
    approved_version = (
        db.query(RevenuePlanVersion)
        .filter(
            RevenuePlanVersion.plan_id == plan.id,
            RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
        )
        .first()
    )

    if not approved_version:
        plan.total_planned_revenue = Decimal("0")
        db.flush([plan])
        return

    # Sum all details from approved version
    total = (
        db.query(func.coalesce(func.sum(
            RevenuePlanDetail.month_01 + RevenuePlanDetail.month_02 +
            RevenuePlanDetail.month_03 + RevenuePlanDetail.month_04 +
            RevenuePlanDetail.month_05 + RevenuePlanDetail.month_06 +
            RevenuePlanDetail.month_07 + RevenuePlanDetail.month_08 +
            RevenuePlanDetail.month_09 + RevenuePlanDetail.month_10 +
            RevenuePlanDetail.month_11 + RevenuePlanDetail.month_12
        ), 0))
        .filter(RevenuePlanDetail.version_id == approved_version.id)
        .scalar()
    )

    plan.total_planned_revenue = Decimal(str(total))
    db.flush([plan])


def check_plan_access(db: Session, plan_id: int, user: User) -> RevenuePlan:
    """
    Check if user has access to revenue plan based on department.
    Raises 404 if plan not found or user lacks access.
    """
    plan = db.query(RevenuePlan).filter(RevenuePlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue plan with id {plan_id} not found"
        )

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if plan.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access revenue plans from your department"
            )

    return plan


# ============================================================================
# Revenue Plans Endpoints
# ============================================================================


@router.get("/", response_model=List[RevenuePlanInDB])
def get_revenue_plans(
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[RevenuePlanStatusEnum] = Query(None, description="Filter by status"),
    department_id: Optional[int] = Query(None, description="Filter by department (MANAGER/ADMIN only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get revenue plans with filtering

    - USER: Can only see plans from their own department
    - MANAGER/ADMIN: Can see plans from all departments or filter by department
    """
    query = db.query(RevenuePlan)

    # Apply filters
    if year:
        query = query.filter(RevenuePlan.year == year)
    if status:
        query = query.filter(RevenuePlan.status == status)

    # SECURITY: Multi-tenancy filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenuePlan.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(RevenuePlan.department_id == department_id)

    total = query.count()
    plans = query.order_by(RevenuePlan.year.desc(), RevenuePlan.created_at.desc()).offset(skip).limit(limit).all()

    log_info(
        "revenue_plans.get_list",
        user_id=current_user.id,
        filters={"year": year, "status": status, "department_id": department_id},
        total=total
    )

    return plans


@router.get("/{plan_id}", response_model=RevenuePlanInDB)
def get_revenue_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get revenue plan by ID"""
    plan = check_plan_access(db, plan_id, current_user)

    log_info("revenue_plans.get", user_id=current_user.id, plan_id=plan_id)

    return plan


@router.post("/", response_model=RevenuePlanInDB, status_code=status.HTTP_201_CREATED)
def create_revenue_plan(
    plan_data: RevenuePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new revenue plan

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
        if plan_data.department_id:
            department_id = plan_data.department_id
        else:
            department_id = current_user.department_id

    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Check for duplicate (same name + year + department)
    existing = (
        db.query(RevenuePlan)
        .filter(
            RevenuePlan.name == plan_data.name,
            RevenuePlan.year == plan_data.year,
            RevenuePlan.department_id == department_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Revenue plan '{plan_data.name}' for year {plan_data.year} already exists in this department"
        )

    # Create plan
    new_plan = RevenuePlan(
        name=plan_data.name,
        year=plan_data.year,
        department_id=department_id,
        revenue_stream_id=plan_data.revenue_stream_id,
        revenue_category_id=plan_data.revenue_category_id,
        description=plan_data.description,
        status=RevenuePlanStatusEnum.DRAFT,
        total_planned_revenue=Decimal("0"),
        created_by=current_user.id,
        created_at=datetime.now()
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info("revenue_plans.create", user_id=current_user.id, plan_id=new_plan.id, plan_name=new_plan.name)

    return new_plan


@router.put("/{plan_id}", response_model=RevenuePlanInDB)
def update_revenue_plan(
    plan_id: int,
    plan_data: RevenuePlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update revenue plan"""
    plan = check_plan_access(db, plan_id, current_user)

    # Only ADMIN/MANAGER can change status
    if plan_data.status and plan_data.status != plan.status:
        if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ADMIN or MANAGER can change plan status"
            )

    # Update fields
    update_fields = plan_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(plan, field, value)

    plan.updated_at = datetime.now()

    db.commit()
    db.refresh(plan)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info("revenue_plans.update", user_id=current_user.id, plan_id=plan_id, updates=update_fields)

    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete revenue plan (ADMIN only)"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete revenue plans"
        )

    plan = check_plan_access(db, plan_id, current_user)

    # Check if plan has approved versions
    has_approved = (
        db.query(RevenuePlanVersion)
        .filter(
            RevenuePlanVersion.plan_id == plan_id,
            RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
        )
        .first()
    )

    if has_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete revenue plan with approved versions. Archive it instead."
        )

    db.delete(plan)
    db.commit()

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info("revenue_plans.delete", user_id=current_user.id, plan_id=plan_id)


@router.post("/{plan_id}/approve", response_model=RevenuePlanInDB)
def approve_revenue_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve revenue plan (MANAGER/ADMIN only)
    Changes status from DRAFT → APPROVED
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or MANAGER can approve revenue plans"
        )

    plan = check_plan_access(db, plan_id, current_user)

    if plan.status == RevenuePlanStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Revenue plan is already approved"
        )

    plan.status = RevenuePlanStatusEnum.APPROVED
    plan.approved_by = current_user.id
    plan.approved_at = datetime.now()
    plan.updated_at = datetime.now()

    db.commit()
    db.refresh(plan)

    # Invalidate cache
    cache_service.delete_pattern(f"{CACHE_NAMESPACE}:*")

    log_info("revenue_plans.approve", user_id=current_user.id, plan_id=plan_id)

    return plan


# ============================================================================
# Revenue Plan Versions Endpoints
# ============================================================================


@router.get("/{plan_id}/versions", response_model=List[RevenuePlanVersionInDB])
def get_plan_versions(
    plan_id: int,
    status: Optional[RevenueVersionStatusEnum] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all versions for a revenue plan"""
    plan = check_plan_access(db, plan_id, current_user)

    query = db.query(RevenuePlanVersion).filter(RevenuePlanVersion.plan_id == plan_id)

    if status:
        query = query.filter(RevenuePlanVersion.status == status)

    versions = query.order_by(RevenuePlanVersion.version_number.desc()).all()

    log_info("revenue_plans.get_versions", user_id=current_user.id, plan_id=plan_id, count=len(versions))

    return versions


@router.post("/{plan_id}/versions", response_model=RevenuePlanVersionInDB, status_code=status.HTTP_201_CREATED)
def create_plan_version(
    plan_id: int,
    version_data: RevenuePlanVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new version for revenue plan
    Version number is auto-incremented
    """
    plan = check_plan_access(db, plan_id, current_user)

    # Override plan_id from URL
    version_data.plan_id = plan_id

    # Get next version number
    max_version = (
        db.query(func.coalesce(func.max(RevenuePlanVersion.version_number), 0))
        .filter(RevenuePlanVersion.plan_id == plan_id)
        .scalar()
    )
    next_version = max_version + 1

    # Create version
    new_version = RevenuePlanVersion(
        plan_id=plan_id,
        version_number=next_version,
        version_name=version_data.version_name or f"Version {next_version}",
        description=version_data.description,
        status=RevenueVersionStatusEnum.DRAFT,
        created_by=current_user.id,
        created_at=datetime.now()
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    log_info("revenue_plans.create_version", user_id=current_user.id, plan_id=plan_id, version_id=new_version.id)

    return new_version


@router.put("/{plan_id}/versions/{version_id}", response_model=RevenuePlanVersionInDB)
def update_plan_version(
    plan_id: int,
    version_id: int,
    version_data: RevenuePlanVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update revenue plan version"""
    plan = check_plan_access(db, plan_id, current_user)

    version = (
        db.query(RevenuePlanVersion)
        .filter(
            RevenuePlanVersion.id == version_id,
            RevenuePlanVersion.plan_id == plan_id
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found for plan {plan_id}"
        )

    # Only ADMIN/MANAGER can change status
    if version_data.status and version_data.status != version.status:
        if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only ADMIN or MANAGER can change version status"
            )

        # If approving, archive other approved versions
        if version_data.status == RevenueVersionStatusEnum.APPROVED:
            db.query(RevenuePlanVersion).filter(
                RevenuePlanVersion.plan_id == plan_id,
                RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED,
                RevenuePlanVersion.id != version_id
            ).update({"status": RevenueVersionStatusEnum.ARCHIVED})

    # Update fields
    update_fields = version_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(version, field, value)

    version.updated_at = datetime.now()

    db.commit()
    db.refresh(version)

    # Recalculate plan totals if version was approved
    if version.status == RevenueVersionStatusEnum.APPROVED:
        recalculate_plan_totals(db, plan)
        db.commit()

    log_info("revenue_plans.update_version", user_id=current_user.id, version_id=version_id, updates=update_fields)

    return version


@router.delete("/{plan_id}/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_version(
    plan_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete revenue plan version (ADMIN only)"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete versions"
        )

    plan = check_plan_access(db, plan_id, current_user)

    version = (
        db.query(RevenuePlanVersion)
        .filter(
            RevenuePlanVersion.id == version_id,
            RevenuePlanVersion.plan_id == plan_id
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found for plan {plan_id}"
        )

    if version.status == RevenueVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete approved version. Archive it instead."
        )

    db.delete(version)
    db.commit()

    log_info("revenue_plans.delete_version", user_id=current_user.id, version_id=version_id)
