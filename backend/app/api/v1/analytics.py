from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.db import get_db
from app.db.models import Expense, BudgetCategory, BudgetPlan, ExpenseStatusEnum, ExpenseTypeEnum, User
from app.services.forecast_service import PaymentForecastService, ForecastMethod
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/dashboard")
def get_dashboard_data(
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard data with key metrics"""
    if not year:
        year = datetime.now().year

    # Get total planned
    plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(BudgetPlan.year == year)
    if month:
        plan_query = plan_query.filter(BudgetPlan.month == month)
    if department_id:
        plan_query = plan_query.filter(BudgetPlan.department_id == department_id)
    total_planned = plan_query.scalar() or 0

    # Get total actual
    actual_query = db.query(func.sum(Expense.amount)).filter(
        extract('year', Expense.request_date) == year
    )
    if month:
        actual_query = actual_query.filter(extract('month', Expense.request_date) == month)
    if department_id:
        actual_query = actual_query.filter(Expense.department_id == department_id)
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
    if department_id:
        status_query = status_query.filter(Expense.department_id == department_id)

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
    if department_id:
        category_query = category_query.filter(Expense.department_id == department_id)

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

    # Get recent expenses with eager loading (fix N+1)
    recent_expenses_query = db.query(Expense).filter(
        extract('year', Expense.request_date) == year
    )
    if department_id:
        recent_expenses_query = recent_expenses_query.filter(Expense.department_id == department_id)

    recent_expenses_query = recent_expenses_query.options(
        joinedload(Expense.category),
        joinedload(Expense.contractor),
        joinedload(Expense.organization)
    )
    recent_expenses = recent_expenses_query.order_by(Expense.request_date.desc()).limit(10).all()

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
def get_budget_execution(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed analytics by category"""
    # Get all categories ordered by parent_id and name for proper hierarchy display
    categories_query = db.query(BudgetCategory).filter(
        BudgetCategory.is_active == True
    )

    if department_id:
        categories_query = categories_query.filter(BudgetCategory.department_id == department_id)

    categories = categories_query.order_by(BudgetCategory.parent_id.nullsfirst(), BudgetCategory.name).all()

    result = []
    for category in categories:
        # Get planned amount
        plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.category_id == category.id
        )
        if month:
            plan_query = plan_query.filter(BudgetPlan.month == month)
        if department_id:
            plan_query = plan_query.filter(BudgetPlan.department_id == department_id)
        planned = plan_query.scalar() or 0

        # Get actual amount
        actual_query = db.query(func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.request_date) == year
        )
        if month:
            actual_query = actual_query.filter(extract('month', Expense.request_date) == month)
        if department_id:
            actual_query = actual_query.filter(Expense.department_id == department_id)
        actual = actual_query.scalar() or 0

        # Get expense count
        count_query = db.query(func.count(Expense.id)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.request_date) == year
        )
        if month:
            count_query = count_query.filter(extract('month', Expense.request_date) == month)
        if department_id:
            count_query = count_query.filter(Expense.department_id == department_id)
        expense_count = count_query.scalar() or 0

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.type.value,
            "parent_id": category.parent_id,
            "planned": float(planned),
            "actual": float(actual),
            "remaining": float(planned) - float(actual),
            "execution_percent": round((float(actual) / float(planned) * 100) if planned > 0 else 0, 2),
            "expense_count": expense_count
        })

    return {
        "year": year,
        "month": month,
        "categories": result
    }


@router.get("/trends")
def get_trends(
    year: int,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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


@router.get("/payment-calendar")
def get_payment_calendar(
    year: int = Query(default=None, description="Year for calendar"),
    month: int = Query(default=None, ge=1, le=12, description="Month (1-12)"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get payment calendar view for a specific month
    Returns daily aggregated payment data
    """
    # Use current year/month if not provided
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month

    forecast_service = PaymentForecastService(db)
    calendar_data = forecast_service.get_payment_calendar(
        year=year,
        month=month,
        category_id=category_id,
        organization_id=organization_id,
    )

    return {
        "year": year,
        "month": month,
        "days": calendar_data
    }


@router.get("/payment-calendar/{date}")
def get_payments_by_day(
    date: str = Path(description="Date in ISO format (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all payments for a specific day
    Returns detailed list of expenses
    """
    try:
        payment_date = datetime.fromisoformat(date)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    forecast_service = PaymentForecastService(db)
    payments = forecast_service.get_payments_by_day(
        date=payment_date,
        category_id=category_id,
        organization_id=organization_id,
    )

    # Convert to dict format
    payments_data = [
        {
            "id": payment.id,
            "number": payment.number,
            "amount": float(payment.amount),
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "category_id": payment.category_id,
            "category_name": payment.category.name if payment.category else None,
            "contractor_id": payment.contractor_id,
            "contractor_name": payment.contractor.name if payment.contractor else None,
            "organization_id": payment.organization_id,
            "organization_name": payment.organization.name if payment.organization else None,
            "status": payment.status.value,
            "comment": payment.comment,
        }
        for payment in payments
    ]

    return {
        "date": date,
        "total_count": len(payments_data),
        "total_amount": sum(p["amount"] for p in payments_data),
        "payments": payments_data
    }


@router.get("/payment-forecast")
def get_payment_forecast(
    start_date: str = Query(description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(description="End date in ISO format (YYYY-MM-DD)"),
    method: ForecastMethod = Query(default="simple_average", description="Forecast method"),
    lookback_days: int = Query(default=90, ge=30, le=365, description="Days to look back for historical data"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate payment forecast for future period
    Methods: simple_average, moving_average, seasonal
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    if end <= start:
        return {"error": "End date must be after start date"}

    forecast_service = PaymentForecastService(db)
    forecast_data = forecast_service.generate_forecast(
        start_date=start,
        end_date=end,
        method=method,
        lookback_days=lookback_days,
        category_id=category_id,
        organization_id=organization_id,
    )

    # Calculate summary statistics
    total_predicted = sum(item['predicted_amount'] for item in forecast_data)
    avg_daily = total_predicted / len(forecast_data) if forecast_data else 0

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "days": len(forecast_data),
        },
        "method": method,
        "lookback_days": lookback_days,
        "summary": {
            "total_predicted": round(total_predicted, 2),
            "average_daily": round(avg_daily, 2),
        },
        "forecast": forecast_data
    }


@router.get("/payment-forecast/summary")
def get_payment_forecast_summary(
    start_date: str = Query(description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(description="End date in ISO format (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get forecast summary comparing different methods
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    forecast_service = PaymentForecastService(db)
    summary = forecast_service.get_forecast_summary(
        start_date=start,
        end_date=end,
        category_id=category_id,
        organization_id=organization_id,
    )

    return summary
