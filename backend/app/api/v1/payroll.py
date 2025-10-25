"""
Payroll planning and actual API endpoints
Handles payroll plans and actual payments
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from decimal import Decimal
import pandas as pd
import io

from app.db.session import get_db
from app.db.models import (
    PayrollPlan, PayrollActual, Employee, User, UserRoleEnum, Department
)
from app.schemas.payroll import (
    PayrollPlanCreate,
    PayrollPlanUpdate,
    PayrollPlanInDB,
    PayrollPlanWithEmployee,
    PayrollActualCreate,
    PayrollActualUpdate,
    PayrollActualInDB,
    PayrollActualWithEmployee,
    PayrollSummary,
    EmployeePayrollStats,
    DepartmentPayrollStats,
    SalaryStatistics,
    PayrollStructureMonth,
    PayrollDynamics,
)
from app.utils.auth import get_current_active_user

router = APIRouter()


def check_department_access(user: User, department_id: int) -> bool:
    """Check if user has access to the department"""
    if user.role == UserRoleEnum.ADMIN:
        return True
    if user.role == UserRoleEnum.MANAGER:
        return True
    if user.role == UserRoleEnum.USER:
        return user.department_id == department_id
    return False


# ==================== Payroll Plan Endpoints ====================

@router.get("/plans", response_model=List[PayrollPlanWithEmployee])
async def list_payroll_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all payroll plans with filtering options
    """
    query = db.query(PayrollPlan)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(PayrollPlan.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollPlan.department_id == department_id)

    # Apply filters
    if employee_id:
        query = query.filter(PayrollPlan.employee_id == employee_id)
    if year:
        query = query.filter(PayrollPlan.year == year)
    if month:
        query = query.filter(PayrollPlan.month == month)

    plans = query.offset(skip).limit(limit).all()
    return plans


@router.get("/plans/{plan_id}", response_model=PayrollPlanWithEmployee)
async def get_payroll_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific payroll plan by ID
    """
    plan = db.query(PayrollPlan).filter(PayrollPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
        )

    # Check department access
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll plan"
        )

    return plan


@router.post("/plans", response_model=PayrollPlanInDB, status_code=status.HTTP_201_CREATED)
async def create_payroll_plan(
    plan_data: PayrollPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new payroll plan (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can create payroll plans
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can create payroll plans"
        )

    # Get employee to check department and get department_id
    employee = db.query(Employee).filter(Employee.id == plan_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee's department"
        )

    # Check if plan already exists for this employee, year, and month
    existing = db.query(PayrollPlan).filter(
        and_(
            PayrollPlan.employee_id == plan_data.employee_id,
            PayrollPlan.year == plan_data.year,
            PayrollPlan.month == plan_data.month
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payroll plan already exists for this employee, year, and month"
        )

    # Calculate total planned amount
    total_planned = plan_data.base_salary + plan_data.bonus + plan_data.other_payments

    # Create new payroll plan
    new_plan = PayrollPlan(
        **plan_data.model_dump(),
        department_id=employee.department_id,
        total_planned=total_planned
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return new_plan


@router.put("/plans/{plan_id}", response_model=PayrollPlanInDB)
async def update_payroll_plan(
    plan_id: int,
    plan_data: PayrollPlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a payroll plan (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can update payroll plans
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can update payroll plans"
        )

    plan = db.query(PayrollPlan).filter(PayrollPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
        )

    # Check department access
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll plan"
        )

    # Update plan fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    # Recalculate total planned amount
    plan.total_planned = plan.base_salary + plan.bonus + plan.other_payments

    db.commit()
    db.refresh(plan)

    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a payroll plan (ADMIN only)
    """
    # Only ADMIN can delete payroll plans
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete payroll plans"
        )

    plan = db.query(PayrollPlan).filter(PayrollPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
        )

    # Check department access
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll plan"
        )

    db.delete(plan)
    db.commit()
    return None


# ==================== Payroll Actual Endpoints ====================

