"""
KPI (Key Performance Indicators) API endpoints
Handles KPI goals, employee KPI tracking, and performance-based bonuses
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer
from datetime import datetime
from decimal import Decimal

from app.db.session import get_db
from app.db.models import (
    KPIGoal, EmployeeKPI, EmployeeKPIGoal, Employee, User, UserRoleEnum, Department,
    BonusTypeEnum, KPIGoalStatusEnum
)
from app.schemas.kpi import (
    KPIGoalCreate,
    KPIGoalUpdate,
    KPIGoalInDB,
    EmployeeKPICreate,
    EmployeeKPIUpdate,
    EmployeeKPIInDB,
    EmployeeKPIWithGoals,
    EmployeeKPIGoalCreate,
    EmployeeKPIGoalUpdate,
    EmployeeKPIGoalInDB,
    EmployeeKPIGoalWithDetails,
    KPIEmployeeSummary,
    KPIDepartmentSummary,
    KPIGoalProgress,
)
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_department_access(user: User, department_id: int) -> bool:
    """Check if user has access to the department"""
    if user.role == UserRoleEnum.ADMIN:
        return True
    if user.role == UserRoleEnum.MANAGER:
        return True
    if user.role == UserRoleEnum.USER:
        return user.department_id == department_id
    return False


def calculate_bonus(
    base_amount: Decimal,
    bonus_type: BonusTypeEnum,
    kpi_percentage: Optional[Decimal],
    fixed_part: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate bonus based on type and KPI percentage

    Args:
        base_amount: Base bonus amount
        bonus_type: Type of bonus calculation
        kpi_percentage: Employee KPI percentage (0-200)
        fixed_part: Percentage of fixed part for MIXED type (0-100)

    Returns:
        Calculated bonus amount
    """
    if bonus_type == BonusTypeEnum.FIXED:
        return base_amount

    elif bonus_type == BonusTypeEnum.PERFORMANCE_BASED:
        if kpi_percentage is None:
            return Decimal(0)
        return base_amount * (kpi_percentage / Decimal(100))

    elif bonus_type == BonusTypeEnum.MIXED:
        if kpi_percentage is None or fixed_part is None:
            return base_amount
        # Fixed part + performance part
        fixed_amount = base_amount * (fixed_part / Decimal(100))
        performance_amount = base_amount * ((Decimal(100) - fixed_part) / Decimal(100)) * (kpi_percentage / Decimal(100))
        return fixed_amount + performance_amount

    return Decimal(0)


# ==================== KPI Goals Endpoints ====================

@router.get("/goals", response_model=List[KPIGoalInDB])
async def list_kpi_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[KPIGoalStatusEnum] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all KPI goals with filtering options"""
    query = db.query(KPIGoal)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(KPIGoal.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(KPIGoal.department_id == department_id)

    # Apply filters
    if year:
        query = query.filter(KPIGoal.year == year)
    if status:
        query = query.filter(KPIGoal.status == status)
    if category:
        query = query.filter(KPIGoal.category == category)

    goals = query.offset(skip).limit(limit).all()
    return goals


@router.get("/goals/{goal_id}", response_model=KPIGoalInDB)
async def get_kpi_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific KPI goal by ID"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this goal"
        )

    return goal


@router.post("/goals", response_model=KPIGoalInDB, status_code=status.HTTP_201_CREATED)
async def create_kpi_goal(
    goal_data: KPIGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new KPI goal"""
    # Check access
    if not check_department_access(current_user, goal_data.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create goal for this department"
        )

    goal = KPIGoal(**goal_data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@router.put("/goals/{goal_id}", response_model=KPIGoalInDB)
async def update_kpi_goal(
    goal_id: int,
    goal_data: KPIGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a KPI goal"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this goal"
        )

    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)

    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a KPI goal"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this goal"
        )

    db.delete(goal)
    db.commit()


# ==================== Employee KPI Endpoints ====================

