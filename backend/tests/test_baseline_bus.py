from datetime import datetime
from decimal import Decimal

from app.db.models import Expense, BudgetCategory, Organization, ExpenseTypeEnum, ExpenseStatusEnum
from app.services.baseline_bus import BaselineCalculationBus, baseline_bus
from app.services.budget_calculator import BudgetCalculator


def _sample_baseline() -> dict:
    return {
        "total_amount": Decimal("100"),
        "monthly_avg": Decimal("10"),
        "monthly_breakdown": [{"month": m, "amount": Decimal("10")} for m in range(1, 13)],
        "capex_total": Decimal("0"),
        "opex_total": Decimal("100"),
    }


def test_baseline_bus_caches_and_invalidates():
    bus = BaselineCalculationBus(ttl_seconds=60)
    call_counter = {"count": 0}

    def loader():
        call_counter["count"] += 1
        return _sample_baseline()

    first = bus.get_or_compute(
        category_id=1,
        base_year=2025,
        department_id=2,
        loader=loader,
    )

    # Mutating consumer copy should not affect cached value
    first["total_amount"] = Decimal("999")

    second = bus.get_or_compute(
        category_id=1,
        base_year=2025,
        department_id=2,
        loader=loader,
    )

    assert call_counter["count"] == 1
    assert second["total_amount"] == Decimal("100")

    bus.invalidate(category_id=1, department_id=2, year=2025)

    third = bus.get_or_compute(
        category_id=1,
        base_year=2025,
        department_id=2,
        loader=loader,
    )

    assert call_counter["count"] == 2
    assert third["total_amount"] == Decimal("100")


def test_budget_calculator_uses_shared_cache(db_session, test_department):
    baseline_bus.invalidate()

    category = BudgetCategory(
        name="Test Category",
        type=ExpenseTypeEnum.OPEX,
        department_id=test_department.id,
        is_active=True,
    )
    organization = Organization(
        name="Test Org",
        department_id=test_department.id,
        is_active=True,
    )
    db_session.add_all([category, organization])
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(organization)

    expense = Expense(
        number="EXP-001",
        department_id=test_department.id,
        category_id=category.id,
        organization_id=organization.id,
        amount=Decimal("120"),
        request_date=datetime(2025, 1, 10),
        status=ExpenseStatusEnum.PENDING,
        is_paid=False,
        is_closed=False,
        imported_from_ftp=False,
        needs_review=False,
    )
    db_session.add(expense)
    db_session.commit()

    calculator = BudgetCalculator(db_session)

    baseline1 = calculator.get_baseline_data(category.id, 2025, test_department.id)
    assert baseline1["total_amount"] == Decimal("120")

    # Mutate consumer copy; cached value remains intact
    baseline1["total_amount"] = Decimal("999")

    baseline2 = calculator.get_baseline_data(category.id, 2025, test_department.id)
    assert baseline2["total_amount"] == Decimal("120")

    # Add new expense but cache should still serve old value until invalidated
    new_expense = Expense(
        number="EXP-002",
        department_id=test_department.id,
        category_id=category.id,
        organization_id=organization.id,
        amount=Decimal("60"),
        request_date=datetime(2025, 2, 5),
        status=ExpenseStatusEnum.PENDING,
        is_paid=False,
        is_closed=False,
        imported_from_ftp=False,
        needs_review=False,
    )
    db_session.add(new_expense)
    db_session.commit()

    cached_again = calculator.get_baseline_data(category.id, 2025, test_department.id)
    assert cached_again["total_amount"] == Decimal("120")

    baseline_bus.invalidate(category_id=category.id, department_id=test_department.id, year=2025)

    refreshed = calculator.get_baseline_data(category.id, 2025, test_department.id)
    assert refreshed["total_amount"] == Decimal("180")
