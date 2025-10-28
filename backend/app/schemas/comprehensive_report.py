"""
Comprehensive Report Schemas

Schemas for integrated reporting combining Budget + Payroll + KPI
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


# ================================================================
# Summary Statistics
# ================================================================

class BudgetSummary(BaseModel):
    """Budget summary statistics"""
    total_planned: float = Field(description="Total planned budget")
    total_actual: float = Field(description="Total actual expenses")
    remaining: float = Field(description="Remaining budget")
    execution_percent: float = Field(description="Execution percentage")
    opex_planned: float = Field(description="OPEX planned")
    opex_actual: float = Field(description="OPEX actual")
    capex_planned: float = Field(description="CAPEX planned")
    capex_actual: float = Field(description="CAPEX actual")


class PayrollSummary(BaseModel):
    """Payroll summary statistics"""
    total_planned: float = Field(description="Total payroll planned")
    total_paid: float = Field(description="Total payroll paid")
    remaining: float = Field(description="Remaining payroll budget")
    execution_percent: float = Field(description="Execution percentage")
    employee_count: int = Field(description="Number of employees")
    avg_salary: float = Field(description="Average salary")
    base_salary_total: float = Field(description="Total base salary")
    monthly_bonus_total: float = Field(description="Total monthly bonuses")
    quarterly_bonus_total: float = Field(description="Total quarterly bonuses")
    annual_bonus_total: float = Field(description="Total annual bonuses")


class KPISummary(BaseModel):
    """KPI summary statistics"""
    avg_kpi_percentage: float = Field(description="Average KPI percentage")
    employees_tracked: int = Field(description="Number of employees with KPI tracking")
    goals_assigned: int = Field(description="Total goals assigned")
    goals_achieved: int = Field(description="Goals fully achieved (>=100%)")
    performance_bonus_paid: float = Field(description="Total performance bonuses paid")
    fixed_bonus_paid: float = Field(description="Total fixed bonuses paid")
    mixed_bonus_paid: float = Field(description="Total mixed bonuses paid")


# ================================================================
# Top Performers and Categories
# ================================================================

class TopPerformer(BaseModel):
    """Top performing employee by KPI"""
    employee_id: int
    employee_name: str
    position: str
    kpi_percentage: float
    total_bonus: float
    department_name: Optional[str] = None


class TopExpenseCategory(BaseModel):
    """Top expense category"""
    category_id: int
    category_name: str
    amount: float
    percent_of_total: float


# ================================================================
# Monthly Breakdown
# ================================================================

class MonthlyBreakdown(BaseModel):
    """Monthly breakdown of budget, payroll, and KPI"""
    month: int
    month_name: str

    # Budget
    budget_planned: float
    budget_actual: float
    budget_variance: float

    # Payroll
    payroll_planned: float
    payroll_paid: float
    payroll_variance: float

    # KPI
    avg_kpi_percentage: float
    total_performance_bonus: float

    # Combined
    total_planned: float = Field(description="Budget + Payroll planned")
    total_actual: float = Field(description="Budget actual + Payroll paid")
    total_variance: float


# ================================================================
# Department Comparison
# ================================================================

class DepartmentComparison(BaseModel):
    """Comparison across departments"""
    department_id: int
    department_name: str

    # Budget
    budget_planned: float
    budget_actual: float
    budget_execution_percent: float

    # Payroll
    payroll_planned: float
    payroll_paid: float
    employee_count: int
    avg_kpi_percentage: float

    # Combined
    total_planned: float
    total_actual: float
    execution_percent: float


# ================================================================
# Cost Efficiency Metrics
# ================================================================

class CostEfficiencyMetrics(BaseModel):
    """Cost efficiency and ROI metrics"""

    # Efficiency ratios
    payroll_to_budget_ratio: float = Field(
        description="Payroll as percentage of total budget"
    )
    cost_per_employee: float = Field(
        description="Average total cost per employee"
    )
    bonus_to_salary_ratio: float = Field(
        description="Bonuses as percentage of base salary"
    )

    # Performance metrics
    cost_per_kpi_point: float = Field(
        description="Cost per 1% of KPI achievement"
    )
    roi_on_performance_bonus: float = Field(
        description="ROI on performance-based bonuses (estimated)"
    )

    # Variance metrics
    budget_variance_percent: float = Field(
        description="Budget variance as percentage"
    )
    payroll_variance_percent: float = Field(
        description="Payroll variance as percentage"
    )


# ================================================================
# Comprehensive Report Response
# ================================================================

class ComprehensiveReport(BaseModel):
    """Complete comprehensive report combining all metrics"""

    # Period info
    year: int
    start_month: Optional[int] = None
    end_month: Optional[int] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None

    # Summary statistics
    budget_summary: BudgetSummary
    payroll_summary: PayrollSummary
    kpi_summary: KPISummary

    # Cost efficiency
    efficiency_metrics: CostEfficiencyMetrics

    # Top performers and categories
    top_performers: List[TopPerformer] = Field(
        description="Top 10 performers by KPI"
    )
    top_expense_categories: List[TopExpenseCategory] = Field(
        description="Top 10 expense categories"
    )

    # Monthly breakdown
    monthly_breakdown: List[MonthlyBreakdown] = Field(
        description="Month-by-month analysis"
    )

    # Department comparison (if no specific department selected)
    department_comparison: Optional[List[DepartmentComparison]] = Field(
        default=None,
        description="Comparison across departments (ADMIN/MANAGER only)"
    )

    # Metadata
    generated_at: date = Field(
        default_factory=date.today,
        description="Report generation date"
    )


# ================================================================
# Request Models
# ================================================================

class ComprehensiveReportRequest(BaseModel):
    """Request parameters for comprehensive report"""
    year: int = Field(description="Year for report")
    start_month: Optional[int] = Field(None, ge=1, le=12, description="Start month (1-12)")
    end_month: Optional[int] = Field(None, ge=1, le=12, description="End month (1-12)")
    department_id: Optional[int] = Field(None, description="Department ID (ADMIN/MANAGER only)")
    include_department_comparison: bool = Field(
        default=False,
        description="Include department comparison (ADMIN/MANAGER only)"
    )


# ================================================================
# Export Models
# ================================================================

class ComprehensiveReportExport(BaseModel):
    """Export format for comprehensive report"""
    report: ComprehensiveReport
    export_format: str = Field(default="json", description="Export format (json, excel, pdf)")
