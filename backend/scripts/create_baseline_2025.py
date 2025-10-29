"""
Quick script to create a baseline budget for 2025 for testing
This will create a simple budget scenario and version with sample data
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import (
    BudgetScenario,
    BudgetVersion,
    BudgetPlanDetail,
    BudgetCategory,
    Department,
    BudgetScenarioTypeEnum,
    BudgetVersionStatusEnum,
    ExpenseTypeEnum,
)


def create_baseline_2025():
    """Create a baseline budget for 2025"""
    db: Session = SessionLocal()

    try:
        # Get first department
        department = db.query(Department).filter(Department.is_active == True).first()
        if not department:
            print("❌ No active departments found. Please create a department first.")
            return

        print(f"✅ Using department: {department.name} (ID: {department.id})")

        # Check if baseline already exists
        existing_baseline = db.query(BudgetVersion).filter(
            BudgetVersion.year == 2025,
            BudgetVersion.department_id == department.id,
            BudgetVersion.is_baseline == True
        ).first()

        if existing_baseline:
            print(f"ℹ️  Baseline already exists: {existing_baseline.version_name} (ID: {existing_baseline.id})")
            print("   Skipping creation.")
            return

        # Create scenario
        print("\n📊 Creating budget scenario for 2025...")
        scenario = BudgetScenario(
            year=2025,
            scenario_name="Базовый сценарий 2025",
            scenario_type=BudgetScenarioTypeEnum.BASE,
            department_id=department.id,
            global_growth_rate=Decimal("5.0"),  # 5% growth
            inflation_rate=Decimal("4.0"),      # 4% inflation
            description="Автоматически созданный базовый сценарий для тестирования",
            created_by="admin",
            is_active=True
        )
        db.add(scenario)
        db.flush()
        print(f"✅ Created scenario: {scenario.scenario_name} (ID: {scenario.id})")

        # Create version
        print("\n📋 Creating budget version...")
        version = BudgetVersion(
            year=2025,
            version_number=1,
            version_name="Первоначальный бюджет 2025",
            department_id=department.id,
            scenario_id=scenario.id,
            status=BudgetVersionStatusEnum.APPROVED,  # Set as approved
            created_by="admin",
            approved_by="admin",
            approved_at=datetime.utcnow(),
            is_baseline=True,  # Set as baseline
            comments="Автоматически созданный baseline для тестирования v0.6.0",
            total_amount=Decimal("0"),
            total_capex=Decimal("0"),
            total_opex=Decimal("0")
        )
        db.add(version)
        db.flush()
        print(f"✅ Created version: {version.version_name} (ID: {version.id})")
        print(f"   Status: {version.status.value}")
        print(f"   Is Baseline: {version.is_baseline}")

        # Get active categories
        categories = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.is_active == True
        ).all()

        if not categories:
            print("\n⚠️  No active budget categories found.")
            print("   Creating sample categories...")

            # Create sample categories
            sample_categories = [
                {"name": "Заработная плата", "type": ExpenseTypeEnum.OPEX},
                {"name": "Аренда офиса", "type": ExpenseTypeEnum.OPEX},
                {"name": "Программное обеспечение", "type": ExpenseTypeEnum.OPEX},
                {"name": "Оборудование", "type": ExpenseTypeEnum.CAPEX},
                {"name": "Обучение персонала", "type": ExpenseTypeEnum.OPEX},
            ]

            categories = []
            for cat_data in sample_categories:
                category = BudgetCategory(
                    name=cat_data["name"],
                    type=cat_data["type"],
                    department_id=department.id,
                    description=f"Автоматически созданная категория для тестирования",
                    is_active=True
                )
                db.add(category)
                categories.append(category)

            db.flush()
            print(f"✅ Created {len(categories)} sample categories")

        # Create budget plan details
        print(f"\n💰 Creating budget plan details for {len(categories)} categories...")

        total_amount = Decimal("0")
        total_capex = Decimal("0")
        total_opex = Decimal("0")
        detail_count = 0

        for category in categories:
            # Sample annual budget per category
            annual_budget = Decimal("100000") if category.type == ExpenseTypeEnum.CAPEX else Decimal("50000")
            monthly_budget = annual_budget / 12

            for month in range(1, 13):
                detail = BudgetPlanDetail(
                    version_id=version.id,
                    month=month,
                    category_id=category.id,
                    planned_amount=monthly_budget,
                    type=category.type,
                    calculation_method=None,
                    justification=f"Тестовые данные - {monthly_budget} руб/месяц"
                )
                db.add(detail)

                total_amount += monthly_budget
                if category.type == ExpenseTypeEnum.CAPEX:
                    total_capex += monthly_budget
                else:
                    total_opex += monthly_budget

                detail_count += 1

        # Update version totals
        version.total_amount = total_amount
        version.total_capex = total_capex
        version.total_opex = total_opex

        db.commit()

        print(f"✅ Created {detail_count} budget plan details")
        print(f"\n📊 Budget Summary:")
        print(f"   Total: {total_amount:,.2f} ₽")
        print(f"   CAPEX: {total_capex:,.2f} ₽")
        print(f"   OPEX: {total_opex:,.2f} ₽")
        print(f"\n🎉 Baseline budget for 2025 created successfully!")
        print(f"\n✨ You can now use:")
        print(f"   - Plan vs Actual analytics")
        print(f"   - Budget validation")
        print(f"   - Payment calendar with baseline")
        print(f"   - Progress bars and heatmap widgets")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating baseline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Baseline Budget for 2025")
    print("=" * 60)
    create_baseline_2025()
    print("=" * 60)
