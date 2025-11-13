"""
API endpoints for Founder Dashboard
Provides aggregated metrics and insights across all departments
"""
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from datetime import datetime

from app.db import get_db
from app.db.models import (
    Expense, BudgetCategory, BudgetPlan, Department,
    ExpenseStatusEnum, ExpenseTypeEnum, User, UserRoleEnum,
    PayrollPlan, PayrollActual, Employee, EmployeeKPI, KPIGoal
)
from app.utils.auth import get_current_active_user
from app.schemas.founder_dashboard import (
    FounderDashboardData,
    CompanySummary,
    DepartmentSummary,
    TopCategoryByDepartment,
    ExpenseTrend,
    DepartmentKPI,
    BudgetAlert,
    FounderDepartmentDetails,
)

router = APIRouter()

MONTH_NAMES_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


@router.get("/dashboard", response_model=FounderDashboardData)
def get_founder_dashboard(
    year: Optional[int] = Query(None, description="Year for dashboard data"),
    month: Optional[int] = Query(None, description="Month for dashboard data (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregated dashboard data for Founder role

    Only accessible by users with FOUNDER or ADMIN role
    Shows company-wide metrics and department breakdowns
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.FOUNDER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Founders and Admins can access this dashboard"
        )

    if not year:
        year = datetime.now().year

    # Get all active departments
    departments = db.query(Department).filter(Department.is_active == True).all()

    # Initialize company-wide metrics
    company_metrics = {
        'total_budget_planned': Decimal('0'),
        'total_budget_actual': Decimal('0'),
        'total_expenses_count': 0,
        'total_expenses_pending': 0,
        'total_expenses_paid': Decimal('0'),
        'total_employees': 0,
        'total_payroll_planned': Decimal('0'),
        'total_payroll_actual': Decimal('0'),
        'departments_count': len(departments)
    }

    department_summaries: List[DepartmentSummary] = []

    # Process each department
    for dept in departments:
        dept_id = dept.id

        # Budget metrics
        budget_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.department_id == dept_id
        )
        if month:
            budget_query = budget_query.filter(BudgetPlan.month == month)
        budget_planned = budget_query.scalar() or Decimal('0')

        # Expense metrics
        expense_filter_year = extract('year', Expense.request_date) == year
        expense_base_query = db.query(Expense).filter(
            expense_filter_year,
            Expense.department_id == dept_id
        )
        if month:
            expense_base_query = expense_base_query.filter(
                extract('month', Expense.request_date) == month
            )

        expenses_count = expense_base_query.count()
        expenses_pending = expense_base_query.filter(
            Expense.status == ExpenseStatusEnum.PENDING
        ).count()

        expenses_paid_query = db.query(func.sum(Expense.amount)).filter(
            expense_filter_year,
            Expense.department_id == dept_id,
            Expense.status == ExpenseStatusEnum.PAID
        )
        if month:
            expenses_paid_query = expenses_paid_query.filter(
                extract('month', Expense.request_date) == month
            )
        expenses_paid = expenses_paid_query.scalar() or Decimal('0')

        # Payroll metrics
        payroll_query = db.query(func.sum(PayrollPlan.total_planned)).filter(
            PayrollPlan.year == year,
            PayrollPlan.department_id == dept_id
        )
        if month:
            payroll_query = payroll_query.filter(PayrollPlan.month == month)
        payroll_planned = payroll_query.scalar() or Decimal('0')

        payroll_actual_query = db.query(func.sum(PayrollActual.total_paid)).filter(
            PayrollActual.year == year,
            PayrollActual.department_id == dept_id
        )
        if month:
            payroll_actual_query = payroll_actual_query.filter(PayrollActual.month == month)
        payroll_actual = payroll_actual_query.scalar() or Decimal('0')

        # Employee count
        employees_count = db.query(func.count(Employee.id)).filter(
            Employee.department_id == dept_id,
            Employee.is_active == True
        ).scalar() or 0

        # KPI metrics
        kpi_query = db.query(func.avg(EmployeeKPI.achievement_percent)).filter(
            EmployeeKPI.year == year,
            Employee.department_id == dept_id
        ).join(Employee, EmployeeKPI.employee_id == Employee.id)
        if month:
            kpi_query = kpi_query.filter(EmployeeKPI.month == month)
        avg_kpi_achievement = kpi_query.scalar()

        # Calculate totals
        total_planned = budget_planned + payroll_planned
        total_actual = expenses_paid + payroll_actual
        remaining = total_planned - total_actual
        execution_percent = float((total_actual / total_planned * 100) if total_planned > 0 else 0)

        # Create department summary
        dept_summary = DepartmentSummary(
            department_id=dept_id,
            department_name=dept.name,
            budget_planned=total_planned,
            budget_actual=total_actual,
            budget_remaining=remaining,
            budget_execution_percent=round(execution_percent, 2),
            expenses_count=expenses_count,
            expenses_pending=expenses_pending,
            expenses_paid_amount=expenses_paid,
            employees_count=employees_count,
            payroll_planned=payroll_planned,
            payroll_actual=payroll_actual,
            avg_kpi_achievement=round(avg_kpi_achievement, 2) if avg_kpi_achievement else None
        )
        department_summaries.append(dept_summary)

        # Aggregate company metrics
        company_metrics['total_budget_planned'] += total_planned
        company_metrics['total_budget_actual'] += total_actual
        company_metrics['total_expenses_count'] += expenses_count
        company_metrics['total_expenses_pending'] += expenses_pending
        company_metrics['total_expenses_paid'] += expenses_paid
        company_metrics['total_employees'] += employees_count
        company_metrics['total_payroll_planned'] += payroll_planned
        company_metrics['total_payroll_actual'] += payroll_actual

    # Calculate company execution percent
    total_remaining = company_metrics['total_budget_planned'] - company_metrics['total_budget_actual']
    total_execution_percent = float(
        (company_metrics['total_budget_actual'] / company_metrics['total_budget_planned'] * 100)
        if company_metrics['total_budget_planned'] > 0 else 0
    )

    company_summary = CompanySummary(
        total_budget_planned=company_metrics['total_budget_planned'],
        total_budget_actual=company_metrics['total_budget_actual'],
        total_budget_remaining=total_remaining,
        total_budget_execution_percent=round(total_execution_percent, 2),
        total_expenses_count=company_metrics['total_expenses_count'],
        total_expenses_pending=company_metrics['total_expenses_pending'],
        total_expenses_paid=company_metrics['total_expenses_paid'],
        total_employees=company_metrics['total_employees'],
        total_payroll_planned=company_metrics['total_payroll_planned'],
        total_payroll_actual=company_metrics['total_payroll_actual'],
        departments_count=company_metrics['departments_count']
    )

    # Get top categories by department
    top_categories = _get_top_categories_by_department(db, year, month, departments)

    # Get expense trends
    expense_trends = _get_expense_trends(db, year, departments)

    # Get department KPIs
    department_kpis = _get_department_kpis(db, year, month, departments)

    # Generate alerts
    alerts = _generate_budget_alerts(department_summaries)

    return FounderDashboardData(
        year=year,
        month=month,
        company_summary=company_summary,
        departments=department_summaries,
        top_categories_by_department=top_categories,
        expense_trends=expense_trends,
        department_kpis=department_kpis,
        alerts=alerts
    )


