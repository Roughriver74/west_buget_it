from typing import Optional
import io
import pandas as pd
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.db import get_db
from app.db.models import (
    Expense, BudgetCategory, BudgetPlan, BudgetVersion, BudgetPlanDetail,
    ExpenseStatusEnum, ExpenseTypeEnum, User, UserRoleEnum,
    PayrollPlan, PayrollActual, Department,
    RevenuePlan, RevenuePlanDetail, RevenuePlanVersion, RevenueActual, RevenueStream, RevenueCategory,
    RevenueVersionStatusEnum, CustomerMetrics
)
from app.services.forecast_service import PaymentForecastService, ForecastMethod
from app.utils.auth import get_current_active_user
from app.utils.excel_export import encode_filename_header
from app.schemas.analytics import (
    DashboardData,
    DashboardTotals,
    DashboardCapexVsOpex,
    DashboardStatusDistribution,
    DashboardTopCategory,
    DashboardRecentExpense,
    CategoryAnalytics,
    CategoryAnalyticsItem,
    Trends,
    TrendItem,
    PaymentCalendar,
    PaymentCalendarDay,
    PaymentsByDay,
    PaymentDetail,
    PaymentForecast,
    PaymentForecastPeriod,
    PaymentForecastSummary,
    PaymentForecastPoint,
    ForecastSummary,
    ForecastSummaryPeriod,
    ForecastSummaryMethods,
    ForecastSummaryMethodStats,
    ForecastMethodEnum,
    PlanVsActualSummary,
    PlanVsActualMonthly,
    PlanVsActualCategory,
    BudgetIncomeStatement,
    BudgetIncomeStatementMonthly,
    BudgetIncomeStatementCategory,
    CustomerMetricsAnalytics,
    CustomerMetricsMonthly,
    CustomerMetricsByStream,
    RevenueAnalytics,
    RevenueAnalyticsMonthly,
    RevenueAnalyticsByStream,
    RevenueAnalyticsByCategory,
)
from app.schemas.budget_validation import (
    BudgetStatusResponse,
    ExpenseValidationResponse,
    BudgetInfo,
)
from app.services.budget_validator import BudgetValidator

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/dashboard", response_model=DashboardData)
def get_dashboard_data(
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard data with key metrics

    - USER: Can only see dashboard data for their own department
    - FOUNDER/MANAGER/ADMIN: Can see dashboard data for all departments or filter by department
    """
    if not year:
        year = datetime.now().year

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # FOUNDER, MANAGER and ADMIN can filter by department or see all
        pass

    # Get total planned from BudgetPlan
    plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(BudgetPlan.year == year)
    if month:
        plan_query = plan_query.filter(BudgetPlan.month == month)
    if department_id:
        plan_query = plan_query.filter(BudgetPlan.department_id == department_id)
    budget_planned = plan_query.scalar() or 0

    # Get total planned from PayrollPlan (FOT)
    payroll_query = db.query(func.sum(PayrollPlan.total_planned)).filter(PayrollPlan.year == year)
    if month:
        payroll_query = payroll_query.filter(PayrollPlan.month == month)
    if department_id:
        payroll_query = payroll_query.filter(PayrollPlan.department_id == department_id)
    payroll_planned = payroll_query.scalar() or 0

    # Combined total planned (BudgetPlan + PayrollPlan)
    total_planned = float(budget_planned) + float(payroll_planned)

    # Get total actual from Expenses
    actual_query = db.query(func.sum(Expense.amount)).filter(
        extract('year', Expense.request_date) == year
    )
    if month:
        actual_query = actual_query.filter(extract('month', Expense.request_date) == month)
    if department_id:
        actual_query = actual_query.filter(Expense.department_id == department_id)
    expenses_actual = actual_query.scalar() or 0

    # Get total actual from PayrollActual (FOT)
    payroll_actual_query = db.query(func.sum(PayrollActual.total_paid)).filter(
        PayrollActual.year == year
    )
    if month:
        payroll_actual_query = payroll_actual_query.filter(PayrollActual.month == month)
    if department_id:
        payroll_actual_query = payroll_actual_query.filter(PayrollActual.department_id == department_id)
    payroll_actual = payroll_actual_query.scalar() or 0

    # Combined total actual (Expenses + PayrollActual)
    total_actual = float(expenses_actual) + float(payroll_actual)

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
    if department_id:
        capex_query = capex_query.filter(Expense.department_id == department_id)

    opex_query = db.query(func.sum(Expense.amount)).join(BudgetCategory).filter(
        BudgetCategory.type == ExpenseTypeEnum.OPEX,
        extract('year', Expense.request_date) == year
    )
    if month:
        opex_query = opex_query.filter(extract('month', Expense.request_date) == month)
    if department_id:
        opex_query = opex_query.filter(Expense.department_id == department_id)

    capex_actual = capex_query.scalar() or 0
    opex_actual = opex_query.scalar() or 0

    return DashboardData(
        year=year,
        month=month,
        totals=DashboardTotals(
            planned=float(total_planned),
            actual=float(total_actual),
            remaining=remaining,
            execution_percent=execution_percent,
        ),
        capex_vs_opex=DashboardCapexVsOpex(
            capex=float(capex_actual),
            opex=float(opex_actual),
            capex_percent=round((float(capex_actual) / float(total_actual) * 100) if total_actual > 0 else 0, 2),
            opex_percent=round((float(opex_actual) / float(total_actual) * 100) if total_actual > 0 else 0, 2),
        ),
        status_distribution=[DashboardStatusDistribution(**item) for item in status_stats],
        top_categories=[DashboardTopCategory(**item) for item in top_categories],
        recent_expenses=[DashboardRecentExpense(**item) for item in recent_expenses_data],
        by_month=None,
        by_category=None,
    )


@router.get("/budget-execution")
def get_budget_execution(
    year: int,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get monthly budget execution for the year

    - USER: Can only see budget execution for their own department
    - MANAGER/ADMIN: Can see budget execution for all departments or filter by department
    """
    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    result = []

    for month in range(1, 13):
        # Get planned
        plan_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == month
        )
        if department_id:
            plan_query = plan_query.filter(BudgetPlan.department_id == department_id)
        planned = plan_query.scalar() or 0

        # Get actual
        actual_query = db.query(func.sum(Expense.amount)).filter(
            extract('year', Expense.request_date) == year,
            extract('month', Expense.request_date) == month
        )
        if department_id:
            actual_query = actual_query.filter(Expense.department_id == department_id)
        actual = actual_query.scalar() or 0

        result.append({
            "month": month,
            "month_name": datetime(year, month, 1).strftime("%B"),
            "planned": float(planned),
            "actual": float(actual),
            "remaining": float(planned) - float(actual),
            "execution_percent": round((float(actual) / float(planned) * 100) if planned > 0 else 0, 2)
        })

    # Get by_category with monthly breakdown
    categories_query = db.query(BudgetCategory).filter(
        BudgetCategory.is_active == True
    )
    if department_id:
        categories_query = categories_query.filter(BudgetCategory.department_id == department_id)
    categories = categories_query.order_by(BudgetCategory.name).all()

    by_category = []
    for category in categories:
        # Get total planned and actual for this category
        plan_total_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.category_id == category.id
        )
        if department_id:
            plan_total_query = plan_total_query.filter(BudgetPlan.department_id == department_id)
        planned_total = plan_total_query.scalar() or 0

        actual_total_query = db.query(func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            extract('year', Expense.request_date) == year
        )
        if department_id:
            actual_total_query = actual_total_query.filter(Expense.department_id == department_id)
        actual_total = actual_total_query.scalar() or 0

        # Get monthly breakdown for this category
        monthly_data = []
        for month in range(1, 13):
            plan_month_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
                BudgetPlan.year == year,
                BudgetPlan.month == month,
                BudgetPlan.category_id == category.id
            )
            if department_id:
                plan_month_query = plan_month_query.filter(BudgetPlan.department_id == department_id)
            planned_month = plan_month_query.scalar() or 0

            actual_month_query = db.query(func.sum(Expense.amount)).filter(
                Expense.category_id == category.id,
                extract('year', Expense.request_date) == year,
                extract('month', Expense.request_date) == month
            )
            if department_id:
                actual_month_query = actual_month_query.filter(Expense.department_id == department_id)
            actual_month = actual_month_query.scalar() or 0

            monthly_data.append({
                "month": month,
                "month_name": datetime(year, month, 1).strftime("%B"),
                "planned": float(planned_month),
                "actual": float(actual_month),
                "difference": float(actual_month) - float(planned_month),
                "execution_percent": round((float(actual_month) / float(planned_month) * 100) if planned_month > 0 else 0, 2)
            })

        by_category.append({
            "category_id": category.id,
            "category_name": category.name,
            "planned": float(planned_total),
            "actual": float(actual_total),
            "difference": float(actual_total) - float(planned_total),
            "execution_percent": round((float(actual_total) / float(planned_total) * 100) if planned_total > 0 else 0, 2),
            "monthly": monthly_data
        })

    # Calculate totals
    total_planned = sum(float(m["planned"]) for m in result)
    total_actual = sum(float(m["actual"]) for m in result)
    total_difference = total_actual - total_planned
    execution_percent = round((total_actual / total_planned * 100) if total_planned > 0 else 0, 2)

    return {
        "year": year,
        "months": result,
        "by_category": by_category,
        "total_planned": total_planned,
        "total_actual": total_actual,
        "total_difference": total_difference,
        "execution_percent": execution_percent
    }


