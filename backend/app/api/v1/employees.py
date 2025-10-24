from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db import get_db
from app.db.models import Employee, Payroll, EmployeeStatusEnum
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeInDB,
    EmployeeList,
    EmployeeWithPayrolls,
)

router = APIRouter()


@router.get("/", response_model=EmployeeList)
def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[EmployeeStatusEnum] = None,
    position: Optional[str] = None,
    organization_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all employees with filtering and pagination"""
    query = db.query(Employee)

    # Фильтры
    if status:
        query = query.filter(Employee.status == status)

    if position:
        query = query.filter(Employee.position.ilike(f"%{position}%"))

    if organization_id:
        query = query.filter(Employee.organization_id == organization_id)

    if search:
        query = query.filter(
            Employee.full_name.ilike(f"%{search}%") |
            Employee.email.ilike(f"%{search}%") |
            Employee.phone.ilike(f"%{search}%")
        )

    # Подсчет всего
    total = query.count()

    # Пагинация
    employees = query.order_by(Employee.created_at.desc()).offset(skip).limit(limit).all()

    # Подсчет страниц
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    return {
        "total": total,
        "items": employees,
        "page": page,
        "page_size": limit,
        "pages": pages,
    }


@router.get("/stats")
def get_employee_stats(db: Session = Depends(get_db)):
    """Get employee statistics"""
    total = db.query(Employee).count()
    active = db.query(Employee).filter(Employee.status == EmployeeStatusEnum.ACTIVE).count()
    dismissed = db.query(Employee).filter(Employee.status == EmployeeStatusEnum.DISMISSED).count()

    # Средняя зарплата активных сотрудников
    avg_salary = db.query(func.avg(Employee.base_salary)).filter(
        Employee.status == EmployeeStatusEnum.ACTIVE
    ).scalar() or 0

    # Суммарная зарплата активных
    total_salary = db.query(func.sum(Employee.base_salary)).filter(
        Employee.status == EmployeeStatusEnum.ACTIVE
    ).scalar() or 0

    return {
        "total_employees": total,
        "active_employees": active,
        "dismissed_employees": dismissed,
        "average_salary": float(avg_salary),
        "total_monthly_salary": float(total_salary),
        "total_annual_fot": float(total_salary * 12 * Decimal('1.30')),  # С налогами работодателя
    }


@router.get("/{employee_id}", response_model=EmployeeWithPayrolls)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID with recent payrolls"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )

    # Получаем последние 12 записей зарплат
    recent_payrolls = db.query(Payroll).filter(
        Payroll.employee_id == employee_id
    ).order_by(
        Payroll.year.desc(),
        Payroll.month.desc()
    ).limit(12).all()

    # Считаем заработано за текущий год
    current_year = 2025  # Можно взять из datetime.now().year
    total_ytd = db.query(func.sum(Payroll.total_cost)).filter(
        Payroll.employee_id == employee_id,
        Payroll.year == current_year
    ).scalar() or Decimal('0')

    return {
        **employee.__dict__,
        "recent_payrolls": recent_payrolls,
        "total_earned_ytd": total_ytd,
    }


@router.post("/", response_model=EmployeeInDB, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create new employee"""
    # Проверяем, не существует ли уже сотрудник с таким именем
    existing = db.query(Employee).filter(
        Employee.full_name == employee.full_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with name '{employee.full_name}' already exists"
        )

    # Создаем сотрудника
    db_employee = Employee(
        **employee.model_dump(),
        status=EmployeeStatusEnum.ACTIVE
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    return db_employee


@router.put("/{employee_id}", response_model=EmployeeInDB)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update employee"""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )

    # Обновляем поля
    update_data = employee.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)

    db.commit()
    db.refresh(db_employee)

    return db_employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete employee (soft delete - mark as dismissed)"""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )

    # Мягкое удаление - помечаем как уволенного
    db_employee.status = EmployeeStatusEnum.DISMISSED
    from datetime import date
    if not db_employee.termination_date:
        db_employee.termination_date = date.today()

    db.commit()

    return None


@router.post("/{employee_id}/restore", response_model=EmployeeInDB)
def restore_employee(employee_id: int, db: Session = Depends(get_db)):
    """Restore dismissed employee"""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )

    db_employee.status = EmployeeStatusEnum.ACTIVE
    db_employee.termination_date = None

    db.commit()
    db.refresh(db_employee)

    return db_employee
