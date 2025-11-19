"""
KPI Validation Service

Provides business logic validation for KPI records to ensure data consistency and integrity.
"""

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import EmployeeKPI, EmployeeKPIGoal, KPIGoal


class KPIValidationError(Exception):
    """Custom exception for KPI validation errors"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class KPIValidationService:
    """Service for validating KPI data"""

    # Constants
    KPI_PERCENTAGE_MIN = Decimal("0")
    KPI_PERCENTAGE_MAX = Decimal("200")
    FIXED_PART_MIN = Decimal("0")
    FIXED_PART_MAX = Decimal("100")
    DEPREMIUM_THRESHOLD_MIN = Decimal("0")
    DEPREMIUM_THRESHOLD_MAX = Decimal("100")
    BONUS_BASE_MIN = Decimal("0")
    TOLERANCE = Decimal("0.01")  # Tolerance for floating point comparison (1%)

    def __init__(self, db: Session):
        self.db = db

    def validate_kpi_percentage(self, kpi_percentage: Optional[Decimal]) -> None:
        """
        Validate KPI percentage is within acceptable range (0-200%).

        Args:
            kpi_percentage: KPI percentage to validate

        Raises:
            KPIValidationError: If validation fails
        """
        if kpi_percentage is None:
            return  # Allow None for draft records

        if kpi_percentage < self.KPI_PERCENTAGE_MIN:
            raise KPIValidationError(
                "kpi_percentage",
                f"KPI% не может быть меньше {self.KPI_PERCENTAGE_MIN}%"
            )

        if kpi_percentage > self.KPI_PERCENTAGE_MAX:
            raise KPIValidationError(
                "kpi_percentage",
                f"KPI% не может быть больше {self.KPI_PERCENTAGE_MAX}%"
            )

    def validate_fixed_part(self, fixed_part: Optional[Decimal], bonus_type: str) -> None:
        """
        Validate fixed part percentage for MIXED bonus type.

        Args:
            fixed_part: Fixed part percentage to validate
            bonus_type: Type of bonus (FIXED, PERFORMANCE_BASED, MIXED)

        Raises:
            KPIValidationError: If validation fails
        """
        if bonus_type != "MIXED":
            return  # Fixed part only applies to MIXED type

        if fixed_part is None:
            raise KPIValidationError(
                "fixed_part",
                "Для типа премии MIXED необходимо указать фиксированную часть (0-100%)"
            )

        if fixed_part < self.FIXED_PART_MIN or fixed_part > self.FIXED_PART_MAX:
            raise KPIValidationError(
                "fixed_part",
                f"Фиксированная часть должна быть в диапазоне {self.FIXED_PART_MIN}-{self.FIXED_PART_MAX}%"
            )

    def validate_depremium_threshold(self, threshold: Optional[Decimal]) -> None:
        """
        Validate depremium threshold is within acceptable range.

        Args:
            threshold: Depremium threshold to validate

        Raises:
            KPIValidationError: If validation fails
        """
        if threshold is None:
            return  # Use default if not specified

        if threshold < self.DEPREMIUM_THRESHOLD_MIN or threshold > self.DEPREMIUM_THRESHOLD_MAX:
            raise KPIValidationError(
                "depremium_threshold",
                f"Порог депремирования должен быть в диапазоне {self.DEPREMIUM_THRESHOLD_MIN}-{self.DEPREMIUM_THRESHOLD_MAX}%"
            )

    def validate_bonus_base(self, bonus_base: Optional[Decimal], bonus_name: str) -> None:
        """
        Validate bonus base amount is non-negative.

        Args:
            bonus_base: Bonus base amount to validate
            bonus_name: Name of bonus for error message

        Raises:
            KPIValidationError: If validation fails
        """
        if bonus_base is None:
            return  # Allow None

        if bonus_base < self.BONUS_BASE_MIN:
            raise KPIValidationError(
                f"{bonus_name}_base",
                f"Базовая сумма {bonus_name} не может быть отрицательной"
            )

    def validate_goal_weights(self, employee_kpi_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that goal weights sum to 100%.

        Args:
            employee_kpi_id: EmployeeKPI ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        goals = self.db.query(EmployeeKPIGoal).filter(
            EmployeeKPIGoal.employee_kpi_id == employee_kpi_id
        ).all()

        if not goals:
            return True, None  # No goals assigned yet

        total_weight = sum(Decimal(str(goal.weight or 0)) for goal in goals)

        # Allow tolerance for floating point comparison
        if abs(total_weight - Decimal("100")) > self.TOLERANCE:
            return False, f"Сумма весов целей ({total_weight}%) должна равняться 100%"

        return True, None

    def validate_kpi_consistency(self, employee_kpi_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that KPI percentage matches weighted sum of goal achievements.

        Args:
            employee_kpi_id: EmployeeKPI ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        employee_kpi = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.id == employee_kpi_id
        ).first()

        if not employee_kpi or employee_kpi.kpi_percentage is None:
            return True, None  # Skip validation for draft records

        goals = self.db.query(EmployeeKPIGoal).filter(
            EmployeeKPIGoal.employee_kpi_id == employee_kpi_id
        ).all()

        if not goals:
            return True, None  # No goals assigned, manual KPI% entry allowed

        # Calculate weighted sum of achievements
        total_weighted_achievement = Decimal("0")
        total_weight = Decimal("0")

        for goal in goals:
            if goal.achievement_percentage is not None and goal.weight is not None:
                achievement = Decimal(str(goal.achievement_percentage))
                weight = Decimal(str(goal.weight))
                total_weighted_achievement += achievement * weight
                total_weight += weight

        if total_weight == 0:
            return True, None  # No weights assigned yet

        calculated_kpi = total_weighted_achievement / total_weight
        actual_kpi = Decimal(str(employee_kpi.kpi_percentage))

        # Allow tolerance for floating point comparison
        if abs(calculated_kpi - actual_kpi) > self.TOLERANCE:
            return False, (
                f"KPI% ({actual_kpi}%) не соответствует расчетному значению "
                f"на основе целей ({calculated_kpi:.2f}%). "
                f"Проверьте достижения по целям."
            )

        return True, None

    def validate_employee_kpi(
        self,
        employee_kpi: EmployeeKPI,
        check_goals: bool = True
    ) -> Dict[str, List[str]]:
        """
        Perform comprehensive validation on an EmployeeKPI record.

        Args:
            employee_kpi: EmployeeKPI object to validate
            check_goals: Whether to validate goal-related consistency

        Returns:
            Dictionary of validation errors (field -> list of error messages)
        """
        errors = {}

        # Validate KPI percentage
        try:
            self.validate_kpi_percentage(employee_kpi.kpi_percentage)
        except KPIValidationError as e:
            errors[e.field] = [e.message]

        # Validate depremium threshold
        try:
            self.validate_depremium_threshold(employee_kpi.depremium_threshold)
        except KPIValidationError as e:
            errors[e.field] = [e.message]

        # Validate bonus types and fixed parts
        try:
            self.validate_fixed_part(
                employee_kpi.monthly_bonus_fixed_part,
                employee_kpi.monthly_bonus_type.value if employee_kpi.monthly_bonus_type else "FIXED"
            )
        except KPIValidationError as e:
            errors.setdefault("monthly_bonus_fixed_part", []).append(e.message)

        try:
            self.validate_fixed_part(
                employee_kpi.quarterly_bonus_fixed_part,
                employee_kpi.quarterly_bonus_type.value if employee_kpi.quarterly_bonus_type else "FIXED"
            )
        except KPIValidationError as e:
            errors.setdefault("quarterly_bonus_fixed_part", []).append(e.message)

        try:
            self.validate_fixed_part(
                employee_kpi.annual_bonus_fixed_part,
                employee_kpi.annual_bonus_type.value if employee_kpi.annual_bonus_type else "FIXED"
            )
        except KPIValidationError as e:
            errors.setdefault("annual_bonus_fixed_part", []).append(e.message)

        # Validate bonus bases
        try:
            self.validate_bonus_base(employee_kpi.monthly_bonus_base, "monthly_bonus")
        except KPIValidationError as e:
            errors.setdefault("monthly_bonus_base", []).append(e.message)

        try:
            self.validate_bonus_base(employee_kpi.quarterly_bonus_base, "quarterly_bonus")
        except KPIValidationError as e:
            errors.setdefault("quarterly_bonus_base", []).append(e.message)

        try:
            self.validate_bonus_base(employee_kpi.annual_bonus_base, "annual_bonus")
        except KPIValidationError as e:
            errors.setdefault("annual_bonus_base", []).append(e.message)

        # Validate goal-related consistency
        if check_goals and employee_kpi.id:
            # Validate goal weights
            is_valid, error_msg = self.validate_goal_weights(employee_kpi.id)
            if not is_valid:
                errors.setdefault("goal_weights", []).append(error_msg)

            # Validate KPI consistency with goals
            is_valid, error_msg = self.validate_kpi_consistency(employee_kpi.id)
            if not is_valid:
                errors.setdefault("kpi_consistency", []).append(error_msg)

        return errors

    def validate_and_raise(
        self,
        employee_kpi: EmployeeKPI,
        check_goals: bool = True
    ) -> None:
        """
        Validate EmployeeKPI and raise HTTPException if validation fails.

        Args:
            employee_kpi: EmployeeKPI object to validate
            check_goals: Whether to validate goal-related consistency

        Raises:
            HTTPException: If validation fails (400 Bad Request)
        """
        from fastapi import HTTPException, status

        errors = self.validate_employee_kpi(employee_kpi, check_goals=check_goals)

        if errors:
            # Format errors for response
            error_details = []
            for field, messages in errors.items():
                for message in messages:
                    error_details.append(f"{field}: {message}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Ошибка валидации KPI",
                    "errors": errors,
                    "detail": "; ".join(error_details)
                }
            )
