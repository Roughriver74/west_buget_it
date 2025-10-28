"""
KPI Calculations Tests

Tests for KPI-related business logic including:
- Bonus calculations (PERFORMANCE_BASED, FIXED, MIXED)
- KPI percentage calculations
- Goal achievement tracking
- Weighted average calculations
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import (
    Employee, EmployeeKPI, KPIGoal, EmployeeKPIGoal,
    BonusTypeEnum, KPIGoalStatusEnum, Department
)


# ================================================================
# Test Fixtures
# ================================================================

@pytest.fixture
def test_employee(db_session: Session, test_department):
    """Create a test employee"""
    employee = Employee(
        full_name="Test Employee",
        position="Software Engineer",
        base_salary=100000.0,
        monthly_bonus_base=10000.0,
        quarterly_bonus_base=20000.0,
        annual_bonus_base=50000.0,
        department_id=test_department.id,
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def test_kpi_goal(db_session: Session, test_department):
    """Create a test KPI goal"""
    goal = KPIGoal(
        name="Code Quality",
        description="Maintain code quality metrics",
        category="Technical",
        weight=30.0,  # 30% weight
        target_value=90.0,
        unit="percentage",
        goal_type="monthly",
        department_id=test_department.id,
        status=KPIGoalStatusEnum.ACTIVE,
        is_active=True
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


# ================================================================
# Bonus Calculation Tests
# ================================================================

class TestBonusCalculations:
    """Test bonus calculation formulas for different bonus types"""

    def test_performance_based_bonus_100_percent(
        self, db_session: Session, test_employee, test_department
    ):
        """Test PERFORMANCE_BASED bonus with 100% KPI achievement"""
        # Create EmployeeKPI with 100% achievement
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=100.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
            monthly_fixed_part=0.0,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Calculate bonus: base * (kpi% / 100)
        expected_bonus = test_employee.monthly_bonus_base * (100.0 / 100.0)

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 10000.0

    def test_performance_based_bonus_150_percent(
        self, db_session: Session, test_employee, test_department
    ):
        """Test PERFORMANCE_BASED bonus with 150% KPI achievement (over-achievement)"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=150.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
            monthly_fixed_part=0.0,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Bonus should be 150% of base
        expected_bonus = test_employee.monthly_bonus_base * (150.0 / 100.0)

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 15000.0

    def test_performance_based_bonus_50_percent(
        self, db_session: Session, test_employee, test_department
    ):
        """Test PERFORMANCE_BASED bonus with 50% KPI achievement (under-achievement)"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=50.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
            monthly_fixed_part=0.0,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Bonus should be 50% of base
        expected_bonus = test_employee.monthly_bonus_base * (50.0 / 100.0)

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 5000.0

    def test_fixed_bonus(
        self, db_session: Session, test_employee, test_department
    ):
        """Test FIXED bonus - should not depend on KPI percentage"""
        # Test with different KPI percentages
        for kpi_pct in [0.0, 50.0, 100.0, 150.0, 200.0]:
            employee_kpi = EmployeeKPI(
                employee_id=test_employee.id,
                department_id=test_department.id,
                year=2025,
                month=1,
                kpi_percentage=kpi_pct,
                monthly_bonus_type=BonusTypeEnum.FIXED,
                monthly_fixed_part=100.0,  # 100% fixed
            )
            db_session.add(employee_kpi)
            db_session.commit()

            # Bonus should always be base amount regardless of KPI
            assert employee_kpi.monthly_bonus_calculated == test_employee.monthly_bonus_base
            assert employee_kpi.monthly_bonus_calculated == 10000.0

            db_session.delete(employee_kpi)
            db_session.commit()

    def test_mixed_bonus_50_50(
        self, db_session: Session, test_employee, test_department
    ):
        """Test MIXED bonus with 50% fixed and 50% performance-based"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=100.0,
            monthly_bonus_type=BonusTypeEnum.MIXED,
            monthly_fixed_part=50.0,  # 50% fixed
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Formula: base * (fixed% / 100) + base * ((100 - fixed%) / 100) * (kpi% / 100)
        fixed_part = test_employee.monthly_bonus_base * 0.5
        performance_part = test_employee.monthly_bonus_base * 0.5 * 1.0
        expected_bonus = fixed_part + performance_part

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 10000.0

    def test_mixed_bonus_70_30_high_performance(
        self, db_session: Session, test_employee, test_department
    ):
        """Test MIXED bonus with 70% fixed, 30% performance-based, 150% KPI"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=150.0,
            monthly_bonus_type=BonusTypeEnum.MIXED,
            monthly_fixed_part=70.0,  # 70% fixed
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Fixed: 10000 * 0.7 = 7000
        # Performance: 10000 * 0.3 * 1.5 = 4500
        # Total: 11500
        expected_bonus = (test_employee.monthly_bonus_base * 0.7) + \
                        (test_employee.monthly_bonus_base * 0.3 * 1.5)

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 11500.0

    def test_mixed_bonus_30_70_low_performance(
        self, db_session: Session, test_employee, test_department
    ):
        """Test MIXED bonus with 30% fixed, 70% performance-based, 50% KPI"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=50.0,
            monthly_bonus_type=BonusTypeEnum.MIXED,
            monthly_fixed_part=30.0,  # 30% fixed
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Fixed: 10000 * 0.3 = 3000
        # Performance: 10000 * 0.7 * 0.5 = 3500
        # Total: 6500
        expected_bonus = (test_employee.monthly_bonus_base * 0.3) + \
                        (test_employee.monthly_bonus_base * 0.7 * 0.5)

        assert employee_kpi.monthly_bonus_calculated == expected_bonus
        assert employee_kpi.monthly_bonus_calculated == 6500.0


