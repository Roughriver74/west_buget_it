"""
Salary Calculator Service

Handles bidirectional Gross ↔ Net salary calculations with NDFL (Russian income tax).

Formulas:
- Net to Gross: gross = net / (1 - tax_rate)
- Gross to Net: net = gross × (1 - tax_rate)
- NDFL amount: ndfl = gross - net

Default NDFL rate: 13% (0.13)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from app.db.models import SalaryTypeEnum


class SalaryCalculator:
    """
    Service for calculating gross and net salaries with NDFL tax.
    """

    # Default NDFL rate (13%)
    DEFAULT_NDFL_RATE = Decimal("0.13")

    @staticmethod
    def calculate_from_gross(
        gross_salary: Decimal,
        ndfl_rate: Decimal = DEFAULT_NDFL_RATE
    ) -> Dict[str, Decimal]:
        """
        Calculate net salary and NDFL amount from gross salary.

        Args:
            gross_salary: Salary before tax deduction (Брутто)
            ndfl_rate: NDFL tax rate (default: 0.13 for 13%)

        Returns:
            Dict with:
                - base_salary_gross: Input gross salary
                - base_salary_net: Calculated net salary (take-home)
                - ndfl_amount: Tax amount to be withheld
                - ndfl_rate: Tax rate used

        Example:
            >>> calc = SalaryCalculator()
            >>> result = calc.calculate_from_gross(Decimal("115000"))
            >>> result["base_salary_net"]  # 100050.00
            >>> result["ndfl_amount"]       # 14950.00
        """
        # Validate inputs
        if gross_salary <= 0:
            raise ValueError("Gross salary must be positive")
        if ndfl_rate < 0 or ndfl_rate >= 1:
            raise ValueError("NDFL rate must be between 0 and 1")

        # Calculate net salary: net = gross × (1 - tax_rate)
        net_salary = gross_salary * (Decimal("1") - ndfl_rate)
        net_salary = net_salary.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate NDFL amount: ndfl = gross - net
        ndfl_amount = gross_salary - net_salary
        ndfl_amount = ndfl_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "base_salary_gross": gross_salary,
            "base_salary_net": net_salary,
            "ndfl_amount": ndfl_amount,
            "ndfl_rate": ndfl_rate
        }

    @staticmethod
    def calculate_from_net(
        net_salary: Decimal,
        ndfl_rate: Decimal = DEFAULT_NDFL_RATE
    ) -> Dict[str, Decimal]:
        """
        Calculate gross salary and NDFL amount from desired net salary.

        Args:
            net_salary: Desired take-home salary (Нетто)
            ndfl_rate: NDFL tax rate (default: 0.13 for 13%)

        Returns:
            Dict with:
                - base_salary_gross: Calculated gross salary (before tax)
                - base_salary_net: Input net salary
                - ndfl_amount: Tax amount that will be withheld
                - ndfl_rate: Tax rate used

        Example:
            >>> calc = SalaryCalculator()
            >>> result = calc.calculate_from_net(Decimal("100000"))
            >>> result["base_salary_gross"]  # 114942.53
            >>> result["ndfl_amount"]        # 14942.53
        """
        # Validate inputs
        if net_salary <= 0:
            raise ValueError("Net salary must be positive")
        if ndfl_rate < 0 or ndfl_rate >= 1:
            raise ValueError("NDFL rate must be between 0 and 1")

        # Calculate gross salary: gross = net / (1 - tax_rate)
        gross_salary = net_salary / (Decimal("1") - ndfl_rate)
        gross_salary = gross_salary.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate NDFL amount: ndfl = gross - net
        ndfl_amount = gross_salary - net_salary
        ndfl_amount = ndfl_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "base_salary_gross": gross_salary,
            "base_salary_net": net_salary,
            "ndfl_amount": ndfl_amount,
            "ndfl_rate": ndfl_rate
        }

    @staticmethod
    def calculate_salaries(
        base_salary: Decimal,
        salary_type: SalaryTypeEnum,
        ndfl_rate: Decimal = DEFAULT_NDFL_RATE
    ) -> Dict[str, Decimal]:
        """
        Universal calculation method that determines which calculation to use
        based on salary_type.

        Args:
            base_salary: The salary value entered by user
            salary_type: How the salary was entered (GROSS or NET)
            ndfl_rate: NDFL tax rate (default: 0.13 for 13%)

        Returns:
            Dict with all calculated salary components

        Example:
            >>> calc = SalaryCalculator()
            >>> # User enters gross
            >>> result = calc.calculate_salaries(
            ...     Decimal("115000"),
            ...     SalaryTypeEnum.GROSS
            ... )
            >>> result["base_salary_net"]  # 100050.00
            >>>
            >>> # User enters net
            >>> result = calc.calculate_salaries(
            ...     Decimal("100000"),
            ...     SalaryTypeEnum.NET
            ... )
            >>> result["base_salary_gross"]  # 114942.53
        """
        if salary_type == SalaryTypeEnum.GROSS:
            return SalaryCalculator.calculate_from_gross(base_salary, ndfl_rate)
        elif salary_type == SalaryTypeEnum.NET:
            return SalaryCalculator.calculate_from_net(base_salary, ndfl_rate)
        else:
            raise ValueError(f"Unknown salary type: {salary_type}")

    @staticmethod
    def validate_and_recalculate(
        base_salary: Decimal,
        salary_type: SalaryTypeEnum,
        base_salary_gross: Decimal | None = None,
        base_salary_net: Decimal | None = None,
        ndfl_amount: Decimal | None = None,
        ndfl_rate: Decimal = DEFAULT_NDFL_RATE
    ) -> Dict[str, Decimal]:
        """
        Validate existing salary data and recalculate if needed.

        This is useful when updating an existing employee record or
        when verifying that stored calculations are correct.

        Args:
            base_salary: The base salary value (what user entered)
            salary_type: How the salary was entered (GROSS or NET)
            base_salary_gross: Existing gross salary value (optional)
            base_salary_net: Existing net salary value (optional)
            ndfl_amount: Existing NDFL amount (optional)
            ndfl_rate: NDFL tax rate

        Returns:
            Dict with recalculated salary components
        """
        # Always recalculate to ensure consistency
        return SalaryCalculator.calculate_salaries(
            base_salary,
            salary_type,
            ndfl_rate
        )


# Example usage and testing
if __name__ == "__main__":
    calc = SalaryCalculator()

    print("=" * 60)
    print("EXAMPLE 1: Calculate from GROSS salary")
    print("=" * 60)
    result = calc.calculate_from_gross(Decimal("115000"))
    print(f"Input: Gross = 115,000 ₽")
    print(f"Output:")
    print(f"  Net (take-home): {result['base_salary_net']:,.2f} ₽")
    print(f"  NDFL (tax):      {result['ndfl_amount']:,.2f} ₽")
    print()

    print("=" * 60)
    print("EXAMPLE 2: Calculate from NET salary")
    print("=" * 60)
    result = calc.calculate_from_net(Decimal("100000"))
    print(f"Input: Net (desired take-home) = 100,000 ₽")
    print(f"Output:")
    print(f"  Gross (before tax): {result['base_salary_gross']:,.2f} ₽")
    print(f"  NDFL (tax):         {result['ndfl_amount']:,.2f} ₽")
    print()

    print("=" * 60)
    print("EXAMPLE 3: Universal calculation (GROSS)")
    print("=" * 60)
    result = calc.calculate_salaries(
        Decimal("115000"),
        SalaryTypeEnum.GROSS
    )
    print(f"Input: base_salary=115,000, type=GROSS")
    print(f"Output:")
    print(f"  Gross: {result['base_salary_gross']:,.2f} ₽")
    print(f"  Net:   {result['base_salary_net']:,.2f} ₽")
    print(f"  NDFL:  {result['ndfl_amount']:,.2f} ₽")
    print()

    print("=" * 60)
    print("EXAMPLE 4: Universal calculation (NET)")
    print("=" * 60)
    result = calc.calculate_salaries(
        Decimal("100000"),
        SalaryTypeEnum.NET
    )
    print(f"Input: base_salary=100,000, type=NET")
    print(f"Output:")
    print(f"  Gross: {result['base_salary_gross']:,.2f} ₽")
    print(f"  Net:   {result['base_salary_net']:,.2f} ₽")
    print(f"  NDFL:  {result['ndfl_amount']:,.2f} ₽")