@router.get("/by-category", response_model=CategoryAnalytics)
def get_analytics_by_category(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed analytics by category

    - USER: Can only see analytics for their own department
    - MANAGER/ADMIN: Can see analytics for all departments or filter by department
    """
    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

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

    return CategoryAnalytics(
        year=year,
        month=month,
        categories=[CategoryAnalyticsItem(**item) for item in result],
    )


@router.get("/trends", response_model=Trends)
def get_trends(
    year: int,
    category_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get spending trends over time

    - USER: Can only see trends for their own department
    - MANAGER/ADMIN: Can see trends for all departments or filter by department
    """
    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    query = db.query(
        extract('month', Expense.request_date).label('month'),
        func.sum(Expense.amount).label('amount'),
        func.count(Expense.id).label('count')
    ).filter(extract('year', Expense.request_date) == year)

    if category_id:
        query = query.filter(Expense.category_id == category_id)

    if department_id:
        query = query.filter(Expense.department_id == department_id)

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

    return Trends(
        year=year,
        category_id=category_id,
        trends=[TrendItem(**item) for item in trends],
    )


@router.get("/payment-calendar", response_model=PaymentCalendar)
def get_payment_calendar(
    year: int = Query(default=None, description="Year for calendar"),
    month: int = Query(default=None, ge=1, le=12, description="Month (1-12)"),
    department_id: Optional[int] = Query(default=None, description="Filter by department"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get payment calendar view for a specific month
    Returns daily aggregated payment data with baseline plan

    - USER: Can only see payment calendar for their own department
    - MANAGER/ADMIN: Can see payment calendar for all departments or filter by department
    """
    # Use current year/month if not provided
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        dept_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        dept_id = department_id if department_id else None
    else:
        dept_id = None

    # Get calendar data from forecast service
    forecast_service = PaymentForecastService(db)
    calendar_data = forecast_service.get_payment_calendar(
        year=year,
        month=month,
        department_id=dept_id,  # Use dept_id instead of department_id
        category_id=category_id,
        organization_id=organization_id,
    )

    # Get baseline budget data
    baseline = db.query(BudgetVersion).filter(
        BudgetVersion.year == year,
        BudgetVersion.department_id == dept_id,
        BudgetVersion.is_baseline == True
    ).first()

    has_baseline = baseline is not None
    baseline_version_name = baseline.version_name if baseline else None

    # Get baseline plan details for the month
    baseline_amounts = {}
    if baseline:
        query = db.query(BudgetPlanDetail).filter(
            BudgetPlanDetail.version_id == baseline.id,
            BudgetPlanDetail.month == month
        )

        if category_id:
            query = query.filter(BudgetPlanDetail.category_id == category_id)

        plan_details = query.all()

        # Calculate total monthly baseline
        total_baseline = sum(float(detail.planned_amount) for detail in plan_details)

        # Distribute evenly across days in month
        import calendar as cal
        days_in_month = cal.monthrange(year, month)[1]
        daily_baseline = total_baseline / days_in_month if days_in_month > 0 else 0

        # Store baseline amount for each day
        for day in range(1, days_in_month + 1):
            day_date = datetime(year, month, day).date()
            baseline_amounts[day_date] = daily_baseline

    # Enhance calendar data with baseline amounts
    enhanced_days = []
    for day_data in calendar_data:
        day_date = day_data['date']
        baseline_amt = baseline_amounts.get(day_date, 0) if has_baseline else None

        enhanced_days.append(PaymentCalendarDay(
            date=day_data['date'],
            total_amount=day_data['total_amount'],
            payment_count=day_data['payment_count'],
            baseline_amount=baseline_amt,
            forecast_amount=None  # Can be populated with forecast data if needed
        ))

    return PaymentCalendar(
        year=year,
        month=month,
        days=enhanced_days,
        has_baseline=has_baseline,
        baseline_version_name=baseline_version_name
    )


@router.get("/payment-calendar/{date}", response_model=PaymentsByDay)
def get_payments_by_day(
    date: str = Path(description="Date in ISO format (YYYY-MM-DD)"),
    department_id: Optional[int] = Query(default=None, description="Filter by department"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all payments for a specific day
    Returns detailed list of expenses

    - USER: Can only see payments for their own department
    - MANAGER/ADMIN: Can see payments for all departments or filter by department
    """
    try:
        payment_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    forecast_service = PaymentForecastService(db)
    result = forecast_service.get_payments_by_day(
        date=payment_date,
        department_id=department_id,
        category_id=category_id,
        organization_id=organization_id,
    )

    payments = result['expenses']
    payroll_forecast = result['payroll_forecast']

    # Convert expenses to dict format
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

    # Add payroll actual payments as a "virtual" payment if exists
    total_amount = sum(p["amount"] for p in payments_data)
    total_count = len(payments_data)

    if payroll_forecast and payroll_forecast['type'] == 'payroll_actual':
        # Add actual payroll payment as a virtual payment entry (only if actual, not forecast)
        payments_data.append({
            "id": -1,  # Virtual ID for payroll
            "number": f"ФОТ-{payment_date.year}-{payment_date.month:02d}-{payment_date.day:02d}",
            "amount": payroll_forecast['amount'],
            "payment_date": payment_date.isoformat(),
            "category_id": None,
            "category_name": "Заработная плата",
            "contractor_id": None,
            "contractor_name": f"{payroll_forecast['employee_count']} сотрудников",
            "organization_id": None,
            "organization_name": None,
            "status": "PAID",
            "comment": payroll_forecast['description'],
        })
        total_amount += payroll_forecast['amount']
        total_count += 1

    return PaymentsByDay(
        date=payment_date.date(),
        total_count=total_count,
        total_amount=total_amount,
        payments=[PaymentDetail(**item) for item in payments_data],
    )


@router.get("/payment-forecast", response_model=PaymentForecast)
def get_payment_forecast(
    start_date: str = Query(description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(description="End date in ISO format (YYYY-MM-DD)"),
    method: ForecastMethod = Query(default="simple_average", description="Forecast method"),
    lookback_days: int = Query(default=90, ge=30, le=365, description="Days to look back for historical data"),
    department_id: Optional[int] = Query(default=None, description="Filter by department (ADMIN/MANAGER only)"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate payment forecast for future period
    Methods: simple_average, moving_average, seasonal

    - USER: Can only generate forecast for their own department
    - MANAGER/ADMIN: Can generate forecast for all departments or filter by department
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if end <= start:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    forecast_service = PaymentForecastService(db)
    forecast_data = forecast_service.generate_forecast(
        start_date=start,
        end_date=end,
        method=method,
        lookback_days=lookback_days,
        department_id=department_id,
        category_id=category_id,
        organization_id=organization_id,
    )

    # Calculate summary statistics
    total_predicted = sum(item['predicted_amount'] for item in forecast_data)
    avg_daily = total_predicted / len(forecast_data) if forecast_data else 0

    return PaymentForecast(
        period=PaymentForecastPeriod(
            start_date=start_date,
            end_date=end_date,
            days=len(forecast_data),
        ),
        method=ForecastMethodEnum(method),
        lookback_days=lookback_days,
        summary=PaymentForecastSummary(
            total_predicted=round(total_predicted, 2),
            average_daily=round(avg_daily, 2),
        ),
        forecast=[
            PaymentForecastPoint(
                date=item["date"],
                predicted_amount=item["predicted_amount"],
                confidence=item["confidence"],
                method=ForecastMethodEnum(item["method"]),
            )
            for item in forecast_data
        ],
    )


@router.get("/payment-forecast/summary", response_model=ForecastSummary)
def get_payment_forecast_summary(
    start_date: str = Query(description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(description="End date in ISO format (YYYY-MM-DD)"),
    department_id: Optional[int] = Query(default=None, description="Filter by department (ADMIN/MANAGER only)"),
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    organization_id: Optional[int] = Query(default=None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get forecast summary comparing different methods

    - USER: Can only see forecast summary for their own department
    - MANAGER/ADMIN: Can see forecast summary for all departments or filter by department
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    forecast_service = PaymentForecastService(db)
    summary = forecast_service.get_forecast_summary(
        start_date=start,
        end_date=end,
        department_id=department_id,
        category_id=category_id,
        organization_id=organization_id,
    )

    return ForecastSummary(
        period=ForecastSummaryPeriod(**summary["period"]),
        forecasts=ForecastSummaryMethods(
            simple_average=ForecastSummaryMethodStats(
                total=summary["forecasts"]["simple_average"]["total"],
                daily_avg=summary["forecasts"]["simple_average"]["daily_avg"],
            ),
            moving_average=ForecastSummaryMethodStats(
                total=summary["forecasts"]["moving_average"]["total"],
                daily_avg=summary["forecasts"]["moving_average"]["daily_avg"],
            ),
            seasonal=ForecastSummaryMethodStats(
                total=summary["forecasts"]["seasonal"]["total"],
                daily_avg=summary["forecasts"]["seasonal"]["daily_avg"],
            ),
        ),
    )


@router.get("/plan-vs-actual", response_model=PlanVsActualSummary)
def get_plan_vs_actual(
    year: int = Query(..., description="Target year for comparison"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare baseline budget plan against actual expenses.
    Returns monthly and category-level breakdown of planned vs actual spending.
    """
    # Find baseline version for the year
    baseline_query = db.query(BudgetVersion).filter(
        BudgetVersion.year == year,
        BudgetVersion.is_baseline == True
    )

    # Filter by department for USERs
    if current_user.role.value == "USER":
        baseline_query = baseline_query.filter(
            BudgetVersion.department_id == current_user.department_id
        )
    elif department_id:
        baseline_query = baseline_query.filter(
            BudgetVersion.department_id == department_id
        )

    baseline_version = baseline_query.first()

    if not baseline_version:
        raise HTTPException(
            status_code=404,
            detail=f"No baseline budget version found for year {year}"
        )

    # Get all plan details for this version
    plan_details = db.query(BudgetPlanDetail).filter(
        BudgetPlanDetail.version_id == baseline_version.id
    ).all()

    # Get all actuals for the year
    actual_query = db.query(
        Expense.category_id,
        extract('month', Expense.request_date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(
        extract('year', Expense.request_date) == year,
        Expense.status.in_([ExpenseStatusEnum.PAID, ExpenseStatusEnum.PENDING])
    )

    # Filter by department if needed
    if current_user.role.value == "USER":
        actual_query = actual_query.filter(
            Expense.department_id == current_user.department_id
        )
    elif department_id:
        actual_query = actual_query.filter(
            Expense.department_id == department_id
        )

    actuals_raw = actual_query.group_by(
        Expense.category_id,
        extract('month', Expense.request_date)
    ).all()

    # Build actuals lookup
    actuals_dict = {}
    for row in actuals_raw:
        key = (row.category_id, int(row.month))
        actuals_dict[key] = float(row.total)

    # Build monthly aggregates
    monthly_planned = {}
    monthly_actual = {}

    for detail in plan_details:
        month = detail.month
        planned = float(detail.planned_amount)

        # Aggregate planned
        monthly_planned[month] = monthly_planned.get(month, 0) + planned

        # Get actual for this category/month
        actual = actuals_dict.get((detail.category_id, month), 0)
        monthly_actual[month] = monthly_actual.get(month, 0) + actual

    # Build by_month list
    by_month = []
    for month in range(1, 13):
        planned = monthly_planned.get(month, 0)
        actual = monthly_actual.get(month, 0)
        difference = actual - planned
        execution_percent = (actual / planned * 100) if planned > 0 else 0

        by_month.append(PlanVsActualMonthly(
            month=month,
            month_name=datetime(year, month, 1).strftime("%B"),
            planned=planned,
            actual=actual,
            difference=difference,
            execution_percent=round(execution_percent, 2)
        ))

    # Build by_category list
    category_aggregates = {}
    for detail in plan_details:
        cat_id = detail.category_id
        if cat_id not in category_aggregates:
            category_aggregates[cat_id] = {
                "planned": 0,
                "actual": 0,
                "monthly": {}
            }

        planned = float(detail.planned_amount)
        actual = actuals_dict.get((cat_id, detail.month), 0)

        category_aggregates[cat_id]["planned"] += planned
        category_aggregates[cat_id]["actual"] += actual
        category_aggregates[cat_id]["monthly"][detail.month] = {
            "planned": planned,
            "actual": actual
        }

    by_category = []
    for cat_id, data in category_aggregates.items():
        # Get category name
        category = db.query(BudgetCategory).filter(
            BudgetCategory.id == cat_id
        ).first()

        planned_total = data["planned"]
        actual_total = data["actual"]
        difference = actual_total - planned_total
        execution_percent = (actual_total / planned_total * 100) if planned_total > 0 else 0

        # Build monthly breakdown for category
        monthly_breakdown = []
        for month in range(1, 13):
            month_data = data["monthly"].get(month, {"planned": 0, "actual": 0})
            m_planned = month_data["planned"]
            m_actual = month_data["actual"]
            m_diff = m_actual - m_planned
            m_exec = (m_actual / m_planned * 100) if m_planned > 0 else 0

            monthly_breakdown.append(PlanVsActualMonthly(
                month=month,
                month_name=datetime(year, month, 1).strftime("%B"),
                planned=m_planned,
                actual=m_actual,
                difference=m_diff,
                execution_percent=round(m_exec, 2)
            ))

        by_category.append(PlanVsActualCategory(
            category_id=cat_id,
            category_name=category.name if category else f"Category {cat_id}",
            planned=planned_total,
            actual=actual_total,
            difference=difference,
            execution_percent=round(execution_percent, 2),
            monthly=monthly_breakdown
        ))

    # Calculate totals
    total_planned = sum(monthly_planned.values())
    total_actual = sum(monthly_actual.values())
    total_difference = total_actual - total_planned
    total_execution_percent = (total_actual / total_planned * 100) if total_planned > 0 else 0

    return PlanVsActualSummary(
        year=year,
        baseline_version_id=baseline_version.id,
        baseline_version_name=baseline_version.version_name,
        total_planned=total_planned,
        total_actual=total_actual,
        total_difference=total_difference,
        execution_percent=round(total_execution_percent, 2),
        by_month=by_month,
        by_category=by_category
    )


@router.get("/budget-status", response_model=BudgetStatusResponse)
def get_budget_status(
    year: int = Query(..., description="Year to check"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current budget status with alerts for overruns and at-risk categories.
    Returns categories that have exceeded budget or are approaching limits (>=90%).
    """
    # Determine department to check
    if current_user.role.value == "USER":
        dept_id = current_user.department_id
    elif department_id:
        dept_id = department_id
    else:
        dept_id = current_user.department_id

    validator = BudgetValidator(db)
    status = validator.get_budget_status(year, dept_id, category_id)

    return BudgetStatusResponse(**status)


@router.post("/validate-expense", response_model=ExpenseValidationResponse)
def validate_expense(
    amount: float = Query(..., description="Expense amount"),
    category_id: int = Query(..., description="Budget category ID"),
    request_date: str = Query(..., description="Request date (YYYY-MM-DD)"),
    expense_id: Optional[int] = Query(None, description="Expense ID (for updates)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate an expense against budget baseline before creating/updating.
    Returns warnings and errors if budget limits would be exceeded.
    """
    try:
        date = datetime.fromisoformat(request_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    validator = BudgetValidator(db)
    result = validator.validate_expense(
        amount=amount,
        category_id=category_id,
        request_date=date,
        department_id=current_user.department_id,
        expense_id=expense_id
    )

    return ExpenseValidationResponse(
        is_valid=result.is_valid,
        warnings=result.warnings,
        errors=result.errors,
        budget_info=BudgetInfo(**result.budget_info) if result.budget_info else None
    )


@router.get("/budget-income-statement", response_model=BudgetIncomeStatement)
def get_budget_income_statement(
    year: int = Query(..., description="Year for the budget income statement"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    БДР (Бюджет доходов и расходов) - Budget Income Statement

    Returns a comprehensive financial report showing:
    - Revenue (planned vs actual)
    - Expenses (planned vs actual)
    - Profit (Revenue - Expenses)
    - Profitability metrics (ROI, Profit Margin)
    - Monthly breakdown

    - USER: Can only see their own department
    - MANAGER/ADMIN: Can filter by department or see all
    """
    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        pass  # Can filter by department or see all

    # Get department name if specific department
    department_name = None
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        department_name = dept.name if dept else None

    # MONTH_NAMES for Russian locale
    MONTH_NAMES = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    # Initialize monthly data structure
    monthly_data = {}
    for month in range(1, 13):
        monthly_data[month] = {
            "month": month,
            "month_name": MONTH_NAMES[month - 1],
            "revenue_planned": 0.0,
            "revenue_actual": 0.0,
            "expenses_planned": 0.0,
            "expenses_actual": 0.0,
        }

    # ========== REVENUE DATA ==========

    # Get revenue planned from RevenuePlanDetail
    # RevenuePlanDetail stores data in fields month_01...month_12
    # Need to get approved plan versions for the year

    approved_versions_query = db.query(RevenuePlanVersion.id).join(
        RevenuePlan, RevenuePlanVersion.plan_id == RevenuePlan.id
    ).filter(
        RevenuePlan.year == year,
        RevenuePlanVersion.status == RevenueVersionStatusEnum.APPROVED
    )

    if department_id:
        approved_versions_query = approved_versions_query.filter(
            RevenuePlan.department_id == department_id
        )

    approved_version_ids = [v.id for v in approved_versions_query.all()]

    if approved_version_ids:
        # Get details of approved versions
        details = db.query(RevenuePlanDetail).filter(
            RevenuePlanDetail.version_id.in_(approved_version_ids)
        ).all()

        # Sum by months
        for detail in details:
            for month_num in range(1, 13):
                month_field = f"month_{month_num:02d}"
                value = getattr(detail, month_field, 0) or 0
                monthly_data[month_num]["revenue_planned"] += float(value)

    # Get revenue actual from RevenueActual
    revenue_actual_query = db.query(
        RevenueActual.month,
        func.sum(RevenueActual.actual_amount).label('total')
    ).filter(RevenueActual.year == year)

    if department_id:
        revenue_actual_query = revenue_actual_query.filter(RevenueActual.department_id == department_id)

    revenue_actual_query = revenue_actual_query.group_by(RevenueActual.month)

    for row in revenue_actual_query.all():
        if row.month in monthly_data:
            monthly_data[row.month]["revenue_actual"] = float(row.total or 0)

    # ========== EXPENSE DATA ==========

    # Get expenses planned from BudgetPlan
    expenses_plan_query = db.query(
        BudgetPlan.month,
        func.sum(BudgetPlan.planned_amount).label('total')
    ).filter(BudgetPlan.year == year)

    if department_id:
        expenses_plan_query = expenses_plan_query.filter(BudgetPlan.department_id == department_id)

    expenses_plan_query = expenses_plan_query.group_by(BudgetPlan.month)

    for row in expenses_plan_query.all():
        if row.month in monthly_data:
            monthly_data[row.month]["expenses_planned"] = float(row.total or 0)

    # Get expenses actual from Expense table
    expenses_actual_query = db.query(
        extract('month', Expense.request_date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(extract('year', Expense.request_date) == year)

    if department_id:
        expenses_actual_query = expenses_actual_query.filter(Expense.department_id == department_id)

    expenses_actual_query = expenses_actual_query.group_by(extract('month', Expense.request_date))

    for row in expenses_actual_query.all():
        month = int(row.month)
        if month in monthly_data:
            monthly_data[month]["expenses_actual"] = float(row.total or 0)

    # Also add PayrollPlan to expenses
    payroll_plan_query = db.query(
        PayrollPlan.month,
        func.sum(PayrollPlan.total_planned).label('total')
    ).filter(PayrollPlan.year == year)

    if department_id:
        payroll_plan_query = payroll_plan_query.filter(PayrollPlan.department_id == department_id)

    payroll_plan_query = payroll_plan_query.group_by(PayrollPlan.month)

    for row in payroll_plan_query.all():
        if row.month in monthly_data:
            monthly_data[row.month]["expenses_planned"] += float(row.total or 0)

    # Add PayrollActual to actual expenses
    payroll_actual_query = db.query(
        PayrollActual.month,
        func.sum(PayrollActual.total_paid).label('total')
    ).filter(PayrollActual.year == year)

    if department_id:
        payroll_actual_query = payroll_actual_query.filter(PayrollActual.department_id == department_id)

    payroll_actual_query = payroll_actual_query.group_by(PayrollActual.month)

    for row in payroll_actual_query.all():
        if row.month in monthly_data:
            monthly_data[row.month]["expenses_actual"] += float(row.total or 0)

    # ========== CALCULATE TOTALS AND METRICS ==========

    total_revenue_planned = sum(m["revenue_planned"] for m in monthly_data.values())
    total_revenue_actual = sum(m["revenue_actual"] for m in monthly_data.values())
    total_expenses_planned = sum(m["expenses_planned"] for m in monthly_data.values())
    total_expenses_actual = sum(m["expenses_actual"] for m in monthly_data.values())

    revenue_difference = total_revenue_actual - total_revenue_planned
    revenue_execution_percent = (
        (total_revenue_actual / total_revenue_planned * 100)
        if total_revenue_planned > 0 else 0
    )

    expenses_difference = total_expenses_actual - total_expenses_planned
    expenses_execution_percent = (
        (total_expenses_actual / total_expenses_planned * 100)
        if total_expenses_planned > 0 else 0
    )

    profit_planned = total_revenue_planned - total_expenses_planned
    profit_actual = total_revenue_actual - total_expenses_actual
    profit_difference = profit_actual - profit_planned

    profit_margin_planned = (
        (profit_planned / total_revenue_planned * 100)
        if total_revenue_planned > 0 else 0
    )
    profit_margin_actual = (
        (profit_actual / total_revenue_actual * 100)
        if total_revenue_actual > 0 else 0
    )

    roi_planned = (
        (profit_planned / total_expenses_planned * 100)
        if total_expenses_planned > 0 else 0
    )
    roi_actual = (
        (profit_actual / total_expenses_actual * 100)
        if total_expenses_actual > 0 else 0
    )

    # ========== BUILD MONTHLY BREAKDOWN ==========

    by_month = []
    for month in range(1, 13):
        m_data = monthly_data[month]
        profit_planned_month = m_data["revenue_planned"] - m_data["expenses_planned"]
        profit_actual_month = m_data["revenue_actual"] - m_data["expenses_actual"]

        profit_margin_planned_month = (
            (profit_planned_month / m_data["revenue_planned"] * 100)
            if m_data["revenue_planned"] > 0 else 0
        )
        profit_margin_actual_month = (
            (profit_actual_month / m_data["revenue_actual"] * 100)
            if m_data["revenue_actual"] > 0 else 0
        )

        by_month.append(
            BudgetIncomeStatementMonthly(
                month=month,
                month_name=m_data["month_name"],
                revenue_planned=m_data["revenue_planned"],
                revenue_actual=m_data["revenue_actual"],
                expenses_planned=m_data["expenses_planned"],
                expenses_actual=m_data["expenses_actual"],
                profit_planned=profit_planned_month,
                profit_actual=profit_actual_month,
                profit_margin_planned=round(profit_margin_planned_month, 2),
                profit_margin_actual=round(profit_margin_actual_month, 2),
            )
        )

    return BudgetIncomeStatement(
        year=year,
        department_id=department_id,
        department_name=department_name,
        revenue_planned=total_revenue_planned,
        revenue_actual=total_revenue_actual,
        revenue_difference=revenue_difference,
        revenue_execution_percent=round(revenue_execution_percent, 2),
        expenses_planned=total_expenses_planned,
        expenses_actual=total_expenses_actual,
        expenses_difference=expenses_difference,
        expenses_execution_percent=round(expenses_execution_percent, 2),
        profit_planned=profit_planned,
        profit_actual=profit_actual,
        profit_difference=profit_difference,
        profit_margin_planned=round(profit_margin_planned, 2),
        profit_margin_actual=round(profit_margin_actual, 2),
        roi_planned=round(roi_planned, 2),
        roi_actual=round(roi_actual, 2),
        by_month=by_month,
    )


@router.get("/customer-metrics-analytics", response_model=CustomerMetricsAnalytics)
def get_customer_metrics_analytics(
    year: int = Query(..., description="Year for customer metrics analytics"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Customer Metrics Analytics (Аналитика клиентских метрик)

    Returns comprehensive customer analytics showing:
    - ОКБ (Общая клиентская база) - Total Customer Base
    - АКБ (Активная клиентская база) - Active Customer Base
    - Покрытие (АКБ/ОКБ) - Coverage Rate
    - Средний чек по сегментам - Average Order Value by segments
    - Динамика по месяцам - Monthly trends
    - Разбивка по потокам доходов - Breakdown by revenue streams
    - Growth metrics compared to previous year
    """
    # Multi-tenancy enforcement
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id

    # Get department name if filtering by department
    department_name = None
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if dept:
            department_name = dept.name

    # Build base query for current year
    query = db.query(CustomerMetrics).filter(CustomerMetrics.year == year)
    if department_id:
        query = query.filter(CustomerMetrics.department_id == department_id)

    # Get all metrics for the year
    current_year_metrics = query.all()

    if not current_year_metrics:
        # Return empty data instead of 404 error for better UX
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        by_month_empty = [
            CustomerMetricsMonthly(
                month=m,
                month_name=month_names[m-1],
                total_customer_base=0,
                active_customer_base=0,
                coverage_rate=0.0,
                avg_order_value=0.0,
                avg_order_value_regular=0.0,
                avg_order_value_network=0.0,
                avg_order_value_new=0.0,
            )
            for m in range(1, 13)
        ]

        return CustomerMetricsAnalytics(
            year=year,
            department_id=department_id,
            department_name=department_name,
            total_customer_base=0,
            active_customer_base=0,
            coverage_rate=0.0,
            regular_clinics=0,
            network_clinics=0,
            new_clinics=0,
            avg_order_value=0.0,
            avg_order_value_regular=0.0,
            avg_order_value_network=0.0,
            avg_order_value_new=0.0,
            customer_base_growth=None,
            active_base_growth=None,
            avg_check_growth=None,
            by_month=by_month_empty,
            by_stream=[],
        )

    # Aggregate totals for current year
    total_customer_base = sum(m.total_customer_base or 0 for m in current_year_metrics)
    active_customer_base = sum(m.active_customer_base or 0 for m in current_year_metrics)
    coverage_rate = (active_customer_base / total_customer_base * 100) if total_customer_base > 0 else 0

    # Clinic segments
    regular_clinics = sum(m.regular_clinics or 0 for m in current_year_metrics)
    network_clinics = sum(m.network_clinics or 0 for m in current_year_metrics)
    new_clinics = sum(m.new_clinics or 0 for m in current_year_metrics)

    # Calculate weighted average order values
    def weighted_avg(metrics_list, field_name):
        total_value = sum(getattr(m, field_name, 0) or 0 for m in metrics_list)
        count = sum(1 for m in metrics_list if getattr(m, field_name, None) is not None)
        return float(total_value / count) if count > 0 else 0.0

    avg_order_value = weighted_avg(current_year_metrics, "avg_order_value")
    avg_order_value_regular = weighted_avg(current_year_metrics, "avg_order_value_regular")
    avg_order_value_network = weighted_avg(current_year_metrics, "avg_order_value_network")
    avg_order_value_new = weighted_avg(current_year_metrics, "avg_order_value_new")

    # Get previous year metrics for growth calculation
    prev_year_query = db.query(CustomerMetrics).filter(CustomerMetrics.year == year - 1)
    if department_id:
        prev_year_query = prev_year_query.filter(CustomerMetrics.department_id == department_id)
    prev_year_metrics = prev_year_query.all()

    customer_base_growth = None
    active_base_growth = None
    avg_check_growth = None

    if prev_year_metrics:
        prev_total_customer_base = sum(m.total_customer_base or 0 for m in prev_year_metrics)
        prev_active_customer_base = sum(m.active_customer_base or 0 for m in prev_year_metrics)
        prev_avg_order_value = weighted_avg(prev_year_metrics, "avg_order_value")

        if prev_total_customer_base > 0:
            customer_base_growth = ((total_customer_base - prev_total_customer_base) / prev_total_customer_base) * 100
        if prev_active_customer_base > 0:
            active_base_growth = ((active_customer_base - prev_active_customer_base) / prev_active_customer_base) * 100
        if prev_avg_order_value > 0:
            avg_check_growth = ((avg_order_value - prev_avg_order_value) / prev_avg_order_value) * 100

    # Monthly breakdown
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    monthly_data = {}
    for month in range(1, 13):
        monthly_data[month] = {
            "month": month,
            "month_name": month_names[month - 1],
            "total_customer_base": 0,
            "active_customer_base": 0,
            "coverage_rate": 0.0,
            "avg_order_value": 0.0,
            "avg_order_value_regular": 0.0,
            "avg_order_value_network": 0.0,
            "avg_order_value_new": 0.0,
        }

    # Aggregate metrics by month
    for metrics in current_year_metrics:
        month = metrics.month
        if month in monthly_data:
            monthly_data[month]["total_customer_base"] += metrics.total_customer_base or 0
            monthly_data[month]["active_customer_base"] += metrics.active_customer_base or 0
            # Average order values - take average across revenue streams
            if metrics.avg_order_value:
                monthly_data[month]["avg_order_value"] += float(metrics.avg_order_value)
            if metrics.avg_order_value_regular:
                monthly_data[month]["avg_order_value_regular"] += float(metrics.avg_order_value_regular)
            if metrics.avg_order_value_network:
                monthly_data[month]["avg_order_value_network"] += float(metrics.avg_order_value_network)
            if metrics.avg_order_value_new:
                monthly_data[month]["avg_order_value_new"] += float(metrics.avg_order_value_new)

    # Calculate coverage rates and averages
    by_month = []
    for month in range(1, 13):
        m_data = monthly_data[month]
        coverage = (m_data["active_customer_base"] / m_data["total_customer_base"] * 100) if m_data["total_customer_base"] > 0 else 0

        # Count streams with data for averaging
        month_metrics = [m for m in current_year_metrics if m.month == month]
        stream_count = len(month_metrics) if month_metrics else 1

        by_month.append(
            CustomerMetricsMonthly(
                month=month,
                month_name=m_data["month_name"],
                total_customer_base=m_data["total_customer_base"],
                active_customer_base=m_data["active_customer_base"],
                coverage_rate=round(coverage, 2),
                avg_order_value=round(m_data["avg_order_value"] / stream_count, 2),
                avg_order_value_regular=round(m_data["avg_order_value_regular"] / stream_count, 2),
                avg_order_value_network=round(m_data["avg_order_value_network"] / stream_count, 2),
                avg_order_value_new=round(m_data["avg_order_value_new"] / stream_count, 2),
            )
        )

    # Breakdown by revenue stream
    stream_data = {}
    for metrics in current_year_metrics:
        stream_id = metrics.revenue_stream_id
        if stream_id not in stream_data:
            stream_data[stream_id] = {
                "revenue_stream_id": stream_id,
                "revenue_stream_name": metrics.revenue_stream.name if metrics.revenue_stream else f"Stream #{stream_id}",
                "total_customer_base": 0,
                "active_customer_base": 0,
                "regular_clinics": 0,
                "network_clinics": 0,
                "new_clinics": 0,
                "avg_order_value_sum": 0.0,
                "count": 0,
            }

        stream_data[stream_id]["total_customer_base"] += metrics.total_customer_base or 0
        stream_data[stream_id]["active_customer_base"] += metrics.active_customer_base or 0
        stream_data[stream_id]["regular_clinics"] += metrics.regular_clinics or 0
        stream_data[stream_id]["network_clinics"] += metrics.network_clinics or 0
        stream_data[stream_id]["new_clinics"] += metrics.new_clinics or 0
        if metrics.avg_order_value:
            stream_data[stream_id]["avg_order_value_sum"] += float(metrics.avg_order_value)
            stream_data[stream_id]["count"] += 1

    by_stream = []
    for stream_id, data in stream_data.items():
        coverage = (data["active_customer_base"] / data["total_customer_base"] * 100) if data["total_customer_base"] > 0 else 0
        avg_order = data["avg_order_value_sum"] / data["count"] if data["count"] > 0 else 0.0

        by_stream.append(
            CustomerMetricsByStream(
                revenue_stream_id=data["revenue_stream_id"],
                revenue_stream_name=data["revenue_stream_name"],
                total_customer_base=data["total_customer_base"],
                active_customer_base=data["active_customer_base"],
                coverage_rate=round(coverage, 2),
                avg_order_value=round(avg_order, 2),
                regular_clinics=data["regular_clinics"],
                network_clinics=data["network_clinics"],
                new_clinics=data["new_clinics"],
            )
        )

    return CustomerMetricsAnalytics(
        year=year,
        department_id=department_id,
        department_name=department_name,
        total_customer_base=total_customer_base,
        active_customer_base=active_customer_base,
        coverage_rate=round(coverage_rate, 2),
        regular_clinics=regular_clinics,
        network_clinics=network_clinics,
        new_clinics=new_clinics,
        avg_order_value=round(avg_order_value, 2),
        avg_order_value_regular=round(avg_order_value_regular, 2),
        avg_order_value_network=round(avg_order_value_network, 2),
        avg_order_value_new=round(avg_order_value_new, 2),
        customer_base_growth=round(customer_base_growth, 2) if customer_base_growth is not None else None,
        active_base_growth=round(active_base_growth, 2) if active_base_growth is not None else None,
        avg_check_growth=round(avg_check_growth, 2) if avg_check_growth is not None else None,
        by_month=by_month,
        by_stream=by_stream,
    )


@router.get("/revenue-analytics", response_model=RevenueAnalytics)
def get_revenue_analytics(
    year: int = Query(..., description="Year for revenue analytics"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Revenue Analytics (Аналитика доходов)
    
    Returns comprehensive revenue analytics showing:
    - Total revenue (planned vs actual)
    - Региональная разбивка (regional breakdown by revenue streams)
    - Продуктовый микс (product mix by revenue categories)
    - Помесячная динамика (monthly trends)
    - Growth metrics compared to previous year
    """
    # Multi-tenancy enforcement
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id

    # Get department name
    department_name = None
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if dept:
            department_name = dept.name

    # Query revenue actuals for current year
    query = db.query(RevenueActual).filter(RevenueActual.year == year)
    if department_id:
        query = query.filter(RevenueActual.department_id == department_id)

    current_year_data = query.all()

    if not current_year_data:
        # Return empty data instead of 404 error for better UX
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        by_month_empty = [
            RevenueAnalyticsMonthly(
                month=m,
                month_name=month_names[m-1],
                planned=0.0,
                actual=0.0,
                variance=0.0,
                variance_percent=0.0,
                execution_percent=0.0,
            )
            for m in range(1, 13)
        ]

        return RevenueAnalytics(
            year=year,
            department_id=department_id,
            department_name=department_name,
            total_planned=0.0,
            total_actual=0.0,
            total_variance=0.0,
            total_variance_percent=0.0,
            total_execution_percent=0.0,
            planned_growth=None,
            actual_growth=None,
            by_month=by_month_empty,
            by_stream=None,
            by_category=None,
        )

    # Calculate totals
    total_planned = sum(float(item.planned_amount or 0) for item in current_year_data)
    total_actual = sum(float(item.actual_amount or 0) for item in current_year_data)
    total_variance = total_actual - total_planned
    total_variance_percent = ((total_variance / total_planned) * 100) if total_planned > 0 else 0
    total_execution_percent = ((total_actual / total_planned) * 100) if total_planned > 0 else 0

    # Get previous year data for growth metrics
    prev_year_query = db.query(RevenueActual).filter(RevenueActual.year == year - 1)
    if department_id:
        prev_year_query = prev_year_query.filter(RevenueActual.department_id == department_id)
    prev_year_data = prev_year_query.all()

    planned_growth = None
    actual_growth = None

    if prev_year_data:
        prev_total_planned = sum(float(item.planned_amount or 0) for item in prev_year_data)
        prev_total_actual = sum(float(item.actual_amount or 0) for item in prev_year_data)

        if prev_total_planned > 0:
            planned_growth = ((total_planned - prev_total_planned) / prev_total_planned) * 100
        if prev_total_actual > 0:
            actual_growth = ((total_actual - prev_total_actual) / prev_total_actual) * 100

    # Monthly breakdown
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    monthly_data = {}
    for month in range(1, 13):
        monthly_data[month] = {
            "month": month,
            "month_name": month_names[month - 1],
            "planned": 0.0,
            "actual": 0.0,
        }

    for item in current_year_data:
        month = item.month
        if month in monthly_data:
            monthly_data[month]["planned"] += float(item.planned_amount or 0)
            monthly_data[month]["actual"] += float(item.actual_amount or 0)

    by_month = []
    for month in range(1, 13):
        m_data = monthly_data[month]
        variance = m_data["actual"] - m_data["planned"]
        variance_percent = ((variance / m_data["planned"]) * 100) if m_data["planned"] > 0 else 0
        execution_percent = ((m_data["actual"] / m_data["planned"]) * 100) if m_data["planned"] > 0 else 0

        by_month.append(
            RevenueAnalyticsMonthly(
                month=month,
                month_name=m_data["month_name"],
                planned=round(m_data["planned"], 2),
                actual=round(m_data["actual"], 2),
                variance=round(variance, 2),
                variance_percent=round(variance_percent, 2),
                execution_percent=round(execution_percent, 2),
            )
        )

    # Breakdown by revenue stream (regional breakdown)
    stream_data = {}
    for item in current_year_data:
        if item.revenue_stream_id:
            stream_id = item.revenue_stream_id
            if stream_id not in stream_data:
                stream_data[stream_id] = {
                    "revenue_stream_id": stream_id,
                    "revenue_stream_name": item.revenue_stream.name if item.revenue_stream else f"Stream #{stream_id}",
                    "stream_type": item.revenue_stream.stream_type.value if item.revenue_stream else "UNKNOWN",
                    "planned": 0.0,
                    "actual": 0.0,
                }

            stream_data[stream_id]["planned"] += float(item.planned_amount or 0)
            stream_data[stream_id]["actual"] += float(item.actual_amount or 0)

    by_stream = []
    for stream_id, data in stream_data.items():
        variance = data["actual"] - data["planned"]
        variance_percent = ((variance / data["planned"]) * 100) if data["planned"] > 0 else 0
        execution_percent = ((data["actual"] / data["planned"]) * 100) if data["planned"] > 0 else 0
        share_of_total = ((data["actual"] / total_actual) * 100) if total_actual > 0 else 0

        by_stream.append(
            RevenueAnalyticsByStream(
                revenue_stream_id=data["revenue_stream_id"],
                revenue_stream_name=data["revenue_stream_name"],
                stream_type=data["stream_type"],
                planned=round(data["planned"], 2),
                actual=round(data["actual"], 2),
                variance=round(variance, 2),
                variance_percent=round(variance_percent, 2),
                execution_percent=round(execution_percent, 2),
                share_of_total=round(share_of_total, 2),
            )
        )

    # Breakdown by revenue category (product mix)
    category_data = {}
    for item in current_year_data:
        if item.revenue_category_id:
            category_id = item.revenue_category_id
            if category_id not in category_data:
                category_data[category_id] = {
                    "revenue_category_id": category_id,
                    "revenue_category_name": item.revenue_category.name if item.revenue_category else f"Category #{category_id}",
                    "category_type": item.revenue_category.category_type.value if item.revenue_category else "UNKNOWN",
                    "planned": 0.0,
                    "actual": 0.0,
                }

            category_data[category_id]["planned"] += float(item.planned_amount or 0)
            category_data[category_id]["actual"] += float(item.actual_amount or 0)

    by_category = []
    for category_id, data in category_data.items():
        variance = data["actual"] - data["planned"]
        variance_percent = ((variance / data["planned"]) * 100) if data["planned"] > 0 else 0
        execution_percent = ((data["actual"] / data["planned"]) * 100) if data["planned"] > 0 else 0
        share_of_total = ((data["actual"] / total_actual) * 100) if total_actual > 0 else 0

        by_category.append(
            RevenueAnalyticsByCategory(
                revenue_category_id=data["revenue_category_id"],
                revenue_category_name=data["revenue_category_name"],
                category_type=data["category_type"],
                planned=round(data["planned"], 2),
                actual=round(data["actual"], 2),
                variance=round(variance, 2),
                variance_percent=round(variance_percent, 2),
                execution_percent=round(execution_percent, 2),
                share_of_total=round(share_of_total, 2),
            )
        )

    return RevenueAnalytics(
        year=year,
        department_id=department_id,
        department_name=department_name,
        total_planned=round(total_planned, 2),
        total_actual=round(total_actual, 2),
        total_variance=round(total_variance, 2),
        total_variance_percent=round(total_variance_percent, 2),
        total_execution_percent=round(total_execution_percent, 2),
        planned_growth=round(planned_growth, 2) if planned_growth is not None else None,
        actual_growth=round(actual_growth, 2) if actual_growth is not None else None,
        by_month=by_month,
        by_stream=by_stream if by_stream else None,
        by_category=by_category if by_category else None,
    )


# ==================== EXPORT ENDPOINTS ====================

@router.get("/budget-income-statement/export")
def export_budget_income_statement(
    year: int = Query(..., description="Year for the budget income statement"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export БДР (Budget Income Statement) to Excel
    
    Creates Excel file with 4 sheets:
    - Summary: Overall financial metrics
    - Monthly: Monthly breakdown
    - Revenue: Revenue by category
    - Expenses: Expenses by category
    """
    # Multi-tenancy: enforce department access
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if department_id is None:
            target_department_id = current_user.department_id
    
    # Get department name
    department_name = None
    if target_department_id:
        dept = db.query(Department).filter(Department.id == target_department_id).first()
        if dept:
            department_name = dept.name
    
    # === REVENUE DATA ===
    revenue_planned_query = db.query(func.sum(RevenuePlanDetail.planned_amount))
    if target_department_id:
        revenue_planned_query = revenue_planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        ).filter(RevenuePlan.department_id == target_department_id)
    else:
        revenue_planned_query = revenue_planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        )
    revenue_planned_query = revenue_planned_query.filter(RevenuePlan.year == year)
    revenue_planned = float(revenue_planned_query.scalar() or 0)
    
    revenue_actual_query = db.query(func.sum(RevenueActual.amount))
    if target_department_id:
        revenue_actual_query = revenue_actual_query.filter(
            RevenueActual.department_id == target_department_id
        )
    revenue_actual_query = revenue_actual_query.filter(extract('year', RevenueActual.date) == year)
    revenue_actual = float(revenue_actual_query.scalar() or 0)
    
    # === EXPENSES DATA ===
    expenses_planned_query = db.query(func.sum(BudgetPlanDetail.planned_amount))
    if target_department_id:
        expenses_planned_query = expenses_planned_query.join(
            BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
        ).join(
            BudgetPlan, BudgetVersion.budget_plan_id == BudgetPlan.id
        ).filter(BudgetPlan.department_id == target_department_id)
    else:
        expenses_planned_query = expenses_planned_query.join(
            BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
        ).join(
            BudgetPlan, BudgetVersion.budget_plan_id == BudgetPlan.id
        )
    expenses_planned_query = expenses_planned_query.filter(BudgetPlan.year == year)
    expenses_planned = float(expenses_planned_query.scalar() or 0)
    
    expenses_actual_query = db.query(func.sum(Expense.amount))
    if target_department_id:
        expenses_actual_query = expenses_actual_query.filter(
            Expense.department_id == target_department_id
        )
    expenses_actual_query = expenses_actual_query.filter(
        extract('year', Expense.expense_date) == year,
        Expense.status.in_([ExpenseStatusEnum.APPROVED, ExpenseStatusEnum.PAID])
    )
    expenses_actual = float(expenses_actual_query.scalar() or 0)
    
    # === PAYROLL DATA ===
    payroll_planned_query = db.query(
        func.sum(PayrollPlan.base_salary + PayrollPlan.monthly_bonus + 
                 PayrollPlan.quarterly_bonus + PayrollPlan.annual_bonus)
    )
    if target_department_id:
        payroll_planned_query = payroll_planned_query.filter(
            PayrollPlan.department_id == target_department_id
        )
    payroll_planned_query = payroll_planned_query.filter(PayrollPlan.year == year)
    payroll_planned = float(payroll_planned_query.scalar() or 0)
    
    payroll_actual_query = db.query(func.sum(PayrollActual.total_amount))
    if target_department_id:
        payroll_actual_query = payroll_actual_query.filter(
            PayrollActual.department_id == target_department_id
        )
    payroll_actual_query = payroll_actual_query.filter(
        extract('year', PayrollActual.payment_date) == year
    )
    payroll_actual = float(payroll_actual_query.scalar() or 0)
    
    # Add payroll to expenses
    expenses_planned += payroll_planned
    expenses_actual += payroll_actual
    
    # === CALCULATIONS ===
    profit_planned = revenue_planned - expenses_planned
    profit_actual = revenue_actual - expenses_actual
    
    profit_margin_planned = (profit_planned / revenue_planned * 100) if revenue_planned > 0 else 0
    profit_margin_actual = (profit_actual / revenue_actual * 100) if revenue_actual > 0 else 0
    roi_planned = (profit_planned / expenses_planned * 100) if expenses_planned > 0 else 0
    roi_actual = (profit_actual / expenses_actual * 100) if expenses_actual > 0 else 0
    
    # === SHEET 1: SUMMARY ===
    summary_data = [
        {"Показатель": "Год", "Значение": year},
        {"Показатель": "Отдел", "Значение": department_name or "Все отделы"},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "ДОХОДЫ", "Значение": ""},
        {"Показатель": "Доходы (План)", "Значение": revenue_planned},
        {"Показатель": "Доходы (Факт)", "Значение": revenue_actual},
        {"Показатель": "Отклонение доходов", "Значение": revenue_actual - revenue_planned},
        {"Показатель": "Исполнение доходов (%)", "Значение": (revenue_actual / revenue_planned * 100) if revenue_planned > 0 else 0},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "РАСХОДЫ", "Значение": ""},
        {"Показатель": "Расходы (План)", "Значение": expenses_planned},
        {"Показатель": "Расходы (Факт)", "Значение": expenses_actual},
        {"Показатель": "Отклонение расходов", "Значение": expenses_actual - expenses_planned},
        {"Показатель": "Исполнение расходов (%)", "Значение": (expenses_actual / expenses_planned * 100) if expenses_planned > 0 else 0},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "ПРИБЫЛЬ", "Значение": ""},
        {"Показатель": "Прибыль (План)", "Значение": profit_planned},
        {"Показатель": "Прибыль (Факт)", "Значение": profit_actual},
        {"Показатель": "Отклонение прибыли", "Значение": profit_actual - profit_planned},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "РЕНТАБЕЛЬНОСТЬ", "Значение": ""},
        {"Показатель": "Рентабельность (План) %", "Значение": profit_margin_planned},
        {"Показатель": "Рентабельность (Факт) %", "Значение": profit_margin_actual},
        {"Показатель": "ROI (План) %", "Значение": roi_planned},
        {"Показатель": "ROI (Факт) %", "Значение": roi_actual},
    ]
    df_summary = pd.DataFrame(summary_data)
    
    # === SHEET 2: MONTHLY BREAKDOWN ===
    monthly_data = []
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    for month in range(1, 13):
        # Revenue monthly
        rev_plan_month = db.query(func.sum(RevenuePlanDetail.planned_amount))
        if target_department_id:
            rev_plan_month = rev_plan_month.join(
                RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
            ).filter(RevenuePlan.department_id == target_department_id)
        else:
            rev_plan_month = rev_plan_month.join(
                RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
            )
        rev_plan_month = rev_plan_month.filter(
            RevenuePlan.year == year,
            RevenuePlanDetail.month == month
        ).scalar() or 0
        
        rev_actual_month = db.query(func.sum(RevenueActual.amount))
        if target_department_id:
            rev_actual_month = rev_actual_month.filter(
                RevenueActual.department_id == target_department_id
            )
        rev_actual_month = rev_actual_month.filter(
            extract('year', RevenueActual.date) == year,
            extract('month', RevenueActual.date) == month
        ).scalar() or 0
        
        # Expenses monthly
        exp_plan_month = db.query(func.sum(BudgetPlanDetail.planned_amount))
        if target_department_id:
            exp_plan_month = exp_plan_month.join(
                BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
            ).join(
                BudgetPlan, BudgetVersion.budget_plan_id == BudgetPlan.id
            ).filter(BudgetPlan.department_id == target_department_id)
        else:
            exp_plan_month = exp_plan_month.join(
                BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
            ).join(
                BudgetPlan, BudgetVersion.budget_plan_id == BudgetPlan.id
            )
        exp_plan_month = exp_plan_month.filter(
            BudgetPlan.year == year,
            BudgetPlanDetail.month == month
        ).scalar() or 0
        
        exp_actual_month = db.query(func.sum(Expense.amount))
        if target_department_id:
            exp_actual_month = exp_actual_month.filter(
                Expense.department_id == target_department_id
            )
        exp_actual_month = exp_actual_month.filter(
            extract('year', Expense.expense_date) == year,
            extract('month', Expense.expense_date) == month,
            Expense.status.in_([ExpenseStatusEnum.APPROVED, ExpenseStatusEnum.PAID])
        ).scalar() or 0
        
        # Payroll monthly
        payroll_plan_month = db.query(
            func.sum(PayrollPlan.base_salary + PayrollPlan.monthly_bonus)
        )
        if target_department_id:
            payroll_plan_month = payroll_plan_month.filter(
                PayrollPlan.department_id == target_department_id
            )
        payroll_plan_month = payroll_plan_month.filter(
            PayrollPlan.year == year,
            PayrollPlan.month == month
        ).scalar() or 0
        
        payroll_actual_month = db.query(func.sum(PayrollActual.total_amount))
        if target_department_id:
            payroll_actual_month = payroll_actual_month.filter(
                PayrollActual.department_id == target_department_id
            )
        payroll_actual_month = payroll_actual_month.filter(
            extract('year', PayrollActual.payment_date) == year,
            extract('month', PayrollActual.payment_date) == month
        ).scalar() or 0
        
        exp_plan_total = float(exp_plan_month) + float(payroll_plan_month)
        exp_actual_total = float(exp_actual_month) + float(payroll_actual_month)
        
        profit_plan = float(rev_plan_month) - exp_plan_total
        profit_act = float(rev_actual_month) - exp_actual_total
        
        monthly_data.append({
            "Месяц": month_names[month - 1],
            "Доходы (План)": float(rev_plan_month),
            "Доходы (Факт)": float(rev_actual_month),
            "Расходы (План)": exp_plan_total,
            "Расходы (Факт)": exp_actual_total,
            "Прибыль (План)": profit_plan,
            "Прибыль (Факт)": profit_act,
            "Рентабельность (План) %": (profit_plan / float(rev_plan_month) * 100) if float(rev_plan_month) > 0 else 0,
            "Рентабельность (Факт) %": (profit_act / float(rev_actual_month) * 100) if float(rev_actual_month) > 0 else 0,
        })
    df_monthly = pd.DataFrame(monthly_data)
    
    # === SHEET 3: REVENUE BY CATEGORY ===
    revenue_by_cat = db.query(
        RevenueCategory.id,
        RevenueCategory.name,
        func.sum(RevenuePlanDetail.planned_amount).label('planned')
    ).join(
        RevenuePlanDetail, RevenueCategory.id == RevenuePlanDetail.revenue_category_id
    ).join(
        RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
    )
    
    if target_department_id:
        revenue_by_cat = revenue_by_cat.filter(
            RevenuePlan.department_id == target_department_id
        )
    
    revenue_by_cat = revenue_by_cat.filter(
        RevenuePlan.year == year
    ).group_by(RevenueCategory.id, RevenueCategory.name).all()
    
    revenue_cat_data = []
    for cat in revenue_by_cat:
        # Get actual for this category
        actual_query = db.query(func.sum(RevenueActual.amount))
        if target_department_id:
            actual_query = actual_query.filter(
                RevenueActual.department_id == target_department_id
            )
        actual_query = actual_query.filter(
            RevenueActual.revenue_category_id == cat.id,
            extract('year', RevenueActual.date) == year
        )
        actual = float(actual_query.scalar() or 0)
        
        planned = float(cat.planned or 0)
        diff = actual - planned
        exec_pct = (actual / planned * 100) if planned > 0 else 0
        
        revenue_cat_data.append({
            "Категория": cat.name,
            "План": planned,
            "Факт": actual,
            "Отклонение": diff,
            "Исполнение %": exec_pct
        })
    df_revenue_cat = pd.DataFrame(revenue_cat_data)
    
    # === SHEET 4: EXPENSES BY CATEGORY ===
    expenses_by_cat = db.query(
        BudgetCategory.id,
        BudgetCategory.name,
        func.sum(BudgetPlanDetail.planned_amount).label('planned')
    ).join(
        BudgetPlanDetail, BudgetCategory.id == BudgetPlanDetail.category_id
    ).join(
        BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
    ).join(
        BudgetPlan, BudgetVersion.budget_plan_id == BudgetPlan.id
    )
    
    if target_department_id:
        expenses_by_cat = expenses_by_cat.filter(
            BudgetPlan.department_id == target_department_id
        )
    
    expenses_by_cat = expenses_by_cat.filter(
        BudgetPlan.year == year
    ).group_by(BudgetCategory.id, BudgetCategory.name).all()
    
    expenses_cat_data = []
    for cat in expenses_by_cat:
        # Get actual for this category
        actual_query = db.query(func.sum(Expense.amount))
        if target_department_id:
            actual_query = actual_query.filter(
                Expense.department_id == target_department_id
            )
        actual_query = actual_query.filter(
            Expense.category_id == cat.id,
            extract('year', Expense.expense_date) == year,
            Expense.status.in_([ExpenseStatusEnum.APPROVED, ExpenseStatusEnum.PAID])
        )
        actual = float(actual_query.scalar() or 0)
        
        planned = float(cat.planned or 0)
        diff = actual - planned
        exec_pct = (actual / planned * 100) if planned > 0 else 0
        
        expenses_cat_data.append({
            "Категория": cat.name,
            "План": planned,
            "Факт": actual,
            "Отклонение": diff,
            "Исполнение %": exec_pct
        })
    
    # Add payroll as a category
    expenses_cat_data.append({
        "Категория": "ФОТ (Фонд оплаты труда)",
        "План": payroll_planned,
        "Факт": payroll_actual,
        "Отклонение": payroll_actual - payroll_planned,
        "Исполнение %": (payroll_actual / payroll_planned * 100) if payroll_planned > 0 else 0
    })
    df_expenses_cat = pd.DataFrame(expenses_cat_data)
    
    # === CREATE EXCEL FILE ===
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Сводка')
        df_monthly.to_excel(writer, index=False, sheet_name='По месяцам')
        df_revenue_cat.to_excel(writer, index=False, sheet_name='Доходы по категориям')
        df_expenses_cat.to_excel(writer, index=False, sheet_name='Расходы по категориям')
    
    output.seek(0)
    
    filename = f"BDR_{year}"
    if department_name:
        filename += f"_{department_name}"
    filename += ".xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=encode_filename_header(filename)
    )


@router.get("/customer-metrics-analytics/export")
def export_customer_metrics_analytics(
    year: int = Query(..., description="Year for customer metrics analytics"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Customer Metrics Analytics to Excel
    
    Creates Excel file with 3 sheets:
    - Summary: Overall customer metrics
    - Monthly: Monthly breakdown
    - Streams: Breakdown by revenue streams
    """
    # Multi-tenancy: enforce department access
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if department_id is None:
            target_department_id = current_user.department_id
    
    # Get department name
    department_name = None
    if target_department_id:
        dept = db.query(Department).filter(Department.id == target_department_id).first()
        if dept:
            department_name = dept.name
    
    # === GET CURRENT YEAR DATA ===
    query = db.query(CustomerMetrics)
    if target_department_id:
        query = query.filter(CustomerMetrics.department_id == target_department_id)
    query = query.filter(CustomerMetrics.year == year)
    
    metrics = query.all()
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No customer metrics found for year {year}"
        )
    
    # Aggregate totals
    total_customer_base = sum(m.total_customer_base or 0 for m in metrics)
    active_customer_base = sum(m.active_customer_base or 0 for m in metrics)
    coverage_rate = (active_customer_base / total_customer_base * 100) if total_customer_base > 0 else 0
    
    regular_clinics = sum(m.regular_clinics or 0 for m in metrics)
    network_clinics = sum(m.network_clinics or 0 for m in metrics)
    new_clinics = sum(m.new_clinics or 0 for m in metrics)
    
    # Weighted average for order values
    total_weight = sum(m.active_customer_base or 0 for m in metrics)
    avg_order_value = sum((m.avg_order_value or 0) * (m.active_customer_base or 0) for m in metrics) / total_weight if total_weight > 0 else 0
    avg_order_value_regular = sum((m.avg_order_value_regular or 0) * (m.regular_clinics or 0) for m in metrics) / regular_clinics if regular_clinics > 0 else 0
    avg_order_value_network = sum((m.avg_order_value_network or 0) * (m.network_clinics or 0) for m in metrics) / network_clinics if network_clinics > 0 else 0
    avg_order_value_new = sum((m.avg_order_value_new or 0) * (m.new_clinics or 0) for m in metrics) / new_clinics if new_clinics > 0 else 0
    
    # Get previous year data for growth metrics
    prev_query = db.query(CustomerMetrics)
    if target_department_id:
        prev_query = prev_query.filter(CustomerMetrics.department_id == target_department_id)
    prev_query = prev_query.filter(CustomerMetrics.year == year - 1)
    prev_metrics = prev_query.all()
    
    customer_base_growth = None
    active_base_growth = None
    avg_check_growth = None
    
    if prev_metrics:
        prev_total_base = sum(m.total_customer_base or 0 for m in prev_metrics)
        prev_active_base = sum(m.active_customer_base or 0 for m in prev_metrics)
        prev_weight = sum(m.active_customer_base or 0 for m in prev_metrics)
        prev_avg_order = sum((m.avg_order_value or 0) * (m.active_customer_base or 0) for m in prev_metrics) / prev_weight if prev_weight > 0 else 0
        
        customer_base_growth = ((total_customer_base - prev_total_base) / prev_total_base * 100) if prev_total_base > 0 else 0
        active_base_growth = ((active_customer_base - prev_active_base) / prev_active_base * 100) if prev_active_base > 0 else 0
        avg_check_growth = ((avg_order_value - prev_avg_order) / prev_avg_order * 100) if prev_avg_order > 0 else 0
    
    # === SHEET 1: SUMMARY ===
    summary_data = [
        {"Показатель": "Год", "Значение": year},
        {"Показатель": "Отдел", "Значение": department_name or "Все отделы"},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "КЛИЕНТСКАЯ БАЗА", "Значение": ""},
        {"Показатель": "ОКБ (Общая клиентская база)", "Значение": total_customer_base},
        {"Показатель": "АКБ (Активная клиентская база)", "Значение": active_customer_base},
        {"Показатель": "Покрытие (АКБ/ОКБ) %", "Значение": coverage_rate},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "СЕГМЕНТЫ", "Значение": ""},
        {"Показатель": "Регулярные клиники", "Значение": regular_clinics},
        {"Показатель": "Сетевые клиники", "Значение": network_clinics},
        {"Показатель": "Новые клиники", "Значение": new_clinics},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "СРЕДНИЙ ЧЕК", "Значение": ""},
        {"Показатель": "Средний чек (общий)", "Значение": avg_order_value},
        {"Показатель": "Средний чек (регулярные)", "Значение": avg_order_value_regular},
        {"Показатель": "Средний чек (сетевые)", "Значение": avg_order_value_network},
        {"Показатель": "Средний чек (новые)", "Значение": avg_order_value_new},
    ]
    
    if customer_base_growth is not None:
        summary_data.extend([
            {"Показатель": "", "Значение": ""},
            {"Показатель": "ДИНАМИКА (год к году)", "Значение": ""},
            {"Показатель": "Рост ОКБ %", "Значение": customer_base_growth},
            {"Показатель": "Рост АКБ %", "Значение": active_base_growth},
            {"Показатель": "Рост среднего чека %", "Значение": avg_check_growth},
        ])
    
    df_summary = pd.DataFrame(summary_data)
    
    # === SHEET 2: MONTHLY BREAKDOWN ===
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    monthly_data = []
    for month in range(1, 13):
        month_query = db.query(CustomerMetrics)
        if target_department_id:
            month_query = month_query.filter(CustomerMetrics.department_id == target_department_id)
        month_query = month_query.filter(
            CustomerMetrics.year == year,
            CustomerMetrics.month == month
        )
        month_metrics = month_query.all()
        
        if month_metrics:
            month_total_base = sum(m.total_customer_base or 0 for m in month_metrics)
            month_active_base = sum(m.active_customer_base or 0 for m in month_metrics)
            month_coverage = (month_active_base / month_total_base * 100) if month_total_base > 0 else 0
            
            month_weight = sum(m.active_customer_base or 0 for m in month_metrics)
            month_avg_order = sum((m.avg_order_value or 0) * (m.active_customer_base or 0) for m in month_metrics) / month_weight if month_weight > 0 else 0
            
            month_regular = sum(m.regular_clinics or 0 for m in month_metrics)
            month_network = sum(m.network_clinics or 0 for m in month_metrics)
            month_new = sum(m.new_clinics or 0 for m in month_metrics)
            
            monthly_data.append({
                "Месяц": month_names[month - 1],
                "ОКБ": month_total_base,
                "АКБ": month_active_base,
                "Покрытие %": month_coverage,
                "Средний чек": month_avg_order,
                "Регулярные": month_regular,
                "Сетевые": month_network,
                "Новые": month_new,
            })
    
    df_monthly = pd.DataFrame(monthly_data)
    
    # === SHEET 3: BY REVENUE STREAMS ===
    stream_data = []
    streams = db.query(RevenueStream).filter(RevenueStream.is_active == True).all()
    
    for stream in streams:
        stream_query = db.query(CustomerMetrics)
        if target_department_id:
            stream_query = stream_query.filter(CustomerMetrics.department_id == target_department_id)
        stream_query = stream_query.filter(
            CustomerMetrics.year == year,
            CustomerMetrics.revenue_stream_id == stream.id
        )
        stream_metrics = stream_query.all()
        
        if stream_metrics:
            stream_total_base = sum(m.total_customer_base or 0 for m in stream_metrics)
            stream_active_base = sum(m.active_customer_base or 0 for m in stream_metrics)
            stream_coverage = (stream_active_base / stream_total_base * 100) if stream_total_base > 0 else 0
            
            stream_weight = sum(m.active_customer_base or 0 for m in stream_metrics)
            stream_avg_order = sum((m.avg_order_value or 0) * (m.active_customer_base or 0) for m in stream_metrics) / stream_weight if stream_weight > 0 else 0
            
            stream_regular = sum(m.regular_clinics or 0 for m in stream_metrics)
            stream_network = sum(m.network_clinics or 0 for m in stream_metrics)
            stream_new = sum(m.new_clinics or 0 for m in stream_metrics)
            
            stream_data.append({
                "Поток доходов": stream.name,
                "Тип": stream.stream_type,
                "ОКБ": stream_total_base,
                "АКБ": stream_active_base,
                "Покрытие %": stream_coverage,
                "Средний чек": stream_avg_order,
                "Регулярные": stream_regular,
                "Сетевые": stream_network,
                "Новые": stream_new,
            })
    
    df_streams = pd.DataFrame(stream_data)
    
    # === CREATE EXCEL FILE ===
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Сводка')
        df_monthly.to_excel(writer, index=False, sheet_name='По месяцам')
        if not df_streams.empty:
            df_streams.to_excel(writer, index=False, sheet_name='По потокам доходов')
    
    output.seek(0)
    
    filename = f"Customer_Metrics_{year}"
    if department_name:
        filename += f"_{department_name}"
    filename += ".xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=encode_filename_header(filename)
    )


@router.get("/revenue-analytics/export")
def export_revenue_analytics(
    year: int = Query(..., description="Year for revenue analytics"),
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export Revenue Analytics to Excel
    
    Creates Excel file with 4 sheets:
    - Summary: Overall revenue metrics
    - Monthly: Monthly breakdown
    - Streams: Regional breakdown by revenue streams
    - Categories: Product mix by revenue categories
    """
    # Multi-tenancy: enforce department access
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if department_id is None:
            target_department_id = current_user.department_id
    
    # Get department name
    department_name = None
    if target_department_id:
        dept = db.query(Department).filter(Department.id == target_department_id).first()
        if dept:
            department_name = dept.name
    
    # === GET REVENUE DATA ===
    # Planned revenue
    planned_query = db.query(func.sum(RevenuePlanDetail.planned_amount))
    if target_department_id:
        planned_query = planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        ).filter(RevenuePlan.department_id == target_department_id)
    else:
        planned_query = planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        )
    planned_query = planned_query.filter(RevenuePlan.year == year)
    total_planned = float(planned_query.scalar() or 0)
    
    # Actual revenue
    actual_query = db.query(func.sum(RevenueActual.amount))
    if target_department_id:
        actual_query = actual_query.filter(RevenueActual.department_id == target_department_id)
    actual_query = actual_query.filter(extract('year', RevenueActual.date) == year)
    total_actual = float(actual_query.scalar() or 0)
    
    # Calculate totals
    total_variance = total_actual - total_planned
    total_variance_percent = (total_variance / total_planned * 100) if total_planned > 0 else 0
    total_execution_percent = (total_actual / total_planned * 100) if total_planned > 0 else 0
    
    # Get previous year data for growth
    prev_planned_query = db.query(func.sum(RevenuePlanDetail.planned_amount))
    if target_department_id:
        prev_planned_query = prev_planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        ).filter(RevenuePlan.department_id == target_department_id)
    else:
        prev_planned_query = prev_planned_query.join(
            RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
        )
    prev_planned_query = prev_planned_query.filter(RevenuePlan.year == year - 1)
    prev_planned = float(prev_planned_query.scalar() or 0)
    
    prev_actual_query = db.query(func.sum(RevenueActual.amount))
    if target_department_id:
        prev_actual_query = prev_actual_query.filter(RevenueActual.department_id == target_department_id)
    prev_actual_query = prev_actual_query.filter(extract('year', RevenueActual.date) == year - 1)
    prev_actual = float(prev_actual_query.scalar() or 0)
    
    planned_growth = ((total_planned - prev_planned) / prev_planned * 100) if prev_planned > 0 else None
    actual_growth = ((total_actual - prev_actual) / prev_actual * 100) if prev_actual > 0 else None
    
    # === SHEET 1: SUMMARY ===
    summary_data = [
        {"Показатель": "Год", "Значение": year},
        {"Показатель": "Отдел", "Значение": department_name or "Все отделы"},
        {"Показатель": "", "Значение": ""},
        {"Показатель": "ДОХОДЫ", "Значение": ""},
        {"Показатель": "План", "Значение": total_planned},
        {"Показатель": "Факт", "Значение": total_actual},
        {"Показатель": "Отклонение", "Значение": total_variance},
        {"Показатель": "Отклонение %", "Значение": total_variance_percent},
        {"Показатель": "Исполнение %", "Значение": total_execution_percent},
    ]
    
    if planned_growth is not None:
        summary_data.extend([
            {"Показатель": "", "Значение": ""},
            {"Показатель": "ДИНАМИКА (год к году)", "Значение": ""},
            {"Показатель": "Рост плана %", "Значение": planned_growth},
            {"Показатель": "Рост факта %", "Значение": actual_growth},
        ])
    
    df_summary = pd.DataFrame(summary_data)
    
    # === SHEET 2: MONTHLY BREAKDOWN ===
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    monthly_data = []
    for month in range(1, 13):
        # Planned monthly
        planned_month = db.query(func.sum(RevenuePlanDetail.planned_amount))
        if target_department_id:
            planned_month = planned_month.join(
                RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
            ).filter(RevenuePlan.department_id == target_department_id)
        else:
            planned_month = planned_month.join(
                RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
            )
        planned_month = planned_month.filter(
            RevenuePlan.year == year,
            RevenuePlanDetail.month == month
        ).scalar() or 0
        
        # Actual monthly
        actual_month = db.query(func.sum(RevenueActual.amount))
        if target_department_id:
            actual_month = actual_month.filter(RevenueActual.department_id == target_department_id)
        actual_month = actual_month.filter(
            extract('year', RevenueActual.date) == year,
            extract('month', RevenueActual.date) == month
        ).scalar() or 0
        
        planned_month = float(planned_month)
        actual_month = float(actual_month)
        variance = actual_month - planned_month
        variance_pct = (variance / planned_month * 100) if planned_month > 0 else 0
        exec_pct = (actual_month / planned_month * 100) if planned_month > 0 else 0
        
        monthly_data.append({
            "Месяц": month_names[month - 1],
            "План": planned_month,
            "Факт": actual_month,
            "Отклонение": variance,
            "Отклонение %": variance_pct,
            "Исполнение %": exec_pct,
        })
    
    df_monthly = pd.DataFrame(monthly_data)
    
    # === SHEET 3: BY REVENUE STREAMS (REGIONAL) ===
    streams = db.query(
        RevenueStream.id,
        RevenueStream.name,
        RevenueStream.stream_type,
        func.sum(RevenuePlanDetail.planned_amount).label('planned')
    ).join(
        RevenuePlanDetail, RevenueStream.id == RevenuePlanDetail.revenue_stream_id
    ).join(
        RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
    )
    
    if target_department_id:
        streams = streams.filter(RevenuePlan.department_id == target_department_id)
    
    streams = streams.filter(
        RevenuePlan.year == year
    ).group_by(RevenueStream.id, RevenueStream.name, RevenueStream.stream_type).all()
    
    stream_data = []
    for stream in streams:
        # Get actual for this stream
        actual_query = db.query(func.sum(RevenueActual.amount))
        if target_department_id:
            actual_query = actual_query.filter(RevenueActual.department_id == target_department_id)
        actual_query = actual_query.filter(
            RevenueActual.revenue_stream_id == stream.id,
            extract('year', RevenueActual.date) == year
        )
        actual = float(actual_query.scalar() or 0)
        
        planned = float(stream.planned or 0)
        variance = actual - planned
        variance_pct = (variance / planned * 100) if planned > 0 else 0
        exec_pct = (actual / planned * 100) if planned > 0 else 0
        share = (actual / total_actual * 100) if total_actual > 0 else 0
        
        stream_data.append({
            "Поток доходов": stream.name,
            "Тип": stream.stream_type,
            "План": planned,
            "Факт": actual,
            "Отклонение": variance,
            "Отклонение %": variance_pct,
            "Исполнение %": exec_pct,
            "Доля от общего дохода %": share,
        })
    
    df_streams = pd.DataFrame(stream_data)
    
    # === SHEET 4: BY REVENUE CATEGORIES (PRODUCT MIX) ===
    categories = db.query(
        RevenueCategory.id,
        RevenueCategory.name,
        RevenueCategory.category_type,
        func.sum(RevenuePlanDetail.planned_amount).label('planned')
    ).join(
        RevenuePlanDetail, RevenueCategory.id == RevenuePlanDetail.revenue_category_id
    ).join(
        RevenuePlan, RevenuePlanDetail.revenue_plan_id == RevenuePlan.id
    )
    
    if target_department_id:
        categories = categories.filter(RevenuePlan.department_id == target_department_id)
    
    categories = categories.filter(
        RevenuePlan.year == year
    ).group_by(RevenueCategory.id, RevenueCategory.name, RevenueCategory.category_type).all()
    
    category_data = []
    for category in categories:
        # Get actual for this category
        actual_query = db.query(func.sum(RevenueActual.amount))
        if target_department_id:
            actual_query = actual_query.filter(RevenueActual.department_id == target_department_id)
        actual_query = actual_query.filter(
            RevenueActual.revenue_category_id == category.id,
            extract('year', RevenueActual.date) == year
        )
        actual = float(actual_query.scalar() or 0)
        
        planned = float(category.planned or 0)
        variance = actual - planned
        variance_pct = (variance / planned * 100) if planned > 0 else 0
        exec_pct = (actual / planned * 100) if planned > 0 else 0
        share = (actual / total_actual * 100) if total_actual > 0 else 0
        
        category_data.append({
            "Категория дохода": category.name,
            "Тип": category.category_type,
            "План": planned,
            "Факт": actual,
            "Отклонение": variance,
            "Отклонение %": variance_pct,
            "Исполнение %": exec_pct,
            "Доля от общего дохода %": share,
        })
    
    df_categories = pd.DataFrame(category_data)
    
    # === CREATE EXCEL FILE ===
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Сводка')
        df_monthly.to_excel(writer, index=False, sheet_name='По месяцам')
        if not df_streams.empty:
            df_streams.to_excel(writer, index=False, sheet_name='Региональная разбивка')
        if not df_categories.empty:
            df_categories.to_excel(writer, index=False, sheet_name='Продуктовый микс')
    
    output.seek(0)
    
    filename = f"Revenue_Analytics_{year}"
    if department_name:
        filename += f"_{department_name}"
    filename += ".xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=encode_filename_header(filename)
    )