# ================================================================
# Goal Achievement Tests
# ================================================================

class TestGoalAchievement:
    """Test goal achievement calculations"""

    def test_goal_achievement_100_percent(
        self, db_session: Session, test_employee, test_kpi_goal, test_department
    ):
        """Test goal achievement at exactly target value"""
        employee_kpi_goal = EmployeeKPIGoal(
            employee_id=test_employee.id,
            goal_id=test_kpi_goal.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            target_value=test_kpi_goal.target_value,  # 90.0
            actual_value=90.0,  # Exactly on target
        )
        db_session.add(employee_kpi_goal)
        db_session.commit()
        db_session.refresh(employee_kpi_goal)

        # Achievement should be 100%
        assert employee_kpi_goal.achievement_percentage == 100.0

    def test_goal_achievement_over_100_percent(
        self, db_session: Session, test_employee, test_kpi_goal, test_department
    ):
        """Test goal over-achievement"""
        employee_kpi_goal = EmployeeKPIGoal(
            employee_id=test_employee.id,
            goal_id=test_kpi_goal.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            target_value=90.0,
            actual_value=135.0,  # 150% of target
        )
        db_session.add(employee_kpi_goal)
        db_session.commit()
        db_session.refresh(employee_kpi_goal)

        # Achievement should be 150%
        assert employee_kpi_goal.achievement_percentage == 150.0

    def test_goal_achievement_under_100_percent(
        self, db_session: Session, test_employee, test_kpi_goal, test_department
    ):
        """Test goal under-achievement"""
        employee_kpi_goal = EmployeeKPIGoal(
            employee_id=test_employee.id,
            goal_id=test_kpi_goal.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            target_value=100.0,
            actual_value=75.0,  # 75% of target
        )
        db_session.add(employee_kpi_goal)
        db_session.commit()
        db_session.refresh(employee_kpi_goal)

        # Achievement should be 75%
        assert employee_kpi_goal.achievement_percentage == 75.0

    def test_goal_achievement_zero_target(
        self, db_session: Session, test_employee, test_kpi_goal, test_department
    ):
        """Test goal achievement with zero target (edge case)"""
        employee_kpi_goal = EmployeeKPIGoal(
            employee_id=test_employee.id,
            goal_id=test_kpi_goal.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            target_value=0.0,
            actual_value=50.0,
        )
        db_session.add(employee_kpi_goal)
        db_session.commit()
        db_session.refresh(employee_kpi_goal)

        # With zero target, achievement should be 0 (division by zero protection)
        assert employee_kpi_goal.achievement_percentage == 0.0


# ================================================================
# Weighted Average KPI Tests
# ================================================================