def _get_top_categories_by_department(
    db: Session,
    year: int,
    month: Optional[int],
    departments: List[Department]
) -> List[TopCategoryByDepartment]:
    """Get top spending category for each department"""
    top_categories = []

    for dept in departments:
        query = db.query(
            BudgetCategory.id.label('category_id'),
            BudgetCategory.name.label('category_name'),
            BudgetCategory.type.label('category_type'),
            func.sum(Expense.amount).label('total_amount')
        ).join(
            Expense, BudgetCategory.id == Expense.category_id
        ).filter(
            extract('year', Expense.request_date) == year,
            Expense.department_id == dept.id,
            Expense.status == ExpenseStatusEnum.PAID
        )

        if month:
            query = query.filter(extract('month', Expense.request_date) == month)

        query = query.group_by(
            BudgetCategory.id,
            BudgetCategory.name,
            BudgetCategory.type
        ).order_by(func.sum(Expense.amount).desc()).limit(1)

        result = query.first()

        if result:
            # Get planned budget for this category
            budget_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
                BudgetPlan.year == year,
                BudgetPlan.department_id == dept.id,
                BudgetPlan.category_id == result.category_id
            )
            if month:
                budget_query = budget_query.filter(BudgetPlan.month == month)

            planned = budget_query.scalar() or Decimal('0')
            execution_percent = float((result.total_amount / planned * 100) if planned > 0 else 0)

            top_categories.append(TopCategoryByDepartment(
                department_id=dept.id,
                department_name=dept.name,
                category_id=result.category_id,
                category_name=result.category_name,
                category_type=result.category_type,
                amount=result.total_amount,
                execution_percent=round(execution_percent, 2)
            ))
        else:
            # No expenses for this department
            top_categories.append(TopCategoryByDepartment(
                department_id=dept.id,
                department_name=dept.name,
                category_id=None,
                category_name="Нет данных",
                category_type=None,
                amount=Decimal('0'),
                execution_percent=0.0
            ))

    return top_categories


