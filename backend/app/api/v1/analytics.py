from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.db import get_db
from app.db.models import Expense, BudgetCategory, BudgetPlan, BudgetVersion, BudgetPlanDetail, ExpenseStatusEnum, ExpenseTypeEnum, User, PayrollPlan
from app.services.forecast_service import PaymentForecastService, ForecastMethod
from app.utils.auth import get_current_active_user
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
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dashboard data with key metrics

    - USER: Can only see dashboard data for their own department
    - MANAGER/ADMIN: Can see dashboard data for all departments or filter by department
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
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
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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

    return {
        "year": year,
        "months": result
    }


@router.get("/by-category", response_model=CategoryAnalytics)
def get_analytics_by_category(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
