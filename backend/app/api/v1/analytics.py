from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.db import get_db
from app.db.models import Expense, BudgetCategory, BudgetPlan, ExpenseStatusEnum, ExpenseTypeEnum

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_data(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get dashboard data with key metrics"""
    if not year:
        year = datetime.now().year

    # Get total planned
    plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(BudgetPlan.year == year)
    if month:
        plan_query = plan_query.filter(BudgetPlan.month == month)
    total_planned = plan_query.scalar() or 0

    # Get total actual
    actual_query = db.query(func.sum(Expense.amount)).filter(
        extract('year', Expense.request_date) == year
    )
    if month:
        actual_query = actual_query.filter(extract('month', Expense.request_date) == month)
    total_actual = actual_query.scalar() or 0

    # Calculate metrics
    remaining = float(total_planned) - float(total_actual)
    execution_percent = round((float(total_actual) / float(total_planned) * 100) if total_planned > 0 else 0, 2)

    # Get status distribution
    status_query = db.query(
        Expense.status,
        func.count(Expense.id).label('count'),
        func.sum(Expense.amount).label('amount')
    ).filter(extract('year', Expense.request_date) == year)

    if month:
        status_query = status_query.filter(extract('month', Expense.request_date) == month)

    status_query = status_query.group_by(Expense.status)
    status_stats = [
        {
            "status": item.status.value,
            "count": item.count,
            "amount": float(item.amount) if item.amount else 0
        }
        for item in status_query.all()
    ]

    # Get top categories by spending
    category_query = db.query(
        BudgetCategory.id,
        BudgetCategory.name,
        BudgetCategory.type,
        func.sum(Expense.amount).label('amount')
    ).join(Expense).filter(
        extract('year', Expense.request_date) == year
    )

    if month:
        category_query = category_query.filter(extract('month', Expense.request_date) == month)

    category_query = category_query.group_by(BudgetCategory.id, BudgetCategory.name, BudgetCategory.type).order_by(func.sum(Expense.amount).desc()).limit(5)

    top_categories = [
        {
            "category_id": item.id,
            "category_name": item.name,
            "category_type": item.type.value,
            "amount": float(item.amount) if item.amount else 0
        }
        for item in category_query.all()
    ]

    # Get recent expenses
    recent_expenses = db.query(Expense).filter(
        extract('year', Expense.request_date) == year
    ).order_by(Expense.request_date.desc()).limit(10).all()

    recent_expenses_data = [
        {
            "id": exp.id,
            "number": exp.number,
            "amount": float(exp.amount),
            "status": exp.status.value,
            "request_date": exp.request_date.isoformat(),
            "category_id": exp.category_id,
        }
        for exp in recent_expenses
    ]

    # Get CAPEX vs OPEX
    capex_query = db.query(func.sum(Expense.amount)).join(BudgetCategory).filter(
        BudgetCategory.type == ExpenseTypeEnum.CAPEX,
        extract('year', Expense.request_date) == year
    )
    if month:
        capex_query = capex_query.filter(extract('month', Expense.request_date) == month)

    opex_query = db.query(func.sum(Expense.amount)).join(BudgetCategory).filter(
        BudgetCategory.type == ExpenseTypeEnum.OPEX,
        extract('year', Expense.request_date) == year
    )
    if month:
        opex_query = opex_query.filter(extract('month', Expense.request_date) == month)

    capex_actual = capex_query.scalar() or 0
    opex_actual = opex_query.scalar() or 0

    return {
        "year": year,
        "month": month,
        "totals": {
            "planned": float(total_planned),
            "actual": float(total_actual),
            "remaining": remaining,
            "execution_percent": execution_percent
        },
        "capex_vs_opex": {
            "capex": float(capex_actual),
            "opex": float(opex_actual),
            "capex_percent": round((float(capex_actual) / float(total_actual) * 100) if total_actual > 0 else 0, 2),
            "opex_percent": round((float(opex_actual) / float(total_actual) * 100) if total_actual > 0 else 0, 2),
        },
        "status_distribution": status_stats,
        "top_categories": top_categories,
        "recent_expenses": recent_expenses_data
    }


@router.get("/budget-execution")
def get_budget_execution(year: int, db: Session = Depends(get_db)):
    """Get monthly budget execution for the year"""
    result = []

    for month in range(1, 13):
        # Get planned
        plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == month
        )
        planned = plan_query.scalar() or 0

        # Get actual
        actual_query = db.query(func.sum(Expense.amount)).filter(
            extract('year', Expense.request_date) == year,
            extract('month', Expense.request_date) == month
        )
        actual = actual_query.scalar() or 0

        result.append({
            "month": month,
            "month_name": datetime(year, month, 1).strftime("%B"),
            "planned": float(planned),
            "actual": float(actual),
            "remaining": float(planned) - float(actual),
            "execution_percent": round((float(actual) / float(planned) * 100) if planned > 0 else 0, 2)
        })

    return {
        "year": year,
        "months": result
    }


@router.get("/by-category")
def get_analytics_by_category(
    year: int,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed analytics by category"""
    # Get all categories
    categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).all()

    result = []
    for category in categories:
        # Get planned amount
        plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.category_id == category.id
        )
        if month:
            plan_query = plan_query.filter(BudgetPlan.month == month)
        planned = plan_query.scalar() or 0

        # Get actual amount
        actual_query = db.query(func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.request_date) == year
        )
        if month:
            actual_query = actual_query.filter(extract('month', Expense.request_date) == month)
        actual = actual_query.scalar() or 0

        # Get expense count
        count_query = db.query(func.count(Expense.id)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.request_date) == year
        )
        if month:
            count_query = count_query.filter(extract('month', Expense.request_date) == month)
        expense_count = count_query.scalar() or 0

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.type.value,
            "planned": float(planned),
            "actual": float(actual),
            "remaining": float(planned) - float(actual),
            "execution_percent": round((float(actual) / float(planned) * 100) if planned > 0 else 0, 2),
            "expense_count": expense_count
        })

    # Sort by actual amount descending
    result.sort(key=lambda x: x["actual"], reverse=True)

    return {
        "year": year,
        "month": month,
        "categories": result
    }


@router.get("/trends")
def get_trends(
    year: int,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get spending trends over time"""
    query = db.query(
        extract('month', Expense.request_date).label('month'),
        func.sum(Expense.amount).label('amount'),
        func.count(Expense.id).label('count')
    ).filter(extract('year', Expense.request_date) == year)

    if category_id:
        query = query.filter(Expense.category_id == category_id)

    query = query.group_by(extract('month', Expense.request_date)).order_by(extract('month', Expense.request_date))

    trends = [
        {
            "month": int(item.month),
            "month_name": datetime(year, int(item.month), 1).strftime("%B"),
            "amount": float(item.amount) if item.amount else 0,
            "count": item.count
        }
        for item in query.all()
    ]

    return {
        "year": year,
        "category_id": category_id,
        "trends": trends
    }