def _get_expense_trends(
    db: Session,
    year: int,
    departments: List[Department]
) -> List[ExpenseTrend]:
    """Get monthly expense trends across all departments"""
    trends = []

    for month_num in range(1, 13):
        # Planned
        planned_query = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == month_num
        )
        payroll_planned_query = db.query(func.sum(PayrollPlan.total_planned)).filter(
            PayrollPlan.year == year,
            PayrollPlan.month == month_num
        )

        planned = (planned_query.scalar() or Decimal('0')) + (payroll_planned_query.scalar() or Decimal('0'))

        # Actual
        actual_expenses = db.query(func.sum(Expense.amount)).filter(
            extract('year', Expense.request_date) == year,
            extract('month', Expense.request_date) == month_num,
            Expense.status == ExpenseStatusEnum.PAID
        ).scalar() or Decimal('0')

        actual_payroll = db.query(func.sum(PayrollActual.total_paid)).filter(
            PayrollActual.year == year,
            PayrollActual.month == month_num
        ).scalar() or Decimal('0')

        actual = actual_expenses + actual_payroll

        execution_percent = float((actual / planned * 100) if planned > 0 else 0)

        trends.append(ExpenseTrend(
            month=month_num,
            month_name=MONTH_NAMES_RU[month_num - 1],
            planned=planned,
            actual=actual,
            execution_percent=round(execution_percent, 2)
        ))

    return trends


def _get_department_kpis(
    db: Session,
    year: int,
    month: Optional[int],
    departments: List[Department]
) -> List[DepartmentKPI]:
    """Get KPI metrics for each department"""
    dept_kpis = []

    for dept in departments:
        # Get employees in this department
        total_employees = db.query(func.count(Employee.id)).filter(
            Employee.department_id == dept.id,
            Employee.is_active == True
        ).scalar() or 0

        # Get employees with KPI data
        kpi_query = db.query(
            func.count(func.distinct(EmployeeKPI.employee_id)),
            func.avg(EmployeeKPI.achievement_percent)
        ).join(
            Employee, EmployeeKPI.employee_id == Employee.id
        ).filter(
            Employee.department_id == dept.id,
            EmployeeKPI.year == year
        )

        if month:
            kpi_query = kpi_query.filter(EmployeeKPI.month == month)

        result = kpi_query.first()
        employees_with_kpi = result[0] if result else 0
        avg_achievement = result[1] if result and result[1] else 0.0

        coverage_percent = float((employees_with_kpi / total_employees * 100) if total_employees > 0 else 0)

        dept_kpis.append(DepartmentKPI(
            department_id=dept.id,
            department_name=dept.name,
            avg_achievement=round(avg_achievement, 2),
            employees_with_kpi=employees_with_kpi,
            total_employees=total_employees,
            coverage_percent=round(coverage_percent, 2)
        ))

    return dept_kpis