@router.get("/actuals", response_model=List[PayrollActualWithEmployee])
async def list_payroll_actuals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all payroll actuals with filtering options
    """
    query = db.query(PayrollActual)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollActual.department_id == department_id)

    # Apply filters
    if employee_id:
        query = query.filter(PayrollActual.employee_id == employee_id)
    if year:
        query = query.filter(PayrollActual.year == year)
    if month:
        query = query.filter(PayrollActual.month == month)

    actuals = query.offset(skip).limit(limit).all()
    return actuals


@router.post("/actuals", response_model=PayrollActualInDB, status_code=status.HTTP_201_CREATED)
async def create_payroll_actual(
    actual_data: PayrollActualCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new payroll actual (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can create payroll actuals
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can create payroll actuals"
        )

    # Get employee to check department and get department_id
    employee = db.query(Employee).filter(Employee.id == actual_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee's department"
        )

    # Check if actual already exists for this employee, year, and month
    existing = db.query(PayrollActual).filter(
        and_(
            PayrollActual.employee_id == actual_data.employee_id,
            PayrollActual.year == actual_data.year,
            PayrollActual.month == actual_data.month
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payroll actual already exists for this employee, year, and month"
        )

    # Calculate total paid amount
    total_paid = actual_data.base_salary_paid + actual_data.bonus_paid + actual_data.other_payments_paid

    # Create new payroll actual
    new_actual = PayrollActual(
        **actual_data.model_dump(),
        department_id=employee.department_id,
        total_paid=total_paid
    )
    db.add(new_actual)
    db.commit()
    db.refresh(new_actual)

    return new_actual


@router.put("/actuals/{actual_id}", response_model=PayrollActualInDB)
async def update_payroll_actual(
    actual_id: int,
    actual_data: PayrollActualUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a payroll actual (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can update payroll actuals
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can update payroll actuals"
        )

    actual = db.query(PayrollActual).filter(PayrollActual.id == actual_id).first()
    if not actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll actual not found"
        )

    # Check department access
    if not check_department_access(current_user, actual.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll actual"
        )

    # Update actual fields
    update_data = actual_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(actual, field, value)

    # Recalculate total paid amount
    actual.total_paid = actual.base_salary_paid + actual.bonus_paid + actual.other_payments_paid

    db.commit()
    db.refresh(actual)

    return actual


@router.delete("/actuals/{actual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll_actual(
    actual_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a payroll actual (ADMIN only)
    """
    # Only ADMIN can delete payroll actuals
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete payroll actuals"
        )

    actual = db.query(PayrollActual).filter(PayrollActual.id == actual_id).first()
    if not actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll actual not found"
        )

    # Check department access
    if not check_department_access(current_user, actual.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this payroll actual"
        )

    db.delete(actual)
    db.commit()
    return None


# ==================== Analytics Endpoints ====================

