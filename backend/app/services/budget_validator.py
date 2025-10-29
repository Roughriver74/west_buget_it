"""
Budget Validation Service
Validates expenses against approved budget baseline and generates alerts
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.db.models import (
    BudgetVersion,
    BudgetPlanDetail,
    Expense,
    ExpenseStatusEnum,
)


class BudgetValidationResult:
    """Result of budget validation"""

    def __init__(
        self,
        is_valid: bool,
        warnings: List[str] = None,
        errors: List[str] = None,
        budget_info: Dict[str, Any] = None
    ):
        self.is_valid = is_valid
        self.warnings = warnings or []
        self.errors = errors or []
        self.budget_info = budget_info or {}


class BudgetValidator:
    """Service for validating expenses against budget baseline"""

    def __init__(self, db: Session):
        self.db = db

    def get_baseline_for_year(self, year: int, department_id: int) -> Optional[BudgetVersion]:
        """Get baseline budget version for a given year and department"""
        return self.db.query(BudgetVersion).filter(
            BudgetVersion.year == year,
            BudgetVersion.department_id == department_id,
            BudgetVersion.is_baseline == True
        ).first()

    def get_category_monthly_budget(
        self,
        baseline_id: int,
        category_id: int,
        month: int
    ) -> Decimal:
        """Get planned budget for a specific category and month"""
        detail = self.db.query(BudgetPlanDetail).filter(
            BudgetPlanDetail.version_id == baseline_id,
            BudgetPlanDetail.category_id == category_id,
            BudgetPlanDetail.month == month
        ).first()

        return detail.planned_amount if detail else Decimal("0")

    def get_category_annual_budget(
        self,
        baseline_id: int,
        category_id: int
    ) -> Decimal:
        """Get total annual budget for a category"""
        total = self.db.query(
            func.sum(BudgetPlanDetail.planned_amount)
        ).filter(
            BudgetPlanDetail.version_id == baseline_id,
            BudgetPlanDetail.category_id == category_id
        ).scalar()

        return total or Decimal("0")

    def get_category_monthly_actual(
        self,
        category_id: int,
        year: int,
        month: int,
        department_id: int,
        exclude_expense_id: Optional[int] = None
    ) -> Decimal:
        """Get actual spent amount for category and month"""
        query = self.db.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.category_id == category_id,
            Expense.department_id == department_id,
            extract('year', Expense.request_date) == year,
            extract('month', Expense.request_date) == month,
            Expense.status.in_([ExpenseStatusEnum.PAID, ExpenseStatusEnum.PENDING])
        )

        if exclude_expense_id:
            query = query.filter(Expense.id != exclude_expense_id)

        total = query.scalar()
        return total or Decimal("0")

    def get_category_annual_actual(
        self,
        category_id: int,
        year: int,
        department_id: int,
        exclude_expense_id: Optional[int] = None
    ) -> Decimal:
        """Get total annual actual spent for category"""
        query = self.db.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.category_id == category_id,
            Expense.department_id == department_id,
            extract('year', Expense.request_date) == year,
            Expense.status.in_([ExpenseStatusEnum.PAID, ExpenseStatusEnum.PENDING])
        )

        if exclude_expense_id:
            query = query.filter(Expense.id != exclude_expense_id)

        total = query.scalar()
        return total or Decimal("0")

    def validate_expense(
        self,
        amount: Decimal,
        category_id: int,
        request_date: datetime,
        department_id: int,
        expense_id: Optional[int] = None
    ) -> BudgetValidationResult:
        """
        Validate an expense against budget baseline.

        Args:
            amount: Expense amount
            category_id: Budget category ID
            request_date: Expense request date
            department_id: Department ID
            expense_id: Optional expense ID to exclude (for updates)

        Returns:
            BudgetValidationResult with validation status and messages
        """
        year = request_date.year
        month = request_date.month

        # Get baseline version
        baseline = self.get_baseline_for_year(year, department_id)

        if not baseline:
            # No baseline - allow but warn
            return BudgetValidationResult(
                is_valid=True,
                warnings=[
                    f"Нет базовой версии бюджета для {year} года. "
                    f"Проверка лимитов недоступна."
                ]
            )

        # Get budgets
        monthly_budget = self.get_category_monthly_budget(
            baseline.id, category_id, month
        )
        annual_budget = self.get_category_annual_budget(
            baseline.id, category_id
        )

        # Get actuals (excluding current expense if updating)
        monthly_actual = self.get_category_monthly_actual(
            category_id, year, month, department_id, expense_id
        )
        annual_actual = self.get_category_annual_actual(
            category_id, year, department_id, expense_id
        )

        # Calculate new totals with this expense
        new_monthly_total = monthly_actual + amount
        new_annual_total = annual_actual + amount

        # Calculate percentages
        monthly_percent = (new_monthly_total / monthly_budget * 100) if monthly_budget > 0 else 0
        annual_percent = (new_annual_total / annual_budget * 100) if annual_budget > 0 else 0

        warnings = []
        errors = []

        # Monthly budget checks
        if monthly_budget > 0:
            if new_monthly_total > monthly_budget:
                monthly_overrun = new_monthly_total - monthly_budget
                errors.append(
                    f"Превышение месячного бюджета: {monthly_overrun:,.2f} ₽ "
                    f"({monthly_percent:.1f}% от лимита)"
                )
            elif monthly_percent >= 90:
                warnings.append(
                    f"Приближение к месячному лимиту: {monthly_percent:.1f}% "
                    f"({new_monthly_total:,.2f} / {monthly_budget:,.2f} ₽)"
                )

        # Annual budget checks
        if annual_budget > 0:
            if new_annual_total > annual_budget:
                annual_overrun = new_annual_total - annual_budget
                errors.append(
                    f"Превышение годового бюджета: {annual_overrun:,.2f} ₽ "
                    f"({annual_percent:.1f}% от лимита)"
                )
            elif annual_percent >= 90:
                warnings.append(
                    f"Приближение к годовому лимиту: {annual_percent:.1f}% "
                    f"({new_annual_total:,.2f} / {annual_budget:,.2f} ₽)"
                )

        # Budget info for reference
        budget_info = {
            "baseline_version_id": baseline.id,
            "baseline_version_name": baseline.version_name,
            "monthly_budget": float(monthly_budget),
            "monthly_actual": float(monthly_actual),
            "monthly_new_total": float(new_monthly_total),
            "monthly_percent": float(monthly_percent),
            "annual_budget": float(annual_budget),
            "annual_actual": float(annual_actual),
            "annual_new_total": float(new_annual_total),
            "annual_percent": float(annual_percent),
        }

        # Determine if valid (no errors)
        is_valid = len(errors) == 0

        return BudgetValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            budget_info=budget_info
        )

    def get_budget_status(
        self,
        year: int,
        department_id: int,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get current budget status for department.

        Args:
            year: Year to check
            department_id: Department ID
            category_id: Optional category filter

        Returns:
            Dictionary with budget status information
        """
        baseline = self.get_baseline_for_year(year, department_id)

        if not baseline:
            return {
                "has_baseline": False,
                "message": f"Нет базовой версии бюджета для {year} года"
            }

        # Get all plan details
        query = self.db.query(BudgetPlanDetail).filter(
            BudgetPlanDetail.version_id == baseline.id
        )

        if category_id:
            query = query.filter(BudgetPlanDetail.category_id == category_id)

        plan_details = query.all()

        # Calculate status
        categories_at_risk = []
        categories_over_budget = []

        for detail in plan_details:
            actual = self.get_category_monthly_actual(
                detail.category_id,
                year,
                detail.month,
                department_id
            )

            if detail.planned_amount > 0:
                percent = (actual / detail.planned_amount) * 100

                if percent > 100:
                    categories_over_budget.append({
                        "category_id": detail.category_id,
                        "month": detail.month,
                        "planned": float(detail.planned_amount),
                        "actual": float(actual),
                        "percent": float(percent)
                    })
                elif percent >= 90:
                    categories_at_risk.append({
                        "category_id": detail.category_id,
                        "month": detail.month,
                        "planned": float(detail.planned_amount),
                        "actual": float(actual),
                        "percent": float(percent)
                    })

        return {
            "has_baseline": True,
            "baseline_version_id": baseline.id,
            "baseline_version_name": baseline.version_name,
            "categories_over_budget": categories_over_budget,
            "categories_at_risk": categories_at_risk,
            "total_over_budget": len(categories_over_budget),
            "total_at_risk": len(categories_at_risk)
        }