def _generate_budget_alerts(
    department_summaries: List[DepartmentSummary]
) -> List[BudgetAlert]:
    """Generate budget alerts based on execution thresholds"""
    alerts = []

    for dept in department_summaries:
        execution = dept.budget_execution_percent

        # Over budget (>100%)
        if execution > 100:
            alerts.append(BudgetAlert(
                alert_type="overbudget",
                department_id=dept.department_id,
                department_name=dept.department_name,
                category_id=None,
                category_name=None,
                planned=dept.budget_planned,
                actual=dept.budget_actual,
                execution_percent=execution,
                message=f"Отдел '{dept.department_name}' превысил бюджет на {execution - 100:.1f}%"
            ))
        # High utilization (90-100%)
        elif execution >= 90:
            alerts.append(BudgetAlert(
                alert_type="high_utilization",
                department_id=dept.department_id,
                department_name=dept.department_name,
                category_id=None,
                category_name=None,
                planned=dept.budget_planned,
                actual=dept.budget_actual,
                execution_percent=execution,
                message=f"Отдел '{dept.department_name}' использовал {execution:.1f}% бюджета"
            ))
        # Low utilization (<50% and month >= 6)
        elif execution < 50:
            current_month = datetime.now().month
            if current_month >= 6:
                alerts.append(BudgetAlert(
                    alert_type="low_utilization",
                    department_id=dept.department_id,
                    department_name=dept.department_name,
                    category_id=None,
                    category_name=None,
                    planned=dept.budget_planned,
                    actual=dept.budget_actual,
                    execution_percent=execution,
                    message=f"Отдел '{dept.department_name}' использовал только {execution:.1f}% бюджета"
                ))

    return alerts


@router.get("/department/{department_id}", response_model=FounderDepartmentDetails)
def get_department_details(
    department_id: int,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information for a specific department

    Only accessible by FOUNDER and ADMIN roles
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.FOUNDER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Founders and Admins can access department details"
        )

    if not year:
        year = datetime.now().year

    # Get department
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Budget by category
    budget_by_category = []
    categories_query = db.query(
        BudgetCategory.id,
        BudgetCategory.name,
        BudgetCategory.type,
        func.sum(BudgetPlan.planned_amount).label('planned'),
        func.sum(case(
            (Expense.status == ExpenseStatusEnum.PAID, Expense.amount),
            else_=0
        )).label('actual')
    ).outerjoin(
        BudgetPlan,
        (BudgetCategory.id == BudgetPlan.category_id) &
        (BudgetPlan.year == year) &
        (BudgetPlan.department_id == department_id)
    ).outerjoin(
        Expense,
        (BudgetCategory.id == Expense.category_id) &
        (extract('year', Expense.request_date) == year) &
        (Expense.department_id == department_id)
    ).filter(
        BudgetCategory.is_active == True
    ).group_by(
        BudgetCategory.id,
        BudgetCategory.name,
        BudgetCategory.type
    ).all()

    for cat in categories_query:
        planned = float(cat.planned or 0)
        actual = float(cat.actual or 0)
        budget_by_category.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'category_type': cat.type,
            'planned': planned,
            'actual': actual,
            'remaining': planned - actual,
            'execution_percent': round((actual / planned * 100) if planned > 0 else 0, 2)
        })

    # Expenses by month (simple version)
    expenses_by_month = []

    # Employee KPIs (simple version)
    employee_kpis = []

    # Recent expenses
    recent_expenses_query = db.query(Expense).filter(
        extract('year', Expense.request_date) == year,
        Expense.department_id == department_id
    ).order_by(Expense.request_date.desc()).limit(10)

    recent_expenses = []
    for exp in recent_expenses_query:
        recent_expenses.append({
            'id': exp.id,
            'number': exp.number,
            'amount': float(exp.amount),
            'status': exp.status.value,
            'request_date': exp.request_date.isoformat(),
            'category_id': exp.category_id
        })

    return FounderDepartmentDetails(
        department_id=department_id,
        department_name=department.name,
        year=year,
        month=month,
        budget_by_category=budget_by_category,
        expenses_by_month=expenses_by_month,
        employee_kpis=employee_kpis,
        recent_expenses=recent_expenses
    )
