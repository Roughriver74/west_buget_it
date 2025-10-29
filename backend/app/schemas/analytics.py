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
