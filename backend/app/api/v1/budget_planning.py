"""
API endpoints for Budget Planning 2026 Module
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
    BudgetVersion,
    BudgetScenario,
    BudgetPlanDetail,
    BudgetApprovalLog,
    BudgetCategory,
    BudgetVersionStatusEnum,
    BudgetScenarioTypeEnum,
    ExpenseTypeEnum,
    ApprovalActionEnum,
)
from app.schemas import (
    # Scenarios
    BudgetScenarioCreate,
    BudgetScenarioUpdate,
    BudgetScenarioInDB,
    # Versions
    BudgetVersionCreate,
    BudgetVersionUpdate,
    BudgetVersionInDB,
    BudgetVersionWithDetails,
    # Plan Details
    BudgetPlanDetailCreate,
    BudgetPlanDetailUpdate,
    BudgetPlanDetailInDB,
    # Approval Log
    BudgetApprovalLogCreate,
    BudgetApprovalLogInDB,
    # Calculator
    CalculateByAverageRequest,
    CalculateByGrowthRequest,
    CalculateByDriverRequest,
    CalculateBySeasonalRequest,
    CalculationResult,
    BaselineSummary,
    VersionComparison,
    VersionComparisonResult,
    # Approval
    SetApprovalsRequest,
)
from app.utils.auth import get_current_active_user
from app.services.budget_calculator import BudgetCalculator

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def recalculate_version_totals(db: Session, version: BudgetVersion) -> None:
    """Recalculate cached totals for a budget version."""
    totals = (
        db.query(
            func.coalesce(func.sum(BudgetPlanDetail.planned_amount), 0).label("amount"),
            BudgetPlanDetail.type,
        )
        .filter(BudgetPlanDetail.version_id == version.id)
        .group_by(BudgetPlanDetail.type)
        .all()
    )

    total_amount = Decimal("0")
    total_capex = Decimal("0")
    total_opex = Decimal("0")

    for amount, detail_type in totals:
        amount = Decimal(amount)
        total_amount += amount
        if detail_type == ExpenseTypeEnum.CAPEX:
            total_capex += amount
        else:
            total_opex += amount

    version.total_amount = total_amount
    version.total_capex = total_capex
    version.total_opex = total_opex
    db.flush([version])


# ============================================================================
# Budget Scenarios Endpoints
# ============================================================================


@router.get("/scenarios", response_model=List[BudgetScenarioInDB])
def get_scenarios(
    year: Optional[int] = Query(None, description="Filter by year"),
    scenario_type: Optional[BudgetScenarioTypeEnum] = Query(None, description="Filter by scenario type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget scenarios"""
    query = db.query(BudgetScenario)

    # Apply filters
    if year:
        query = query.filter(BudgetScenario.year == year)
    if scenario_type:
        query = query.filter(BudgetScenario.scenario_type == scenario_type)
    if is_active is not None:
        query = query.filter(BudgetScenario.is_active == is_active)

    # Multi-tenancy: filter by department
    query = query.filter(BudgetScenario.department_id == current_user.department_id)

    scenarios = query.order_by(BudgetScenario.year.desc(), BudgetScenario.scenario_type).all()
    return scenarios


@router.get("/scenarios/{scenario_id}", response_model=BudgetScenarioInDB)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific scenario by ID"""
    scenario = db.query(BudgetScenario).filter(
        BudgetScenario.id == scenario_id,
        BudgetScenario.department_id == current_user.department_id
    ).first()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with id {scenario_id} not found"
        )

    return scenario


@router.post("/scenarios", response_model=BudgetScenarioInDB, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario: BudgetScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new budget scenario"""
    # Auto-assign department_id from current_user
    scenario_data = scenario.model_dump()
    scenario_data['department_id'] = current_user.department_id
    scenario_data['created_by'] = current_user.username

    # Create scenario
    db_scenario = BudgetScenario(**scenario_data)
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)

    return db_scenario


