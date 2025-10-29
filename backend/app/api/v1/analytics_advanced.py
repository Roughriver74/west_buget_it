"""
Advanced Analytics API endpoints
Provides deep analytical insights into expenses, contractors, departments, and efficiency
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, and_, distinct
from datetime import datetime, date, timedelta
from decimal import Decimal
from calendar import month_name as calendar_month_names

from app.db.session import get_db
from app.db.models import (
    Expense, BudgetCategory, Contractor, Department, Employee,
    BudgetPlan, BudgetVersion, User, UserRoleEnum, ExpenseStatusEnum,
    ExpenseTypeEnum
)
from app.utils.auth import get_current_active_user
from app.schemas.analytics_advanced import (
    ExpenseTrendsResponse, ExpenseTrendPoint, ExpenseTrendSummary,
    ContractorAnalysisResponse, ContractorStats,
    DepartmentComparisonResponse, DepartmentMetrics,
    SeasonalPatternsResponse, SeasonalPattern,
    CostEfficiencyResponse, CostEfficiencyMetrics, CategoryEfficiency
)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_department_access(user: User, department_id: Optional[int]) -> bool:
    """Check if user has access to specified department"""
    if user.role == UserRoleEnum.ADMIN:
        return True
    if user.role == UserRoleEnum.MANAGER:
        if not user.department_id:
            return False
        return department_id is None or department_id == user.department_id
    if user.role == UserRoleEnum.USER:
        if not user.department_id:
            return False
        return department_id is None or department_id == user.department_id
    return False


@router.get("/expense-trends", response_model=ExpenseTrendsResponse)
def get_expense_trends(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    period: str = Query("month", regex="^(month|quarter)$", description="Aggregation period"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze expense trends over time by categories

    - Shows growth rates and patterns
    - Identifies top growing and declining categories
    - Provides volatility metrics
    """
    # Check access
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
        department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
        if department_id and department_id != current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        department_id = current_user.department_id

    # Base query
    query = db.query(
        extract('year', Expense.expense_date).label('year'),
        extract('month', Expense.expense_date).label('month'),
        BudgetCategory.id.label('category_id'),
        BudgetCategory.name.label('category_name'),
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('expense_count'),
        func.avg(Expense.amount).label('average_amount')
    ).join(
        BudgetCategory, Expense.category_id == BudgetCategory.id
    ).filter(
        and_(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
    )

    # Apply filters
    if department_id:
        query = query.filter(Expense.department_id == department_id)
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    # Group by period
    if period == "month":
        query = query.group_by('year', 'month', BudgetCategory.id, BudgetCategory.name)
        query = query.order_by('year', 'month', BudgetCategory.id)
    else:  # quarter
        query = query.group_by('year', 'month', BudgetCategory.id, BudgetCategory.name)

    results = query.all()

    # Build trends with growth rates
    trends = []
    prev_amounts = {}  # Track previous period for growth calculation

    for r in results:
        period_key = f"{int(r.year)}-{int(r.month):02d}" if period == "month" else f"{int(r.year)}-Q{(int(r.month)-1)//3 + 1}"
        cat_key = f"{r.category_id}"

        growth_rate = None
        if cat_key in prev_amounts:
            if prev_amounts[cat_key] > 0:
                growth_rate = ((r.total_amount - prev_amounts[cat_key]) / prev_amounts[cat_key]) * 100

        prev_amounts[cat_key] = r.total_amount

        trends.append(ExpenseTrendPoint(
            period=period_key,
            category_id=r.category_id,
            category_name=r.category_name,
            total_amount=r.total_amount,
            expense_count=r.expense_count,
            average_amount=r.average_amount,
            growth_rate=growth_rate
        ))

    # Calculate summary statistics
    if trends:
        total_amount = sum(t.total_amount for t in trends)
        amounts = [float(t.total_amount) for t in trends]
        avg_per_period = Decimal(str(sum(amounts) / len(amounts)))
        max_amount = Decimal(str(max(amounts)))
        min_amount = Decimal(str(min(amounts)))

        # Calculate volatility (standard deviation)
        mean = sum(amounts) / len(amounts)
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        volatility = Decimal(str(variance ** 0.5))

        summary = ExpenseTrendSummary(
            total_periods=len(set(t.period for t in trends)),
            date_from=start_date,
            date_to=end_date,
            total_amount=total_amount,
            average_per_period=avg_per_period,
            max_period_amount=max_amount,
            min_period_amount=min_amount,
            volatility=volatility
        )
    else:
        summary = ExpenseTrendSummary(
            total_periods=0,
            date_from=start_date,
            date_to=end_date,
            total_amount=Decimal(0),
            average_per_period=Decimal(0),
            max_period_amount=Decimal(0),
            min_period_amount=Decimal(0),
            volatility=Decimal(0)
        )

    # Find top growing and declining categories
    category_growth = {}
    for t in trends:
        if t.growth_rate is not None:
            if t.category_name not in category_growth:
                category_growth[t.category_name] = []
            category_growth[t.category_name].append(float(t.growth_rate))

    avg_growth = {cat: sum(rates)/len(rates) for cat, rates in category_growth.items() if rates}
    top_growing = sorted(avg_growth.items(), key=lambda x: x[1], reverse=True)[:5]
    top_declining = sorted(avg_growth.items(), key=lambda x: x[1])[:5]

    return ExpenseTrendsResponse(
        trends=trends,
        summary=summary,
        top_growing_categories=[{"name": name, "growth_rate": round(rate, 2)} for name, rate in top_growing],
        top_declining_categories=[{"name": name, "growth_rate": round(rate, 2)} for name, rate in top_declining]
    )


@router.get("/contractor-analysis", response_model=ContractorAnalysisResponse)
def get_contractor_analysis(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    min_amount: Optional[Decimal] = Query(None, description="Minimum total amount"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze expenses by contractor

    - Shows top contractors by spending
    - Calculates concentration ratios
    - Identifies new and inactive contractors
    """
    # Check access
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
        department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
        if department_id and department_id != current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        department_id = current_user.department_id

    # Query contractor statistics
    query = db.query(
        Contractor.id.label('contractor_id'),
        Contractor.name.label('contractor_name'),
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('expense_count'),
        func.avg(Expense.amount).label('average_expense'),
        func.min(Expense.expense_date).label('first_expense_date'),
        func.max(Expense.expense_date).label('last_expense_date'),
        func.count(distinct(func.concat(
            extract('year', Expense.expense_date),
            '-',
            extract('month', Expense.expense_date)
        ))).label('active_months'),
        func.count(distinct(Expense.category_id)).label('categories_count')
    ).join(
        Expense, Contractor.id == Expense.contractor_id
    ).filter(
        and_(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
    )

    if department_id:
        query = query.filter(Expense.department_id == department_id)

    query = query.group_by(Contractor.id, Contractor.name)
    query = query.order_by(func.sum(Expense.amount).desc())

    results = query.all()

    # Calculate total for share calculation
    total_amount = sum(r.total_amount for r in results) if results else Decimal(0)

    # Get top category for each contractor
    contractors = []
    for r in results:
        if min_amount and r.total_amount < min_amount:
            continue

        # Get top category for this contractor
        top_cat = db.query(
            BudgetCategory.name
        ).join(
            Expense, BudgetCategory.id == Expense.category_id
        ).filter(
            and_(
                Expense.contractor_id == r.contractor_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        ).group_by(
            BudgetCategory.name
        ).order_by(
            func.sum(Expense.amount).desc()
        ).first()

        share = (r.total_amount / total_amount * 100) if total_amount > 0 else Decimal(0)

        contractors.append(ContractorStats(
            contractor_id=r.contractor_id,
            contractor_name=r.contractor_name,
            total_amount=r.total_amount,
            expense_count=r.expense_count,
            average_expense=r.average_expense,
            first_expense_date=r.first_expense_date,
            last_expense_date=r.last_expense_date,
            active_months=r.active_months,
            categories_count=r.categories_count,
            top_category=top_cat[0] if top_cat else "N/A",
            share_of_total=share
        ))

    # Calculate concentration ratio (top 10 contractors)
    top_10_amount = sum(c.total_amount for c in contractors[:10])
    concentration_ratio = (top_10_amount / total_amount * 100) if total_amount > 0 else Decimal(0)

    # Count new contractors (first expense in period)
    new_contractors = sum(1 for c in contractors if c.first_expense_date >= start_date)

    # Count inactive contractors (had expenses before but not in period)
    all_contractors = db.query(func.count(distinct(Expense.contractor_id))).filter(
        Expense.expense_date < start_date
    )
    if department_id:
        all_contractors = all_contractors.filter(Expense.department_id == department_id)
    prev_count = all_contractors.scalar() or 0
    inactive_count = prev_count - len(contractors) + new_contractors

    return ContractorAnalysisResponse(
        contractors=contractors,
        total_contractors=len(contractors),
        total_amount=total_amount,
        concentration_ratio=concentration_ratio,
        average_contractor_amount=total_amount / len(contractors) if contractors else Decimal(0),
        new_contractors_count=new_contractors,
        inactive_contractors_count=max(0, inactive_count)
    )


@router.get("/department-comparison", response_model=DepartmentComparisonResponse)
def get_department_comparison(
    year: int = Query(..., description="Year for analysis"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Optional month filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Compare departments across key metrics

    - Budget vs actual execution
    - Cost per employee
    - CAPEX/OPEX ratios
    - Identifies best and worst performing departments

    Only ADMIN can see all departments, MANAGER/USER see only own department
    """
    # Query departments
    dept_query = db.query(Department)

    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
        dept_query = dept_query.filter(Department.id == current_user.department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
        dept_query = dept_query.filter(Department.id == current_user.department_id)

    departments = dept_query.all()

    metrics_list = []
    total_budget = Decimal(0)
    total_actual = Decimal(0)

    for dept in departments:
        # Get budget (from baseline version)
        budget_query = db.query(
            func.sum(BudgetPlanDetail.amount).label('total_budget')
        ).join(
            BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
        ).filter(
            and_(
                BudgetVersion.department_id == dept.id,
                BudgetVersion.year == year,
                BudgetVersion.is_baseline == True
            )
        )

        if month:
            budget_query = budget_query.filter(BudgetPlanDetail.month == month)

        budget_result = budget_query.first()
        dept_budget = budget_result.total_budget if budget_result and budget_result.total_budget else Decimal(0)

        # Get actual expenses
        actual_query = db.query(
            func.sum(Expense.amount).label('total_actual'),
            func.count(Expense.id).label('expense_count'),
            func.avg(Expense.amount).label('average_expense')
        ).filter(
            and_(
                Expense.department_id == dept.id,
                extract('year', Expense.expense_date) == year
            )
        )

        if month:
            actual_query = actual_query.filter(extract('month', Expense.expense_date) == month)

        actual_result = actual_query.first()
        dept_actual = actual_result.total_actual if actual_result and actual_result.total_actual else Decimal(0)
        expense_count = actual_result.expense_count if actual_result else 0
        average_expense = actual_result.average_expense if actual_result and actual_result.average_expense else Decimal(0)

        # Calculate CAPEX/OPEX
        capex = db.query(func.sum(Expense.amount)).join(
            BudgetCategory, Expense.category_id == BudgetCategory.id
        ).filter(
            and_(
                Expense.department_id == dept.id,
                extract('year', Expense.expense_date) == year,
                BudgetCategory.type == ExpenseTypeEnum.CAPEX
            )
        ).scalar() or Decimal(0)

        opex = dept_actual - capex

        # Get employee count
        employee_count = db.query(func.count(Employee.id)).filter(
            Employee.department_id == dept.id
        ).scalar() or 0

        # Get top category
        top_cat = db.query(
            BudgetCategory.name,
            func.sum(Expense.amount).label('cat_total')
        ).join(
            Expense, BudgetCategory.id == Expense.category_id
        ).filter(
            and_(
                Expense.department_id == dept.id,
                extract('year', Expense.expense_date) == year
            )
        ).group_by(BudgetCategory.name).order_by(func.sum(Expense.amount).desc()).first()

        # Calculate metrics
        execution_rate = (dept_actual / dept_budget * 100) if dept_budget > 0 else Decimal(0)
        variance = dept_actual - dept_budget
        variance_percent = (variance / dept_budget * 100) if dept_budget > 0 else Decimal(0)
        capex_ratio = (capex / dept_actual * 100) if dept_actual > 0 else Decimal(0)
        cost_per_employee = (dept_actual / employee_count) if employee_count > 0 else Decimal(0)

        metrics_list.append(DepartmentMetrics(
            department_id=dept.id,
            department_name=dept.name,
            total_budget=dept_budget,
            total_actual=dept_actual,
            execution_rate=execution_rate,
            variance=variance,
            variance_percent=variance_percent,
            capex_amount=capex,
            opex_amount=opex,
            capex_ratio=capex_ratio,
            expense_count=expense_count,
            average_expense=average_expense,
            employee_count=employee_count,
            cost_per_employee=cost_per_employee,
            top_category=top_cat[0] if top_cat else "N/A",
            top_category_amount=top_cat[1] if top_cat else Decimal(0)
        ))

        total_budget += dept_budget
        total_actual += dept_actual

    # Find best/worst performers
    if metrics_list:
        # Best: closest to budget (smallest abs variance %)
        best_dept = min(metrics_list, key=lambda x: abs(float(x.variance_percent)))
        # Highest variance
        highest_var = max(metrics_list, key=lambda x: abs(float(x.variance)))
        # Most efficient: lowest cost per employee (if has employees)
        efficient_depts = [m for m in metrics_list if m.employee_count > 0]
        most_efficient = min(efficient_depts, key=lambda x: float(x.cost_per_employee)) if efficient_depts else None
    else:
        best_dept = None
        highest_var = None
        most_efficient = None

    overall_execution = (total_actual / total_budget * 100) if total_budget > 0 else Decimal(0)

    return DepartmentComparisonResponse(
        departments=metrics_list,
        total_departments=len(metrics_list),
        total_budget=total_budget,
        total_actual=total_actual,
        overall_execution_rate=overall_execution,
        best_performing_dept=best_dept.department_name if best_dept else None,
        highest_variance_dept=highest_var.department_name if highest_var else None,
        most_efficient_dept=most_efficient.department_name if most_efficient else None
    )


@router.get("/seasonal-patterns", response_model=SeasonalPatternsResponse)
def get_seasonal_patterns(
    start_year: int = Query(..., description="Start year for analysis (need multiple years)"),
    end_year: int = Query(..., description="End year for analysis"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze seasonal spending patterns

    - Shows average spending by month across multiple years
    - Calculates seasonality index
    - Identifies peak and lowest spending months
    - Provides budget distribution recommendations
    """
    # Check access
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
        department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
        if department_id and department_id != current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        department_id = current_user.department_id

    # Query monthly aggregates
    query = db.query(
        extract('year', Expense.expense_date).label('year'),
        extract('month', Expense.expense_date).label('month'),
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('expense_count')
    ).filter(
        and_(
            extract('year', Expense.expense_date) >= start_year,
            extract('year', Expense.expense_date) <= end_year
        )
    )

    if department_id:
        query = query.filter(Expense.department_id == department_id)

    query = query.group_by('year', 'month').order_by('month')
    results = query.all()

    # Aggregate by month across all years
    monthly_data = {}
    for r in results:
        month_num = int(r.month)
        if month_num not in monthly_data:
            monthly_data[month_num] = {'amounts': [], 'counts': []}
        monthly_data[month_num]['amounts'].append(float(r.total_amount))
        monthly_data[month_num]['counts'].append(r.expense_count)

    # Calculate yearly average for seasonality index
    yearly_avg = sum(sum(data['amounts']) for data in monthly_data.values()) / (end_year - start_year + 1) if monthly_data else 0
    monthly_avg_for_index = yearly_avg / 12 if yearly_avg > 0 else 0

    # Build patterns
    patterns = []
    for month_num in range(1, 13):
        if month_num in monthly_data:
            amounts = monthly_data[month_num]['amounts']
            counts = monthly_data[month_num]['counts']

            avg_amount = Decimal(str(sum(amounts) / len(amounts)))
            sorted_amounts = sorted(amounts)
            median_amount = Decimal(str(sorted_amounts[len(sorted_amounts) // 2]))
            min_amount = Decimal(str(min(amounts)))
            max_amount = Decimal(str(max(amounts)))
            avg_count = int(sum(counts) / len(counts))

            # Seasonality index
            seasonality_index = Decimal(str((sum(amounts) / len(amounts)) / monthly_avg_for_index)) if monthly_avg_for_index > 0 else Decimal(1)

            # YoY growth (if we have at least 2 years)
            yoy_growth = None
            if len(amounts) >= 2:
                yoy_growth = Decimal(str(((amounts[-1] - amounts[0]) / amounts[0] * 100) if amounts[0] > 0 else 0))
        else:
            avg_amount = Decimal(0)
            median_amount = Decimal(0)
            min_amount = Decimal(0)
            max_amount = Decimal(0)
            avg_count = 0
            seasonality_index = Decimal(1)
            yoy_growth = None

        patterns.append(SeasonalPattern(
            month=month_num,
            month_name=calendar_month_names[month_num],
            average_amount=avg_amount,
            median_amount=median_amount,
            min_amount=min_amount,
            max_amount=max_amount,
            expense_count_average=avg_count,
            seasonality_index=seasonality_index,
            year_over_year_growth=yoy_growth
        ))

    # Find peak and lowest months
    if patterns:
        peak_month = max(patterns, key=lambda x: float(x.average_amount))
        lowest_month = min(patterns, key=lambda x: float(x.average_amount) if x.average_amount > 0 else float('inf'))
    else:
        peak_month = None
        lowest_month = None

    # Calculate seasonality strength (coefficient of variation)
    amounts_list = [float(p.average_amount) for p in patterns if p.average_amount > 0]
    if amounts_list:
        mean = sum(amounts_list) / len(amounts_list)
        variance = sum((x - mean) ** 2 for x in amounts_list) / len(amounts_list)
        std_dev = variance ** 0.5
        cv = (std_dev / mean * 100) if mean > 0 else 0
        seasonality_strength = Decimal(str(cv))
    else:
        seasonality_strength = Decimal(0)

    # Predictability score (inverse of CV, normalized to 0-100)
    predictability_score = max(Decimal(0), Decimal(100) - seasonality_strength)

    # Recommended budget distribution
    total_seasonal = sum(float(p.seasonality_index) for p in patterns)
    recommended_distribution = [
        {
            "month": p.month_name,
            "recommended_percent": round(float(p.seasonality_index) / total_seasonal * 100, 2) if total_seasonal > 0 else 8.33
        }
        for p in patterns
    ]

    return SeasonalPatternsResponse(
        patterns=patterns,
        peak_month=peak_month.month_name if peak_month else "N/A",
        lowest_month=lowest_month.month_name if lowest_month else "N/A",
        seasonality_strength=seasonality_strength,
        predictability_score=predictability_score,
        recommended_budget_distribution=recommended_distribution
    )


@router.get("/cost-efficiency", response_model=CostEfficiencyResponse)
def get_cost_efficiency(
    year: int = Query(..., description="Year for analysis"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Optional month filter"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze cost efficiency and savings

    - Compares budget vs actual by category
    - Calculates savings rates
    - Shows processing times and payment rates
    - Provides actionable recommendations
    """
    # Check access
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no department")
        department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager has no department")
        if department_id and department_id != current_user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        department_id = current_user.department_id

    # Get categories with budget and actual
    categories_query = db.query(
        BudgetCategory.id.label('category_id'),
        BudgetCategory.name.label('category_name')
    )

    if department_id:
        categories_query = categories_query.filter(BudgetCategory.department_id == department_id)

    categories = categories_query.all()

    category_metrics = []
    total_budget = Decimal(0)
    total_actual = Decimal(0)
    total_processing_days = 0
    total_on_time = 0
    total_expenses = 0

    for cat in categories:
        # Get budget from baseline version
        budget_query = db.query(
            func.sum(BudgetPlanDetail.amount).label('budget')
        ).join(
            BudgetVersion, BudgetPlanDetail.version_id == BudgetVersion.id
        ).filter(
            and_(
                BudgetVersion.year == year,
                BudgetVersion.is_baseline == True,
                BudgetPlanDetail.category_id == cat.category_id
            )
        )

        if department_id:
            budget_query = budget_query.filter(BudgetVersion.department_id == department_id)
        if month:
            budget_query = budget_query.filter(BudgetPlanDetail.month == month)

        budget_result = budget_query.first()
        cat_budget = budget_result.budget if budget_result and budget_result.budget else Decimal(0)

        # Get actual expenses with timing metrics
        actual_query = db.query(
            func.sum(Expense.amount).label('actual'),
            func.count(Expense.id).label('expense_count'),
            func.avg(func.extract('day', Expense.updated_at - Expense.created_at)).label('avg_processing_days'),
            func.sum(case((Expense.status == ExpenseStatusEnum.PAID, 1), else_=0)).label('paid_count')
        ).filter(
            and_(
                Expense.category_id == cat.category_id,
                extract('year', Expense.expense_date) == year
            )
        )

        if department_id:
            actual_query = actual_query.filter(Expense.department_id == department_id)
        if month:
            actual_query = actual_query.filter(extract('month', Expense.expense_date) == month)

        actual_result = actual_query.first()
        cat_actual = actual_result.actual if actual_result and actual_result.actual else Decimal(0)
        expense_count = actual_result.expense_count if actual_result else 0
        avg_proc_days = float(actual_result.avg_processing_days or 0)
        paid_count = actual_result.paid_count if actual_result else 0

        if expense_count > 0:
            savings = cat_budget - cat_actual
            savings_rate = (savings / cat_budget * 100) if cat_budget > 0 else Decimal(0)
            on_time_rate = Decimal(paid_count / expense_count * 100)

            # Efficiency score (0-100)
            # Based on: savings rate (50%), on-time payments (30%), low processing time (20%)
            savings_component = max(0, min(50, float(savings_rate) * 0.5))
            payment_component = float(on_time_rate) * 0.3
            processing_component = max(0, 20 - (avg_proc_days / 10 * 20))  # Lower days = higher score
            efficiency_score = Decimal(str(savings_component + payment_component + processing_component))

            category_metrics.append(CategoryEfficiency(
                category_id=cat.category_id,
                category_name=cat.category_name,
                budget_amount=cat_budget,
                actual_amount=cat_actual,
                savings=savings,
                savings_rate=savings_rate,
                expense_count=expense_count,
                average_processing_days=avg_proc_days,
                on_time_payment_rate=on_time_rate,
                efficiency_score=efficiency_score
            ))

            total_budget += cat_budget
            total_actual += cat_actual
            total_processing_days += avg_proc_days * expense_count
            total_on_time += paid_count
            total_expenses += expense_count

    # Calculate overall metrics
    total_savings = total_budget - total_actual
    savings_rate = (total_savings / total_budget * 100) if total_budget > 0 else Decimal(0)
    avg_processing = total_processing_days / total_expenses if total_expenses > 0 else 0
    on_time_rate = Decimal(total_on_time / total_expenses * 100) if total_expenses > 0 else Decimal(0)
    utilization_rate = (total_actual / total_budget * 100) if total_budget > 0 else Decimal(0)

    # Cost control score (how well costs are managed)
    control_score = Decimal(str(
        (float(savings_rate) * 0.4) +  # Savings importance: 40%
        (float(on_time_rate) * 0.3) +   # Payment timeliness: 30%
        (max(0, 30 - (avg_processing / 10 * 30)))  # Processing efficiency: 30%
    ))

    metrics = CostEfficiencyMetrics(
        total_budget=total_budget,
        total_actual=total_actual,
        total_savings=total_savings,
        savings_rate=savings_rate,
        average_processing_days=avg_processing,
        on_time_payment_rate=on_time_rate,
        budget_utilization_rate=utilization_rate,
        cost_control_score=control_score,
        roi_estimate=None  # Would require business metrics
    )

    # Find best and worst performers
    sorted_by_savings = sorted(category_metrics, key=lambda x: float(x.savings_rate), reverse=True)
    best_performing = [c.category_name for c in sorted_by_savings[:5] if c.savings > 0]
    areas_for_improvement = [c.category_name for c in sorted_by_savings[-5:] if c.savings < 0]

    # Efficiency trends (would need historical data - placeholder)
    efficiency_trends = [{"month": i, "score": 75} for i in range(1, 13)]

    # Generate recommendations
    recommendations = []
    if savings_rate < 0:
        recommendations.append(f"Overall budget exceeded by {abs(float(savings_rate)):.1f}% - review high-variance categories")
    if on_time_rate < 80:
        recommendations.append(f"Only {float(on_time_rate):.1f}% of payments are on-time - streamline approval process")
    if avg_processing > 7:
        recommendations.append(f"Average processing time is {avg_processing:.1f} days - consider automation")
    if utilization_rate < 70:
        recommendations.append(f"Budget utilization is only {float(utilization_rate):.1f}% - reallocate unused funds")

    for cat in category_metrics:
        if cat.savings < 0 and abs(float(cat.savings_rate)) > 10:
            recommendations.append(f"{cat.category_name} is {abs(float(cat.savings_rate)):.1f}% over budget - review and adjust")

    return CostEfficiencyResponse(
        metrics=metrics,
        categories=category_metrics,
        best_performing_categories=best_performing,
        areas_for_improvement=areas_for_improvement,
        efficiency_trends=efficiency_trends,
        recommendations=recommendations[:10]  # Limit to top 10
    )
