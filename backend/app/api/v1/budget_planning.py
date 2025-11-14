"""
API endpoints for Budget Planning 2026 Module
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from decimal import Decimal
import pandas as pd
import io

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
    """Recalculate cached totals for a budget version.

    Only sums leaf categories (categories without children) to avoid double counting.
    """
    from sqlalchemy import exists, select

    # Subquery to identify parent categories (categories that have children)
    parent_categories_subq = (
        select(BudgetCategory.parent_id)
        .where(BudgetCategory.parent_id.isnot(None))
        .distinct()
        .subquery()
    )

    # Query totals only for leaf categories (categories NOT in parent list)
    totals = (
        db.query(
            func.coalesce(func.sum(BudgetPlanDetail.planned_amount), 0).label("amount"),
            BudgetPlanDetail.type,
        )
        .join(BudgetCategory, BudgetPlanDetail.category_id == BudgetCategory.id)
        .filter(
            BudgetPlanDetail.version_id == version.id,
            # Exclude parent categories (only include leaf categories)
            ~BudgetCategory.id.in_(parent_categories_subq)
        )
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
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget scenarios

    - USER: Can only see scenarios from their own department
    - MANAGER/ADMIN: Can see scenarios from all departments or filter by department
    """
    from app.db.models import UserRoleEnum

    query = db.query(BudgetScenario)

    # Apply filters
    if year:
        query = query.filter(BudgetScenario.year == year)
    if scenario_type:
        query = query.filter(BudgetScenario.scenario_type == scenario_type)
    if is_active is not None:
        query = query.filter(BudgetScenario.is_active == is_active)

    # SECURITY: Multi-tenancy filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetScenario.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(BudgetScenario.department_id == department_id)

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

    # Check if scenario has versions with protected statuses
    protected_versions = db.query(BudgetVersion).filter(
        BudgetVersion.scenario_id == scenario_id,
        BudgetVersion.status.in_([
            BudgetVersionStatusEnum.IN_REVIEW,
            BudgetVersionStatusEnum.APPROVED,
            BudgetVersionStatusEnum.ARCHIVED
        ])
    ).count()

    if protected_versions > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete scenario - it has {protected_versions} version(s) in IN_REVIEW, APPROVED, or ARCHIVED status"
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
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget versions

    - USER: Can only see versions from their own department
    - MANAGER/ADMIN: Can see versions from all departments or filter by department
    """
    from app.db.models import UserRoleEnum

    query = db.query(BudgetVersion)

    # Apply filters
    if year:
        query = query.filter(BudgetVersion.year == year)
    if status:
        query = query.filter(BudgetVersion.status == status)
    if scenario_id:
        query = query.filter(BudgetVersion.scenario_id == scenario_id)

    # SECURITY: Multi-tenancy filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetVersion.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(BudgetVersion.department_id == department_id)

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

    # Load payroll summary for the same year and department
    from app.db.models import PayrollPlan
    from app.schemas.budget_planning import PayrollMonthlySummary, PayrollYearlySummary
    from decimal import Decimal

    payroll_plans = db.query(PayrollPlan).filter(
        PayrollPlan.year == version.year,
        PayrollPlan.department_id == version.department_id
    ).all()

    if payroll_plans:
        # Aggregate payroll data by month
        monthly_data = {}
        unique_employees = set()

        for plan in payroll_plans:
            month = plan.month
            unique_employees.add(plan.employee_id)

            if month not in monthly_data:
                monthly_data[month] = {
                    'employee_count': 0,
                    'total_base_salary': Decimal('0'),
                    'total_bonuses': Decimal('0'),
                    'total_other': Decimal('0'),
                    'total_planned': Decimal('0'),
                }

            monthly_data[month]['employee_count'] += 1
            monthly_data[month]['total_base_salary'] += Decimal(str(plan.base_salary))

            # Sum all bonuses
            bonuses = Decimal('0')
            if plan.monthly_bonus:
                bonuses += Decimal(str(plan.monthly_bonus))
            if plan.quarterly_bonus:
                bonuses += Decimal(str(plan.quarterly_bonus))
            if plan.annual_bonus:
                bonuses += Decimal(str(plan.annual_bonus))

            monthly_data[month]['total_bonuses'] += bonuses

            if plan.other_payments:
                monthly_data[month]['total_other'] += Decimal(str(plan.other_payments))

            monthly_data[month]['total_planned'] += Decimal(str(plan.total_planned))

        # Create monthly breakdown
        monthly_breakdown = []
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            monthly_breakdown.append(PayrollMonthlySummary(
                month=month,
                employee_count=data['employee_count'],
                total_base_salary=data['total_base_salary'],
                total_bonuses=data['total_bonuses'],
                total_other=data['total_other'],
                total_planned=data['total_planned']
            ))

        # Calculate yearly totals
        total_planned_annual = sum(m.total_planned for m in monthly_breakdown)
        total_base_salary_annual = sum(m.total_base_salary for m in monthly_breakdown)
        total_bonuses_annual = sum(m.total_bonuses for m in monthly_breakdown)

        version_dict["payroll_summary"] = PayrollYearlySummary(
            year=version.year,
            total_employees=len(unique_employees),
            total_planned_annual=total_planned_annual,
            total_base_salary_annual=total_base_salary_annual,
            total_bonuses_annual=total_bonuses_annual,
            monthly_breakdown=monthly_breakdown
        )

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

    # Don't allow deletion of versions with protected statuses
    protected_statuses = [
        BudgetVersionStatusEnum.IN_REVIEW,
        BudgetVersionStatusEnum.APPROVED,
        BudgetVersionStatusEnum.ARCHIVED
    ]
    if db_version.status in protected_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete version with status {db_version.status.value}"
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


@router.post("/versions/{version_id}/apply-to-plan", response_model=BudgetVersionInDB)
def apply_version_to_plan(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Apply APPROVED version to budget plan table.
    Copies all plan details from the version to budget_plans for the year.
    Only ADMIN and MANAGER can apply versions to plan.
    """
    from app.db.models import UserRoleEnum, BudgetPlan, BudgetStatusEnum

    # Only ADMIN and MANAGER can apply to plan
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER users can apply budget versions to plan"
        )

    # Get version with details
    version = db.query(BudgetVersion).filter(
        BudgetVersion.id == version_id,
        BudgetVersion.department_id == current_user.department_id
    ).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Only APPROVED versions can be applied to plan
    if version.status != BudgetVersionStatusEnum.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only APPROVED versions can be applied to plan. Current status: {version.status}"
        )

    # Get all plan details for this version
    plan_details = db.query(BudgetPlanDetail).filter(
        BudgetPlanDetail.version_id == version_id
    ).all()

    if not plan_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply empty version. No budget details found."
        )

    # Group details by category and month for efficient upsert
    applied_count = 0
    updated_count = 0

    for detail in plan_details:
        # Check if budget plan record already exists
        existing_plan = db.query(BudgetPlan).filter(
            BudgetPlan.year == version.year,
            BudgetPlan.month == detail.month,
            BudgetPlan.department_id == version.department_id,
            BudgetPlan.category_id == detail.category_id
        ).first()

        # Calculate CAPEX and OPEX amounts
        capex_amount = detail.planned_amount if detail.type == ExpenseTypeEnum.CAPEX else Decimal("0")
        opex_amount = detail.planned_amount if detail.type == ExpenseTypeEnum.OPEX else Decimal("0")

        if existing_plan:
            # Update existing record
            existing_plan.planned_amount = detail.planned_amount
            existing_plan.capex_planned = capex_amount
            existing_plan.opex_planned = opex_amount
            existing_plan.status = BudgetStatusEnum.APPROVED
            existing_plan.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new record
            new_plan = BudgetPlan(
                year=version.year,
                month=detail.month,
                department_id=version.department_id,
                category_id=detail.category_id,
                planned_amount=detail.planned_amount,
                capex_planned=capex_amount,
                opex_planned=opex_amount,
                status=BudgetStatusEnum.APPROVED
            )
            db.add(new_plan)
            applied_count += 1

    # Commit all changes
    db.commit()
    db.refresh(version)

    # Log the result
    total_records = applied_count + updated_count
    print(f"Applied version {version_id} to plan: {applied_count} created, {updated_count} updated ({total_records} total)")

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