@router.put("/scenarios/{scenario_id}", response_model=BudgetScenarioInDB)
def update_scenario(
    scenario_id: int,
    scenario_update: BudgetScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a scenario"""
    db_scenario = db.query(BudgetScenario).filter(
        BudgetScenario.id == scenario_id,
        BudgetScenario.department_id == current_user.department_id
    ).first()

    if not db_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with id {scenario_id} not found"
        )

    # Update fields
    update_data = scenario_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_scenario, field, value)

    db.commit()
    db.refresh(db_scenario)

    return db_scenario


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a scenario"""
    db_scenario = db.query(BudgetScenario).filter(
        BudgetScenario.id == scenario_id,
        BudgetScenario.department_id == current_user.department_id
    ).first()

    if not db_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with id {scenario_id} not found"
        )

    # Check if scenario is used by any versions
    versions_count = db.query(BudgetVersion).filter(
        BudgetVersion.scenario_id == scenario_id
    ).count()

    if versions_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete scenario - it is used by {versions_count} version(s)"
        )

    db.delete(db_scenario)
    db.commit()

    return None


# ============================================================================
# Budget Versions Endpoints
# ============================================================================


@router.get("/versions", response_model=List[BudgetVersionInDB])
def get_versions(
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[BudgetVersionStatusEnum] = Query(None, description="Filter by status"),
    scenario_id: Optional[int] = Query(None, description="Filter by scenario"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget versions"""
    query = db.query(BudgetVersion)

    # Apply filters
    if year:
        query = query.filter(BudgetVersion.year == year)
    if status:
        query = query.filter(BudgetVersion.status == status)
    if scenario_id:
        query = query.filter(BudgetVersion.scenario_id == scenario_id)

    # Multi-tenancy
    query = query.filter(BudgetVersion.department_id == current_user.department_id)

    versions = query.order_by(
        BudgetVersion.year.desc(),
        BudgetVersion.version_number.desc()
    ).all()

    return versions


@router.get("/versions/{version_id}", response_model=BudgetVersionWithDetails)
def get_version(
    version_id: int,
    include_details: bool = Query(True, description="Include plan details"),
    include_approval_logs: bool = Query(True, description="Include approval logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific version with optional details"""
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Convert to dict to add related data
    version_dict = {
        **BudgetVersionInDB.model_validate(version).model_dump(),
        "plan_details": [],
        "approval_logs": [],
        "scenario": None
    }

    # Load details if requested
    if include_details:
        details = db.query(BudgetPlanDetail).filter(
            BudgetPlanDetail.version_id == version_id
        ).all()
        version_dict["plan_details"] = [BudgetPlanDetailInDB.model_validate(d) for d in details]

    # Load approval logs if requested
    if include_approval_logs:
        logs = db.query(BudgetApprovalLog).filter(
            BudgetApprovalLog.version_id == version_id
        ).order_by(BudgetApprovalLog.iteration_number).all()
        version_dict["approval_logs"] = [BudgetApprovalLogInDB.model_validate(log) for log in logs]

    # Load scenario
    if version.scenario_id:
        scenario = db.query(BudgetScenario).filter(
            BudgetScenario.id == version.scenario_id
        ).first()
        if scenario:
            version_dict["scenario"] = BudgetScenarioInDB.model_validate(scenario)

    return BudgetVersionWithDetails(**version_dict)


@router.post("/versions", response_model=BudgetVersionInDB, status_code=status.HTTP_201_CREATED)
def create_version(
    version: BudgetVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new budget version"""
    # Auto-increment version number for the year
    max_version = db.query(func.max(BudgetVersion.version_number)).filter(
        BudgetVersion.year == version.year,
        BudgetVersion.department_id == current_user.department_id
    ).scalar()

    version_number = (max_version or 0) + 1

    # Extract extra fields that are not in the model
    copy_from_version_id = version.copy_from_version_id
    auto_calculate = version.auto_calculate

    # Create version with auto-assigned department_id
    version_data = version.model_dump(exclude={'copy_from_version_id', 'auto_calculate'})
    version_data['department_id'] = current_user.department_id
    version_data['version_number'] = version_number
    version_data['created_by'] = current_user.username

    db_version = BudgetVersion(**version_data)
    db.add(db_version)
    db.flush()  # Get the ID without committing

    # Copy from existing version if requested
    if copy_from_version_id:
        source_version = db.query(BudgetVersion).filter(
            BudgetVersion.id == copy_from_version_id,
            BudgetVersion.department_id == current_user.department_id
        ).first()

        if source_version:
            # Copy plan details
            source_details = db.query(BudgetPlanDetail).filter(
                BudgetPlanDetail.version_id == copy_from_version_id
            ).all()

            for detail in source_details:
                new_detail = BudgetPlanDetail(
                    version_id=db_version.id,
                    month=detail.month,
                    category_id=detail.category_id,
                    subcategory=detail.subcategory,
                    planned_amount=detail.planned_amount,
                    type=detail.type,
                    calculation_method=detail.calculation_method,
                    calculation_params=detail.calculation_params,
                    business_driver=detail.business_driver,
                    justification=detail.justification,
                    based_on_year=detail.based_on_year,
                    based_on_avg=detail.based_on_avg,
                    based_on_total=detail.based_on_total,
                    growth_rate=detail.growth_rate,
                )
                db.add(new_detail)

            # Copy totals
            db_version.total_amount = source_version.total_amount
            db_version.total_capex = source_version.total_capex
            db_version.total_opex = source_version.total_opex

    db.commit()
    db.refresh(db_version)

    return db_version


@router.put("/versions/{version_id}", response_model=BudgetVersionInDB)
def update_version(
    version_id: int,
    version_update: BudgetVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a version"""
    db_version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not db_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Update fields
    update_data = version_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_version, field, value)

    db_version.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_version)

    return db_version


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a version (and all its details via cascade)"""
    db_version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not db_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Don't allow deletion of approved versions
    if db_version.status == BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete approved version"
        )

    db.delete(db_version)
    db.commit()

    return None


# ============================================================================
# Budget Plan Details Endpoints
# ============================================================================


@router.get("/plan-details", response_model=List[BudgetPlanDetailInDB])
def get_plan_details(
    version_id: Optional[int] = Query(None, description="Filter by version ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget plan details with optional filters"""
    query = db.query(BudgetPlanDetail)

    # Apply filters
    if version_id:
        query = query.filter(BudgetPlanDetail.version_id == version_id)
    if category_id:
        query = query.filter(BudgetPlanDetail.category_id == category_id)
    if month:
        query = query.filter(BudgetPlanDetail.month == month)

    # Multi-tenancy: filter by department through version
    query = query.join(BudgetVersion).filter(
        BudgetVersion.department_id == current_user.department_id
    )

    details = query.order_by(
        BudgetPlanDetail.version_id,
        BudgetPlanDetail.month,
        BudgetPlanDetail.category_id
    ).all()

    return details


@router.get("/plan-details/{detail_id}", response_model=BudgetPlanDetailInDB)
def get_plan_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific plan detail by ID"""
    detail = db.query(BudgetPlanDetail).join(BudgetVersion).filter(
        BudgetPlanDetail.id == detail_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan detail with id {detail_id} not found"
        )

    return detail


@router.post("/plan-details", response_model=BudgetPlanDetailInDB, status_code=status.HTTP_201_CREATED)
def create_plan_detail(
    detail: BudgetPlanDetailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new plan detail"""
    # Verify version exists and belongs to user's department
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == detail.version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {detail.version_id} not found"
        )

    # Don't allow editing approved versions
    if version.status == BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit approved version"
        )

    # Verify category exists
    category = db.query(BudgetCategory).filter(
        BudgetCategory.id == detail.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {detail.category_id} not found"
        )

    # Create new detail
    db_detail = BudgetPlanDetail(**detail.model_dump())
    db.add(db_detail)
    db.flush()

    recalculate_version_totals(db, version)
    db.commit()
    db.refresh(db_detail)
    db.refresh(version)

    return db_detail


