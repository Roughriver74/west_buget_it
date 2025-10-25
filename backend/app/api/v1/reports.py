"""
Reports API endpoints with department grouping
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date
import pandas as pd
import io

from app.db import get_db
from app.db.models import (
    Expense, BudgetCategory, Contractor, Organization,
    Department, User, UserRoleEnum, ExpenseStatusEnum, BudgetPlan
)
from app.utils.auth import get_current_active_user
from app.utils.audit import audit_export

router = APIRouter()


@router.get("/expenses/by-department")
def get_expenses_by_department_report(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    status: Optional[ExpenseStatusEnum] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get expenses report grouped by department

    Returns summary statistics for each department:
    - Total expenses
    - Count of expenses
    - Average expense amount
    - OPEX vs CAPEX breakdown
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view cross-department reports"
        )

    # Build query
    query = db.query(
        Department.id.label('department_id'),
        Department.name.label('department_name'),
        Department.code.label('department_code'),
        func.count(Expense.id).label('expense_count'),
        func.sum(Expense.amount).label('total_amount'),
        func.avg(Expense.amount).label('average_amount'),
    ).join(
        Expense, Department.id == Expense.department_id
    ).join(
        BudgetCategory, Expense.category_id == BudgetCategory.id
    ).group_by(
        Department.id, Department.name, Department.code
    )

    # Apply filters
    if year:
        query = query.filter(extract('year', Expense.request_date) == year)

    if month:
        query = query.filter(extract('month', Expense.request_date) == month)

    if category_id:
        query = query.filter(Expense.category_id == category_id)

    if status:
        query = query.filter(Expense.status == status)

    results = query.all()

    # Format results
    report = []
    for row in results:
        # Get OPEX/CAPEX breakdown for this department
        opex_capex_query = db.query(
            BudgetCategory.type,
            func.sum(Expense.amount).label('amount')
        ).join(
            Expense, BudgetCategory.id == Expense.category_id
        ).filter(
            Expense.department_id == row.department_id
        )

        if year:
            opex_capex_query = opex_capex_query.filter(
                extract('year', Expense.request_date) == year
            )
        if month:
            opex_capex_query = opex_capex_query.filter(
                extract('month', Expense.request_date) == month
            )
        if status:
            opex_capex_query = opex_capex_query.filter(Expense.status == status)

        opex_capex = opex_capex_query.group_by(BudgetCategory.type).all()

        opex_amount = 0
        capex_amount = 0
        for item in opex_capex:
            if item.type.value == "OPEX":
                opex_amount = float(item.amount or 0)
            elif item.type.value == "CAPEX":
                capex_amount = float(item.amount or 0)

        report.append({
            "department_id": row.department_id,
            "department_name": row.department_name,
            "department_code": row.department_code,
            "expense_count": row.expense_count,
            "total_amount": float(row.total_amount or 0),
            "average_amount": float(row.average_amount or 0),
            "opex_amount": opex_amount,
            "capex_amount": capex_amount,
        })

    return report


@router.get("/budget/by-department")
def get_budget_by_department_report(
    year: int = Query(..., description="Year for budget report"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get budget vs actual report grouped by department

    Returns for each department:
    - Planned budget (OPEX/CAPEX)
    - Actual expenses (OPEX/CAPEX)
    - Variance (planned - actual)
    - Utilization percentage
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view cross-department reports"
        )

    # Get all departments
    departments = db.query(Department).filter(Department.is_active == True).all()

    report = []
    for dept in departments:
        # Get planned budget
        budget_query = db.query(
            func.sum(BudgetPlan.opex_planned).label('planned_opex'),
            func.sum(BudgetPlan.capex_planned).label('planned_capex'),
        ).filter(
            BudgetPlan.department_id == dept.id,
            BudgetPlan.year == year
        )
        budget_result = budget_query.first()

        planned_opex = float(budget_result.planned_opex or 0)
        planned_capex = float(budget_result.planned_capex or 0)
        planned_total = planned_opex + planned_capex

        # Get actual expenses
        actual_query = db.query(
            BudgetCategory.type,
            func.sum(Expense.amount).label('amount')
        ).join(
            Expense, BudgetCategory.id == Expense.category_id
        ).filter(
            Expense.department_id == dept.id,
            extract('year', Expense.request_date) == year
        ).group_by(BudgetCategory.type)

        actual_results = actual_query.all()

        actual_opex = 0
        actual_capex = 0
        for item in actual_results:
            if item.type.value == "OPEX":
                actual_opex = float(item.amount or 0)
            elif item.type.value == "CAPEX":
                actual_capex = float(item.amount or 0)

        actual_total = actual_opex + actual_capex

        # Calculate variances
        opex_variance = planned_opex - actual_opex
        capex_variance = planned_capex - actual_capex
        total_variance = planned_total - actual_total

        # Calculate utilization %
        opex_utilization = (actual_opex / planned_opex * 100) if planned_opex > 0 else 0
        capex_utilization = (actual_capex / planned_capex * 100) if planned_capex > 0 else 0
        total_utilization = (actual_total / planned_total * 100) if planned_total > 0 else 0

        report.append({
            "department_id": dept.id,
            "department_name": dept.name,
            "department_code": dept.code,
            "planned_opex": planned_opex,
            "planned_capex": planned_capex,
            "planned_total": planned_total,
            "actual_opex": actual_opex,
            "actual_capex": actual_capex,
            "actual_total": actual_total,
            "opex_variance": opex_variance,
            "capex_variance": capex_variance,
            "total_variance": total_variance,
            "opex_utilization_pct": round(opex_utilization, 2),
            "capex_utilization_pct": round(capex_utilization, 2),
            "total_utilization_pct": round(total_utilization, 2),
        })

    return report


@router.get("/expenses/export-by-department", response_class=StreamingResponse)
def export_expenses_by_department(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export expenses report by department to Excel"""
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export cross-department reports"
        )

    # Get report data (reuse the logic from get_expenses_by_department_report)
    query = db.query(
        Department.name.label('Отдел'),
        Department.code.label('Код отдела'),
        func.count(Expense.id).label('Количество заявок'),
        func.sum(Expense.amount).label('Общая сумма'),
        func.avg(Expense.amount).label('Средняя сумма'),
    ).join(
        Expense, Department.id == Expense.department_id
    ).group_by(
        Department.id, Department.name, Department.code
    )

    if year:
        query = query.filter(extract('year', Expense.request_date) == year)
    if month:
        query = query.filter(extract('month', Expense.request_date) == month)

    results = query.all()

    # Convert to DataFrame
    data = []
    for row in results:
        data.append({
            "Отдел": row[0],
            "Код отдела": row[1],
            "Количество заявок": row[2],
            "Общая сумма": float(row[3] or 0),
            "Средняя сумма": float(row[4] or 0),
        })

    df = pd.DataFrame(data)

    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Расходы по отделам')

    output.seek(0)

    # Audit log
    description = f"Exported expenses by department report"
    if year:
        description += f" for year {year}"
    if month:
        description += f" month {month}"

    audit_export(
        db=db,
        entity_type="Report",
        description=description,
        user=current_user
    )

    # Return file
    filename = f"expenses_by_department_{year or 'all'}_{month or 'all'}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