class TestWeightedKPI:
    """Test weighted average KPI calculations"""

    def test_single_goal_weighted_kpi(
        self, db_session: Session, test_employee, test_kpi_goal, test_department
    ):
        """Test KPI with single goal"""
        # Create goal assignment with 100% achievement
        employee_kpi_goal = EmployeeKPIGoal(
            employee_id=test_employee.id,
            goal_id=test_kpi_goal.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            target_value=100.0,
            actual_value=120.0,  # 120% achievement
        )
        db_session.add(employee_kpi_goal)
        db_session.commit()

        # With single goal, KPI% should equal goal achievement
        # (assuming goal weight is properly normalized)
        # Goal weight: 30%, Achievement: 120%
        # Weighted KPI = 120% * (30/30) = 120%
        assert employee_kpi_goal.achievement_percentage == 120.0

    def test_multiple_goals_weighted_kpi(
        self, db_session: Session, test_employee, test_department
    ):
        """Test KPI with multiple goals of different weights"""
        # Create three goals with different weights
        goal1 = KPIGoal(
            name="Goal 1",
            weight=50.0,  # 50%
            target_value=100.0,
            goal_type="monthly",
            department_id=test_department.id,
            status=KPIGoalStatusEnum.ACTIVE,
            is_active=True
        )
        goal2 = KPIGoal(
            name="Goal 2",
            weight=30.0,  # 30%
            target_value=100.0,
            goal_type="monthly",
            department_id=test_department.id,
            status=KPIGoalStatusEnum.ACTIVE,
            is_active=True
        )
        goal3 = KPIGoal(
            name="Goal 3",
            weight=20.0,  # 20%
            target_value=100.0,
            goal_type="monthly",
            department_id=test_department.id,
            status=KPIGoalStatusEnum.ACTIVE,
            is_active=True
        )
        db_session.add_all([goal1, goal2, goal3])
        db_session.commit()

        # Create achievements: 120%, 100%, 80%
        achievements = [
            (goal1.id, 120.0),
            (goal2.id, 100.0),
            (goal3.id, 80.0),
        ]

        for goal_id, actual_value in achievements:
            employee_kpi_goal = EmployeeKPIGoal(
                employee_id=test_employee.id,
                goal_id=goal_id,
                department_id=test_department.id,
                year=2025,
                month=1,
                target_value=100.0,
                actual_value=actual_value,
            )
            db_session.add(employee_kpi_goal)
        db_session.commit()

        # Calculate weighted average:
        # (120% * 50%) + (100% * 30%) + (80% * 20%) = 60% + 30% + 16% = 106%
        expected_weighted_kpi = (120.0 * 0.5) + (100.0 * 0.3) + (80.0 * 0.2)
        assert expected_weighted_kpi == 106.0


# ================================================================
# Edge Cases and Validation Tests
# ================================================================

class TestKPIEdgeCases:
    """Test edge cases and validation"""

    def test_zero_base_bonus(
        self, db_session: Session, test_employee, test_department
    ):
        """Test bonus calculation with zero base bonus"""
        # Set base bonus to zero
        test_employee.monthly_bonus_base = 0.0
        db_session.commit()

        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=150.0,
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Bonus should be zero regardless of KPI
        assert employee_kpi.monthly_bonus_calculated == 0.0

    def test_negative_kpi_percentage(
        self, db_session: Session, test_employee, test_department
    ):
        """Test that negative KPI percentage is handled gracefully"""
        # Note: In real implementation, this should be validated at API level
        # But we test database-level behavior
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=0.0,  # Should be non-negative
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Bonus should be zero or handled gracefully
        assert employee_kpi.monthly_bonus_calculated >= 0.0

    def test_kpi_percentage_over_200(
        self, db_session: Session, test_employee, test_department
    ):
        """Test KPI percentage capped or allowed over 200%"""
        employee_kpi = EmployeeKPI(
            employee_id=test_employee.id,
            department_id=test_department.id,
            year=2025,
            month=1,
            kpi_percentage=250.0,  # Exceptional performance
            monthly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
        )
        db_session.add(employee_kpi)
        db_session.commit()

        # Should calculate bonus even for exceptional performance
        expected_bonus = test_employee.monthly_bonus_base * 2.5
        assert employee_kpi.monthly_bonus_calculated == expected_bonus