@router.put("/plan-details/{detail_id}", response_model=BudgetPlanDetailInDB)
def update_plan_detail(
    detail_id: int,
    detail: BudgetPlanDetailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a plan detail"""
    # Get detail with department check
    db_detail = db.query(BudgetPlanDetail).join(BudgetVersion).filter(
        BudgetPlanDetail.id == detail_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not db_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan detail with id {detail_id} not found"
        )

    # Check version status
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == db_detail.version_id
    ).first()

    if version.status == BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit approved version"
        )

    # Update fields
    update_data = detail.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_detail, field, value)

    db.flush()

    recalculate_version_totals(db, version)
    db.commit()
    db.refresh(db_detail)
    db.refresh(version)

    return db_detail


@router.delete("/plan-details/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a plan detail"""
    # Get detail with department check
    db_detail = db.query(BudgetPlanDetail).join(BudgetVersion).filter(
        BudgetPlanDetail.id == detail_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not db_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan detail with id {detail_id} not found"
        )

    # Check version status
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == db_detail.version_id
    ).first()

    if version.status == BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete from approved version"
        )

    db.delete(db_detail)
    db.flush()

    recalculate_version_totals(db, version)
    db.commit()
    db.refresh(version)

    return None


# ============================================================================
# Version Approval Workflow Endpoints
# ============================================================================


