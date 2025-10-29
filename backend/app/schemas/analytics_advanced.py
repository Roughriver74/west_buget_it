"""
Pydantic schemas for advanced analytics endpoints
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date


# ==================== Expense Trends ====================

class ExpenseTrendPoint(BaseModel):
    """Single point in expense trend"""
    period: str  # "2025-01" for monthly, "2025-Q1" for quarterly
    category_id: int
    category_name: str
    total_amount: Decimal
    expense_count: int
    average_amount: Decimal
    growth_rate: Optional[Decimal] = None  # % change from previous period


class ExpenseTrendSummary(BaseModel):
    """Summary statistics for expense trends"""
    total_periods: int
    date_from: date
    date_to: date
    total_amount: Decimal
    average_per_period: Decimal
    max_period_amount: Decimal
    min_period_amount: Decimal
    volatility: Decimal  # Standard deviation


class ExpenseTrendsResponse(BaseModel):
    """Response for expense trends analysis"""
    trends: List[ExpenseTrendPoint]
    summary: ExpenseTrendSummary
    top_growing_categories: List[dict]  # Top 5 with highest growth
    top_declining_categories: List[dict]  # Top 5 with highest decline


# ==================== Contractor Analysis ====================

class ContractorStats(BaseModel):
    """Statistics for a single contractor"""
    contractor_id: int
    contractor_name: str
    total_amount: Decimal
    expense_count: int
    average_expense: Decimal
    first_expense_date: date
    last_expense_date: date
    active_months: int
    categories_count: int  # How many different categories
    top_category: str
    share_of_total: Decimal  # % of total expenses


class ContractorAnalysisResponse(BaseModel):
    """Response for contractor analysis"""
    contractors: List[ContractorStats]
    total_contractors: int
    total_amount: Decimal
    concentration_ratio: Decimal  # Top 10 contractors % of total
    average_contractor_amount: Decimal
    new_contractors_count: int  # New in selected period
    inactive_contractors_count: int  # Had expenses before but not in period


# ==================== Department Comparison ====================

class DepartmentMetrics(BaseModel):
    """Metrics for a single department"""
    department_id: int
    department_name: str
    total_budget: Decimal
    total_actual: Decimal
    execution_rate: Decimal  # actual / budget * 100
    variance: Decimal  # actual - budget
    variance_percent: Decimal
    capex_amount: Decimal
    opex_amount: Decimal
    capex_ratio: Decimal  # capex / total * 100
    expense_count: int
    average_expense: Decimal
    employee_count: int
    cost_per_employee: Decimal
    top_category: str
    top_category_amount: Decimal


class DepartmentComparisonResponse(BaseModel):
    """Response for department comparison"""
    departments: List[DepartmentMetrics]
    total_departments: int
    total_budget: Decimal
    total_actual: Decimal
    overall_execution_rate: Decimal
    best_performing_dept: Optional[str] = None  # Closest to budget
    highest_variance_dept: Optional[str] = None
    most_efficient_dept: Optional[str] = None  # Lowest cost per employee


# ==================== Seasonal Patterns ====================

class SeasonalPattern(BaseModel):
    """Seasonal pattern for a specific period"""
    month: int  # 1-12
    month_name: str
    average_amount: Decimal
    median_amount: Decimal
    min_amount: Decimal
    max_amount: Decimal
    expense_count_average: int
    seasonality_index: Decimal  # Ratio to yearly average (1.0 = average)
    year_over_year_growth: Optional[Decimal] = None


class SeasonalPatternsResponse(BaseModel):
    """Response for seasonal patterns analysis"""
    patterns: List[SeasonalPattern]
    peak_month: str
    lowest_month: str
    seasonality_strength: Decimal  # Coefficient of variation
    predictability_score: Decimal  # How consistent patterns are (0-100)
    recommended_budget_distribution: List[dict]  # Suggested % per month


# ==================== Cost Efficiency ====================

class CategoryEfficiency(BaseModel):
    """Efficiency metrics for a category"""
    category_id: int
    category_name: str
    budget_amount: Decimal
    actual_amount: Decimal
    savings: Decimal  # budget - actual (positive = under budget)
    savings_rate: Decimal  # savings / budget * 100
    expense_count: int
    average_processing_days: float
    on_time_payment_rate: Decimal  # % paid by due date
    efficiency_score: Decimal  # Composite score (0-100)


class CostEfficiencyMetrics(BaseModel):
    """Overall cost efficiency metrics"""
    total_budget: Decimal
    total_actual: Decimal
    total_savings: Decimal
    savings_rate: Decimal
    average_processing_days: float
    on_time_payment_rate: Decimal
    budget_utilization_rate: Decimal  # actual / budget * 100
    cost_control_score: Decimal  # How well costs are controlled (0-100)
    roi_estimate: Optional[Decimal] = None  # If business metrics available


class CostEfficiencyResponse(BaseModel):
    """Response for cost efficiency analysis"""
    metrics: CostEfficiencyMetrics
    categories: List[CategoryEfficiency]
    best_performing_categories: List[str]  # Top 5 with highest savings rate
    areas_for_improvement: List[str]  # Top 5 over budget
    efficiency_trends: List[dict]  # Monthly efficiency trends
    recommendations: List[str]  # AI-generated recommendations