# ============================================================================
# Budget Plan Import/Export
# ============================================================================


@router.post("/versions/{version_id}/import", status_code=status.HTTP_200_OK)
async def import_budget_plan_details(
    version_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import budget plan details from Excel file

    Expected Excel format:
    - Категория (Category name)
    - Тип (OPEX/CAPEX)
    - Январь, Февраль, ..., Декабрь (12 month columns with amounts)
    - Обоснование (optional justification)
    """
    from app.db.models import UserRoleEnum
    from app.utils.logger import logger, log_info, log_error

    # Verify version exists and user has access
    version = db.query(BudgetVersion).filter(BudgetVersion.id == version_id).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version with id {version_id} not found"
        )

    # Security check - verify user has access to this version
    if current_user.role == UserRoleEnum.USER:
        if version.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version with id {version_id} not found"
            )

    # Check version status
    if version.status not in [BudgetVersionStatusEnum.DRAFT, BudgetVersionStatusEnum.IN_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot import to version with status {version.status.value}. Only DRAFT or IN_REVIEW versions can be modified."
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    try:
        # Read Excel file
        log_info(f"Starting budget plan import from {file.filename} for version {version_id}", "Import")
        content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is 10MB"
            )

        # Parse Excel
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            log_error(e, "Failed to parse Excel file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Excel file format: {str(e)}"
            )

        # Check if dataframe is empty
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel file is empty"
            )

        # Validate required columns
        required_columns = ['Категория', 'Тип']
        month_columns = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}"
            )

        # Get all categories for this department
        categories_query = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == version.department_id,
            BudgetCategory.is_active == True
        )
        categories = {cat.name: cat for cat in categories_query.all()}

        created_count = 0
        updated_count = 0
        errors = []
        total_rows = len(df)

        for index, row in df.iterrows():
            try:
                category_name = str(row['Категория']).strip()
                type_val = str(row['Тип']).strip().upper()

                if not category_name or category_name == 'nan':
                    errors.append(f"Строка {index + 2}: Не указана категория")
                    continue

                if type_val not in ['OPEX', 'CAPEX']:
                    errors.append(f"Строка {index + 2}: Тип должен быть OPEX или CAPEX")
                    continue

                # Find category
                category = categories.get(category_name)
                if not category:
                    errors.append(f"Строка {index + 2}: Категория '{category_name}' не найдена")
                    continue

                # Get justification if provided
                justification = None
                if 'Обоснование' in df.columns:
                    just_val = row.get('Обоснование')
                    if pd.notna(just_val):
                        justification = str(just_val).strip()

                # Process each month
                for month_idx, month_name in enumerate(month_columns, start=1):
                    if month_name not in df.columns:
                        continue

                    amount_val = row.get(month_name)
                    if pd.isna(amount_val):
                        amount = Decimal("0")
                    else:
                        try:
                            amount = Decimal(str(amount_val))
                        except:
                            errors.append(f"Строка {index + 2}, {month_name}: Неверный формат суммы")
                            continue

                    # Check if detail already exists
                    existing = db.query(BudgetPlanDetail).filter(
                        BudgetPlanDetail.version_id == version_id,
                        BudgetPlanDetail.month == month_idx,
                        BudgetPlanDetail.category_id == category.id
                    ).first()

                    if existing:
                        # Update existing
                        existing.planned_amount = amount
                        existing.type = type_val
                        if justification:
                            existing.justification = justification
                        existing.calculation_method = "manual"
                        updated_count += 1
                    else:
                        # Create new
                        new_detail = BudgetPlanDetail(
                            version_id=version_id,
                            month=month_idx,
                            category_id=category.id,
                            planned_amount=amount,
                            type=type_val,
                            justification=justification,
                            calculation_method="manual"
                        )
                        db.add(new_detail)
                        created_count += 1

            except Exception as e:
                errors.append(f"Строка {index + 2}: {str(e)}")

        db.commit()

        # Recalculate version totals
        recalculate_version_totals(db, version)
        db.commit()

        log_info(f"Import completed: created={created_count}, updated={updated_count}, errors={len(errors)}", "Import")

        return {
            "success": len(errors) == 0 or (created_count + updated_count) > 0,
            "message": "Import completed" if len(errors) == 0 else "Import completed with errors",
            "total_rows": total_rows,
            "created": created_count,
            "updated": updated_count,
            "skipped": len(errors),
            "errors": errors[:50] if errors else []  # Limit errors to first 50
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "Budget plan import failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing file: {str(e)}"
        )


@router.get("/versions/template/download", status_code=status.HTTP_200_OK)
async def download_budget_template(
    current_user: User = Depends(get_current_active_user)
):
    """
    Download Excel template for budget plan import
    """
    # Create a template DataFrame with the correct structure
    template_data = {
        'Категория': ['Пример категории 1', 'Пример категории 2'],
        'Тип': ['OPEX', 'CAPEX'],
        'Январь': [0, 0],
        'Февраль': [0, 0],
        'Март': [0, 0],
        'Апрель': [0, 0],
        'Май': [0, 0],
        'Июнь': [0, 0],
        'Июль': [0, 0],
        'Август': [0, 0],
        'Сентябрь': [0, 0],
        'Октябрь': [0, 0],
        'Ноябрь': [0, 0],
        'Декабрь': [0, 0],
        'Обоснование': ['Пример обоснования', 'Пример обоснования']
    }

    df = pd.DataFrame(template_data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='План бюджета')

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['План бюджета']

        # Auto-adjust column widths
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length, 50)

    output.seek(0)

    # Return as streaming response
    # Use RFC 5987 encoding for non-ASCII filename
    import urllib.parse
    filename = "Шаблон_План_Бюджета.xlsx"
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
