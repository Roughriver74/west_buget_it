"""
Employee management API endpoints for Payroll (FOT)
Handles CRUD operations for employees
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
import pandas as pd
import io

from app.db.session import get_db
from app.db.models import (
    Employee, User, UserRoleEnum, Department, SalaryHistory, EmployeeStatusEnum,
    PayrollPlan, PayrollActual, EmployeeKPI
)
from app.schemas.payroll import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeInDB,
    EmployeeWithSalaryHistory,
    SalaryHistoryCreate,
    SalaryHistoryInDB,
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


@router.get("/", response_model=List[EmployeeInDB])
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    status_filter: Optional[EmployeeStatusEnum] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all employees with filtering options

    - **ADMIN/MANAGER**: Can see all employees from all departments
    - **USER**: Can only see employees from their own department
    """
    query = db.query(Employee)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    # Apply status filter
    if status_filter:
        query = query.filter(Employee.status == status_filter)

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(search_pattern),
                Employee.position.ilike(search_pattern),
                Employee.employee_number.ilike(search_pattern)
            )
        )

    employees = query.offset(skip).limit(limit).all()
    return employees


@router.get("/{employee_id}", response_model=EmployeeWithSalaryHistory)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific employee by ID with salary history
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    return employee


@router.post("/", response_model=EmployeeInDB, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new employee (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can create employees
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can create employees"
        )

    # Auto-assign department_id from current_user
    department_id = current_user.department_id

    # Check if department exists
    department = db.query(Department).filter(
        Department.id == department_id
    ).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Check if employee number already exists (if provided)
    if employee_data.employee_number:
        existing = db.query(Employee).filter(
            Employee.employee_number == employee_data.employee_number,
            Employee.department_id == department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee number already exists in this department"
            )

    # Create new employee with auto-assigned department_id
    employee_dict = employee_data.model_dump()
    employee_dict['department_id'] = department_id
    new_employee = Employee(**employee_dict)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    # Create initial salary history record
    salary_history = SalaryHistory(
        employee_id=new_employee.id,
        old_salary=None,
        new_salary=employee_data.base_salary,
        effective_date=employee_data.hire_date or datetime.now().date(),
        reason="Initial hire",
        notes="Created during employee registration"
    )
    db.add(salary_history)
    db.commit()

    return new_employee


@router.put("/{employee_id}", response_model=EmployeeInDB)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an employee (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can update employees
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can update employees"
        )

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    # Track salary change
    old_salary = employee.base_salary

    # Update employee fields
    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    # If salary changed, create salary history record
    if "base_salary" in update_data and update_data["base_salary"] != old_salary:
        salary_history = SalaryHistory(
            employee_id=employee.id,
            old_salary=old_salary,
            new_salary=update_data["base_salary"],
            effective_date=datetime.now().date(),
            reason="Salary adjustment",
            notes="Updated via employee edit"
        )
        db.add(salary_history)
        db.commit()

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an employee (ADMIN only)

    NOTE: Employees with payroll history, salary history, or KPI records cannot be deleted.
    Instead, change their status to FIRED.
    """
    # Only ADMIN can delete employees
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete employees"
        )

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    # Check for related records
    related_issues = []

    # Check salary history
    salary_history_count = db.query(SalaryHistory).filter(
        SalaryHistory.employee_id == employee_id
    ).count()
    if salary_history_count > 0:
        related_issues.append(f"История изменений зарплаты: {salary_history_count} записей")

    # Check payroll plans
    payroll_plans_count = db.query(PayrollPlan).filter(
        PayrollPlan.employee_id == employee_id
    ).count()
    if payroll_plans_count > 0:
        related_issues.append(f"Плановые начисления: {payroll_plans_count} записей")

    # Check payroll actuals
    payroll_actuals_count = db.query(PayrollActual).filter(
        PayrollActual.employee_id == employee_id
    ).count()
    if payroll_actuals_count > 0:
        related_issues.append(f"Фактические выплаты: {payroll_actuals_count} записей")

    # Check employee KPIs
    employee_kpis_count = db.query(EmployeeKPI).filter(
        EmployeeKPI.employee_id == employee_id
    ).count()
    if employee_kpis_count > 0:
        related_issues.append(f"Записи KPI: {employee_kpis_count} записей")

    # If there are related records, prevent deletion
    if related_issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Невозможно удалить сотрудника с историей начислений и выплат",
                "reason": "У сотрудника есть связанные записи",
                "related_records": related_issues,
                "suggestion": f"Вместо удаления измените статус сотрудника на 'Уволен' (FIRED). ФИО: {employee.full_name}"
            }
        )

    # If no related records, safe to delete
    db.delete(employee)
    db.commit()
    return None


@router.get("/{employee_id}/salary-history", response_model=List[SalaryHistoryInDB])
async def get_salary_history(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get salary history for an employee
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    salary_history = db.query(SalaryHistory).filter(
        SalaryHistory.employee_id == employee_id
    ).order_by(SalaryHistory.effective_date.desc()).all()

    return salary_history


@router.post("/{employee_id}/salary-history", response_model=SalaryHistoryInDB, status_code=status.HTTP_201_CREATED)
async def add_salary_history(
    employee_id: int,
    salary_data: SalaryHistoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a salary history record (ADMIN/MANAGER only)
    """
    # Only ADMIN and MANAGER can add salary history
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can add salary history"
        )

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee"
        )

    # Create salary history record
    new_history = SalaryHistory(**salary_data.model_dump())
    db.add(new_history)

    # Update employee base salary if this is the most recent change
    if salary_data.effective_date >= datetime.now().date():
        employee.base_salary = salary_data.new_salary

    db.commit()
    db.refresh(new_history)

    return new_history


# ==================== Export Endpoints ====================

@router.get("/export", response_class=StreamingResponse)
async def export_employees(
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export employees list to Excel
    """
    query = db.query(Employee).join(Department)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    # Apply status filter
    if status:
        query = query.filter(Employee.status == status)

    employees = query.all()

    # Define status labels
    status_labels = {
        "ACTIVE": "Активен",
        "ON_VACATION": "В отпуске",
        "ON_LEAVE": "В отпуске/Больничный",
        "FIRED": "Уволен",
    }

    # Convert to DataFrame
    data = []
    for emp in employees:
        data.append({
            "ID": emp.id,
            "ФИО": emp.full_name,
            "Должность": emp.position,
            "Табельный номер": emp.employee_number or "",
            "Оклад": float(emp.base_salary),
            "Отдел": emp.department_rel.name if emp.department_rel else "",
            "Статус": status_labels.get(emp.status, emp.status),
            "Дата приема": emp.hire_date.strftime("%Y-%m-%d") if emp.hire_date else "",
            "Дата увольнения": emp.fire_date.strftime("%Y-%m-%d") if emp.fire_date else "",
            "Email": emp.email or "",
            "Телефон": emp.phone or "",
            "Примечания": emp.notes or "",
            "Дата создания": emp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Сотрудники')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employees_export.xlsx"}
    )