@router.get("/employee-kpis", response_model=List[EmployeeKPIWithGoals])
async def list_employee_kpis(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employee KPIs with filtering options"""
    query = db.query(EmployeeKPI)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(EmployeeKPI.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(EmployeeKPI.department_id == department_id)

    # Apply filters
    if employee_id:
        query = query.filter(EmployeeKPI.employee_id == employee_id)
    if year:
        query = query.filter(EmployeeKPI.year == year)
    if month:
        query = query.filter(EmployeeKPI.month == month)

    kpis = query.offset(skip).limit(limit).all()
    return kpis


@router.get("/employee-kpis/{kpi_id}", response_model=EmployeeKPIWithGoals)
async def get_employee_kpi(
    kpi_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific employee KPI by ID"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this KPI"
        )

    return kpi


@router.post("/employee-kpis", response_model=EmployeeKPIInDB, status_code=status.HTTP_201_CREATED)
async def create_employee_kpi(
    kpi_data: EmployeeKPICreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new employee KPI record"""
    # Check access
    if not check_department_access(current_user, kpi_data.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create KPI for this department"
        )

    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == kpi_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {kpi_data.employee_id} not found"
        )

    # Check for duplicate (employee_id, year, month)
    existing = db.query(EmployeeKPI).filter(
        and_(
            EmployeeKPI.employee_id == kpi_data.employee_id,
            EmployeeKPI.year == kpi_data.year,
            EmployeeKPI.month == kpi_data.month
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee KPI for {kpi_data.year}-{kpi_data.month:02d} already exists"
        )

    # Create KPI record
    kpi_dict = kpi_data.model_dump()

    # Calculate bonuses if not provided
    if kpi_data.kpi_percentage is not None:
        if kpi_dict.get('monthly_bonus_calculated') is None:
            kpi_dict['monthly_bonus_calculated'] = calculate_bonus(
                kpi_data.monthly_bonus_base,
                kpi_data.monthly_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.monthly_bonus_fixed_part
            )

        if kpi_dict.get('quarterly_bonus_calculated') is None:
            kpi_dict['quarterly_bonus_calculated'] = calculate_bonus(
                kpi_data.quarterly_bonus_base,
                kpi_data.quarterly_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.quarterly_bonus_fixed_part
            )

        if kpi_dict.get('annual_bonus_calculated') is None:
            kpi_dict['annual_bonus_calculated'] = calculate_bonus(
                kpi_data.annual_bonus_base,
                kpi_data.annual_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.annual_bonus_fixed_part
            )

    kpi = EmployeeKPI(**kpi_dict)
    db.add(kpi)
    db.commit()
    db.refresh(kpi)

    return kpi


@router.put("/employee-kpis/{kpi_id}", response_model=EmployeeKPIInDB)
async def update_employee_kpi(
    kpi_id: int,
    kpi_data: EmployeeKPIUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an employee KPI record"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this KPI"
        )

    # Update fields
    update_data = kpi_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kpi, field, value)

    # Recalculate bonuses if KPI percentage changed
    if 'kpi_percentage' in update_data and kpi.kpi_percentage is not None:
        kpi.monthly_bonus_calculated = calculate_bonus(
            kpi.monthly_bonus_base,
            kpi.monthly_bonus_type,
            kpi.kpi_percentage,
            kpi.monthly_bonus_fixed_part
        )
        kpi.quarterly_bonus_calculated = calculate_bonus(
            kpi.quarterly_bonus_base,
            kpi.quarterly_bonus_type,
            kpi.kpi_percentage,
            kpi.quarterly_bonus_fixed_part
        )
        kpi.annual_bonus_calculated = calculate_bonus(
            kpi.annual_bonus_base,
            kpi.annual_bonus_type,
            kpi.kpi_percentage,
            kpi.annual_bonus_fixed_part
        )

    kpi.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(kpi)

    return kpi


@router.delete("/employee-kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_kpi(
    kpi_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an employee KPI record"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this KPI"
        )

    db.delete(kpi)
    db.commit()


# ==================== Employee KPI Goals Endpoints ====================

@router.get("/employee-kpi-goals", response_model=List[EmployeeKPIGoalWithDetails])
async def list_employee_kpi_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    employee_id: Optional[int] = None,
    goal_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[KPIGoalStatusEnum] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employee KPI goal assignments"""
    query = db.query(EmployeeKPIGoal)

    # Apply filters
    if employee_id:
        query = query.filter(EmployeeKPIGoal.employee_id == employee_id)
    if goal_id:
        query = query.filter(EmployeeKPIGoal.goal_id == goal_id)
    if year:
        query = query.filter(EmployeeKPIGoal.year == year)
    if month is not None:
        query = query.filter(EmployeeKPIGoal.month == month)
    if status:
        query = query.filter(EmployeeKPIGoal.status == status)

    # Department filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        # Filter by employee's department
        query = query.join(Employee).filter(Employee.department_id == current_user.department_id)

    goal_assignments = query.offset(skip).limit(limit).all()
    return goal_assignments


@router.post("/employee-kpi-goals", response_model=EmployeeKPIGoalInDB, status_code=status.HTTP_201_CREATED)
async def create_employee_kpi_goal(
    goal_data: EmployeeKPIGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a KPI goal to an employee"""
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == goal_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {goal_data.employee_id} not found"
        )

    # Check access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to assign goal to this employee"
        )

    # Check if goal exists
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_data.goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_data.goal_id} not found"
        )

    # Create assignment
    goal_assignment = EmployeeKPIGoal(**goal_data.model_dump())
    db.add(goal_assignment)
    db.commit()
    db.refresh(goal_assignment)

    return goal_assignment


