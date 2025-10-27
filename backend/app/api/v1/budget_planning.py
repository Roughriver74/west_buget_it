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
    CalculationResult,
    BaselineSummary,
    VersionComparison,
    VersionComparisonResult,
)
from app.utils.auth import get_current_active_user
from app.services.budget_calculator import BudgetCalculator

router = APIRouter(dependencies=[Depends(get_current_active_user)])


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
