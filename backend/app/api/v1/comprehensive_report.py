"""
Comprehensive Report API

Integrated reporting endpoint combining Budget + Payroll + KPI metrics
Provides holistic view of organizational performance and spending
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, date
from calendar import month_name

from app.db import get_db
from app.db.models import (
    User, Department, Expense, BudgetPlan, PayrollPlan, PayrollActual,
    Employee, EmployeeKPI, KPIGoal, EmployeeKPIGoal,
    ExpenseTypeEnum, BonusTypeEnum, UserRoleEnum
)
from app.utils.auth import get_current_active_user
from app.schemas.comprehensive_report import (
    ComprehensiveReport, BudgetSummary, PayrollSummary, KPISummary,
    CostEfficiencyMetrics, TopPerformer, TopExpenseCategory,
    MonthlyBreakdown, DepartmentComparison
)

router = APIRouter()


def _check_department_access(
    current_user: User,
    department_id: Optional[int],
    db: Session
) -> Optional[int]:
    """Check department access based on user role"""
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        return current_user.department_id
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER/ADMIN can specify department or see all
        return department_id
    return current_user.department_id


@router.get("/", response_model=ComprehensiveReport)
def get_comprehensive_report(
    year: int = Query(..., description="Year for report"),
    start_month: Optional[int] = Query(None, ge=1, le=12, description="Start month (1-12)"),
    end_month: Optional[int] = Query(None, ge=1, le=12, description="End month (1-12)"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    include_department_comparison: bool = Query(
        False,
        description="Include department comparison (ADMIN/MANAGER only)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive report combining Budget, Payroll, and KPI metrics

    Provides integrated view of:
    - Budget execution (planned vs actual)
    - Payroll costs and KPI-based bonuses
    - Top performers and expense categories
    - Monthly breakdown
    - Cost efficiency metrics
    - Department comparison (for ADMIN/MANAGER)
    """

    # Validate month range
    if start_month and end_month and start_month > end_month:
        raise HTTPException(status_code=400, detail="start_month must be <= end_month")

    # Check department access
    effective_department_id = _check_department_access(current_user, department_id, db)

    # Set default month range (full year)
    if not start_month:
        start_month = 1
    if not end_month:
        end_month = 12

    # ================================================================
    # 1. Budget Summary
    # ================================================================

    budget_query = db.query(
        func.sum(BudgetPlan.planned_amount).label('total_planned')
    ).filter(BudgetPlan.year == year)

    if start_month and end_month:
        budget_query = budget_query.filter(
            BudgetPlan.month.between(start_month, end_month)
        )
    if effective_department_id:
        budget_query = budget_query.filter(BudgetPlan.department_id == effective_department_id)

    budget_planned_result = budget_query.first()
    budget_planned = float(budget_planned_result.total_planned or 0)

    # Get actual expenses
    expense_query = db.query(
        func.sum(Expense.amount).label('total_actual')
    ).filter(extract('year', Expense.request_date) == year)

    if start_month and end_month:
        expense_query = expense_query.filter(
            extract('month', Expense.request_date).between(start_month, end_month)
        )
    if effective_department_id:
        expense_query = expense_query.filter(Expense.department_id == effective_department_id)

    budget_actual_result = expense_query.first()
    budget_actual = float(budget_actual_result.total_actual or 0)

    # OPEX/CAPEX breakdown
    opex_query = db.query(func.sum(Expense.amount)).join(
        Expense.category_rel
    ).filter(
        extract('year', Expense.request_date) == year,
        Expense.category_rel.has(type=ExpenseTypeEnum.OPEX)
    )
    if start_month and end_month:
        opex_query = opex_query.filter(
            extract('month', Expense.request_date).between(start_month, end_month)
        )
    if effective_department_id:
        opex_query = opex_query.filter(Expense.department_id == effective_department_id)
    opex_actual = float(opex_query.scalar() or 0)

    capex_actual = budget_actual - opex_actual

    budget_summary = BudgetSummary(
        total_planned=budget_planned,
        total_actual=budget_actual,
        remaining=budget_planned - budget_actual,
        execution_percent=round((budget_actual / budget_planned * 100) if budget_planned > 0 else 0, 2),
        opex_planned=budget_planned * 0.7,  # Estimate
        opex_actual=opex_actual,
        capex_planned=budget_planned * 0.3,  # Estimate
        capex_actual=capex_actual
    )

    # ================================================================
    # 2. Payroll Summary
    # ================================================================

    payroll_plan_query = db.query(
        func.sum(PayrollPlan.total_planned).label('total_planned'),
        func.sum(PayrollPlan.base_salary).label('base_salary'),
        func.sum(PayrollPlan.monthly_bonus).label('monthly_bonus'),
        func.sum(PayrollPlan.quarterly_bonus).label('quarterly_bonus'),
        func.sum(PayrollPlan.annual_bonus).label('annual_bonus'),
        func.count(func.distinct(PayrollPlan.employee_id)).label('employee_count')
    ).filter(PayrollPlan.year == year)

    if start_month and end_month:
        payroll_plan_query = payroll_plan_query.filter(
            PayrollPlan.month.between(start_month, end_month)
        )
    if effective_department_id:
        payroll_plan_query = payroll_plan_query.filter(
            PayrollPlan.department_id == effective_department_id
        )

    payroll_plan_result = payroll_plan_query.first()

    payroll_actual_query = db.query(
        func.sum(PayrollActual.total_paid).label('total_paid')
    ).filter(PayrollActual.year == year)

    if start_month and end_month:
        payroll_actual_query = payroll_actual_query.filter(
            PayrollActual.month.between(start_month, end_month)
        )
    if effective_department_id:
        payroll_actual_query = payroll_actual_query.filter(
            PayrollActual.department_id == effective_department_id
        )

    payroll_actual_result = payroll_actual_query.first()

    payroll_planned = float(payroll_plan_result.total_planned or 0)
    payroll_paid = float(payroll_actual_result.total_paid or 0)
    employee_count = int(payroll_plan_result.employee_count or 0)

    payroll_summary = PayrollSummary(
        total_planned=payroll_planned,
        total_paid=payroll_paid,
        remaining=payroll_planned - payroll_paid,
        execution_percent=round((payroll_paid / payroll_planned * 100) if payroll_planned > 0 else 0, 2),
        employee_count=employee_count,
        avg_salary=round(payroll_planned / employee_count if employee_count > 0 else 0, 2),
        base_salary_total=float(payroll_plan_result.base_salary or 0),
        monthly_bonus_total=float(payroll_plan_result.monthly_bonus or 0),
        quarterly_bonus_total=float(payroll_plan_result.quarterly_bonus or 0),
        annual_bonus_total=float(payroll_plan_result.annual_bonus or 0)
    )

    # ================================================================
    # 3. KPI Summary
    # ================================================================

    kpi_query = db.query(
        func.avg(EmployeeKPI.kpi_percentage).label('avg_kpi'),
        func.count(func.distinct(EmployeeKPI.employee_id)).label('employees_tracked'),
        func.sum(EmployeeKPI.monthly_bonus_calculated).label('total_bonus')
    ).filter(EmployeeKPI.year == year)

    if start_month and end_month:
        kpi_query = kpi_query.filter(EmployeeKPI.month.between(start_month, end_month))
    if effective_department_id:
        kpi_query = kpi_query.filter(EmployeeKPI.department_id == effective_department_id)

    kpi_result = kpi_query.first()

    # Goals statistics
    goal_query = db.query(
        func.count(EmployeeKPIGoal.id).label('total_goals'),
        func.sum(
            func.case(
                (EmployeeKPIGoal.achievement_percentage >= 100, 1),
                else_=0
            )
        ).label('goals_achieved')
    ).filter(EmployeeKPIGoal.year == year)

    if start_month and end_month:
        goal_query = goal_query.filter(EmployeeKPIGoal.month.between(start_month, end_month))
    if effective_department_id:
        goal_query = goal_query.filter(EmployeeKPIGoal.department_id == effective_department_id)

    goal_result = goal_query.first()

    # Bonus breakdown by type
    performance_bonus = db.query(
        func.sum(EmployeeKPI.monthly_bonus_calculated)
    ).filter(
        EmployeeKPI.year == year,
        EmployeeKPI.monthly_bonus_type == BonusTypeEnum.PERFORMANCE_BASED
    )
    if start_month and end_month:
        performance_bonus = performance_bonus.filter(
            EmployeeKPI.month.between(start_month, end_month)
        )
    if effective_department_id:
        performance_bonus = performance_bonus.filter(
            EmployeeKPI.department_id == effective_department_id
        )
    performance_bonus_paid = float(performance_bonus.scalar() or 0)

    fixed_bonus = db.query(
        func.sum(EmployeeKPI.monthly_bonus_calculated)
    ).filter(
        EmployeeKPI.year == year,
        EmployeeKPI.monthly_bonus_type == BonusTypeEnum.FIXED
    )
    if start_month and end_month:
        fixed_bonus = fixed_bonus.filter(EmployeeKPI.month.between(start_month, end_month))
    if effective_department_id:
        fixed_bonus = fixed_bonus.filter(EmployeeKPI.department_id == effective_department_id)
    fixed_bonus_paid = float(fixed_bonus.scalar() or 0)

    mixed_bonus = db.query(
        func.sum(EmployeeKPI.monthly_bonus_calculated)
    ).filter(
        EmployeeKPI.year == year,
        EmployeeKPI.monthly_bonus_type == BonusTypeEnum.MIXED
    )
    if start_month and end_month:
        mixed_bonus = mixed_bonus.filter(EmployeeKPI.month.between(start_month, end_month))
    if effective_department_id:
        mixed_bonus = mixed_bonus.filter(EmployeeKPI.department_id == effective_department_id)
    mixed_bonus_paid = float(mixed_bonus.scalar() or 0)

    kpi_summary = KPISummary(
        avg_kpi_percentage=round(float(kpi_result.avg_kpi or 0), 2),
        employees_tracked=int(kpi_result.employees_tracked or 0),
        goals_assigned=int(goal_result.total_goals or 0),
        goals_achieved=int(goal_result.goals_achieved or 0),
        performance_bonus_paid=performance_bonus_paid,
        fixed_bonus_paid=fixed_bonus_paid,
        mixed_bonus_paid=mixed_bonus_paid
    )

    # ================================================================
    # 4. Cost Efficiency Metrics
    # ================================================================

    total_planned = budget_planned + payroll_planned
    total_actual = budget_actual + payroll_paid

    efficiency_metrics = CostEfficiencyMetrics(
        payroll_to_budget_ratio=round(
            (payroll_planned / total_planned * 100) if total_planned > 0 else 0, 2
        ),
        cost_per_employee=round(
            total_planned / employee_count if employee_count > 0 else 0, 2
        ),
        bonus_to_salary_ratio=round(
            ((payroll_summary.monthly_bonus_total +
              payroll_summary.quarterly_bonus_total +
              payroll_summary.annual_bonus_total) /
             payroll_summary.base_salary_total * 100)
            if payroll_summary.base_salary_total > 0 else 0, 2
        ),
        cost_per_kpi_point=round(
            (payroll_paid / (kpi_summary.avg_kpi_percentage * employee_count))
            if (kpi_summary.avg_kpi_percentage > 0 and employee_count > 0) else 0, 2
        ),
        roi_on_performance_bonus=round(
            (kpi_summary.avg_kpi_percentage / 100 * performance_bonus_paid)
            if performance_bonus_paid > 0 else 0, 2
        ),
        budget_variance_percent=round(
            ((budget_actual - budget_planned) / budget_planned * 100)
            if budget_planned > 0 else 0, 2
        ),
        payroll_variance_percent=round(
            ((payroll_paid - payroll_planned) / payroll_planned * 100)
            if payroll_planned > 0 else 0, 2
        )
    )

    # ================================================================
    # 5. Top Performers
    # ================================================================

    top_performers_query = db.query(
        Employee.id,
        Employee.full_name,
        Employee.position,
        func.avg(EmployeeKPI.kpi_percentage).label('avg_kpi'),
        func.sum(EmployeeKPI.monthly_bonus_calculated).label('total_bonus'),
        Department.name.label('department_name')
    ).join(EmployeeKPI, Employee.id == EmployeeKPI.employee_id).join(
        Department, Employee.department_id == Department.id
    ).filter(EmployeeKPI.year == year)

    if start_month and end_month:
        top_performers_query = top_performers_query.filter(
            EmployeeKPI.month.between(start_month, end_month)
        )
    if effective_department_id:
        top_performers_query = top_performers_query.filter(
            Employee.department_id == effective_department_id
        )

    top_performers_query = top_performers_query.group_by(
        Employee.id, Employee.full_name, Employee.position, Department.name
    ).order_by(func.avg(EmployeeKPI.kpi_percentage).desc()).limit(10)

    top_performers = [
        TopPerformer(
            employee_id=row.id,
            employee_name=row.full_name,
            position=row.position,
            kpi_percentage=round(float(row.avg_kpi), 2),
            total_bonus=float(row.total_bonus),
            department_name=row.department_name
        )
        for row in top_performers_query.all()
    ]

    # ================================================================
    # 6. Top Expense Categories
    # ================================================================

    top_categories_query = db.query(
        Expense.category_id,
        Expense.category_rel.name.label('category_name'),
        func.sum(Expense.amount).label('total_amount')
    ).filter(extract('year', Expense.request_date) == year)

    if start_month and end_month:
        top_categories_query = top_categories_query.filter(
            extract('month', Expense.request_date).between(start_month, end_month)
        )
    if effective_department_id:
        top_categories_query = top_categories_query.filter(
            Expense.department_id == effective_department_id
        )

    top_categories_query = top_categories_query.group_by(
        Expense.category_id, Expense.category_rel.name
    ).order_by(func.sum(Expense.amount).desc()).limit(10)

    top_expense_categories = [
        TopExpenseCategory(
            category_id=row.category_id,
            category_name=row.category_name,
            amount=float(row.total_amount),
            percent_of_total=round(
                (float(row.total_amount) / budget_actual * 100) if budget_actual > 0 else 0, 2
            )
        )
        for row in top_categories_query.all()
    ]

    # ================================================================
    # 7. Monthly Breakdown
    # ================================================================

    monthly_breakdown = []
    for month in range(start_month, end_month + 1):
        # Budget for month
        month_budget_planned = db.query(
            func.sum(BudgetPlan.planned_amount)
        ).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == month
        )
        if effective_department_id:
            month_budget_planned = month_budget_planned.filter(
                BudgetPlan.department_id == effective_department_id
            )
        month_budget_planned = float(month_budget_planned.scalar() or 0)

        month_budget_actual = db.query(
            func.sum(Expense.amount)
        ).filter(
            extract('year', Expense.request_date) == year,
            extract('month', Expense.request_date) == month
        )
        if effective_department_id:
            month_budget_actual = month_budget_actual.filter(
                Expense.department_id == effective_department_id
            )
        month_budget_actual = float(month_budget_actual.scalar() or 0)

        # Payroll for month
        month_payroll_planned = db.query(
            func.sum(PayrollPlan.total_planned)
        ).filter(
            PayrollPlan.year == year,
            PayrollPlan.month == month
        )
        if effective_department_id:
            month_payroll_planned = month_payroll_planned.filter(
                PayrollPlan.department_id == effective_department_id
            )
        month_payroll_planned = float(month_payroll_planned.scalar() or 0)

        month_payroll_paid = db.query(
            func.sum(PayrollActual.total_paid)
        ).filter(
            PayrollActual.year == year,
            PayrollActual.month == month
        )
        if effective_department_id:
            month_payroll_paid = month_payroll_paid.filter(
                PayrollActual.department_id == effective_department_id
            )
        month_payroll_paid = float(month_payroll_paid.scalar() or 0)

        # KPI for month
        month_avg_kpi = db.query(
            func.avg(EmployeeKPI.kpi_percentage)
        ).filter(
            EmployeeKPI.year == year,
            EmployeeKPI.month == month
        )
        if effective_department_id:
            month_avg_kpi = month_avg_kpi.filter(
                EmployeeKPI.department_id == effective_department_id
            )
        month_avg_kpi = float(month_avg_kpi.scalar() or 0)

        month_performance_bonus = db.query(
            func.sum(EmployeeKPI.monthly_bonus_calculated)
        ).filter(
            EmployeeKPI.year == year,
            EmployeeKPI.month == month,
            EmployeeKPI.monthly_bonus_type == BonusTypeEnum.PERFORMANCE_BASED
        )
        if effective_department_id:
            month_performance_bonus = month_performance_bonus.filter(
                EmployeeKPI.department_id == effective_department_id
            )
        month_performance_bonus = float(month_performance_bonus.scalar() or 0)

        monthly_breakdown.append(
            MonthlyBreakdown(
                month=month,
                month_name=month_name[month],
                budget_planned=month_budget_planned,
                budget_actual=month_budget_actual,
                budget_variance=month_budget_actual - month_budget_planned,
                payroll_planned=month_payroll_planned,
                payroll_paid=month_payroll_paid,
                payroll_variance=month_payroll_paid - month_payroll_planned,
                avg_kpi_percentage=round(month_avg_kpi, 2),
                total_performance_bonus=month_performance_bonus,
                total_planned=month_budget_planned + month_payroll_planned,
                total_actual=month_budget_actual + month_payroll_paid,
                total_variance=(month_budget_actual + month_payroll_paid) -
                              (month_budget_planned + month_payroll_planned)
            )
        )

    # ================================================================
    # 8. Department Comparison (if requested and authorized)
    # ================================================================

    department_comparison = None
    if (include_department_comparison and
        current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN] and
        not effective_department_id):  # Only if not filtering by specific department

        departments = db.query(Department).filter(Department.is_active == True).all()
        department_comparison = []

        for dept in departments:
            dept_budget_planned = db.query(
                func.sum(BudgetPlan.planned_amount)
            ).filter(
                BudgetPlan.year == year,
                BudgetPlan.department_id == dept.id
            )
            if start_month and end_month:
                dept_budget_planned = dept_budget_planned.filter(
                    BudgetPlan.month.between(start_month, end_month)
                )
            dept_budget_planned = float(dept_budget_planned.scalar() or 0)

            dept_budget_actual = db.query(
                func.sum(Expense.amount)
            ).filter(
                extract('year', Expense.request_date) == year,
                Expense.department_id == dept.id
            )
            if start_month and end_month:
                dept_budget_actual = dept_budget_actual.filter(
                    extract('month', Expense.request_date).between(start_month, end_month)
                )
            dept_budget_actual = float(dept_budget_actual.scalar() or 0)

            dept_payroll_planned = db.query(
                func.sum(PayrollPlan.total_planned)
            ).filter(
                PayrollPlan.year == year,
                PayrollPlan.department_id == dept.id
            )
            if start_month and end_month:
                dept_payroll_planned = dept_payroll_planned.filter(
                    PayrollPlan.month.between(start_month, end_month)
                )
            dept_payroll_planned = float(dept_payroll_planned.scalar() or 0)

            dept_payroll_paid = db.query(
                func.sum(PayrollActual.total_paid)
            ).filter(
                PayrollActual.year == year,
                PayrollActual.department_id == dept.id
            )
            if start_month and end_month:
                dept_payroll_paid = dept_payroll_paid.filter(
                    PayrollActual.month.between(start_month, end_month)
                )
            dept_payroll_paid = float(dept_payroll_paid.scalar() or 0)

            dept_employee_count = db.query(
                func.count(func.distinct(PayrollPlan.employee_id))
            ).filter(
                PayrollPlan.year == year,
                PayrollPlan.department_id == dept.id
            )
            if start_month and end_month:
                dept_employee_count = dept_employee_count.filter(
                    PayrollPlan.month.between(start_month, end_month)
                )
            dept_employee_count = int(dept_employee_count.scalar() or 0)

            dept_avg_kpi = db.query(
                func.avg(EmployeeKPI.kpi_percentage)
            ).filter(
                EmployeeKPI.year == year,
                EmployeeKPI.department_id == dept.id
            )
            if start_month and end_month:
                dept_avg_kpi = dept_avg_kpi.filter(
                    EmployeeKPI.month.between(start_month, end_month)
                )
            dept_avg_kpi = float(dept_avg_kpi.scalar() or 0)

            dept_total_planned = dept_budget_planned + dept_payroll_planned
            dept_total_actual = dept_budget_actual + dept_payroll_paid

            department_comparison.append(
                DepartmentComparison(
                    department_id=dept.id,
                    department_name=dept.name,
                    budget_planned=dept_budget_planned,
                    budget_actual=dept_budget_actual,
                    budget_execution_percent=round(
                        (dept_budget_actual / dept_budget_planned * 100)
                        if dept_budget_planned > 0 else 0, 2
                    ),
                    payroll_planned=dept_payroll_planned,
                    payroll_paid=dept_payroll_paid,
                    employee_count=dept_employee_count,
                    avg_kpi_percentage=round(dept_avg_kpi, 2),
                    total_planned=dept_total_planned,
                    total_actual=dept_total_actual,
                    execution_percent=round(
                        (dept_total_actual / dept_total_planned * 100)
                        if dept_total_planned > 0 else 0, 2
                    )
                )
            )

    # ================================================================
    # Build final report
    # ================================================================

    department_name = None
    if effective_department_id:
        dept = db.query(Department).filter(Department.id == effective_department_id).first()
        if dept:
            department_name = dept.name

    report = ComprehensiveReport(
        year=year,
        start_month=start_month,
        end_month=end_month,
        department_id=effective_department_id,
        department_name=department_name,
        budget_summary=budget_summary,
        payroll_summary=payroll_summary,
        kpi_summary=kpi_summary,
        efficiency_metrics=efficiency_metrics,
        top_performers=top_performers,
        top_expense_categories=top_expense_categories,
        monthly_breakdown=monthly_breakdown,
        department_comparison=department_comparison,
        generated_at=date.today()
    )

    return report