@router.post("/versions/{version_id}/submit", response_model=BudgetVersionInDB)
def submit_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit version for approval (DRAFT -> IN_REVIEW)"""
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only DRAFT versions can be submitted
    if version.status != BudgetVersionStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit version with status {version.status}. Only DRAFT versions can be submitted."
        )

    # Check if version has any plan details
    details_count = db.query(func.count(BudgetPlanDetail.id)).filter(
        BudgetPlanDetail.version_id == version_id
    ).scalar()

    if details_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit empty version. Please add budget details first."
        )

    # Update status and metadata
    version.status = BudgetVersionStatusEnum.IN_REVIEW
    version.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(version)

    # Determine iteration number (append to existing history if present)
    max_iteration = db.query(func.max(BudgetApprovalLog.iteration_number)).filter(
        BudgetApprovalLog.version_id == version_id
    ).scalar() or 0

    # Create approval log entry
    log_entry = BudgetApprovalLog(
        version_id=version_id,
        iteration_number=max_iteration + 1,
        action=ApprovalActionEnum.SUBMITTED,
        reviewer_name=current_user.username,
        reviewer_role=current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        comments=f"Version submitted for approval by {current_user.username}",
        decision_date=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

    return version


@router.post("/versions/{version_id}/approve", response_model=BudgetVersionInDB)
def approve_version(
    version_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Approve a submitted version (IN_REVIEW|REVISION_REQUESTED -> APPROVED)"""
    # Only ADMIN and MANAGER can approve
    from app.db.models import UserRoleEnum
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER users can approve budget versions"
        )

    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only IN_REVIEW or REVISION_REQUESTED versions can be approved
    if version.status not in [BudgetVersionStatusEnum.IN_REVIEW, BudgetVersionStatusEnum.REVISION_REQUESTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve version with status {version.status}"
        )

    # Get current iteration number
    max_iteration = db.query(func.max(BudgetApprovalLog.iteration_number)).filter(
        BudgetApprovalLog.version_id == version_id
    ).scalar() or 0

    # Update status
    version.status = BudgetVersionStatusEnum.APPROVED
    version.approved_at = datetime.utcnow()
    version.approved_by = current_user.username
    db.commit()
    db.refresh(version)

    # Create approval log entry
    log_entry = BudgetApprovalLog(
        version_id=version_id,
        iteration_number=max_iteration + 1,
        action=ApprovalActionEnum.APPROVED,
        reviewer_name=current_user.username,
        reviewer_role=current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        comments=comments or f"Version approved by {current_user.username}",
        decision_date=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

    return version


@router.post("/versions/{version_id}/reject", response_model=BudgetVersionInDB)
def reject_version(
    version_id: int,
    comments: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reject a submitted version (IN_REVIEW|REVISION_REQUESTED -> REJECTED)"""
    # Only ADMIN and MANAGER can reject
    from app.db.models import UserRoleEnum
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER users can reject budget versions"
        )

    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only IN_REVIEW or REVISION_REQUESTED versions can be rejected
    if version.status not in [BudgetVersionStatusEnum.IN_REVIEW, BudgetVersionStatusEnum.REVISION_REQUESTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject version with status {version.status}"
        )

    # Get current iteration number
    max_iteration = db.query(func.max(BudgetApprovalLog.iteration_number)).filter(
        BudgetApprovalLog.version_id == version_id
    ).scalar() or 0

    # Update status
    version.status = BudgetVersionStatusEnum.REJECTED
    version.approved_at = None
    version.approved_by = None
    db.commit()
    db.refresh(version)

    # Create approval log entry
    log_entry = BudgetApprovalLog(
        version_id=version_id,
        iteration_number=max_iteration + 1,
        action=ApprovalActionEnum.REJECTED,
        reviewer_name=current_user.username,
        reviewer_role=current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        comments=comments,
        decision_date=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

    return version


@router.post("/versions/{version_id}/request-changes", response_model=BudgetVersionInDB)
def request_changes(
    version_id: int,
    comments: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Request changes to a submitted version (IN_REVIEW -> REVISION_REQUESTED)"""
    # Only ADMIN and MANAGER can request changes
    from app.db.models import UserRoleEnum
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER users can request changes to budget versions"
        )

    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only IN_REVIEW versions can have changes requested
    if version.status != BudgetVersionStatusEnum.IN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot request changes for version with status {version.status}"
        )

    # Get current iteration number
    max_iteration = db.query(func.max(BudgetApprovalLog.iteration_number)).filter(
        BudgetApprovalLog.version_id == version_id
    ).scalar() or 0

    # Update status
    version.status = BudgetVersionStatusEnum.REVISION_REQUESTED
    db.commit()
    db.refresh(version)

    # Create approval log entry
    log_entry = BudgetApprovalLog(
        version_id=version_id,
        iteration_number=max_iteration + 1,
        action=ApprovalActionEnum.REVISION_REQUESTED,
        reviewer_name=current_user.username,
        reviewer_role=current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        comments=comments,
        decision_date=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

    return version


@router.post("/versions/{version_id}/set-approvals", response_model=BudgetVersionInDB)
def set_custom_approvals(
    version_id: int,
    approvals: SetApprovalsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set custom approval checkboxes for presentation (Manager, CFO, 3 Founders)"""
    # Only ADMIN and MANAGER can update approvals
    from app.db.models import UserRoleEnum
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER users can set approvals"
        )

    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Update approval checkboxes with timestamps
    now = datetime.utcnow()

    if approvals.manager_approved is not None:
        version.manager_approved = approvals.manager_approved
        if approvals.manager_approved:
            version.manager_approved_at = now
        else:
            version.manager_approved_at = None

    if approvals.cfo_approved is not None:
        version.cfo_approved = approvals.cfo_approved
        if approvals.cfo_approved:
            version.cfo_approved_at = now
        else:
            version.cfo_approved_at = None

    if approvals.founder1_approved is not None:
        version.founder1_approved = approvals.founder1_approved
        if approvals.founder1_approved:
            version.founder1_approved_at = now
        else:
            version.founder1_approved_at = None

    if approvals.founder2_approved is not None:
        version.founder2_approved = approvals.founder2_approved
        if approvals.founder2_approved:
            version.founder2_approved_at = now
        else:
            version.founder2_approved_at = None

    if approvals.founder3_approved is not None:
        version.founder3_approved = approvals.founder3_approved
        if approvals.founder3_approved:
            version.founder3_approved_at = now
        else:
            version.founder3_approved_at = None

    db.commit()
    db.refresh(version)

    return version


# ============================================================================
# Version Comparison Endpoints
# ============================================================================


@router.get("/versions/compare", response_model=VersionComparisonResult)
def compare_versions(
    v1: int = Query(..., description="First version ID"),
    v2: int = Query(..., description="Second version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Compare two budget versions"""
    # Get both versions
    version1 = db.query(BudgetVersion).filter(
        BudgetVersion.id == v1,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    version2 = db.query(BudgetVersion).filter(
        BudgetVersion.id == v2,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {v1} not found"
        )

    if not version2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {v2} not found"
        )

    # Get plan details for both versions
    details1 = db.query(BudgetPlanDetail).filter(
        BudgetPlanDetail.version_id == v1
    ).all()

    details2 = db.query(BudgetPlanDetail).filter(
        BudgetPlanDetail.version_id == v2
    ).all()

    # Calculate totals
    total1 = sum(d.planned_amount for d in details1)
    total2 = sum(d.planned_amount for d in details2)
    diff_amount = total2 - total1
    diff_percent = (diff_amount / total1 * 100) if total1 > 0 else 0

    # Group by category for comparison
    from collections import defaultdict
    category_map1 = defaultdict(Decimal)
    category_map2 = defaultdict(Decimal)

    for d in details1:
        category_map1[d.category_id] += d.planned_amount

    for d in details2:
        category_map2[d.category_id] += d.planned_amount

    # Build category comparisons
    all_categories = set(category_map1.keys()) | set(category_map2.keys())
    category_comparisons = []

    for cat_id in all_categories:
        amount1 = category_map1.get(cat_id, Decimal(0))
        amount2 = category_map2.get(cat_id, Decimal(0))
        diff = amount2 - amount1
        diff_pct = (diff / amount1 * 100) if amount1 > 0 else 0

        # Get category name
        category = db.query(BudgetCategory).filter(BudgetCategory.id == cat_id).first()

        category_comparisons.append({
            "category_id": cat_id,
            "category_name": category.name if category else f"Category {cat_id}",
            "version1_amount": float(amount1),
            "version2_amount": float(amount2),
            "difference_amount": float(diff),
            "difference_percent": float(diff_pct)
        })

    # Sort by absolute difference
    category_comparisons.sort(key=lambda x: abs(x["difference_amount"]), reverse=True)

    return VersionComparisonResult(
        version1={
            "id": version1.id,
            "version_name": version1.version_name,
            "version_number": version1.version_number,
            "status": version1.status,
            "total_amount": float(total1)
        },
        version2={
            "id": version2.id,
            "version_name": version2.version_name,
            "version_number": version2.version_number,
            "status": version2.status,
            "total_amount": float(total2)
        },
        total_difference_amount=float(diff_amount),
        total_difference_percent=float(diff_percent),
        category_comparisons=category_comparisons
    )


# ============================================================================
# Calculator Endpoints
# ============================================================================


@router.get("/baseline/{category_id}", response_model=BaselineSummary)
def get_baseline(
    category_id: int,
    year: int = Query(..., description="Base year for calculation (e.g., 2025)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get baseline data for a category from a specific year"""
    # Verify category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    calculator = BudgetCalculator(db)
    baseline = calculator.get_baseline_data(category_id, year, current_user.department_id)

    return BaselineSummary(
        category_id=category_id,
        category_name=category.name,
        total_amount=baseline["total_amount"],
        monthly_avg=baseline["monthly_avg"],
        monthly_breakdown=baseline["monthly_breakdown"],
        capex_total=baseline["capex_total"],
        opex_total=baseline["opex_total"],
    )


@router.post("/calculate/average", response_model=CalculationResult)
def calculate_by_average(
    request: CalculateByAverageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate budget using average method"""
    calculator = BudgetCalculator(db)
    result = calculator.calculate_by_average(
        category_id=request.category_id,
        base_year=request.base_year,
        department_id=current_user.department_id,
        adjustment_percent=request.adjustment_percent,
        target_year=request.target_year,
    )

    return CalculationResult(**result)


@router.post("/calculate/growth", response_model=CalculationResult)
def calculate_by_growth(
    request: CalculateByGrowthRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate budget using growth method"""
    calculator = BudgetCalculator(db)
    result = calculator.calculate_by_growth(
        category_id=request.category_id,
        base_year=request.base_year,
        department_id=current_user.department_id,
        growth_rate=request.growth_rate,
        inflation_rate=request.inflation_rate,
        target_year=request.target_year,
    )

    return CalculationResult(**result)


@router.post("/calculate/driver", response_model=CalculationResult)
def calculate_by_driver(
    request: CalculateByDriverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate budget using driver-based method"""
    calculator = BudgetCalculator(db)
    result = calculator.calculate_by_driver(
        category_id=request.category_id,
        base_year=request.base_year,
        department_id=current_user.department_id,
        driver_type=request.driver_type,
        base_driver_value=request.base_driver_value,
        planned_driver_value=request.planned_driver_value,
        cost_per_unit=request.cost_per_unit,
        adjustment_percent=request.adjustment_percent,
        target_year=request.target_year,
    )

    return CalculationResult(**result)


@router.post("/calculate/seasonal", response_model=CalculationResult)
def calculate_by_seasonal(
    request: CalculateBySeasonalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate budget using seasonal patterns from historical data"""
    calculator = BudgetCalculator(db)
    result = calculator.calculate_by_seasonal(
        category_id=request.category_id,
        base_year=request.base_year,
        department_id=current_user.department_id,
        annual_budget=request.annual_budget,
        adjustment_percent=request.adjustment_percent,
        target_year=request.target_year,
    )

    return CalculationResult(**result)


# ============================================================================
# Baseline Management
# ============================================================================

@router.post("/versions/{version_id}/set-as-baseline", response_model=BudgetVersionInDB)
def set_version_as_baseline(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set an approved budget version as baseline for the year.
    Only one version per year can be baseline.
    """
    # Get the version
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only APPROVED versions can be set as baseline
    if version.status != BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only APPROVED versions can be set as baseline"
        )

    # Unset any existing baseline for the same year and department
    db.query(BudgetVersion).filter(
        BudgetVersion.year == version.year,
        BudgetVersion.department_id == current_user.department_id,
        BudgetVersion.is_baseline == True
    ).update({"is_baseline": False})

    # Set this version as baseline
    version.is_baseline = True
    db.commit()
    db.refresh(version)

    return version


@router.delete("/versions/{version_id}/unset-baseline", response_model=BudgetVersionInDB)
def unset_version_baseline(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove baseline flag from a budget version"""
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    version.is_baseline = False
    db.commit()
    db.refresh(version)

    return version
