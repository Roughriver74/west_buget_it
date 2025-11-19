#!/usr/bin/env python3
"""Add test data to the database"""

import sys
sys.path.insert(0, '/home/user/acme_buget_it/backend')

from datetime import datetime, timedelta
from decimal import Decimal
from random import randint, choice
from app.db.session import SessionLocal
from app.db.models import BudgetPlan, Expense, BudgetCategory, Organization, Contractor

def add_budget_plan_data():
    """Add test budget plan data for 2025"""
    db = SessionLocal()

    try:
        # Get categories
        categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).all()

        print("Adding budget plan data for 2025...")

        # Update plans with realistic amounts
        test_amounts = {
            "Аутсорс": [300000, 350000, 320000, 330000, 340000, 350000, 360000, 340000, 330000, 350000, 360000, 380000],
            "Лицензии": [150000, 150000, 150000, 200000, 150000, 150000, 150000, 150000, 150000, 150000, 150000, 200000],
            "Оборудование": [0, 500000, 0, 0, 0, 800000, 0, 0, 0, 0, 1000000, 0],
            "Облачные сервисы": [200000, 200000, 220000, 220000, 230000, 240000, 240000, 250000, 250000, 260000, 270000, 280000],
            "Обучение": [50000, 50000, 100000, 50000, 50000, 50000, 50000, 50000, 100000, 50000, 50000, 50000],
            "ЗП IT персонала": [2000000, 2000000, 2000000, 2000000, 2000000, 2000000, 2200000, 2200000, 2200000, 2200000, 2200000, 2400000],
            "Серверы": [0, 0, 0, 1500000, 0, 0, 0, 0, 0, 2000000, 0, 0],
            "Сетевое оборудование": [0, 0, 300000, 0, 0, 0, 500000, 0, 0, 0, 400000, 0],
            "Хостинг": [80000, 80000, 80000, 80000, 90000, 90000, 90000, 90000, 100000, 100000, 100000, 100000],
            "Прочее": [50000, 50000, 50000, 50000, 50000, 50000, 50000, 50000, 50000, 50000, 50000, 50000],
        }

        updated_count = 0
        for category in categories:
            if category.name in test_amounts:
                amounts = test_amounts[category.name]
                for month in range(1, 13):
                    plan = db.query(BudgetPlan).filter(
                        BudgetPlan.year == 2025,
                        BudgetPlan.month == month,
                        BudgetPlan.category_id == category.id
                    ).first()

                    if plan:
                        amount = Decimal(str(amounts[month - 1]))
                        plan.planned_amount = amount

                        # Set CAPEX/OPEX based on category type
                        if category.type == "CAPEX":
                            plan.capex_planned = amount
                            plan.opex_planned = Decimal(0)
                        else:
                            plan.opex_planned = amount
                            plan.capex_planned = Decimal(0)

                        updated_count += 1

        db.commit()
        print(f"✅ Updated {updated_count} budget plan entries")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def add_contractors():
    """Add test contractors"""
    db = SessionLocal()

    try:
        # Check if contractors already exist
        existing = db.query(Contractor).count()
        if existing > 0:
            print(f"Contractors already exist ({existing}), skipping...")
            return

        contractors = [
            Contractor(
                name="Amazon Web Services",
                short_name="AWS",
                inn="9909999999",
                contact_info="support@aws.com",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Contractor(
                name="Microsoft Azure",
                short_name="Azure",
                inn="9909999998",
                contact_info="support@azure.com",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Contractor(
                name="ООО \"ИТ Аутсорс\"",
                short_name="ИТ Аутсорс",
                inn="7777888899",
                contact_info="info@it-outsource.ru",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Contractor(
                name="ООО \"Серверные Технологии\"",
                short_name="СерверТех",
                inn="7777888890",
                contact_info="sales@servertech.ru",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
        ]

        db.add_all(contractors)
        db.commit()
        print(f"✅ Added {len(contractors)} contractors")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def add_expenses():
    """Add test expenses for January-October 2025"""
    db = SessionLocal()

    try:
        # Check if expenses already exist
        existing = db.query(Expense).count()
        if existing > 0:
            print(f"Expenses already exist ({existing}), skipping...")
            return

        categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).all()
        organizations = db.query(Organization).all()
        contractors = db.query(Contractor).all()

        if not contractors:
            print("No contractors found, adding them first...")
            add_contractors()
            contractors = db.query(Contractor).all()

        print("Adding test expenses for 2025...")

        expenses = []
        expense_num = 1

        # Add expenses for January to October (10 months)
        for month in range(1, 11):
            for category in categories:
                # Get planned amount for this month
                plan = db.query(BudgetPlan).filter(
                    BudgetPlan.year == 2025,
                    BudgetPlan.month == month,
                    BudgetPlan.category_id == category.id
                ).first()

                if plan and plan.planned_amount > 0:
                    # Add 1-3 expenses per month per category
                    num_expenses = randint(1, 3) if plan.planned_amount > 100000 else 1

                    for _ in range(num_expenses):
                        # Random amount (70-95% of planned / num_expenses)
                        amount_per_expense = float(plan.planned_amount) / num_expenses
                        actual_amount = amount_per_expense * (70 + randint(0, 25)) / 100

                        # Random date in the month
                        day = randint(1, 28)
                        request_date = datetime(2025, month, day)

                        expense = Expense(
                            number=f"EXP-2025-{expense_num:04d}",
                            category_id=category.id,
                            contractor_id=choice(contractors).id if contractors else None,
                            organization_id=choice(organizations).id,
                            amount=Decimal(str(round(actual_amount, 2))),
                            request_date=request_date,
                            payment_date=request_date + timedelta(days=randint(1, 14)),
                            status="Оплачена",
                            is_paid=True,
                            is_closed=True,
                            comment=f"Тестовый расход по категории {category.name}",
                            requester="Иванов И.И.",
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        expenses.append(expense)
                        expense_num += 1

        db.add_all(expenses)
        db.commit()
        print(f"✅ Added {len(expenses)} test expenses")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function"""
    print("=" * 60)
    print("Adding test data to database...")
    print("=" * 60)

    add_contractors()
    add_budget_plan_data()
    add_expenses()

    print("\n" + "=" * 60)
    print("✅ Test data added successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