@router.put("/employee-kpi-goals/{assignment_id}", response_model=EmployeeKPIGoalInDB)
async def update_employee_kpi_goal(
    assignment_id: int,
    goal_data: EmployeeKPIGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an employee KPI goal assignment"""
    assignment = db.query(EmployeeKPIGoal).filter(EmployeeKPIGoal.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI goal assignment with id {assignment_id} not found"
        )

    # Check access through employee
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee or not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this assignment"
        )

    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)

    # Auto-calculate achievement percentage if actual_value provided
    if 'actual_value' in update_data and assignment.target_value and assignment.target_value > 0:
        achievement_pct = (update_data['actual_value'] / assignment.target_value) * Decimal(100)
        update_data['achievement_percentage'] = achievement_pct

    for field, value in update_data.items():
        setattr(assignment, field, value)

    assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete("/employee-kpi-goals/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_kpi_goal(
    assignment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an employee KPI goal assignment"""
    assignment = db.query(EmployeeKPIGoal).filter(EmployeeKPIGoal.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI goal assignment with id {assignment_id} not found"
        )

    # Check access
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee or not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this assignment"
        )

    db.delete(assignment)
    db.commit()


# ==================== KPI Analytics Endpoints ====================

@router.get("/analytics/employee-summary", response_model=List[KPIEmployeeSummary])
async def get_employee_kpi_summary(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get KPI summary for employees"""
    query = db.query(
        EmployeeKPI.employee_id,
        Employee.full_name.label('employee_name'),
        Employee.position,
        EmployeeKPI.year,
        EmployeeKPI.month,
        EmployeeKPI.kpi_percentage,
        (EmployeeKPI.monthly_bonus_calculated +
         EmployeeKPI.quarterly_bonus_calculated +
         EmployeeKPI.annual_bonus_calculated).label('total_bonus_calculated'),
        EmployeeKPI.monthly_bonus_calculated,
        EmployeeKPI.quarterly_bonus_calculated,
        EmployeeKPI.annual_bonus_calculated,
        func.count(EmployeeKPIGoal.id).label('goals_count'),
        func.sum(
            func.cast(EmployeeKPIGoal.status == KPIGoalStatusEnum.ACHIEVED, Integer)
        ).label('goals_achieved')
    ).join(Employee).outerjoin(EmployeeKPIGoal).filter(
        EmployeeKPI.year == year
    )

    if month is not None:
        query = query.filter(EmployeeKPI.month == month)

    # Department filter
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    query = query.group_by(
        EmployeeKPI.employee_id,
        Employee.full_name,
        Employee.position,
        EmployeeKPI.year,
        EmployeeKPI.month,
        EmployeeKPI.kpi_percentage,
        EmployeeKPI.monthly_bonus_calculated,
        EmployeeKPI.quarterly_bonus_calculated,
        EmployeeKPI.annual_bonus_calculated
    )

    results = query.all()

    return [
        KPIEmployeeSummary(
            employee_id=r.employee_id,
            employee_name=r.employee_name,
            position=r.position,
            year=r.year,
            month=r.month,
            kpi_percentage=r.kpi_percentage,
            total_bonus_calculated=r.total_bonus_calculated or Decimal(0),
            monthly_bonus_calculated=r.monthly_bonus_calculated or Decimal(0),
            quarterly_bonus_calculated=r.quarterly_bonus_calculated or Decimal(0),
            annual_bonus_calculated=r.annual_bonus_calculated or Decimal(0),
            goals_count=r.goals_count or 0,
            goals_achieved=r.goals_achieved or 0
        )
        for r in results
    ]
