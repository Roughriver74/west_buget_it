"""
Service for payment forecasting and analysis
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from decimal import Decimal
from collections import defaultdict

from app.db.models import Expense, ExpenseStatusEnum, PayrollPlan, PayrollActual


ForecastMethod = Literal["simple_average", "moving_average", "seasonal"]


class PaymentForecastService:
    """Service for generating payment forecasts based on historical data"""

    def __init__(self, db: Session):
        self.db = db

    def get_payment_calendar(
        self,
        year: int,
        month: int,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get calendar view of payments for a specific month

        Returns list of days with payments and totals
        """
        # Build query filters
        filters = [
            extract('year', Expense.payment_date) == year,
            extract('month', Expense.payment_date) == month,
            Expense.is_paid == True,
        ]

        if department_id:
            filters.append(Expense.department_id == department_id)
        if category_id:
            filters.append(Expense.category_id == category_id)
        if organization_id:
            filters.append(Expense.organization_id == organization_id)

        # Query payments grouped by day
        query = (
            self.db.query(
                func.date(Expense.payment_date).label('payment_day'),
                func.sum(Expense.amount).label('total_amount'),
                func.count(Expense.id).label('payment_count'),
            )
            .filter(and_(*filters))
            .group_by(func.date(Expense.payment_date))
            .order_by(func.date(Expense.payment_date))
        )

        results = query.all()

        # Convert to dict format
        calendar_data = []
        for row in results:
            calendar_data.append({
                'date': row.payment_day.isoformat(),
                'total_amount': float(row.total_amount),
                'payment_count': row.payment_count,
                'is_forecast': False,
            })

        # Add actual payroll payments (FOT) from PayrollActual
        # Query actual payroll payments grouped by payment_date
        actual_payroll_query = self.db.query(
            func.date(PayrollActual.payment_date).label('payment_day'),
            func.sum(PayrollActual.total_paid).label('total_paid'),
            func.count(PayrollActual.id).label('employee_count')
        ).filter(
            PayrollActual.year == year,
            PayrollActual.month == month,
            PayrollActual.payment_date.isnot(None)
        )

        if department_id:
            actual_payroll_query = actual_payroll_query.filter(PayrollActual.department_id == department_id)

        actual_payroll_results = actual_payroll_query.group_by(func.date(PayrollActual.payment_date)).all()

        # Add actual payroll payments to calendar
        for row in actual_payroll_results:
            calendar_data.append({
                'date': row.payment_day.isoformat(),
                'total_amount': float(row.total_paid),
                'payment_count': row.employee_count,
                'is_forecast': False,
                'payment_type': 'payroll_actual',
            })

        # Sort by date
        calendar_data.sort(key=lambda x: x['date'])

        return calendar_data

    def get_payments_by_day(
        self,
        date: datetime,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        include_forecast: bool = True,
    ):
        """
        Get all payments for a specific day
        Returns: dict with 'expenses' list and optional 'payroll_forecast' data
        """
        filters = [
            func.date(Expense.payment_date) == date.date(),
            Expense.is_paid == True,
        ]

        if department_id:
            filters.append(Expense.department_id == department_id)
        if category_id:
            filters.append(Expense.category_id == category_id)
        if organization_id:
            filters.append(Expense.organization_id == organization_id)

        expenses = self.db.query(Expense).filter(and_(*filters)).all()

        result = {
            'expenses': expenses,
            'payroll_forecast': None
        }

        # Check for actual payroll payments on this date
        actual_payroll_query = self.db.query(
            func.sum(PayrollActual.total_paid).label('total_paid'),
            func.count(PayrollActual.id).label('employee_count')
        ).filter(
            func.date(PayrollActual.payment_date) == date.date()
        )

        if department_id:
            actual_payroll_query = actual_payroll_query.filter(PayrollActual.department_id == department_id)

        actual_payroll_result = actual_payroll_query.first()

        # If actual payroll payments exist for this date, show them
        if actual_payroll_result and actual_payroll_result.total_paid:
            result['payroll_forecast'] = {
                'amount': float(actual_payroll_result.total_paid),
                'employee_count': actual_payroll_result.employee_count,
                'type': 'payroll_actual',
                'description': f"Фактическая выплата зарплаты ({actual_payroll_result.employee_count} сотрудников)"
            }

        return result

    def generate_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        method: ForecastMethod = "simple_average",
        lookback_days: int = 90,
        category_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Generate payment forecast for future period

        Args:
            start_date: Start of forecast period
            end_date: End of forecast period
            method: Forecasting method to use
            lookback_days: Number of days to look back for historical data
            category_id: Optional category filter
            organization_id: Optional organization filter
        """
        # Get historical data
        historical_start = start_date - timedelta(days=lookback_days)
        historical_payments = self._get_historical_payments(
            historical_start,
            start_date,
            category_id,
            organization_id,
        )

        # Generate forecast based on method
        if method == "simple_average":
            return self._forecast_simple_average(
                historical_payments,
                start_date,
                end_date,
            )
        elif method == "moving_average":
            return self._forecast_moving_average(
                historical_payments,
                start_date,
                end_date,
                window_days=30,
            )
        elif method == "seasonal":
            return self._forecast_seasonal(
                historical_payments,
                start_date,
                end_date,
            )
        else:
            raise ValueError(f"Unknown forecast method: {method}")

    def _get_historical_payments(
        self,
        start_date: datetime,
        end_date: datetime,
        category_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> List[Dict]:
        """Get historical payment data"""
        filters = [
            Expense.payment_date >= start_date,
            Expense.payment_date < end_date,
            Expense.is_paid == True,
        ]

        if category_id:
            filters.append(Expense.category_id == category_id)
        if organization_id:
            filters.append(Expense.organization_id == organization_id)

        query = (
            self.db.query(
                func.date(Expense.payment_date).label('payment_day'),
                func.sum(Expense.amount).label('total_amount'),
                func.count(Expense.id).label('payment_count'),
            )
            .filter(and_(*filters))
            .group_by(func.date(Expense.payment_date))
            .order_by(func.date(Expense.payment_date))
        )

        results = query.all()
        return [
            {
                'date': row.payment_day,
                'amount': float(row.total_amount),
                'count': row.payment_count,
            }
            for row in results
        ]

    def _forecast_simple_average(
        self,
        historical_data: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Simple average forecast - average daily payment"""
        if not historical_data:
            return []

        # Calculate average daily payment
        total_amount = sum(item['amount'] for item in historical_data)
        avg_daily = total_amount / len(historical_data)

        # Calculate weekday pattern
        weekday_totals = defaultdict(list)
        for item in historical_data:
            weekday = item['date'].weekday()
            weekday_totals[weekday].append(item['amount'])

        weekday_avg = {}
        for weekday, amounts in weekday_totals.items():
            weekday_avg[weekday] = sum(amounts) / len(amounts)

        # Generate forecast
        forecast = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            weekday = current_date.weekday()

            # Use weekday average if available, otherwise overall average
            predicted_amount = weekday_avg.get(weekday, avg_daily)

            # Confidence based on data availability
            confidence = self._calculate_confidence(
                len(historical_data),
                weekday in weekday_avg,
            )

            forecast.append({
                'date': current_date.isoformat(),
                'predicted_amount': round(predicted_amount, 2),
                'confidence': confidence,
                'method': 'simple_average',
            })

            current_date += timedelta(days=1)

        return forecast

    def _forecast_moving_average(
        self,
        historical_data: List[Dict],
        start_date: datetime,
        end_date: datetime,
        window_days: int = 30,
    ) -> List[Dict]:
        """Moving average forecast"""
        if not historical_data:
            return []

        # Calculate moving average from most recent data
        recent_data = sorted(historical_data, key=lambda x: x['date'])[-window_days:]
        avg_amount = sum(item['amount'] for item in recent_data) / len(recent_data)

        # Generate forecast with constant value
        forecast = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            confidence = self._calculate_confidence(
                len(recent_data),
                True,
            )

            forecast.append({
                'date': current_date.isoformat(),
                'predicted_amount': round(avg_amount, 2),
                'confidence': confidence,
                'method': 'moving_average',
            })

            current_date += timedelta(days=1)

        return forecast

    def _forecast_seasonal(
        self,
        historical_data: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Seasonal forecast - considers day of week and day of month patterns"""
        if not historical_data:
            return []

        # Group by day of month and weekday
        day_of_month_totals = defaultdict(list)
        weekday_totals = defaultdict(list)

        for item in historical_data:
            day_of_month = item['date'].day
            weekday = item['date'].weekday()
            day_of_month_totals[day_of_month].append(item['amount'])
            weekday_totals[weekday].append(item['amount'])

        # Calculate averages
        day_of_month_avg = {
            day: sum(amounts) / len(amounts)
            for day, amounts in day_of_month_totals.items()
        }
        weekday_avg = {
            day: sum(amounts) / len(amounts)
            for day, amounts in weekday_totals.items()
        }

        # Overall average as fallback
        overall_avg = sum(item['amount'] for item in historical_data) / len(historical_data)

        # Generate forecast
        forecast = []
        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            day_of_month = current_date.day
            weekday = current_date.weekday()

            # Combine day of month and weekday patterns
            dom_value = day_of_month_avg.get(day_of_month, overall_avg)
            wd_value = weekday_avg.get(weekday, overall_avg)

            # Weight both factors
            predicted_amount = (dom_value * 0.6 + wd_value * 0.4)

            confidence = self._calculate_confidence(
                len(historical_data),
                day_of_month in day_of_month_avg and weekday in weekday_avg,
            )

            forecast.append({
                'date': current_date.isoformat(),
                'predicted_amount': round(predicted_amount, 2),
                'confidence': confidence,
                'method': 'seasonal',
            })

            current_date += timedelta(days=1)

        return forecast

    def _calculate_confidence(
        self,
        data_points: int,
        has_pattern: bool,
    ) -> str:
        """Calculate confidence level based on available data"""
        if data_points < 30:
            return 'low'
        elif data_points < 60:
            return 'medium' if has_pattern else 'low'
        else:
            return 'high' if has_pattern else 'medium'

    def get_forecast_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        category_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Dict:
        """Get summary statistics for forecast period"""
        # Get forecasts using different methods
        simple_forecast = self.generate_forecast(
            start_date,
            end_date,
            method="simple_average",
            category_id=category_id,
            organization_id=organization_id,
        )

        moving_forecast = self.generate_forecast(
            start_date,
            end_date,
            method="moving_average",
            category_id=category_id,
            organization_id=organization_id,
        )

        seasonal_forecast = self.generate_forecast(
            start_date,
            end_date,
            method="seasonal",
            category_id=category_id,
            organization_id=organization_id,
        )

        # Calculate summary
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'forecasts': {
                'simple_average': {
                    'total': sum(item['predicted_amount'] for item in simple_forecast),
                    'daily_avg': sum(item['predicted_amount'] for item in simple_forecast) / len(simple_forecast) if simple_forecast else 0,
                },
                'moving_average': {
                    'total': sum(item['predicted_amount'] for item in moving_forecast),
                    'daily_avg': sum(item['predicted_amount'] for item in moving_forecast) / len(moving_forecast) if moving_forecast else 0,
                },
                'seasonal': {
                    'total': sum(item['predicted_amount'] for item in seasonal_forecast),
                    'daily_avg': sum(item['predicted_amount'] for item in seasonal_forecast) / len(seasonal_forecast) if seasonal_forecast else 0,
                },
            }
        }
