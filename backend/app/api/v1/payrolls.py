from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date

from app.db import get_db
from app.db.models import Payroll, Employee, EmployeeStatusEnum
from app.schemas.employee import (
    PayrollCreate,
    PayrollUpdate,
    PayrollInDB,
    PayrollList,
    PayrollSummary,
)

router = APIRouter()


def calculate_payroll_amounts(
    base_salary: Decimal,
    bonus: Decimal,
    other_payments: Decimal,
    tax_rate: Decimal = Decimal('30.0')
) -> dict:
    """Calculate all payroll amounts"""
    gross_salary = base_salary + bonus + other_payments

    # Налоги с сотрудника (НДФЛ 13%)
    taxes = gross_salary * Decimal('0.13')
    net_salary = gross_salary - taxes

    # Налоги работодателя (ЕСН)
    employer_taxes = gross_salary * (tax_rate / 100)
    total_cost = gross_salary + employer_taxes

    return {
        "gross_salary": gross_salary,
        "taxes": taxes,
        "net_salary": net_salary,
        "employer_taxes": employer_taxes,
        "total_cost": total_cost,
    }


@router.get("/", response_model=PayrollList)
def get_payrolls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all payrolls with filtering and pagination"""
    query = db.query(Payroll)

    # Фильтры
    if employee_id:
        query = query.filter(Payroll.employee_id == employee_id)

    if year:
        query = query.filter(Payroll.year == year)

    if month:
        query = query.filter(Payroll.month == month)

    # Подсчет всего
    total = query.count()

    # Пагинация
    payrolls = query.order_by(
        Payroll.year.desc(),
        Payroll.month.desc()
    ).offset(skip).limit(limit).all()

    # Подсчет страниц
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    return {
        "total": total,
        "items": payrolls,
        "page": page,
        "page_size": limit,
        "pages": pages,
    }


@router.get("/summary", response_model=PayrollSummary)
def get_payroll_summary(
    year: int,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get payroll summary for year or specific month"""
    query = db.query(Payroll).filter(Payroll.year == year)

    if month:
        query = query.filter(Payroll.month == month)

    payrolls = query.all()

    if not payrolls:
        # Возвращаем пустую статистику
        return PayrollSummary(
            year=year,
            month=month,
            total_employees=0,
            total_base_salary=Decimal('0'),
            total_bonuses=Decimal('0'),
            total_gross_salary=Decimal('0'),
            total_taxes=Decimal('0'),
            total_net_salary=Decimal('0'),
            total_employer_taxes=Decimal('0'),
            total_cost=Decimal('0'),
            average_salary=Decimal('0'),
        )

    # Подсчеты
    total_employees = len(set(p.employee_id for p in payrolls))
    total_base = sum(p.base_salary for p in payrolls)
    total_bonus = sum(p.bonus for p in payrolls)
    total_gross = sum(p.gross_salary for p in payrolls)
    total_taxes = sum(p.taxes for p in payrolls)
    total_net = sum(p.net_salary for p in payrolls)
    total_employer_tax = sum(p.employer_taxes for p in payrolls)
    total_cost = sum(p.total_cost for p in payrolls)

    avg_salary = total_gross / len(payrolls) if payrolls else Decimal('0')

    return PayrollSummary(
        year=year,
        month=month,
        total_employees=total_employees,
        total_base_salary=total_base,
        total_bonuses=total_bonus,
        total_gross_salary=total_gross,
        total_taxes=total_taxes,
        total_net_salary=total_net,
        total_employer_taxes=total_employer_tax,
        total_cost=total_cost,
        average_salary=avg_salary,
    )


