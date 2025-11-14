from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class DashboardTotals(BaseModel):
    planned: float
    actual: float
    remaining: float
    execution_percent: float


class DashboardCapexVsOpex(BaseModel):
    capex: float
    opex: float
    capex_percent: float
    opex_percent: float


class DashboardStatusDistribution(BaseModel):
    status: str
    count: int
    amount: float


class DashboardTopCategory(BaseModel):
    category_id: int
    category_name: str
    category_type: str
    amount: float


class DashboardRecentExpense(BaseModel):
    id: int
    number: str
    amount: float
    status: str
    request_date: str
    category_id: Optional[int]


class DashboardByMonthItem(BaseModel):
    month: int
    planned: float
    actual: float
    remaining: float


class DashboardByCategoryItem(BaseModel):
    category_id: Optional[int]
    category_name: str
    planned: float
    actual: float
    remaining: float


class DashboardData(BaseModel):
    year: int
    month: Optional[int] = None
    totals: DashboardTotals
    capex_vs_opex: DashboardCapexVsOpex
    status_distribution: List[DashboardStatusDistribution]
    top_categories: List[DashboardTopCategory]
    recent_expenses: List[DashboardRecentExpense]
    by_month: Optional[List[DashboardByMonthItem]] = None
    by_category: Optional[List[DashboardByCategoryItem]] = None


class CategoryAnalyticsItem(BaseModel):
    category_id: int
    category_name: str
    category_type: str
    parent_id: Optional[int]
    planned: float
    actual: float
    remaining: float
    execution_percent: float
    expense_count: int


class CategoryAnalytics(BaseModel):
    year: int
    month: Optional[int] = None
    categories: List[CategoryAnalyticsItem]


class TrendItem(BaseModel):
    month: int
    month_name: str
    amount: float
    count: int


class Trends(BaseModel):
    year: int
    category_id: Optional[int] = None
    trends: List[TrendItem]


class PaymentCalendarDay(BaseModel):
    date: date
    total_amount: float
    payment_count: int
    planned_amount: Optional[float] = None  # Amount from PENDING expenses (к оплате)
    planned_count: Optional[int] = None  # Count of PENDING expenses
    baseline_amount: Optional[float] = None  # Planned amount from baseline budget
    forecast_amount: Optional[float] = None   # Forecasted amount


class PaymentCalendar(BaseModel):
    year: int
    month: int
    days: List[PaymentCalendarDay]
    has_baseline: bool = False
    baseline_version_name: Optional[str] = None


class PaymentDetail(BaseModel):
    id: int
    number: str
    amount: float
    payment_date: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    contractor_id: Optional[int]
    contractor_name: Optional[str]
    organization_id: Optional[int]
    organization_name: Optional[str]
    status: str
    comment: Optional[str]


class PaymentsByDay(BaseModel):
    date: date
    total_count: int
    total_amount: float
    payments: List[PaymentDetail]


class ForecastMethodEnum(str, Enum):
    SIMPLE_AVERAGE = "simple_average"
    MOVING_AVERAGE = "moving_average"
    SEASONAL = "seasonal"


class PaymentForecastPeriod(BaseModel):
    start_date: str
    end_date: str
    days: int


class PaymentForecastSummary(BaseModel):
    total_predicted: float
    average_daily: float


class PaymentForecastPoint(BaseModel):
    date: str
    predicted_amount: float
    confidence: str
    method: ForecastMethodEnum


class PaymentForecast(BaseModel):
    period: PaymentForecastPeriod
    method: ForecastMethodEnum
    lookback_days: int
    summary: PaymentForecastSummary
    forecast: List[PaymentForecastPoint]


class ForecastSummaryPeriod(BaseModel):
    start_date: str
    end_date: str


class ForecastSummaryMethodStats(BaseModel):
    total: float
    daily_avg: float


class ForecastSummaryMethods(BaseModel):
    simple_average: ForecastSummaryMethodStats
    moving_average: ForecastSummaryMethodStats
    seasonal: ForecastSummaryMethodStats


class ForecastSummary(BaseModel):
    period: ForecastSummaryPeriod
    forecasts: ForecastSummaryMethods


# ============================================================================
# Plan vs Actual Schemas
# ============================================================================

class PlanVsActualMonthly(BaseModel):
    month: int
    month_name: str
    planned: float
    actual: float
    difference: float
    execution_percent: float


class PlanVsActualCategory(BaseModel):
    category_id: int
    category_name: str
    planned: float
    actual: float
    difference: float
    execution_percent: float
    monthly: list[PlanVsActualMonthly]


class PlanVsActualSummary(BaseModel):
    year: int
    baseline_version_id: Optional[int]
    baseline_version_name: Optional[str]
    total_planned: float
    total_actual: float
    total_difference: float
    execution_percent: float
    by_month: list[PlanVsActualMonthly]
    by_category: list[PlanVsActualCategory]


# ============================================================================
# Budget Income Statement (БДР) Schemas
# ============================================================================

class BudgetIncomeStatementMonthly(BaseModel):
    """Monthly breakdown for budget income statement"""
    month: int
    month_name: str
    revenue_planned: float
    revenue_actual: float
    expenses_planned: float
    expenses_actual: float
    profit_planned: float
    profit_actual: float
    profit_margin_planned: float  # %
    profit_margin_actual: float   # %


class BudgetIncomeStatementCategory(BaseModel):
    """Category-level breakdown (revenue streams and expense categories)"""
    category_id: int
    category_name: str
    category_type: str  # 'revenue' or 'expense'
    planned: float
    actual: float
    difference: float
    execution_percent: float


