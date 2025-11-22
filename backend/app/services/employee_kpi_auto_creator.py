"""
Service for automatic creation of EmployeeKPI records

Automatically creates EmployeeKPI records for active employees at the start of each month
"""
import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import (
    Employee,
    EmployeeKPI,
    EmployeeKPIGoal,
    KPIGoal,
    Department,
    EmployeeKPIStatusEnum
)

logger = logging.getLogger(__name__)


class EmployeeKPIAutoCreator:
    """Service for automatic creation of EmployeeKPI records"""

    def __init__(self, db: Session):
        self.db = db

    def create_monthly_kpis(
        self,
        year: int,
        month: int,
        department_id: int = None
    ) -> Dict[str, int]:
        """
        Create EmployeeKPI records for all active employees for specified year/month

        Args:
            year: Year for KPI records
            month: Month for KPI records (1-12)
            department_id: Optional department filter (None = all departments)

        Returns:
            dict: Statistics of created records
        """
        logger.info(
            f"Starting automatic EmployeeKPI creation for {year}-{month:02d}"
            f"{f' (department_id={department_id})' if department_id else ' (all departments)'}"
        )

        # Query active employees
        employee_query = self.db.query(Employee).filter(Employee.is_active == True)

        if department_id:
            employee_query = employee_query.filter(Employee.department_id == department_id)

        active_employees = employee_query.all()

        logger.info(f"Found {len(active_employees)} active employees")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for employee in active_employees:
            try:
                # Check if EmployeeKPI already exists for this employee/year/month
                existing_kpi = self.db.query(EmployeeKPI).filter(
                    and_(
                        EmployeeKPI.employee_id == employee.id,
                        EmployeeKPI.year == year,
                        EmployeeKPI.month == month
                    )
                ).first()

                if existing_kpi:
                    logger.debug(
                        f"EmployeeKPI already exists for employee {employee.id} "
                        f"({employee.full_name}) for {year}-{month:02d}"
                    )
                    skipped_count += 1
                    continue

                # Create new EmployeeKPI record
                new_kpi = self._create_employee_kpi(employee, year, month)

                # Copy goals from previous month or create default goals
                self._copy_or_create_goals(employee, new_kpi, year, month)

                self.db.commit()

                logger.info(
                    f"Created EmployeeKPI for employee {employee.id} ({employee.full_name}) "
                    f"for {year}-{month:02d}"
                )
                created_count += 1

            except Exception as e:
                logger.error(
                    f"Error creating EmployeeKPI for employee {employee.id} ({employee.full_name}): {e}",
                    exc_info=True
                )
                self.db.rollback()
                error_count += 1

        result = {
            "total_employees": len(active_employees),
            "created": created_count,
            "skipped": skipped_count,
            "errors": error_count
        }

        logger.info(
            f"EmployeeKPI auto-creation completed: {created_count} created, "
            f"{skipped_count} skipped, {error_count} errors"
        )

        return result

    def _create_employee_kpi(
        self,
        employee: Employee,
        year: int,
        month: int
    ) -> EmployeeKPI:
        """Create new EmployeeKPI record"""
        new_kpi = EmployeeKPI(
            employee_id=employee.id,
            department_id=employee.department_id,
            year=year,
            month=month,
            status=EmployeeKPIStatusEnum.DRAFT,
            # Bonus fields will be calculated when goals are set and approved
            monthly_bonus_performance=0.0,
            quarterly_bonus_performance=0.0,
            annual_bonus_performance=0.0,
            kpi_percentage_performance=0.0
        )

        self.db.add(new_kpi)
        self.db.flush()  # Get ID for new_kpi

        return new_kpi

    def _copy_or_create_goals(
        self,
        employee: Employee,
        new_kpi: EmployeeKPI,
        year: int,
        month: int
    ):
        """
        Copy goals from previous month or create default goals for employee

        Logic:
        1. Try to find EmployeeKPI from previous month
        2. If found, copy goals (without actual values)
        3. If not found, get default goals for employee's department
        """
        # Find previous month's KPI
        previous_month = month - 1 if month > 1 else 12
        previous_year = year if month > 1 else year - 1

        previous_kpi = self.db.query(EmployeeKPI).filter(
            and_(
                EmployeeKPI.employee_id == employee.id,
                EmployeeKPI.year == previous_year,
                EmployeeKPI.month == previous_month
            )
        ).first()

        if previous_kpi:
            # Copy goals from previous month
            previous_goals = self.db.query(EmployeeKPIGoal).filter(
                EmployeeKPIGoal.employee_kpi_id == previous_kpi.id
            ).all()

            logger.debug(
                f"Copying {len(previous_goals)} goals from previous month "
                f"({previous_year}-{previous_month:02d})"
            )

            for prev_goal in previous_goals:
                new_goal = EmployeeKPIGoal(
                    employee_kpi_id=new_kpi.id,
                    kpi_goal_id=prev_goal.kpi_goal_id,
                    target_value=prev_goal.target_value,
                    weight=prev_goal.weight,
                    actual_value=0.0,  # Reset actual value
                    achievement_percentage=0.0  # Reset achievement
                )
                self.db.add(new_goal)

        else:
            # No previous KPI - create default goals from department's active KPI goals
            logger.debug(
                f"No previous KPI found, creating default goals for department {employee.department_id}"
            )

            default_goals = self.db.query(KPIGoal).filter(
                and_(
                    KPIGoal.department_id == employee.department_id,
                    KPIGoal.is_active == True
                )
            ).all()

            # If there are default goals, distribute weights equally
            if default_goals:
                weight_per_goal = 100.0 / len(default_goals)

                for kpi_goal in default_goals:
                    new_goal = EmployeeKPIGoal(
                        employee_kpi_id=new_kpi.id,
                        kpi_goal_id=kpi_goal.id,
                        target_value=0.0,  # Manager will set this
                        weight=weight_per_goal,
                        actual_value=0.0,
                        achievement_percentage=0.0
                    )
                    self.db.add(new_goal)

                logger.debug(f"Created {len(default_goals)} default goals with weight {weight_per_goal:.2f}%")
            else:
                logger.warning(
                    f"No active KPI goals found for department {employee.department_id}. "
                    f"EmployeeKPI created without goals."
                )
