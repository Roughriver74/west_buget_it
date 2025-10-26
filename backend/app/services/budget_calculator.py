"""
Budget Calculator Service for Budget Planning 2026 Module

Provides different calculation methods for budget planning:
1. Average method - Calculate based on average of base year
2. Growth method - Apply growth rate to base year
3. Driver-based method - Calculate based on business drivers (headcount, projects, etc.)
4. Seasonal method - Account for seasonal patterns
5. Manual method - User provides values directly
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Expense, BudgetCategory, ExpenseTypeEnum


class BudgetCalculator:
    """Budget calculation service with multiple methods"""

    def __init__(self, db: Session):
        self.db = db

    def get_baseline_data(
        self,
        category_id: int,
        base_year: int,
        department_id: int
    ) -> Dict[str, Any]:
        """
        Get baseline data from expenses for a category in base year

        Returns:
            Dict containing:
            - total_amount: Total expenses for the category
            - monthly_avg: Average monthly expense
            - monthly_breakdown: List of monthly amounts
            - capex_total: Total CAPEX
            - opex_total: Total OPEX
        """
        # Query all expenses for the category in base year
        expenses = self.db.query(Expense).filter(
            Expense.category_id == category_id,
            Expense.department_id == department_id,
            func.extract('year', Expense.request_date) == base_year
        ).all()

        if not expenses:
            return {
                "total_amount": Decimal("0"),
                "monthly_avg": Decimal("0"),
                "monthly_breakdown": [{"month": m, "amount": Decimal("0")} for m in range(1, 13)],
                "capex_total": Decimal("0"),
                "opex_total": Decimal("0"),
            }

        # Calculate total
        total_amount = sum(exp.amount for exp in expenses)

        # Calculate CAPEX/OPEX split (we'll need to add expense_type field to Expense model)
        # For now, assume we can infer from category or use a simple rule
        # TODO: Add expense_type field to Expense model in future migration
        capex_total = Decimal("0")
        opex_total = total_amount  # For now, assume all OPEX

        # Calculate monthly breakdown
        monthly_amounts = {}
        for exp in expenses:
            month = exp.request_date.month
            if month not in monthly_amounts:
                monthly_amounts[month] = Decimal("0")
            monthly_amounts[month] += exp.amount

        monthly_breakdown = [
            {"month": m, "amount": monthly_amounts.get(m, Decimal("0"))}
            for m in range(1, 13)
        ]

        monthly_avg = total_amount / 12

        return {
            "total_amount": total_amount,
            "monthly_avg": monthly_avg,
            "monthly_breakdown": monthly_breakdown,
            "capex_total": capex_total,
            "opex_total": opex_total,
        }

    def calculate_by_average(
        self,
        category_id: int,
        base_year: int,
        department_id: int,
        adjustment_percent: Decimal = Decimal("0"),
        target_year: int = 2026,
    ) -> Dict[str, Any]:
        """
        Calculate budget based on average of base year

        Args:
            category_id: Budget category ID
            base_year: Year to use as baseline (typically 2025)
            department_id: Department ID for multi-tenancy
            adjustment_percent: Adjustment percentage (e.g., 5 for +5%)
            target_year: Target year for budget (typically 2026)

        Returns:
            Dict containing calculation results
        """
        baseline = self.get_baseline_data(category_id, base_year, department_id)

        # Apply adjustment
        adjustment_factor = Decimal("1") + (adjustment_percent / Decimal("100"))
        adjusted_monthly_avg = baseline["monthly_avg"] * adjustment_factor
        annual_total = adjusted_monthly_avg * 12

        # Calculate growth percentage
        if baseline["total_amount"] > 0:
            growth_percent = ((annual_total - baseline["total_amount"]) / baseline["total_amount"]) * 100
        else:
            growth_percent = Decimal("0")

        # Monthly breakdown (equal distribution)
        monthly_breakdown = [
            {"month": m, "amount": adjusted_monthly_avg}
            for m in range(1, 13)
        ]

        return {
            "category_id": category_id,
            "annual_total": annual_total,
            "monthly_avg": adjusted_monthly_avg,
            "growth_percent": growth_percent,
            "monthly_breakdown": monthly_breakdown,
            "calculation_method": "average",
            "calculation_params": {
                "base_year": base_year,
                "adjustment_percent": float(adjustment_percent),
                "adjustment_factor": float(adjustment_factor),
            },
            "based_on_total": baseline["total_amount"],
            "based_on_avg": baseline["monthly_avg"],
        }

    def calculate_by_growth(
        self,
        category_id: int,
        base_year: int,
        department_id: int,
        growth_rate: Decimal,
        inflation_rate: Decimal = Decimal("0"),
        target_year: int = 2026,
    ) -> Dict[str, Any]:
        """
        Calculate budget with growth rate

        Args:
            category_id: Budget category ID
            base_year: Year to use as baseline
            department_id: Department ID
            growth_rate: Growth rate percentage (e.g., 10 for +10%)
            inflation_rate: Inflation rate percentage (e.g., 6 for +6%)
            target_year: Target year for budget

        Returns:
            Dict containing calculation results
        """
        baseline = self.get_baseline_data(category_id, base_year, department_id)

        # Apply growth and inflation
        total_adjustment = growth_rate + inflation_rate
        adjustment_factor = Decimal("1") + (total_adjustment / Decimal("100"))
        annual_total = baseline["total_amount"] * adjustment_factor
        monthly_avg = annual_total / 12

        # Calculate growth percentage
        if baseline["total_amount"] > 0:
            growth_percent = ((annual_total - baseline["total_amount"]) / baseline["total_amount"]) * 100
        else:
            growth_percent = Decimal("0")

        # Monthly breakdown (equal distribution)
        monthly_breakdown = [
            {"month": m, "amount": monthly_avg}
            for m in range(1, 13)
        ]

        return {
            "category_id": category_id,
            "annual_total": annual_total,
            "monthly_avg": monthly_avg,
            "growth_percent": growth_percent,
            "monthly_breakdown": monthly_breakdown,
            "calculation_method": "growth",
            "calculation_params": {
                "base_year": base_year,
                "growth_rate": float(growth_rate),
                "inflation_rate": float(inflation_rate),
                "total_adjustment": float(total_adjustment),
            },
            "based_on_total": baseline["total_amount"],
            "based_on_avg": baseline["monthly_avg"],
        }

    def calculate_by_driver(
        self,
        category_id: int,
        base_year: int,
        department_id: int,
        driver_type: str,
        base_driver_value: Decimal,
        planned_driver_value: Decimal,
        cost_per_unit: Optional[Decimal] = None,
        adjustment_percent: Decimal = Decimal("0"),
        target_year: int = 2026,
    ) -> Dict[str, Any]:
        """
        Calculate budget based on business drivers

        Args:
            category_id: Budget category ID
            base_year: Year to use as baseline
            department_id: Department ID
            driver_type: Type of driver (e.g., "headcount", "projects", "revenue")
            base_driver_value: Driver value in base year (e.g., 6 employees)
            planned_driver_value: Planned driver value (e.g., 7 employees)
            cost_per_unit: Cost per driver unit (if None, will calculate from baseline)
            adjustment_percent: Additional adjustment % (e.g., for salary indexation)
            target_year: Target year for budget

        Returns:
            Dict containing calculation results
        """
        baseline = self.get_baseline_data(category_id, base_year, department_id)

        # Calculate cost per unit if not provided
        if cost_per_unit is None:
            if base_driver_value > 0:
                cost_per_unit = baseline["total_amount"] / base_driver_value
            else:
                cost_per_unit = Decimal("0")

        # Calculate base annual total
        base_annual = cost_per_unit * planned_driver_value

        # Apply additional adjustment (e.g., salary indexation)
        adjustment_factor = Decimal("1") + (adjustment_percent / Decimal("100"))
        annual_total = base_annual * adjustment_factor
        monthly_avg = annual_total / 12

        # Calculate growth percentage
        if baseline["total_amount"] > 0:
            growth_percent = ((annual_total - baseline["total_amount"]) / baseline["total_amount"]) * 100
        else:
            growth_percent = Decimal("0")

        # Monthly breakdown (equal distribution)
        monthly_breakdown = [
            {"month": m, "amount": monthly_avg}
            for m in range(1, 13)
        ]

        return {
            "category_id": category_id,
            "annual_total": annual_total,
            "monthly_avg": monthly_avg,
            "growth_percent": growth_percent,
            "monthly_breakdown": monthly_breakdown,
            "calculation_method": "driver_based",
            "calculation_params": {
                "base_year": base_year,
                "driver_type": driver_type,
                "base_driver_value": float(base_driver_value),
                "planned_driver_value": float(planned_driver_value),
                "cost_per_unit": float(cost_per_unit),
                "adjustment_percent": float(adjustment_percent),
            },
            "based_on_total": baseline["total_amount"],
            "based_on_avg": baseline["monthly_avg"],
        }

    def calculate_seasonal_indices(
        self,
        category_id: int,
        base_year: int,
        department_id: int,
    ) -> List[Decimal]:
        """
        Calculate seasonal indices for a category based on historical data

        Returns a list of 12 indices (one per month), where 1.0 = average month
        """
        baseline = self.get_baseline_data(category_id, base_year, department_id)

        if baseline["monthly_avg"] == 0:
            # No data, return neutral indices
            return [Decimal("1.0") for _ in range(12)]

        # Calculate index for each month
        indices = []
        for month_data in baseline["monthly_breakdown"]:
            if baseline["monthly_avg"] > 0:
                index = month_data["amount"] / baseline["monthly_avg"]
            else:
                index = Decimal("1.0")
            indices.append(index)

        return indices