@router.get("/analytics/summary", response_model=List[PayrollSummary])
async def get_payroll_summary(
    year: int = Query(..., ge=2000, le=2100),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll summary by month for a given year
    """
    # Filter by department based on user role
    dept_filter = None
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        dept_filter = current_user.department_id
    elif department_id:
        dept_filter = department_id

    # Get plan data
    plan_query = db.query(
        PayrollPlan.month,
        func.count(func.distinct(PayrollPlan.employee_id)).label('employee_count'),
        func.sum(PayrollPlan.total_planned).label('total_planned')
    ).filter(PayrollPlan.year == year)

    if dept_filter:
        plan_query = plan_query.filter(PayrollPlan.department_id == dept_filter)

    plan_data = plan_query.group_by(PayrollPlan.month).all()

    # Get actual data
    actual_query = db.query(
        PayrollActual.month,
        func.sum(PayrollActual.total_paid).label('total_paid')
    ).filter(PayrollActual.year == year)

    if dept_filter:
        actual_query = actual_query.filter(PayrollActual.department_id == dept_filter)

    actual_data = actual_query.group_by(PayrollActual.month).all()

    # Combine data
    actual_dict = {a.month: a.total_paid for a in actual_data}
    summaries = []

    for plan in plan_data:
        total_paid = actual_dict.get(plan.month, Decimal(0))
        variance = total_paid - plan.total_planned
        variance_percent = float((variance / plan.total_planned * 100) if plan.total_planned > 0 else 0)

        summaries.append(PayrollSummary(
            year=year,
            month=plan.month,
            total_employees=plan.employee_count,
            total_planned=plan.total_planned,
            total_paid=total_paid,
            variance=variance,
            variance_percent=variance_percent
        ))

    # Sort by month
    summaries.sort(key=lambda x: x.month)

    return summaries


# ==================== Export Endpoints ====================

@router.get("/plans/export", response_class=StreamingResponse)
async def export_payroll_plans(
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export payroll plans to Excel
    """
    query = db.query(PayrollPlan).join(Employee)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(PayrollPlan.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollPlan.department_id == department_id)

    # Apply filters
    if year:
        query = query.filter(PayrollPlan.year == year)
    if month:
        query = query.filter(PayrollPlan.month == month)

    plans = query.all()

    # Convert to DataFrame
    data = []
    for plan in plans:
        data.append({
            "ID": plan.id,
            "Год": plan.year,
            "Месяц": plan.month,
            "Сотрудник": plan.employee_rel.full_name,
            "Должность": plan.employee_rel.position,
            "Оклад": float(plan.base_salary),
            "Премия": float(plan.bonus),
            "Прочие выплаты": float(plan.other_payments),
            "Итого запланировано": float(plan.total_planned),
            "Примечания": plan.notes or "",
            "Дата создания": plan.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='План ФОТ')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=payroll_plans_export.xlsx"}
    )


@router.get("/actuals/export", response_class=StreamingResponse)
async def export_payroll_actuals(
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export payroll actuals to Excel
    """
    query = db.query(PayrollActual).join(Employee)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollActual.department_id == department_id)

    # Apply filters
    if year:
        query = query.filter(PayrollActual.year == year)
    if month:
        query = query.filter(PayrollActual.month == month)

    actuals = query.all()

    # Convert to DataFrame
    data = []
    for actual in actuals:
        data.append({
            "ID": actual.id,
            "Год": actual.year,
            "Месяц": actual.month,
            "Сотрудник": actual.employee_rel.full_name,
            "Должность": actual.employee_rel.position,
            "Оклад выплачено": float(actual.base_salary_paid),
            "Премия выплачено": float(actual.bonus_paid),
            "Прочие выплаты": float(actual.other_payments_paid),
            "Итого выплачено": float(actual.total_paid),
            "Дата выплаты": actual.payment_date.strftime("%Y-%m-%d") if actual.payment_date else "",
            "Примечания": actual.notes or "",
            "Дата создания": actual.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Факт ФОТ')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=payroll_actuals_export.xlsx"}
    )


# ==================== Advanced Analytics Endpoints ====================

@router.get("/analytics/salary-stats", response_model=SalaryStatistics)
async def get_salary_statistics(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get salary distribution statistics including median and percentiles
    """
    query = db.query(Employee)

    # Filter by department based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    # Get all employees and active employees
    all_employees = query.all()
    active_employees = [e for e in all_employees if e.status == 'ACTIVE']

    if not active_employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active employees found"
        )

    # Get salary values sorted
    salaries = sorted([float(e.base_salary) for e in active_employees])
    n = len(salaries)

    # Calculate statistics
    def percentile(data, p):
        """Calculate percentile"""
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = k - f
        if f + 1 < len(data):
            return data[f] + (data[f + 1] - data[f]) * c
        return data[f]

    median = percentile(salaries, 50)
    p25 = percentile(salaries, 25)
    p75 = percentile(salaries, 75)
    p90 = percentile(salaries, 90)

    total_payroll = sum(salaries)
    avg_salary = total_payroll / n if n > 0 else 0

    return SalaryStatistics(
        total_employees=len(all_employees),
        active_employees=n,
        min_salary=Decimal(str(min(salaries))),
        max_salary=Decimal(str(max(salaries))),
        average_salary=Decimal(str(avg_salary)),
        median_salary=Decimal(str(median)),
        percentile_25=Decimal(str(p25)),
        percentile_75=Decimal(str(p75)),
        percentile_90=Decimal(str(p90)),
        total_payroll=Decimal(str(total_payroll))
    )


@router.get("/analytics/structure", response_model=List[PayrollStructureMonth])
async def get_payroll_structure(
    year: int = Query(..., ge=2000, le=2100),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll structure breakdown by month (base salary vs bonus vs other payments)
    """
    # Filter by department based on user role
    dept_filter = None
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        dept_filter = current_user.department_id
    elif department_id:
        dept_filter = department_id

    # Get plan data grouped by month
    query = db.query(
        PayrollPlan.month,
        func.sum(PayrollPlan.base_salary).label('total_base_salary'),
        func.sum(PayrollPlan.bonus).label('total_bonus'),
        func.sum(PayrollPlan.other_payments).label('total_other_payments'),
        func.sum(PayrollPlan.total_planned).label('total_amount'),
        func.count(func.distinct(PayrollPlan.employee_id)).label('employee_count')
    ).filter(PayrollPlan.year == year)

    if dept_filter:
        query = query.filter(PayrollPlan.department_id == dept_filter)

    results = query.group_by(PayrollPlan.month).order_by(PayrollPlan.month).all()

    structure = []
    for row in results:
        structure.append(PayrollStructureMonth(
            year=year,
            month=row.month,
            total_base_salary=row.total_base_salary or Decimal(0),
            total_bonus=row.total_bonus or Decimal(0),
            total_other_payments=row.total_other_payments or Decimal(0),
            total_amount=row.total_amount or Decimal(0),
            employee_count=row.employee_count
        ))

    return structure


@router.get("/analytics/dynamics", response_model=List[PayrollDynamics])
async def get_payroll_dynamics(
    year: int = Query(..., ge=2000, le=2100),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll dynamics over time including plan vs actual breakdown
    """
    # Filter by department based on user role
    dept_filter = None
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        dept_filter = current_user.department_id
    elif department_id:
        dept_filter = department_id

    # Get plan data
    plan_query = db.query(
        PayrollPlan.month,
        func.sum(PayrollPlan.base_salary).label('planned_base_salary'),
        func.sum(PayrollPlan.bonus).label('planned_bonus'),
        func.sum(PayrollPlan.other_payments).label('planned_other'),
        func.sum(PayrollPlan.total_planned).label('planned_total'),
        func.count(func.distinct(PayrollPlan.employee_id)).label('employee_count')
    ).filter(PayrollPlan.year == year)

    if dept_filter:
        plan_query = plan_query.filter(PayrollPlan.department_id == dept_filter)

    plan_data = {
        row.month: row for row in
        plan_query.group_by(PayrollPlan.month).all()
    }

    # Get actual data
    actual_query = db.query(
        PayrollActual.month,
        func.sum(PayrollActual.base_salary_paid).label('actual_base_salary'),
        func.sum(PayrollActual.bonus_paid).label('actual_bonus'),
        func.sum(PayrollActual.other_payments_paid).label('actual_other'),
        func.sum(PayrollActual.total_paid).label('actual_total')
    ).filter(PayrollActual.year == year)

    if dept_filter:
        actual_query = actual_query.filter(PayrollActual.department_id == dept_filter)

    actual_data = {
        row.month: row for row in
        actual_query.group_by(PayrollActual.month).all()
    }

    # Combine plan and actual data
    dynamics = []
    for month in range(1, 13):
        plan = plan_data.get(month)
        actual = actual_data.get(month)

        if plan or actual:
            dynamics.append(PayrollDynamics(
                year=year,
                month=month,
                planned_base_salary=plan.planned_base_salary if plan else Decimal(0),
                planned_bonus=plan.planned_bonus if plan else Decimal(0),
                planned_other=plan.planned_other if plan else Decimal(0),
                planned_total=plan.planned_total if plan else Decimal(0),
                actual_base_salary=actual.actual_base_salary if actual else Decimal(0),
                actual_bonus=actual.actual_bonus if actual else Decimal(0),
                actual_other=actual.actual_other if actual else Decimal(0),
                actual_total=actual.actual_total if actual else Decimal(0),
                employee_count=plan.employee_count if plan else 0
            ))

    return dynamics
