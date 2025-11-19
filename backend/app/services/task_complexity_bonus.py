"""
Task Complexity Bonus Calculator Service

Calculates bonus component based on completed task complexity.
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models import KPITask, EmployeeKPI, KPITaskStatusEnum


class TaskComplexityBonusCalculator:
    """
    Calculates bonus component based on task complexity for employees.

    Complexity multiplier formula:
    - Tasks 1-3 (simple): multiplier 0.70-0.85
    - Tasks 4-6 (medium): multiplier 0.85-1.00
    - Tasks 7-10 (complex): multiplier 1.00-1.30

    Bonus component: base_bonus * complexity_multiplier * complexity_weight
    """

    # Complexity tiers and multipliers
    COMPLEXITY_TIERS = {
        "simple": {"range": (1, 3), "multiplier_range": (0.70, 0.85)},
        "medium": {"range": (4, 6), "multiplier_range": (0.85, 1.00)},
        "complex": {"range": (7, 10), "multiplier_range": (1.00, 1.30)},
    }

    # Default complexity weight in total bonus (20%)
    DEFAULT_COMPLEXITY_WEIGHT = Decimal("20.00")

    def __init__(self, db: Session):
        self.db = db

    def calculate_complexity_multiplier(self, avg_complexity: Decimal) -> Decimal:
        """
        Calculate complexity multiplier based on average task complexity.

        Args:
            avg_complexity: Average complexity of completed tasks (1-10 scale)

        Returns:
            Complexity multiplier (0.70-1.30)
        """
        if avg_complexity is None:
            return Decimal("1.00")  # Neutral multiplier

        complexity_float = float(avg_complexity)

        # Determine tier
        if 1 <= complexity_float <= 3:
            # Simple tasks: linear interpolation 0.70-0.85
            tier = self.COMPLEXITY_TIERS["simple"]
            min_mult, max_mult = tier["multiplier_range"]
            progress = (complexity_float - 1) / 2  # 0-1 scale within tier
            multiplier = min_mult + (max_mult - min_mult) * progress

        elif 4 <= complexity_float <= 6:
            # Medium tasks: linear interpolation 0.85-1.00
            tier = self.COMPLEXITY_TIERS["medium"]
            min_mult, max_mult = tier["multiplier_range"]
            progress = (complexity_float - 4) / 2  # 0-1 scale within tier
            multiplier = min_mult + (max_mult - min_mult) * progress

        elif 7 <= complexity_float <= 10:
            # Complex tasks: linear interpolation 1.00-1.30
            tier = self.COMPLEXITY_TIERS["complex"]
            min_mult, max_mult = tier["multiplier_range"]
            progress = (complexity_float - 7) / 3  # 0-1 scale within tier
            multiplier = min_mult + (max_mult - min_mult) * progress

        else:
            # Out of range: neutral multiplier
            multiplier = 1.00

        return Decimal(str(round(multiplier, 4)))

    def get_completed_tasks_avg_complexity(
        self,
        employee_id: int,
        year: int,
        month: int,
        department_id: int
    ) -> Optional[Decimal]:
        """
        Get average complexity of tasks completed in given period.

        Args:
            employee_id: Employee ID
            year: Year
            month: Month (1-12)
            department_id: Department ID

        Returns:
            Average complexity or None if no completed tasks
        """
        # Get completed tasks in period
        result = self.db.query(func.avg(KPITask.complexity)).filter(
            and_(
                KPITask.employee_id == employee_id,
                KPITask.department_id == department_id,
                KPITask.status == KPITaskStatusEnum.DONE,
                KPITask.complexity.isnot(None),
                func.extract('year', KPITask.completed_at) == year,
                func.extract('month', KPITask.completed_at) == month,
            )
        ).scalar()

        return Decimal(str(result)) if result else None

    def calculate_complexity_bonus(
        self,
        base_bonus: Decimal,
        avg_complexity: Optional[Decimal],
        complexity_weight: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate complexity bonus component.

        Args:
            base_bonus: Base bonus amount
            avg_complexity: Average task complexity (1-10)
            complexity_weight: Weight of complexity component in total bonus (0-100%)

        Returns:
            Dictionary with:
            - complexity_multiplier: Calculated multiplier
            - complexity_bonus: Bonus component amount
            - avg_complexity: Average complexity used
        """
        if complexity_weight is None:
            complexity_weight = self.DEFAULT_COMPLEXITY_WEIGHT

        # Calculate multiplier
        multiplier = self.calculate_complexity_multiplier(avg_complexity)

        # Calculate bonus component
        # Formula: base_bonus * multiplier * (weight / 100)
        complexity_bonus = base_bonus * multiplier * (complexity_weight / Decimal("100.00"))

        return {
            "avg_complexity": avg_complexity,
            "complexity_multiplier": multiplier,
            "complexity_weight": complexity_weight,
            "complexity_bonus": round(complexity_bonus, 2),
        }

    def update_employee_kpi_complexity_data(
        self,
        employee_kpi: EmployeeKPI,
        employee_id: int,
        year: int,
        month: int
    ) -> EmployeeKPI:
        """
        Update EmployeeKPI record with calculated complexity data.

        Args:
            employee_kpi: EmployeeKPI record to update
            employee_id: Employee ID
            year: Year
            month: Month

        Returns:
            Updated EmployeeKPI record
        """
        # Get average complexity from completed tasks
        avg_complexity = self.get_completed_tasks_avg_complexity(
            employee_id=employee_id,
            year=year,
            month=month,
            department_id=employee_kpi.department_id
        )

        # Update basic complexity data
        employee_kpi.task_complexity_avg = avg_complexity

        if avg_complexity is not None:
            multiplier = self.calculate_complexity_multiplier(avg_complexity)
            employee_kpi.task_complexity_multiplier = multiplier

            # Calculate complexity bonus components
            if employee_kpi.monthly_bonus_base:
                monthly_result = self.calculate_complexity_bonus(
                    base_bonus=employee_kpi.monthly_bonus_base,
                    avg_complexity=avg_complexity,
                    complexity_weight=employee_kpi.task_complexity_weight
                )
                employee_kpi.monthly_bonus_complexity = monthly_result["complexity_bonus"]

            if employee_kpi.quarterly_bonus_base:
                quarterly_result = self.calculate_complexity_bonus(
                    base_bonus=employee_kpi.quarterly_bonus_base,
                    avg_complexity=avg_complexity,
                    complexity_weight=employee_kpi.task_complexity_weight
                )
                employee_kpi.quarterly_bonus_complexity = quarterly_result["complexity_bonus"]

            if employee_kpi.annual_bonus_base:
                annual_result = self.calculate_complexity_bonus(
                    base_bonus=employee_kpi.annual_bonus_base,
                    avg_complexity=avg_complexity,
                    complexity_weight=employee_kpi.task_complexity_weight
                )
                employee_kpi.annual_bonus_complexity = annual_result["complexity_bonus"]

        return employee_kpi

    def bulk_update_complexity_bonuses(
        self,
        year: int,
        month: int,
        department_id: int
    ) -> Dict[str, int]:
        """
        Bulk update complexity bonuses for all employee KPIs in period.

        Args:
            year: Year
            month: Month
            department_id: Department ID

        Returns:
            Dictionary with statistics: updated_count, skipped_count
        """
        # Get all employee KPIs for period
        employee_kpis = self.db.query(EmployeeKPI).filter(
            and_(
                EmployeeKPI.year == year,
                EmployeeKPI.month == month,
                EmployeeKPI.department_id == department_id
            )
        ).all()

        updated_count = 0
        skipped_count = 0

        for employee_kpi in employee_kpis:
            # Update complexity data
            self.update_employee_kpi_complexity_data(
                employee_kpi=employee_kpi,
                employee_id=employee_kpi.employee_id,
                year=year,
                month=month
            )

            if employee_kpi.task_complexity_avg is not None:
                updated_count += 1
            else:
                skipped_count += 1

        self.db.commit()

        return {
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "total_count": len(employee_kpis)
        }