@router.get("/{payroll_id}", response_model=PayrollInDB)
def get_payroll(payroll_id: int, db: Session = Depends(get_db)):
    """Get payroll by ID"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with id {payroll_id} not found"
        )

    return payroll


@router.post("/", response_model=PayrollInDB, status_code=status.HTTP_201_CREATED)
def create_payroll(payroll: PayrollCreate, db: Session = Depends(get_db)):
    """Create new payroll record with automatic tax calculation"""
    # Проверяем существование сотрудника
    employee = db.query(Employee).filter(Employee.id == payroll.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {payroll.employee_id} not found"
        )

    # Проверяем, не существует ли уже запись за этот период
    existing = db.query(Payroll).filter(
        and_(
            Payroll.employee_id == payroll.employee_id,
            Payroll.year == payroll.year,
            Payroll.month == payroll.month
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payroll for employee {payroll.employee_id} for {payroll.year}-{payroll.month:02d} already exists"
        )

    # Рассчитываем суммы
    calculations = calculate_payroll_amounts(
        payroll.base_salary,
        payroll.bonus,
        payroll.other_payments,
        employee.tax_rate
    )

    # Создаем запись
    db_payroll = Payroll(
        **payroll.model_dump(),
        **calculations
    )
    db.add(db_payroll)
    db.commit()
    db.refresh(db_payroll)

    return db_payroll


@router.put("/{payroll_id}", response_model=PayrollInDB)
def update_payroll(
    payroll_id: int,
    payroll: PayrollUpdate,
    db: Session = Depends(get_db)
):
    """Update payroll record with automatic recalculation"""
    db_payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not db_payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with id {payroll_id} not found"
        )

    # Получаем сотрудника для ставки налогов
    employee = db.query(Employee).filter(Employee.id == db_payroll.employee_id).first()

    # Обновляем поля
    update_data = payroll.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payroll, field, value)

    # Пересчитываем суммы если изменились базовые поля
    if any(k in update_data for k in ['base_salary', 'bonus', 'other_payments']):
        calculations = calculate_payroll_amounts(
            db_payroll.base_salary,
            db_payroll.bonus,
            db_payroll.other_payments,
            employee.tax_rate
        )
        for field, value in calculations.items():
            setattr(db_payroll, field, value)

    db.commit()
    db.refresh(db_payroll)

    return db_payroll


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payroll(payroll_id: int, db: Session = Depends(get_db)):
    """Delete payroll record"""
    db_payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not db_payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with id {payroll_id} not found"
        )

    db.delete(db_payroll)
    db.commit()

    return None


@router.post("/generate/{year}", status_code=status.HTTP_201_CREATED)
def generate_payrolls_for_year(
    year: int,
    month_start: int = Query(1, ge=1, le=12),
    month_end: int = Query(12, ge=1, le=12),
    db: Session = Depends(get_db)
):
    """Generate payroll records for all active employees for specified period"""
    # Получаем всех активных сотрудников
    employees = db.query(Employee).filter(
        Employee.status == EmployeeStatusEnum.ACTIVE
    ).all()

    created_count = 0
    skipped_count = 0

    for employee in employees:
        for month in range(month_start, month_end + 1):
            # Проверяем, есть ли уже запись
            existing = db.query(Payroll).filter(
                and_(
                    Payroll.employee_id == employee.id,
                    Payroll.year == year,
                    Payroll.month == month
                )
            ).first()

            if existing:
                skipped_count += 1
                continue

            # Рассчитываем суммы
            calculations = calculate_payroll_amounts(
                employee.base_salary,
                Decimal('0'),  # Без премий по умолчанию
                Decimal('0'),  # Без прочих выплат
                employee.tax_rate
            )

            # Создаем запись
            payroll = Payroll(
                employee_id=employee.id,
                year=year,
                month=month,
                base_salary=employee.base_salary,
                bonus=Decimal('0'),
                other_payments=Decimal('0'),
                **calculations
            )
            db.add(payroll)
            created_count += 1

    db.commit()

    return {
        "message": f"Generated payrolls for {year}",
        "created": created_count,
        "skipped": skipped_count,
        "employees": len(employees),
    }