class BudgetIncomeStatement(BaseModel):
    """
    БДР (Бюджет доходов и расходов) - Budget Income Statement

    Shows the complete financial picture:
    - Revenue (from revenue_plans and revenue_actuals)
    - Expenses (from budget_plans and expenses)
    - Profit (Revenue - Expenses)
    - Profitability metrics (ROI, Profit Margin)
    """
    year: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None

    # Revenue totals
    revenue_planned: float
    revenue_actual: float
    revenue_difference: float
    revenue_execution_percent: float

    # Expense totals
    expenses_planned: float
    expenses_actual: float
    expenses_difference: float
    expenses_execution_percent: float

    # Profit calculations
    profit_planned: float  # Revenue - Expenses (planned)
    profit_actual: float   # Revenue - Expenses (actual)
    profit_difference: float

    # Profitability metrics
    profit_margin_planned: float  # Profit / Revenue * 100 (%)
    profit_margin_actual: float   # Profit / Revenue * 100 (%)
    roi_planned: float            # Profit / Expenses * 100 (%)
    roi_actual: float             # Profit / Expenses * 100 (%)

    # Monthly breakdown
    by_month: List[BudgetIncomeStatementMonthly]

    # Category breakdown (optional)
    revenue_by_category: Optional[List[BudgetIncomeStatementCategory]] = None
    expenses_by_category: Optional[List[BudgetIncomeStatementCategory]] = None


# ============================================================================
# Customer Metrics Analytics
# ============================================================================

class CustomerMetricsMonthly(BaseModel):
    """Monthly customer metrics"""
    month: int
    month_name: str
    total_customer_base: int
    active_customer_base: int
    coverage_rate: float  # АКБ/ОКБ * 100 (%)
    avg_order_value: float
    avg_order_value_regular: float
    avg_order_value_network: float
    avg_order_value_new: float


class CustomerMetricsByStream(BaseModel):
    """Customer metrics by revenue stream"""
    revenue_stream_id: int
    revenue_stream_name: str
    total_customer_base: int
    active_customer_base: int
    coverage_rate: float
    avg_order_value: float
    # Clinic segments
    regular_clinics: int
    network_clinics: int
    new_clinics: int


class CustomerMetricsAnalytics(BaseModel):
    """
    Customer Metrics Analytics (Аналитика клиентских метрик)

    Aggregated analytics showing:
    - ОКБ (Общая клиентская база) - Total Customer Base
    - АКБ (Активная клиентская база) - Active Customer Base
    - Покрытие (АКБ/ОКБ) - Coverage Rate
    - Средний чек по сегментам - Average Order Value by segments
    - Динамика по месяцам - Monthly trends
    - Разбивка по потокам доходов - Breakdown by revenue streams
    """
    year: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None

    # Summary totals
    total_customer_base: int
    active_customer_base: int
    coverage_rate: float  # %

    # Clinic segments totals
    regular_clinics: int
    network_clinics: int
    new_clinics: int

    # Average order values
    avg_order_value: float
    avg_order_value_regular: float
    avg_order_value_network: float
    avg_order_value_new: float

    # Growth metrics (compared to previous year)
    customer_base_growth: Optional[float] = None  # %
    active_base_growth: Optional[float] = None    # %
    avg_check_growth: Optional[float] = None      # %

    # Monthly breakdown
    by_month: List[CustomerMetricsMonthly]

    # Breakdown by revenue stream
    by_stream: Optional[List[CustomerMetricsByStream]] = None


# ============================================================================
# Revenue Analytics
# ============================================================================

class RevenueAnalyticsMonthly(BaseModel):
    """Monthly revenue analytics"""
    month: int
    month_name: str
    planned: float
    actual: float
    variance: float
    variance_percent: float
    execution_percent: float


class RevenueAnalyticsByStream(BaseModel):
    """Revenue analytics by stream (regional breakdown)"""
    revenue_stream_id: int
    revenue_stream_name: str
    stream_type: str  # REGIONAL, CHANNEL, PRODUCT
    planned: float
    actual: float
    variance: float
    variance_percent: float
    execution_percent: float
    share_of_total: float  # % of total revenue


class RevenueAnalyticsByCategory(BaseModel):
    """Revenue analytics by category (product mix)"""
    revenue_category_id: int
    revenue_category_name: str
    category_type: str  # PRODUCT, SERVICE, EQUIPMENT, TENDER
    planned: float
    actual: float
    variance: float
    variance_percent: float
    execution_percent: float
    share_of_total: float  # % of total revenue


class RevenueAnalytics(BaseModel):
    """
    Revenue Analytics (Аналитика доходов)

    Comprehensive revenue analytics showing:
    - Total revenue (planned vs actual)
    - Региональная разбивка (regional breakdown by revenue streams)
    - Продуктовый микс (product mix by revenue categories)
    - Помесячная динамика (monthly trends)
    - Growth metrics compared to previous year
    """
    year: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None

    # Summary totals
    total_planned: float
    total_actual: float
    total_variance: float
    total_variance_percent: float
    total_execution_percent: float

    # Growth metrics (compared to previous year)
    planned_growth: Optional[float] = None  # %
    actual_growth: Optional[float] = None   # %

    # Monthly breakdown
    by_month: List[RevenueAnalyticsMonthly]

    # Regional breakdown (by revenue streams)
    by_stream: Optional[List[RevenueAnalyticsByStream]] = None

    # Product mix (by revenue categories)
    by_category: Optional[List[RevenueAnalyticsByCategory]] = None
