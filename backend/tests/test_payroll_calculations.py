"""
Payroll Calculations Tests

Tests for payroll-related business logic including:
- Salary calculations (base + bonuses)
- Advance vs final payment calculations
- Payroll plan vs actual tracking
- Total compensation calculations
- Payment date logic (10th and 25th)
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import (
    Employee, PayrollPlan, PayrollActual, EmployeeKPI,
    BonusTypeEnum, Department
)


# ================================================================
# Test Fixtures
# ================================================================

@pytest.fixture
def test_employee_with_salary(db_session: Session, test_department):
    """Create a test employee with standard salary structure"""
    employee = Employee(
        full_name="Test Payroll Employee",
        position="Senior Developer",
        base_salary=150000.0,  # 150k annually = 12,500/month
        monthly_bonus_base=15000.0,
        quarterly_bonus_base=30000.0,
        annual_bonus_base=75000.0,
        department_id=test_department.id,
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def test_payroll_plan(db_session: Session, test_employee_with_salary, test_department):
    """Create a test payroll plan"""
    plan = PayrollPlan(
        employee_id=test_employee_with_salary.id,
        department_id=test_department.id,
        year=2025,
        month=1,
        base_salary=12500.0,  # Monthly base
        monthly_bonus=15000.0,
        quarterly_bonus=0.0,  # No quarterly this month
        annual_bonus=0.0,  # No annual this month
        other_payments=0.0,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


# ================================================================
# Basic Payroll Calculation Tests
# ================================================================

class TestPayrollCalculations:
    """Test basic payroll calculations"""

    def test_total_planned_calculation(
        self, db_session: Session, test_payroll_plan
    ):
        """Test total_planned is calculated correctly from components"""
        # total_planned = base_salary + monthly_bonus + quarterly_bonus + annual_bonus + other_payments
        expected_total = (
            test_payroll_plan.base_salary +
            test_payroll_plan.monthly_bonus +
            test_payroll_plan.quarterly_bonus +
            test_payroll_plan.annual_bonus +
            test_payroll_plan.other_payments
        )

        assert test_payroll_plan.total_planned == expected_total
        assert test_payroll_plan.total_planned == 27500.0

    def test_total_planned_with_all_components(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test total_planned with all bonus types"""
        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=3,  # March - end of Q1
            base_salary=12500.0,
            monthly_bonus=15000.0,
            quarterly_bonus=30000.0,  # Q1 bonus
            annual_bonus=0.0,
            other_payments=5000.0,  # Additional payment
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        expected_total = 12500.0 + 15000.0 + 30000.0 + 0.0 + 5000.0
        assert plan.total_planned == expected_total
        assert plan.total_planned == 62500.0

    def test_total_planned_only_base_salary(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test total_planned with only base salary (no bonuses)"""
        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=2,
            base_salary=12500.0,
            monthly_bonus=0.0,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        assert plan.total_planned == 12500.0


# ================================================================
# Advance vs Final Payment Tests
# ================================================================

class TestAdvanceAndFinalPayments:
    """Test advance and final payment split logic"""

    def test_advance_payment_calculation(
        self, db_session: Session, test_employee_with_salary, test_payroll_plan, test_department
    ):
        """Test advance payment is 50% of base salary only"""
        # Advance = 50% of base_salary (no bonuses)
        expected_advance = test_payroll_plan.base_salary * 0.5

        # Create PayrollActual for advance
        advance_payment = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            payment_type='advance',
            payment_date=date(2025, 1, 25),
            base_salary_paid=expected_advance,
            monthly_bonus_paid=0.0,
            quarterly_bonus_paid=0.0,
            annual_bonus_paid=0.0,
            other_payments_paid=0.0,
        )
        db_session.add(advance_payment)
        db_session.commit()
        db_session.refresh(advance_payment)

        assert advance_payment.base_salary_paid == 6250.0
        assert advance_payment.total_paid == 6250.0

    def test_final_payment_calculation(
        self, db_session: Session, test_employee_with_salary, test_payroll_plan, test_department
    ):
        """Test final payment includes remaining salary + all bonuses"""
        # Final = 50% of base_salary + 100% of bonuses
        expected_base_final = test_payroll_plan.base_salary * 0.5
        expected_bonus = (
            test_payroll_plan.monthly_bonus +
            test_payroll_plan.quarterly_bonus +
            test_payroll_plan.annual_bonus +
            test_payroll_plan.other_payments
        )
        expected_total = expected_base_final + expected_bonus

        # Create PayrollActual for final payment
        final_payment = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            payment_type='final',
            payment_date=date(2025, 2, 10),  # 10th of next month
            base_salary_paid=expected_base_final,
            monthly_bonus_paid=test_payroll_plan.monthly_bonus,
            quarterly_bonus_paid=test_payroll_plan.quarterly_bonus,
            annual_bonus_paid=test_payroll_plan.annual_bonus,
            other_payments_paid=test_payroll_plan.other_payments,
        )
        db_session.add(final_payment)
        db_session.commit()
        db_session.refresh(final_payment)

        assert final_payment.base_salary_paid == 6250.0
        assert final_payment.monthly_bonus_paid == 15000.0
        assert final_payment.total_paid == 21250.0

    def test_advance_plus_final_equals_plan(
        self, db_session: Session, test_employee_with_salary, test_payroll_plan, test_department
    ):
        """Test that advance + final = total planned"""
        # Create advance payment
        advance = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            payment_type='advance',
            payment_date=date(2025, 1, 25),
            base_salary_paid=test_payroll_plan.base_salary * 0.5,
            monthly_bonus_paid=0.0,
            quarterly_bonus_paid=0.0,
            annual_bonus_paid=0.0,
            other_payments_paid=0.0,
        )

        # Create final payment
        final = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            payment_type='final',
            payment_date=date(2025, 2, 10),
            base_salary_paid=test_payroll_plan.base_salary * 0.5,
            monthly_bonus_paid=test_payroll_plan.monthly_bonus,
            quarterly_bonus_paid=test_payroll_plan.quarterly_bonus,
            annual_bonus_paid=test_payroll_plan.annual_bonus,
            other_payments_paid=test_payroll_plan.other_payments,
        )

        db_session.add_all([advance, final])
        db_session.commit()

        total_paid = advance.total_paid + final.total_paid
        assert total_paid == test_payroll_plan.total_planned
        assert total_paid == 27500.0


# ================================================================
# KPI Integration Tests
# ================================================================

class TestPayrollKPIIntegration:
    """Test integration between payroll and KPI systems"""

    def test_bonus_calculation_with_kpi_100_percent(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test payroll bonus matches KPI calculation at 100%"""
        # Create EmployeeKPI with 100% achievement
        employee_kpi = EmployeeKPI(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=100.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Create payroll plan with calculated bonus
        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            base_salary=12500.0,
            monthly_bonus=employee_kpi.monthly_bonus_calculated,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()

        # Bonus should match KPI calculation
        assert plan.monthly_bonus == test_employee_with_salary.monthly_bonus_base
        assert plan.monthly_bonus == 15000.0

    def test_bonus_calculation_with_kpi_150_percent(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test payroll bonus with over-achievement (150% KPI)"""
        # Create EmployeeKPI with 150% achievement
        employee_kpi = EmployeeKPI(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=150.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Create payroll plan with calculated bonus
        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            base_salary=12500.0,
            monthly_bonus=employee_kpi.monthly_bonus_calculated,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()

        # Bonus should be 150% of base
        expected_bonus = test_employee_with_salary.monthly_bonus_base * 1.5
        assert plan.monthly_bonus == expected_bonus
        assert plan.monthly_bonus == 22500.0

    def test_fixed_bonus_ignores_kpi(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test that FIXED bonus type ignores KPI percentage"""
        # Create EmployeeKPI with FIXED bonus type (low KPI)
        employee_kpi = EmployeeKPI(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=50.0,  # Low performance
            monthly_bonus_type=BonusTypeEnum.FIXED,
            monthly_fixed_part=100.0,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Create payroll plan with fixed bonus
        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            base_salary=12500.0,
            monthly_bonus=employee_kpi.monthly_bonus_calculated,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()

        # Bonus should be full base amount despite low KPI
        assert plan.monthly_bonus == test_employee_with_salary.monthly_bonus_base
        assert plan.monthly_bonus == 15000.0


# ================================================================
# Payment Date Logic Tests
# ================================================================

class TestPaymentDates:
    """Test payment date logic and business rules"""

    def test_advance_payment_date_25th(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test advance payment should be on 25th of current month"""
        payment = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            payment_type='advance',
            payment_date=date(2025, 1, 25),
            base_salary_paid=6250.0,
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.payment_date.day == 25
        assert payment.payment_date.month == 1

    def test_final_payment_date_10th_next_month(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test final payment should be on 10th of next month"""
        payment = PayrollActual(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,  # January payroll
            payment_type='final',
            payment_date=date(2025, 2, 10),  # 10th of February
            base_salary_paid=6250.0,
            monthly_bonus_paid=15000.0,
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.payment_date.day == 10
        assert payment.payment_date.month == 2


# ================================================================
# Annual Totals and Statistics Tests
# ================================================================

class TestAnnualCalculations:
    """Test annual payroll totals and statistics"""

    def test_annual_compensation_calculation(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test total annual compensation calculation"""
        # Create 12 months of payroll plans
        total_annual = 0.0
        for month in range(1, 13):
            plan = PayrollPlan(
                employee_id=test_employee_with_salary.id,
                department_id=test_department.id,
                year=2025,
                month=month,
                base_salary=12500.0,
                monthly_bonus=15000.0,
                quarterly_bonus=30000.0 if month in [3, 6, 9, 12] else 0.0,
                annual_bonus=75000.0 if month == 12 else 0.0,
                other_payments=0.0,
            )
            db_session.add(plan)
            total_annual += plan.total_planned

        db_session.commit()

        # Expected: 12 * (12500 + 15000) + 4 * 30000 + 75000
        # = 12 * 27500 + 120000 + 75000
        # = 330000 + 120000 + 75000 = 525000
        expected_total = (12 * 27500.0) + (4 * 30000.0) + 75000.0
        assert total_annual == expected_total
        assert total_annual == 525000.0


# ================================================================
# Edge Cases and Validation Tests
# ================================================================

class TestPayrollEdgeCases:
    """Test edge cases and validation"""

    def test_zero_salary_employee(
        self, db_session: Session, test_department
    ):
        """Test payroll calculation for employee with zero salary"""
        employee = Employee(
            full_name="Unpaid Intern",
            position="Intern",
            base_salary=0.0,
            monthly_bonus_base=0.0,
            quarterly_bonus_base=0.0,
            annual_bonus_base=0.0,
            department_id=test_department.id,
            is_active=True
        )
        db_session.add(employee)
        db_session.commit()

        plan = PayrollPlan(
            employee_id=employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            base_salary=0.0,
            monthly_bonus=0.0,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()

        assert plan.total_planned == 0.0

    def test_partial_month_payment(
        self, db_session: Session, test_employee_with_salary, test_department
    ):
        """Test payroll for partial month (e.g., employee joined mid-month)"""
        # Employee worked 15 days out of 30
        days_worked = 15
        days_in_month = 30
        pro_rata_factor = days_worked / days_in_month

        plan = PayrollPlan(
            employee_id=test_employee_with_salary.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            base_salary=12500.0 * pro_rata_factor,
            monthly_bonus=15000.0 * pro_rata_factor,
            quarterly_bonus=0.0,
            annual_bonus=0.0,
            other_payments=0.0,
        )
        db_session.add(plan)
        db_session.commit()

        expected_total = (12500.0 + 15000.0) * 0.5
        assert plan.total_planned == expected_total
        assert plan.total_planned == 13750.0
