"""Pydantic schemas for Founder Dashboard"""
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel


class DepartmentSummary(BaseModel):
    """Сводка по отделу"""
    department_id: int
    department_name: str
    # Бюджет
    budget_planned: Decimal
    budget_actual: Decimal
    budget_remaining: Decimal
    budget_execution_percent: float
    # Расходы
    expenses_count: int
    expenses_pending: int
    expenses_paid_amount: Decimal
    # Сотрудники и зарплаты
    employees_count: int
    payroll_planned: Decimal
    payroll_actual: Decimal
    # КПИ
    avg_kpi_achievement: Optional[float] = None


class CompanySummary(BaseModel):
    """Общая сводка по компании"""
    # Бюджет
    total_budget_planned: Decimal
    total_budget_actual: Decimal
    total_budget_remaining: Decimal
    total_budget_execution_percent: float
    # Расходы
    total_expenses_count: int
    total_expenses_pending: int
    total_expenses_paid: Decimal
    # Сотрудники
    total_employees: int
    total_payroll_planned: Decimal
    total_payroll_actual: Decimal
    # Отделы
    departments_count: int


class TopCategoryByDepartment(BaseModel):
    """Топ категория расходов по отделу"""
    department_id: int
    department_name: str
    category_id: Optional[int]
    category_name: str
    category_type: Optional[str]
    amount: Decimal
    execution_percent: float


class ExpenseTrend(BaseModel):
    """Тренд расходов по месяцам"""
    month: int
    month_name: str
    planned: Decimal
    actual: Decimal
    execution_percent: float


class DepartmentKPI(BaseModel):
    """КПИ отдела"""
    department_id: int
    department_name: str
    avg_achievement: float
    employees_with_kpi: int
    total_employees: int
    coverage_percent: float


class BudgetAlert(BaseModel):
    """Предупреждение о бюджете"""
    alert_type: str  # "overbudget", "high_utilization", "low_utilization"
    department_id: int
    department_name: str
    category_id: Optional[int]
    category_name: Optional[str]
    planned: Decimal
    actual: Decimal
    execution_percent: float
    message: str


class FounderDashboardData(BaseModel):
    """Главный дашборд учредителя"""
    year: int
    month: Optional[int] = None

    # Общая сводка
    company_summary: CompanySummary

    # Детали по отделам
    departments: List[DepartmentSummary]

    # Топ категории расходов по отделам
    top_categories_by_department: List[TopCategoryByDepartment]

    # Тренды
    expense_trends: List[ExpenseTrend]

    # КПИ
    department_kpis: List[DepartmentKPI]

    # Предупреждения
    alerts: List[BudgetAlert]


class FounderDepartmentDetails(BaseModel):
    """Детальная информация по отделу для учредителя"""
    department_id: int
    department_name: str
    year: int
    month: Optional[int] = None

    # Бюджет по категориям
    budget_by_category: List[dict]

    # Расходы по месяцам
    expenses_by_month: List[dict]

    # КПИ сотрудников
    employee_kpis: List[dict]

    # Последние расходы
    recent_expenses: List[dict]
