"""
Payroll planning and actual API endpoints
Handles payroll plans and actual payments
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

from app.db.session import get_db
from app.db.models import (
    PayrollPlan, PayrollActual, Employee, User, UserRoleEnum, Department, EmployeeKPI, EmployeeStatusEnum
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
    PayrollForecast,
)
from app.utils.auth import get_current_active_user
from app.utils.ndfl_calculator import calculate_progressive_ndfl, calculate_gross_from_net
from app.utils.social_contributions_calculator import (
    calculate_social_contributions,
    calculate_total_tax_burden
)

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


# ==================== Export Endpoints ====================

@router.get("/plans/export")
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
            "Премия месячная": float(plan.monthly_bonus),
            "Премия квартальная": float(plan.quarterly_bonus),
            "Премия годовая": float(plan.annual_bonus),
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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
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

    # Calculate total planned amount (salary + all bonus types + other)
    total_planned = (
        plan_data.base_salary +
        plan_data.monthly_bonus +
        plan_data.quarterly_bonus +
        plan_data.annual_bonus +
        plan_data.other_payments
    )

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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
        )

    # Update plan fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    # Recalculate total planned amount (salary + all bonus types + other)
    plan.total_planned = (
        plan.base_salary +
        plan.monthly_bonus +
        plan.quarterly_bonus +
        plan.annual_bonus +
        plan.other_payments
    )

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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, plan.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll plan not found"
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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
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

    # Calculate total paid amount (salary + all bonus types + other)
    total_paid = (
        actual_data.base_salary_paid +
        actual_data.monthly_bonus_paid +
        actual_data.quarterly_bonus_paid +
        actual_data.annual_bonus_paid +
        actual_data.other_payments_paid
    )

    # Auto-calculate НДФЛ using progressive scale if not explicitly provided
    # Get YTD income and tax before current month
    from app.utils.ndfl_calculator import calculate_monthly_ndfl_withholding

    ytd_before = db.query(
        func.sum(PayrollActual.total_paid).label('ytd_income'),
        func.sum(PayrollActual.income_tax_amount).label('ytd_tax')
    ).filter(
        PayrollActual.employee_id == actual_data.employee_id,
        PayrollActual.year == actual_data.year,
        PayrollActual.month < actual_data.month
    ).first()

    ytd_income_before = ytd_before.ytd_income if ytd_before.ytd_income else Decimal('0')
    ytd_tax_before = ytd_before.ytd_tax if ytd_before.ytd_tax else Decimal('0')

    # Calculate НДФЛ for current month
    ndfl_calc = calculate_monthly_ndfl_withholding(
        current_month_income=total_paid,
        ytd_income_before_month=ytd_income_before,
        ytd_tax_withheld=ytd_tax_before,
        year=actual_data.year
    )

    # Override income_tax_amount with calculated value
    income_tax_amount = Decimal(str(ndfl_calc['tax_to_withhold']))
    income_tax_rate = Decimal(str(ndfl_calc['monthly_effective_rate'])) / Decimal('100')

    # Create new payroll actual
    new_actual = PayrollActual(
        **{**actual_data.model_dump(), 'income_tax_amount': income_tax_amount, 'income_tax_rate': income_tax_rate},
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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, actual.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll actual not found"
        )

    # Update actual fields
    update_data = actual_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(actual, field, value)

    # Recalculate total paid amount (salary + all bonus types + other)
    actual.total_paid = (
        actual.base_salary_paid +
        actual.monthly_bonus_paid +
        actual.quarterly_bonus_paid +
        actual.annual_bonus_paid +
        actual.other_payments_paid
    )

    # Auto-recalculate НДФЛ using progressive scale
    # Get YTD income and tax before current month (excluding current month)
    from app.utils.ndfl_calculator import calculate_monthly_ndfl_withholding

    ytd_before = db.query(
        func.sum(PayrollActual.total_paid).label('ytd_income'),
        func.sum(PayrollActual.income_tax_amount).label('ytd_tax')
    ).filter(
        PayrollActual.employee_id == actual.employee_id,
        PayrollActual.year == actual.year,
        PayrollActual.month < actual.month
    ).first()

    ytd_income_before = ytd_before.ytd_income if ytd_before.ytd_income else Decimal('0')
    ytd_tax_before = ytd_before.ytd_tax if ytd_before.ytd_tax else Decimal('0')

    # Calculate НДФЛ for current month
    ndfl_calc = calculate_monthly_ndfl_withholding(
        current_month_income=actual.total_paid,
        ytd_income_before_month=ytd_income_before,
        ytd_tax_withheld=ytd_tax_before,
        year=actual.year
    )

    # Update income_tax_amount and rate with calculated values
    actual.income_tax_amount = Decimal(str(ndfl_calc['tax_to_withhold']))
    actual.income_tax_rate = Decimal(str(ndfl_calc['monthly_effective_rate'])) / Decimal('100')

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
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, actual.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll actual not found"
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


@router.get("/actuals/export")
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
            "Премия месячная выплачено": float(actual.monthly_bonus_paid),
            "Премия квартальная выплачено": float(actual.quarterly_bonus_paid),
            "Премия годовая выплачено": float(actual.annual_bonus_paid),
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
        func.sum(PayrollPlan.monthly_bonus).label('total_monthly_bonus'),
        func.sum(PayrollPlan.quarterly_bonus).label('total_quarterly_bonus'),
        func.sum(PayrollPlan.annual_bonus).label('total_annual_bonus'),
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
            total_monthly_bonus=row.total_monthly_bonus or Decimal(0),
            total_quarterly_bonus=row.total_quarterly_bonus or Decimal(0),
            total_annual_bonus=row.total_annual_bonus or Decimal(0),
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
        func.sum(PayrollPlan.monthly_bonus).label('planned_monthly_bonus'),
        func.sum(PayrollPlan.quarterly_bonus).label('planned_quarterly_bonus'),
        func.sum(PayrollPlan.annual_bonus).label('planned_annual_bonus'),
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
        func.sum(PayrollActual.monthly_bonus_paid).label('actual_monthly_bonus'),
        func.sum(PayrollActual.quarterly_bonus_paid).label('actual_quarterly_bonus'),
        func.sum(PayrollActual.annual_bonus_paid).label('actual_annual_bonus'),
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
            # Calculate individual bonus components
            planned_monthly = plan.planned_monthly_bonus if plan else Decimal(0)
            planned_quarterly = plan.planned_quarterly_bonus if plan else Decimal(0)
            planned_annual = plan.planned_annual_bonus if plan else Decimal(0)
            actual_monthly = actual.actual_monthly_bonus if actual else Decimal(0)
            actual_quarterly = actual.actual_quarterly_bonus if actual else Decimal(0)
            actual_annual = actual.actual_annual_bonus if actual else Decimal(0)

            dynamics.append(PayrollDynamics(
                year=year,
                month=month,
                planned_base_salary=plan.planned_base_salary if plan else Decimal(0),
                planned_monthly_bonus=planned_monthly,
                planned_quarterly_bonus=planned_quarterly,
                planned_annual_bonus=planned_annual,
                planned_bonus=planned_monthly + planned_quarterly + planned_annual,  # Total planned bonuses
                planned_other=plan.planned_other if plan else Decimal(0),
                planned_total=plan.planned_total if plan else Decimal(0),
                actual_base_salary=actual.actual_base_salary if actual else Decimal(0),
                actual_monthly_bonus=actual_monthly,
                actual_quarterly_bonus=actual_quarterly,
                actual_annual_bonus=actual_annual,
                actual_bonus=actual_monthly + actual_quarterly + actual_annual,  # Total actual bonuses
                actual_other=actual.actual_other if actual else Decimal(0),
                actual_total=actual.actual_total if actual else Decimal(0),
                employee_count=plan.employee_count if plan else 0
            ))

    return dynamics


@router.get("/analytics/forecast", response_model=List[PayrollForecast])
async def get_payroll_forecast(
    months_ahead: int = Query(3, ge=1, le=12, description="Number of months to forecast"),
    historical_months: int = Query(6, ge=3, le=12, description="Number of historical months to use"),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll forecast for future months based on historical data

    Uses simple moving average with trend adjustment for forecasting
    """
    from datetime import datetime as dt
    from dateutil.relativedelta import relativedelta

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

    # Get current date
    now = dt.now()
    current_year = now.year
    current_month = now.month

    # Get historical data for the last N months
    historical_data = []
    for i in range(historical_months, 0, -1):
        date = now - relativedelta(months=i)
        year = date.year
        month = date.month

        # Query plans for this month
        plan_query = db.query(
            func.sum(PayrollPlan.base_salary).label('base_salary'),
            func.sum(PayrollPlan.monthly_bonus).label('monthly_bonus'),
            func.sum(PayrollPlan.quarterly_bonus).label('quarterly_bonus'),
            func.sum(PayrollPlan.annual_bonus).label('annual_bonus'),
            func.sum(PayrollPlan.other_payments).label('other_payments'),
            func.sum(PayrollPlan.total_planned).label('total'),
            func.count(func.distinct(PayrollPlan.employee_id)).label('employee_count')
        ).filter(
            and_(
                PayrollPlan.year == year,
                PayrollPlan.month == month
            )
        )

        if dept_filter:
            plan_query = plan_query.filter(PayrollPlan.department_id == dept_filter)

        result = plan_query.first()

        if result and result.total:
            historical_data.append({
                'year': year,
                'month': month,
                'base_salary': float(result.base_salary or 0),
                'monthly_bonus': float(result.monthly_bonus or 0),
                'quarterly_bonus': float(result.quarterly_bonus or 0),
                'annual_bonus': float(result.annual_bonus or 0),
                'other_payments': float(result.other_payments or 0),
                'total': float(result.total or 0),
                'employee_count': result.employee_count
            })

    if not historical_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No historical data available for forecasting"
        )

    # Calculate averages from historical data
    avg_base_salary = sum(d['base_salary'] for d in historical_data) / len(historical_data)
    avg_monthly_bonus = sum(d['monthly_bonus'] for d in historical_data) / len(historical_data)
    avg_quarterly_bonus = sum(d['quarterly_bonus'] for d in historical_data) / len(historical_data)
    avg_annual_bonus = sum(d['annual_bonus'] for d in historical_data) / len(historical_data)
    avg_other = sum(d['other_payments'] for d in historical_data) / len(historical_data)
    avg_total = sum(d['total'] for d in historical_data) / len(historical_data)
    avg_employee_count = int(sum(d['employee_count'] for d in historical_data) / len(historical_data))

    # Calculate trend (simple linear trend based on first and last months)
    if len(historical_data) >= 3:
        first_half_avg = sum(d['total'] for d in historical_data[:len(historical_data)//2]) / (len(historical_data)//2)
        second_half_avg = sum(d['total'] for d in historical_data[len(historical_data)//2:]) / (len(historical_data) - len(historical_data)//2)
        trend_factor = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
    else:
        trend_factor = 0

    # Determine confidence level
    if len(historical_data) >= 6:
        confidence = "high"
    elif len(historical_data) >= 4:
        confidence = "medium"
    else:
        confidence = "low"

    # Generate forecasts
    forecasts = []
    for i in range(1, months_ahead + 1):
        forecast_date = now + relativedelta(months=i)
        forecast_year = forecast_date.year
        forecast_month = forecast_date.month

        # Apply trend to forecast (compound monthly)
        monthly_trend = trend_factor / len(historical_data)
        trend_multiplier = 1 + (monthly_trend * i)

        # Calculate individual bonus components
        fc_monthly = Decimal(str(avg_monthly_bonus * trend_multiplier))
        fc_quarterly = Decimal(str(avg_quarterly_bonus * trend_multiplier))
        fc_annual = Decimal(str(avg_annual_bonus * trend_multiplier))

        forecasts.append(PayrollForecast(
            year=forecast_year,
            month=forecast_month,
            forecasted_total=Decimal(str(avg_total * trend_multiplier)),
            forecasted_base_salary=Decimal(str(avg_base_salary * trend_multiplier)),
            forecasted_monthly_bonus=fc_monthly,
            forecasted_quarterly_bonus=fc_quarterly,
            forecasted_annual_bonus=fc_annual,
            forecasted_bonus=fc_monthly + fc_quarterly + fc_annual,  # Total forecasted bonuses
            forecasted_other=Decimal(str(avg_other * trend_multiplier)),
            employee_count=avg_employee_count,
            confidence=confidence,
            based_on_months=len(historical_data)
        ))

    return forecasts


# ==================== Import Endpoints ====================

@router.post("/plans/import", status_code=status.HTTP_200_OK)
async def import_payroll_plans(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import payroll plans from Excel file

    Expected columns:
    - Год (Year)
    - Месяц (Month)
    - Сотрудник (Employee full name)
    - Оклад (Base salary)
    - Премия (Bonus) - optional
    - Прочие выплаты (Other payments) - optional
    - Примечания (Notes) - optional

    Only ADMIN and MANAGER can import payroll plans
    """
    # Only ADMIN and MANAGER can import
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can import payroll plans"
        )

    # Get user's department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    else:
        # For ADMIN/MANAGER, use their department or allow specifying in file
        department_id = current_user.department_id

    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    try:
        # Read file content
        content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10MB"
            )

        # Parse Excel file
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
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
        required_columns = ['Год', 'Месяц', 'Сотрудник', 'Оклад']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}"
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        total_rows = len(df)

        for index, row in df.iterrows():
            try:
                # Extract and validate data
                year = int(row['Год']) if pd.notna(row['Год']) else None
                month = int(row['Месяц']) if pd.notna(row['Месяц']) else None
                employee_name = str(row['Сотрудник']).strip() if pd.notna(row['Сотрудник']) else None
                base_salary = float(row['Оклад']) if pd.notna(row['Оклад']) else None
                bonus = float(row.get('Премия', 0)) if pd.notna(row.get('Премия', 0)) else 0
                other_payments = float(row.get('Прочие выплаты', 0)) if pd.notna(row.get('Прочие выплаты', 0)) else 0
                notes = str(row.get('Примечания', '')).strip() if pd.notna(row.get('Примечания')) else None

                # Validate required fields
                if not year or not month or not employee_name or base_salary is None:
                    errors.append(f"Row {index + 2}: Missing required fields")
                    skipped_count += 1
                    continue

                if year < 2000 or year > 2100:
                    errors.append(f"Row {index + 2}: Invalid year {year}")
                    skipped_count += 1
                    continue

                if month < 1 or month > 12:
                    errors.append(f"Row {index + 2}: Invalid month {month}")
                    skipped_count += 1
                    continue

                if base_salary < 0:
                    errors.append(f"Row {index + 2}: Base salary cannot be negative")
                    skipped_count += 1
                    continue

                # Find employee by name
                employee = db.query(Employee).filter(
                    Employee.full_name == employee_name
                ).first()

                if not employee:
                    errors.append(f"Row {index + 2}: Employee '{employee_name}' not found")
                    skipped_count += 1
                    continue

                # Check department access - USER and MANAGER can only import to their own department
                if current_user.role in [UserRoleEnum.USER, UserRoleEnum.MANAGER]:
                    if not current_user.department_id:
                        errors.append(f"Row {index + 2}: User has no assigned department")
                        skipped_count += 1
                        continue
                    if employee.department_id != current_user.department_id:
                        errors.append(f"Row {index + 2}: No access to employee from another department")
                        skipped_count += 1
                        continue

                # Check if plan already exists
                existing_plan = db.query(PayrollPlan).filter(
                    and_(
                        PayrollPlan.employee_id == employee.id,
                        PayrollPlan.year == year,
                        PayrollPlan.month == month
                    )
                ).first()

                total_planned = Decimal(str(base_salary)) + Decimal(str(bonus)) + Decimal(str(other_payments))

                if existing_plan:
                    # Update existing plan
                    existing_plan.base_salary = Decimal(str(base_salary))
                    existing_plan.bonus = Decimal(str(bonus))
                    existing_plan.other_payments = Decimal(str(other_payments))
                    existing_plan.total_planned = total_planned
                    if notes:
                        existing_plan.notes = notes
                    updated_count += 1
                else:
                    # Create new plan
                    new_plan = PayrollPlan(
                        employee_id=employee.id,
                        year=year,
                        month=month,
                        base_salary=Decimal(str(base_salary)),
                        bonus=Decimal(str(bonus)),
                        other_payments=Decimal(str(other_payments)),
                        total_planned=total_planned,
                        department_id=employee.department_id,
                        notes=notes
                    )
                    db.add(new_plan)
                    created_count += 1

            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                skipped_count += 1
                continue

        # Commit all changes
        db.commit()

        return {
            "success": True,
            "message": f"Import completed",
            "total_rows": total_rows,
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": errors[:10] if errors else []  # Return first 10 errors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ==================== Integration with Expenses ====================

@router.post("/generate-payroll-expenses")
async def generate_payroll_expenses(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    department_id: Optional[int] = None,
    dry_run: bool = Query(False, description="Preview without creating expenses"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate expense requests for payroll based on PayrollPlan + EmployeeKPI data.

    This integrates FOT (payroll) + KPI + Budget systems by automatically creating
    expense requests for salary payments.

    Args:
        year: Target year
        month: Target month (1-12)
        department_id: Optional department filter (ADMIN/MANAGER can specify, USER auto-filtered)
        dry_run: If True, returns preview without creating expenses

    Returns:
        Statistics about generated expenses and preview data
    """
    from app.db.models import BudgetCategory, CategoryTypeEnum, Expense, ExpenseStatusEnum, EmployeeKPI

    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can generate payroll expenses"
        )

    # Department filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id

    # Find or create "Заработная плата" category
    salary_category = db.query(BudgetCategory).filter(
        BudgetCategory.name == "Заработная плата",
        BudgetCategory.type == CategoryTypeEnum.OPEX
    ).first()

    if not salary_category:
        # Create category for each department or as global
        departments = db.query(Department).filter(Department.is_active == True).all()
        if not departments:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No active departments found"
            )

        # Create for first department (can be enhanced later)
        salary_category = BudgetCategory(
            name="Заработная плата",
            type=CategoryTypeEnum.OPEX,
            description="Автоматически созданная категория для учета зарплаты сотрудников",
            is_active=True,
            department_id=departments[0].id
        )
        db.add(salary_category)
        db.flush()  # Get ID without committing

    # Query payroll plans
    query = db.query(PayrollPlan).join(Employee).filter(
        PayrollPlan.year == year,
        PayrollPlan.month == month,
        Employee.status == EmployeeStatusEnum.ACTIVE
    )

    if department_id:
        query = query.filter(PayrollPlan.department_id == department_id)

    payroll_plans = query.all()

    if not payroll_plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No payroll plans found for {year}-{month:02d}"
        )

    # Prepare expense data
    expenses_to_create = []
    total_amount = Decimal(0)
    employee_count = 0

    for plan in payroll_plans:
        # Get employee
        employee = db.query(Employee).filter(Employee.id == plan.employee_id).first()
        if not employee:
            continue

        # Get KPI data for the same period
        kpi_data = db.query(EmployeeKPI).filter(
            EmployeeKPI.employee_id == plan.employee_id,
            EmployeeKPI.year == year,
            EmployeeKPI.month == month
        ).first()

        # Calculate total salary: base salary + bonuses from KPI
        total_salary = plan.base_salary or Decimal(0)

        if kpi_data:
            # Add KPI bonuses
            total_salary += (kpi_data.monthly_bonus_calculated or Decimal(0))
            total_salary += (kpi_data.quarterly_bonus_calculated or Decimal(0))
            total_salary += (kpi_data.annual_bonus_calculated or Decimal(0))

        # Check if expense already exists
        existing = db.query(Expense).filter(
            Expense.department_id == plan.department_id,
            Expense.category_id == salary_category.id,
            func.extract('year', Expense.request_date) == year,
            func.extract('month', Expense.request_date) == month,
            Expense.comment.ilike(f"%{employee.full_name}%")
        ).first()

        if existing:
            continue  # Skip if already exists

        # Prepare expense data
        expense_data = {
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "position": employee.position,
            "base_salary": plan.base_salary or Decimal(0),
            "kpi_percentage": kpi_data.kpi_percentage if kpi_data else None,
            "kpi_bonuses": (
                (kpi_data.monthly_bonus_calculated or Decimal(0)) +
                (kpi_data.quarterly_bonus_calculated or Decimal(0)) +
                (kpi_data.annual_bonus_calculated or Decimal(0))
            ) if kpi_data else Decimal(0),
            "total_amount": total_salary,
            "department_id": plan.department_id,
        }

        expenses_to_create.append(expense_data)
        total_amount += total_salary
        employee_count += 1

        # If not dry run, create the expense
        if not dry_run:
            expense = Expense(
                department_id=plan.department_id,
                category_id=salary_category.id,
                amount=total_salary,
                request_date=datetime(year, month, 1),
                status=ExpenseStatusEnum.PENDING,
                comment=f"Заработная плата: {employee.full_name} ({employee.position}) за {month:02d}.{year}. "
                        f"Оклад: {plan.base_salary or 0:,.2f} ₽"
                        + (f", КПИ премии: {expense_data['kpi_bonuses']:,.2f} ₽" if expense_data['kpi_bonuses'] > 0 else ""),
                requester=current_user.full_name or current_user.username
            )
            db.add(expense)

    # Commit if not dry run
    if not dry_run:
        db.commit()

    return {
        "success": True,
        "dry_run": dry_run,
        "year": year,
        "month": month,
        "department_id": department_id,
        "salary_category_id": salary_category.id,
        "salary_category_name": salary_category.name,
        "statistics": {
            "employee_count": employee_count,
            "total_amount": float(total_amount),
            "expenses_created": employee_count if not dry_run else 0,
        },
        "preview": expenses_to_create if dry_run else expenses_to_create[:5],  # Show first 5 in non-dry-run
        "message": f"{'Preview: Would create' if dry_run else 'Created'} {employee_count} payroll expense{'s' if employee_count != 1 else ''} for {year}-{month:02d}"
    }


@router.get("/analytics/budget-summary")
async def get_payroll_budget_summary(
    year: int = Query(..., ge=2020, le=2100),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payroll data aggregated in budget format (by month)
    For integration with overall budget planning and analytics
    """
    # Build base query
    query = db.query(
        PayrollPlan.month,
        func.sum(PayrollPlan.total_planned).label('total_planned'),
        func.count(PayrollPlan.id).label('employee_count')
    ).filter(
        PayrollPlan.year == year
    )

    # Apply department filter based on role
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(PayrollPlan.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(PayrollPlan.department_id == department_id)

    # Group by month
    query = query.group_by(PayrollPlan.month).order_by(PayrollPlan.month)

    results = query.all()

    # Format results
    summary = []
    for row in results:
        summary.append({
            "month": row.month,
            "total_planned": float(row.total_planned or 0),
            "employee_count": row.employee_count,
            "category_name": "Заработная плата",
            "type": "OPEX"
        })

    # Calculate totals
    total_amount = sum(item['total_planned'] for item in summary)
    total_employees = sum(item['employee_count'] for item in summary) // len(summary) if summary else 0

    return {
        "year": year,
        "department_id": department_id,
        "monthly_summary": summary,
        "totals": {
            "total_amount": total_amount,
            "average_employees": total_employees,
            "months_with_data": len(summary)
        }
    }


@router.post("/analytics/register-payroll-payment")
async def register_payroll_payment(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    payment_type: str = Query(..., description="Payment type: 'advance' or 'final'"),
    payment_date: Optional[str] = Query(None, description="Payment date in ISO format (YYYY-MM-DD)"),
    department_id: Optional[int] = None,
    dry_run: bool = Query(False, description="Preview without creating records"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Register actual payroll payments based on PayrollPlan

    Creates PayrollActual records with auto-filled amounts from PayrollPlan and EmployeeKPI.
    Supports two payment types:
    - 'advance': 50% of base salary only, no bonuses (typically paid on 25th)
    - 'final': 50% of base salary + 100% bonuses from previous month (typically paid on 10th)

    Args:
        year: Year of payment
        month: Month of payment (1-12)
        payment_type: 'advance' or 'final'
        payment_date: Optional payment date (defaults to 10th for advance, 25th for final)
        department_id: Optional department filter (MANAGER/ADMIN only)
        dry_run: If True, returns preview without creating records

    Returns:
        {
            "success": bool,
            "dry_run": bool,
            "payment_type": str,
            "payment_date": str,
            "statistics": {
                "employee_count": int,
                "total_amount": float,
                "records_created": int
            },
            "preview": List[dict],
            "message": str
        }
    """
    # Validate payment type
    if payment_type not in ['advance', 'final']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payment_type must be 'advance' or 'final'"
        )

    # Calculate payment date if not provided
    if payment_date:
        try:
            parsed_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment_date format. Use YYYY-MM-DD"
            )
    else:
        # Default dates: 25th for advance, 10th for final
        day = 25 if payment_type == 'advance' else 10
        parsed_date = datetime(year, month, day).date()

    # For advance: 50% of base salary only
    # For final: 50% of base salary + 100% of bonuses
    is_advance = payment_type == 'advance'

    # Query PayrollPlan with Employee join
    query = db.query(PayrollPlan, Employee).join(
        Employee, PayrollPlan.employee_id == Employee.id
    ).filter(
        PayrollPlan.year == year,
        PayrollPlan.month == month,
        Employee.status == EmployeeStatusEnum.ACTIVE
    )

    # Apply department filter based on role
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(PayrollPlan.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(PayrollPlan.department_id == department_id)

    payroll_plans = query.all()

    if not payroll_plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active payroll plans found for {year}-{month:02d}"
        )

    # Prepare PayrollActual data
    actuals_to_create = []
    total_amount = Decimal(0)
    employee_count = 0
    skipped_count = 0

    for plan, employee in payroll_plans:
        # Check if PayrollActual already exists for this payment
        existing = db.query(PayrollActual).filter(
            PayrollActual.employee_id == plan.employee_id,
            PayrollActual.year == year,
            PayrollActual.month == month,
            PayrollActual.payment_date == parsed_date
        ).first()

        if existing:
            skipped_count += 1
            continue  # Skip if already registered

        # Calculate amounts based on payment_type
        # Advance (25th): 50% of base salary only
        # Final (10th): 50% of base salary + 100% of bonuses
        if is_advance:
            # Аванс: 50% оклада, без премий
            base_salary = (plan.base_salary or Decimal(0)) * Decimal('0.5')
            monthly_bonus = Decimal(0)
            quarterly_bonus = Decimal(0)
            annual_bonus = Decimal(0)
        else:
            # Окончательный расчет: 50% оклада + все премии
            base_salary = (plan.base_salary or Decimal(0)) * Decimal('0.5')

            # Get KPI data for the same period (only for final payment)
            kpi_data = db.query(EmployeeKPI).filter(
                EmployeeKPI.employee_id == plan.employee_id,
                EmployeeKPI.year == year,
                EmployeeKPI.month == month
            ).first()

            if kpi_data:
                # Используем рассчитанные премии из KPI
                # Месячные премии: всегда начисляются
                monthly_bonus = kpi_data.monthly_bonus_calculated or Decimal(0)

                # Квартальные премии: только в марте, июне, сентябре, декабре
                if month in [3, 6, 9, 12]:
                    quarterly_bonus = kpi_data.quarterly_bonus_calculated or Decimal(0)
                else:
                    quarterly_bonus = Decimal(0)

                # Годовые премии: только в декабре
                if month == 12:
                    annual_bonus = kpi_data.annual_bonus_calculated or Decimal(0)
                else:
                    annual_bonus = Decimal(0)
            else:
                # Если нет данных KPI, используем запланированные премии из PayrollPlan
                monthly_bonus = plan.monthly_bonus or Decimal(0)

                # Квартальные премии: только в марте, июне, сентябре, декабре
                if month in [3, 6, 9, 12]:
                    quarterly_bonus = plan.quarterly_bonus or Decimal(0)
                else:
                    quarterly_bonus = Decimal(0)

                # Годовые премии: только в декабре
                if month == 12:
                    annual_bonus = plan.annual_bonus or Decimal(0)
                else:
                    annual_bonus = Decimal(0)

        # Calculate total
        total_paid = base_salary + monthly_bonus + quarterly_bonus + annual_bonus

        # Prepare actual data
        actual_data = {
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "position": employee.position,
            "base_salary_paid": float(base_salary),
            "monthly_bonus_paid": float(monthly_bonus),
            "quarterly_bonus_paid": float(quarterly_bonus),
            "annual_bonus_paid": float(annual_bonus),
            "total_paid": float(total_paid),
            "payment_type": payment_type,
            "payment_date": parsed_date.isoformat(),
            "department_id": plan.department_id,
        }

        actuals_to_create.append(actual_data)
        total_amount += total_paid
        employee_count += 1

        # If not dry run, create the PayrollActual record
        if not dry_run:
            payroll_actual = PayrollActual(
                year=year,
                month=month,
                employee_id=plan.employee_id,
                department_id=plan.department_id,
                base_salary_paid=base_salary,
                monthly_bonus_paid=monthly_bonus,
                quarterly_bonus_paid=quarterly_bonus,
                annual_bonus_paid=annual_bonus,
                other_payments_paid=Decimal(0),
                total_paid=total_paid,
                payment_date=parsed_date,
                notes=f"{'Аванс' if payment_type == 'advance' else 'Окончательный расчет'} за {month:02d}.{year}"
            )
            db.add(payroll_actual)

    # Commit if not dry run
    if not dry_run:
        db.commit()

    return {
        "success": True,
        "dry_run": dry_run,
        "payment_type": payment_type,
        "payment_date": parsed_date.isoformat(),
        "year": year,
        "month": month,
        "department_id": department_id,
        "statistics": {
            "employee_count": employee_count,
            "total_amount": float(total_amount),
            "records_created": employee_count if not dry_run else 0,
            "skipped_existing": skipped_count,
        },
        "preview": actuals_to_create if dry_run else actuals_to_create[:10],  # Show first 10 in non-dry-run
        "message": f"{'Preview: Would register' if dry_run else 'Registered'} {employee_count} payroll payment{'s' if employee_count != 1 else ''} "
                   f"({payment_type}) for {year}-{month:02d}{f'. Skipped {skipped_count} existing record(s)' if skipped_count > 0 else ''}"
    }


# ==================== Salary Distribution (Histogram) ====================

@router.post("/analytics/register-payroll-payment-bulk")
async def register_payroll_payment_bulk(
    payments: List[PayrollActualCreate],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk register payroll payments with custom amounts (for edited data)

    This endpoint allows registering multiple PayrollActual records at once
    with custom amounts that can be edited by the user.

    Args:
        payments: List of payroll actual records to create

    Returns:
        {
            "success": bool,
            "created_count": int,
            "skipped_count": int,
            "total_amount": Decimal,
            "errors": List[str]
        }
    """
    # Only ADMIN and MANAGER can register payroll
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can register payroll payments"
        )

    created_count = 0
    skipped_count = 0
    total_amount = Decimal(0)
    errors = []

    for payment in payments:
        try:
            # Get employee to verify access and get department_id
            employee = db.query(Employee).filter(Employee.id == payment.employee_id).first()
            if not employee:
                errors.append(f"Employee ID {payment.employee_id} not found")
                skipped_count += 1
                continue

            # Check department access
            # Don't disclose which employees exist in other departments
            if not check_department_access(current_user, employee.department_id):
                errors.append(f"Employee ID {payment.employee_id} not found")
                skipped_count += 1
                continue

            # Check if actual already exists
            existing = db.query(PayrollActual).filter(
                PayrollActual.employee_id == payment.employee_id,
                PayrollActual.year == payment.year,
                PayrollActual.month == payment.month,
                PayrollActual.payment_date == payment.payment_date
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Calculate total paid
            total_paid = (
                payment.base_salary_paid +
                payment.monthly_bonus_paid +
                payment.quarterly_bonus_paid +
                payment.annual_bonus_paid +
                payment.other_payments_paid
            )

            # Create PayrollActual record
            payroll_actual = PayrollActual(
                year=payment.year,
                month=payment.month,
                employee_id=payment.employee_id,
                department_id=employee.department_id,
                base_salary_paid=payment.base_salary_paid,
                monthly_bonus_paid=payment.monthly_bonus_paid,
                quarterly_bonus_paid=payment.quarterly_bonus_paid,
                annual_bonus_paid=payment.annual_bonus_paid,
                other_payments_paid=payment.other_payments_paid,
                income_tax_rate=payment.income_tax_rate,
                income_tax_amount=payment.income_tax_amount,
                social_tax_amount=payment.social_tax_amount,
                total_paid=total_paid,
                payment_date=payment.payment_date,
                notes=f"Массовая регистрация выплат за {payment.month:02d}.{payment.year}"
            )
            db.add(payroll_actual)

            created_count += 1
            total_amount += total_paid

        except Exception as e:
            errors.append(f"Error processing employee ID {payment.employee_id}: {str(e)}")
            skipped_count += 1
            continue

    # Commit all changes
    if created_count > 0:
        db.commit()

    return {
        "success": True,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "total_amount": float(total_amount),
        "errors": errors[:10] if errors else []  # Return first 10 errors
    }


@router.get("/analytics/salary-distribution")
async def get_salary_distribution(
    year: Optional[int] = Query(None, description="Filter by year"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    bucket_size: int = Query(50000, ge=10000, le=200000, description="Size of each salary bucket (default 50000)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get salary distribution across employees (histogram)

    Returns distribution of salaries by buckets (ranges) with statistics:
    - Number of employees in each range
    - Percentage of total employees
    - Average salary in range

    Args:
        year: Optional year to filter by (uses most recent payroll plans if not specified)
        department_id: Optional department filter
        bucket_size: Size of each salary bucket/bin (default 50000)

    Returns:
        {
            "total_employees": int,
            "buckets": [
                {
                    "range_min": Decimal,
                    "range_max": Decimal,
                    "range_label": str,
                    "employee_count": int,
                    "percentage": float,
                    "avg_salary": Decimal
                }
            ],
            "statistics": SalaryStatistics
        }
    """
    from app.schemas.payroll import SalaryDistribution, SalaryDistributionBucket

    # Apply department filter based on role
    dept_filter = None
    if current_user.role == UserRoleEnum.USER:
        dept_filter = current_user.department_id
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            dept_filter = department_id

    # Get active employees with their total compensation
    # Total compensation = base_salary + monthly_bonus_base + quarterly_bonus_base/4 + annual_bonus_base/12
    # (amortizing quarterly and annual bonuses to monthly equivalent)

    query = db.query(
        Employee,
        (
            Employee.base_salary +
            func.coalesce(Employee.monthly_bonus_base, 0) +
            func.coalesce(Employee.quarterly_bonus_base, 0) / 4 +
            func.coalesce(Employee.annual_bonus_base, 0) / 12
        ).label('total_compensation')
    ).filter(
        Employee.status == EmployeeStatusEnum.ACTIVE
    )

    if dept_filter:
        query = query.filter(Employee.department_id == dept_filter)

    # Get all employees with their total compensation
    employees_data = query.all()

    if not employees_data:
        # Return empty distribution
        return {
            "total_employees": 0,
            "buckets": [],
            "statistics": {
                "total_employees": 0,
                "avg_salary": 0,
                "median_salary": 0,
                "min_salary": 0,
                "max_salary": 0,
                "percentile_25": 0,
                "percentile_75": 0,
                "percentile_90": 0,
                "std_deviation": 0
            }
        }

    # Extract salaries
    salaries = [float(total_comp) for _, total_comp in employees_data]
    salaries_sorted = sorted(salaries)
    total_employees = len(salaries)

    # Calculate statistics
    import statistics
    avg_salary = statistics.mean(salaries)
    median_salary = statistics.median(salaries)
    min_salary = min(salaries)
    max_salary = max(salaries)

    # Calculate percentiles
    def percentile(data, p):
        n = len(data)
        if n == 0:
            return 0
        k = (n - 1) * p / 100
        f = int(k)
        c = k - f
        if f + 1 < n:
            return data[f] + (data[f + 1] - data[f]) * c
        else:
            return data[f]

    percentile_25 = percentile(salaries_sorted, 25)
    percentile_75 = percentile(salaries_sorted, 75)
    percentile_90 = percentile(salaries_sorted, 90)

    std_deviation = statistics.stdev(salaries) if len(salaries) > 1 else 0

    # Create buckets (histogram bins)
    buckets = []

    # Determine min and max bucket boundaries
    bucket_min = int(min_salary // bucket_size) * bucket_size
    bucket_max = int(max_salary // bucket_size + 1) * bucket_size

    # Create bucket ranges
    current_min = bucket_min
    while current_min < bucket_max:
        current_max = current_min + bucket_size

        # Count employees in this range
        employees_in_range = [
            sal for sal in salaries
            if current_min <= sal < current_max or (current_max == bucket_max and sal == current_max)
        ]

        if employees_in_range:
            count = len(employees_in_range)
            percentage = (count / total_employees) * 100
            avg_in_range = sum(employees_in_range) / count

            # Format range label
            if current_min >= 1000000:
                label = f"{current_min // 1000}k-{current_max // 1000}k"
            else:
                label = f"{int(current_min):,}-{int(current_max):,}"

            buckets.append({
                "range_min": Decimal(str(current_min)),
                "range_max": Decimal(str(current_max)),
                "range_label": label,
                "employee_count": count,
                "percentage": round(percentage, 2),
                "avg_salary": Decimal(str(round(avg_in_range, 2)))
            })

        current_min = current_max

    return {
        "total_employees": total_employees,
        "buckets": buckets,
        "statistics": {
            "total_employees": total_employees,
            "avg_salary": Decimal(str(round(avg_salary, 2))),
            "median_salary": Decimal(str(round(median_salary, 2))),
            "min_salary": Decimal(str(round(min_salary, 2))),
            "max_salary": Decimal(str(round(max_salary, 2))),
            "percentile_25": Decimal(str(round(percentile_25, 2))),
            "percentile_75": Decimal(str(round(percentile_75, 2))),
            "percentile_90": Decimal(str(round(percentile_90, 2))),
            "std_deviation": Decimal(str(round(std_deviation, 2)))
        }
    }

# ============================================
# НДФЛ (Income Tax) Calculation Endpoints
# ============================================

from pydantic import BaseModel, Field
from app.utils.ndfl_calculator import (
    calculate_progressive_ndfl,
    calculate_monthly_ndfl_withholding,
    get_tax_brackets_info
)


class NDFLCalculationRequest(BaseModel):
    """Request for NDFL calculation"""
    annual_income: Decimal = Field(..., ge=0, description="Годовой доход (брутто)")
    year: Optional[int] = Field(None, description="Год (по умолчанию текущий)")


class MonthlyNDFLRequest(BaseModel):
    """Request for monthly NDFL withholding calculation"""
    current_month_income: Decimal = Field(..., ge=0, description="Доход за текущий месяц (брутто)")
    ytd_income_before_month: Decimal = Field(0, ge=0, description="Доход с начала года до текущего месяца")
    ytd_tax_withheld: Decimal = Field(0, ge=0, description="НДФЛ удержанный с начала года")
    year: Optional[int] = Field(None, description="Год (по умолчанию текущий)")


class EmployeeYTDIncomeRequest(BaseModel):
    """Request to calculate YTD income for employee"""
    employee_id: int
    year: int
    up_to_month: int = Field(..., ge=1, le=12, description="До какого месяца включительно")


@router.post("/ndfl/calculate")
def calculate_ndfl(
    request: NDFLCalculationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Расчет НДФЛ по прогрессивной шкале для годового дохода.

    Поддерживает:
    - 2024: двухступенчатая шкала (13% / 15%)
    - 2025+: пятиступенчатая шкала (13% / 15% / 18% / 20% / 22%)

    Режимы расчета:
    - gross (по умолчанию): расчет налога от дохода до налогов
    - net: обратный расчет - находит необходимый доход до налогов для получения желаемого дохода на руки

    Returns:
        - total_tax: Сумма НДФЛ
        - effective_rate: Эффективная ставка (%)
        - net_income: Чистый доход (на руки)
        - gross_income: Доход до налогов (только для режима 'net')
        - breakdown: Разбивка по ступеням
        - details: Детальный расчет
        - calculation_mode: Режим расчета
    """
    # Get calculation mode from request using model_dump to handle defaults properly
    request_data = request.model_dump()
    mode = request_data.get('calculation_mode', 'gross') or "gross"

    # Debug logging
    print(f"[NDFL DEBUG] Request: annual_income={request.annual_income}, year={request.year}, mode={mode}")

    if mode == "net":
        # Обратный расчет: net -> gross
        result = calculate_gross_from_net(
            net_income=request.annual_income,
            year=request.year
        )
        input_label = "desired_net_income"
    else:
        # Прямой расчет: gross -> net
        result = calculate_progressive_ndfl(
            annual_income=request.annual_income,
            year=request.year
        )
        input_label = "annual_income"

    result['calculation_mode'] = mode

    return {
        "success": True,
        "calculation": result,
        "input": {
            input_label: float(request.annual_income),
            "year": result['year'],
            "calculation_mode": mode
        }
    }


@router.post("/ndfl/calculate-monthly")
def calculate_monthly_ndfl(
    request: MonthlyNDFLRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Расчет НДФЛ к удержанию за текущий месяц с учетом накопленного дохода.

    Правильный расчет по формуле:
    1. Рассчитать общий НДФЛ на доход с начала года (включая текущий месяц)
    2. Вычесть НДФЛ, уже удержанный в предыдущих месяцах
    3. Результат = НДФЛ к удержанию в текущем месяце

    Returns:
        - tax_to_withhold: НДФЛ к удержанию в этом месяце
        - ytd_income_total: Доход с начала года (всего)
        - ytd_tax_total: НДФЛ с начала года (всего)
        - monthly_effective_rate: Эффективная ставка за месяц
        - net_income_this_month: Чистый доход за месяц (на руки)
        - calculation_details: Детали расчета
        - breakdown: Разбивка по ступеням
    """
    result = calculate_monthly_ndfl_withholding(
        current_month_income=request.current_month_income,
        ytd_income_before_month=request.ytd_income_before_month,
        ytd_tax_withheld=request.ytd_tax_withheld,
        year=request.year
    )

    return {
        "success": True,
        "calculation": result,
        "input": {
            "current_month_income": float(request.current_month_income),
            "ytd_income_before_month": float(request.ytd_income_before_month),
            "ytd_tax_withheld": float(request.ytd_tax_withheld),
            "year": result['year']
        }
    }


@router.get("/ndfl/brackets")
def get_ndfl_brackets(
    year: Optional[int] = Query(None, description="Год (по умолчанию текущий)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить информацию о ступенях НДФЛ для заданного года.

    Returns:
        - year: Год
        - system: Тип системы налогообложения
        - brackets: Список ступеней с порогами и ставками
        - description: Описание системы
    """
    result = get_tax_brackets_info(year=year)

    return {
        "success": True,
        "brackets_info": result
    }


@router.post("/ndfl/employee-ytd")
def get_employee_ytd_income(
    request: EmployeeYTDIncomeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить накопленный доход и удержанный НДФЛ для сотрудника с начала года.

    Используется для автоматического расчета НДФЛ при вводе зарплаты.

    Returns:
        - employee_id: ID сотрудника
        - year: Год
        - up_to_month: До какого месяца (включительно)
        - ytd_income: Доход с начала года
        - ytd_tax_withheld: НДФЛ удержанный с начала года
        - months_data: Детализация по месяцам
    """
    # Check employee exists and user has access
    employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access (multi-tenancy)
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if employee.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

    # Query payroll actuals for the year up to specified month
    payroll_actuals = db.query(PayrollActual).filter(
        PayrollActual.employee_id == request.employee_id,
        PayrollActual.year == request.year,
        PayrollActual.month <= request.up_to_month
    ).order_by(PayrollActual.month).all()

    ytd_income = Decimal('0')
    ytd_tax_withheld = Decimal('0')
    months_data = []

    for actual in payroll_actuals:
        ytd_income += actual.total_paid
        ytd_tax_withheld += actual.income_tax_amount

        months_data.append({
            'month': actual.month,
            'income': float(actual.total_paid),
            'tax_withheld': float(actual.income_tax_amount),
            'tax_rate': float(actual.income_tax_rate)
        })

    return {
        "success": True,
        "employee_id": request.employee_id,
        "employee_name": employee.full_name,
        "year": request.year,
        "up_to_month": request.up_to_month,
        "ytd_income": float(ytd_income),
        "ytd_tax_withheld": float(ytd_tax_withheld),
        "months_count": len(payroll_actuals),
        "months_data": months_data
    }


# ============================================================================
# TAX & SOCIAL CONTRIBUTIONS ANALYTICS
# ============================================================================

@router.get("/analytics/tax-burden")
async def get_tax_burden_analytics(
    year: int = Query(..., description="Year"),
    month: Optional[int] = Query(None, description="Month (1-12), if None - year total"),
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    employee_id: Optional[int] = Query(None, description="Employee ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get tax burden analytics: НДФЛ + social contributions.

    Returns total tax burden for specified period.
    """
    # Build query filters
    filters = [
        PayrollActual.year == year,
        PayrollActual.is_active == True
    ]

    if month:
        filters.append(PayrollActual.month == month)

    # Department access control
    if current_user.role == UserRoleEnum.USER:
        filters.append(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        filters.append(PayrollActual.department_id == department_id)

    if employee_id:
        filters.append(PayrollActual.employee_id == employee_id)

    # Get payroll actuals
    payroll_actuals = db.query(PayrollActual).filter(and_(*filters)).all()

    if not payroll_actuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payroll data found for the specified period"
        )

    # Calculate totals
    gross_payroll = sum(actual.total_paid for actual in payroll_actuals)

    # Calculate НДФЛ
    ndfl_result = calculate_progressive_ndfl(Decimal(gross_payroll), year)

    # Calculate social contributions
    contributions_result = calculate_social_contributions(Decimal(gross_payroll), year)

    # Total tax burden
    total_ndfl = Decimal(str(ndfl_result['total_tax']))
    total_contributions = Decimal(str(contributions_result['total_contributions']))
    total_taxes = total_ndfl + total_contributions

    # Net payroll
    net_payroll = gross_payroll - total_ndfl

    # Employer cost
    employer_cost = gross_payroll + total_contributions

    # Effective rates
    effective_burden_rate = float((total_taxes / Decimal(gross_payroll) * 100)) if gross_payroll > 0 else 0.0

    return {
        "period": f"{year}-{month:02d}" if month else f"{year}",
        "gross_payroll": float(gross_payroll),
        "ndfl": {
            "total": float(total_ndfl),
            "effective_rate": ndfl_result['effective_rate'],
            "breakdown": ndfl_result.get('breakdown', [])
        },
        "social_contributions": contributions_result,
        "net_payroll": float(net_payroll),
        "total_tax_burden": float(total_taxes),
        "effective_burden_rate": effective_burden_rate,
        "employer_cost": float(employer_cost),
        "employees_count": len(set(a.employee_id for a in payroll_actuals))
    }


@router.get("/analytics/tax-breakdown-by-month")
async def get_tax_breakdown_by_month(
    year: int = Query(..., description="Year"),
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly tax breakdown for the year.

    Returns array of monthly data with НДФЛ and social contributions.
    """
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    # Build base filters
    base_filters = [
        PayrollActual.year == year
    ]

    # Department access control
    if current_user.role == UserRoleEnum.USER:
        base_filters.append(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        base_filters.append(PayrollActual.department_id == department_id)

    result = []

    for month in range(1, 13):
        filters = base_filters + [PayrollActual.month == month]

        # Get monthly payroll
        monthly_actuals = db.query(PayrollActual).filter(and_(*filters)).all()

        if not monthly_actuals:
            # No data for this month - add zero values
            result.append({
                "month": month,
                "month_name": month_names[month - 1],
                "gross_payroll": 0.0,
                "ndfl": 0.0,
                "pfr": 0.0,
                "foms": 0.0,
                "fss": 0.0,
                "total_taxes": 0.0,
                "net_payroll": 0.0,
                "employer_cost": 0.0
            })
            continue

        # Calculate monthly gross
        monthly_gross = sum(actual.total_paid for actual in monthly_actuals)

        # Calculate НДФЛ
        ndfl_result = calculate_progressive_ndfl(Decimal(monthly_gross), year)
        monthly_ndfl = Decimal(str(ndfl_result['total_tax']))

        # Calculate social contributions
        contributions = calculate_social_contributions(Decimal(monthly_gross), year)
        monthly_pfr = Decimal(str(contributions['pfr']['total']))
        monthly_foms = Decimal(str(contributions['foms']['total']))
        monthly_fss = Decimal(str(contributions['fss']['total']))
        monthly_contributions = monthly_pfr + monthly_foms + monthly_fss

        # Totals
        monthly_taxes = monthly_ndfl + monthly_contributions
        monthly_net = monthly_gross - monthly_ndfl
        monthly_employer_cost = monthly_gross + monthly_contributions

        result.append({
            "month": month,
            "month_name": month_names[month - 1],
            "gross_payroll": float(monthly_gross),
            "ndfl": float(monthly_ndfl),
            "pfr": float(monthly_pfr),
            "foms": float(monthly_foms),
            "fss": float(monthly_fss),
            "total_taxes": float(monthly_taxes),
            "net_payroll": float(monthly_net),
            "employer_cost": float(monthly_employer_cost)
        })

    return result


@router.get("/analytics/tax-by-employee")
async def get_tax_by_employee(
    year: int = Query(..., description="Year"),
    month: Optional[int] = Query(None, description="Month (1-12), if None - year total"),
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get tax burden by employee.

    Returns array of employee tax data.
    """
    # Build filters
    filters = [
        PayrollActual.year == year,
        PayrollActual.is_active == True
    ]

    if month:
        filters.append(PayrollActual.month == month)

    # Department access control
    if current_user.role == UserRoleEnum.USER:
        filters.append(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        filters.append(PayrollActual.department_id == department_id)

    # Get payroll actuals
    payroll_actuals = db.query(PayrollActual).filter(and_(*filters)).all()

    if not payroll_actuals:
        return []

    # Group by employee
    employee_data = {}
    for actual in payroll_actuals:
        emp_id = actual.employee_id
        if emp_id not in employee_data:
            employee_data[emp_id] = {
                'employee_id': emp_id,
                'gross_income': 0.0,
            }
        employee_data[emp_id]['gross_income'] += actual.total_paid

    # Get employee details
    employee_ids = list(employee_data.keys())
    employees = db.query(Employee).filter(Employee.id.in_(employee_ids)).all()
    employee_map = {e.id: e for e in employees}

    result = []
    for emp_id, data in employee_data.items():
        employee = employee_map.get(emp_id)
        if not employee:
            continue

        gross_income = Decimal(str(data['gross_income']))

        # Calculate taxes
        ndfl_result = calculate_progressive_ndfl(gross_income, year)
        contributions = calculate_social_contributions(gross_income, year)

        ndfl_total = Decimal(str(ndfl_result['total_tax']))
        contributions_total = Decimal(str(contributions['total_contributions']))

        net_income = gross_income - ndfl_total
        total_taxes = ndfl_total + contributions_total

        effective_tax_rate = float(ndfl_result['effective_rate'])
        effective_burden_rate = float((total_taxes / gross_income * 100)) if gross_income > 0 else 0.0

        result.append({
            'employee_id': emp_id,
            'employee_name': employee.full_name,
            'position': employee.position,
            'gross_income': float(gross_income),
            'ndfl': float(ndfl_total),
            'social_contributions': float(contributions_total),
            'net_income': float(net_income),
            'total_taxes': float(total_taxes),
            'effective_tax_rate': effective_tax_rate,
            'effective_burden_rate': effective_burden_rate
        })

    # Sort by gross_income descending
    result.sort(key=lambda x: x['gross_income'], reverse=True)

    return result


@router.get("/analytics/cost-waterfall")
async def get_cost_waterfall(
    year: int = Query(..., description="Year"),
    month: Optional[int] = Query(None, description="Month (1-12), if None - year total"),
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get cost waterfall data for Waterfall chart.

    Returns breakdown of: Base Salary → Bonuses → Taxes → Net
    """
    # Build filters
    filters = [
        PayrollActual.year == year,
        PayrollActual.is_active == True
    ]

    if month:
        filters.append(PayrollActual.month == month)

    # Department access control
    if current_user.role == UserRoleEnum.USER:
        filters.append(PayrollActual.department_id == current_user.department_id)
    elif department_id:
        filters.append(PayrollActual.department_id == department_id)

    # Get payroll actuals
    payroll_actuals = db.query(PayrollActual).filter(and_(*filters)).all()

    if not payroll_actuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payroll data found for the specified period"
        )

    # Calculate components
    base_salary = sum(actual.base_salary or 0 for actual in payroll_actuals)
    monthly_bonus = sum(actual.monthly_bonus or 0 for actual in payroll_actuals)
    quarterly_bonus = sum(actual.quarterly_bonus or 0 for actual in payroll_actuals)
    annual_bonus = sum(actual.annual_bonus or 0 for actual in payroll_actuals)

    gross_total = base_salary + monthly_bonus + quarterly_bonus + annual_bonus

    # Calculate taxes
    ndfl_result = calculate_progressive_ndfl(Decimal(gross_total), year)
    contributions = calculate_social_contributions(Decimal(gross_total), year)

    ndfl = Decimal(str(ndfl_result['total_tax']))
    pfr = Decimal(str(contributions['pfr']['total']))
    foms = Decimal(str(contributions['foms']['total']))
    fss = Decimal(str(contributions['fss']['total']))

    net_payroll = gross_total - ndfl
    total_employer_cost = gross_total + pfr + foms + fss

    return {
        'base_salary': float(base_salary),
        'monthly_bonus': float(monthly_bonus),
        'quarterly_bonus': float(quarterly_bonus),
        'annual_bonus': float(annual_bonus),
        'gross_total': float(gross_total),
        'ndfl': float(ndfl),
        'pfr': float(pfr),
        'foms': float(foms),
        'fss': float(fss),
        'net_payroll': float(net_payroll),
        'total_employer_cost': float(total_employer_cost)
    }
