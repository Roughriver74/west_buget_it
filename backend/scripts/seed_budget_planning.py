"""
Seed data for Budget 2026 Module
Creates test scenarios and versions for development
"""
import sys
import os
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    Department,
    BudgetScenario,
    BudgetVersion,
    BudgetScenarioTypeEnum,
    BudgetVersionStatusEnum,
)


def seed_budget_2026():
    """Create seed data for budget 2026 module"""
    db: Session = SessionLocal()

    try:
        print("🌱 Seeding Budget 2026 data...")

        # Get first department (IT Department)
        department = db.query(Department).first()
        if not department:
            print("❌ No departments found. Please create departments first.")
            return

        print(f"✅ Using department: {department.name} (ID: {department.id})")

        # Create scenarios
        scenarios_data = [
            {
                "year": 2026,
                "scenario_name": "Базовый сценарий 2026",
                "scenario_type": BudgetScenarioTypeEnum.BASE,
                "department_id": department.id,
                "global_growth_rate": Decimal("5.0"),
                "inflation_rate": Decimal("6.0"),
                "assumptions": {
                    "headcount_growth": "6 → 7 человек",
                    "new_projects": 2,
                    "cloud_migration": "partial",
                    "server_upgrade": True
                },
                "description": "Базовый сценарий планирования на 2026 год с умеренным ростом",
                "created_by": "admin"
            },
            {
                "year": 2026,
                "scenario_name": "Оптимистичный сценарий",
                "scenario_type": BudgetScenarioTypeEnum.OPTIMISTIC,
                "department_id": department.id,
                "global_growth_rate": Decimal("15.0"),
                "inflation_rate": Decimal("6.0"),
                "assumptions": {
                    "headcount_growth": "6 → 9 человек",
                    "new_projects": 4,
                    "cloud_migration": "full",
                    "additional_budget": "+20% на инфраструктуру"
                },
                "description": "Оптимистичный сценарий с активным ростом бизнеса",
                "created_by": "admin"
            },
            {
                "year": 2026,
                "scenario_name": "Пессимистичный сценарий",
                "scenario_type": BudgetScenarioTypeEnum.PESSIMISTIC,
                "department_id": department.id,
                "global_growth_rate": Decimal("-5.0"),
                "inflation_rate": Decimal("6.0"),
                "assumptions": {
                    "headcount_growth": "6 → 6 (заморозка найма)",
                    "new_projects": 1,
                    "cloud_migration": "postponed",
                    "cost_optimization": "aggressive"
                },
                "description": "Пессимистичный сценарий с режимом экономии",
                "created_by": "admin"
            }
        ]

        created_scenarios = []
        for scenario_data in scenarios_data:
            # Check if scenario already exists
            existing = db.query(BudgetScenario).filter(
                BudgetScenario.year == scenario_data["year"],
                BudgetScenario.scenario_type == scenario_data["scenario_type"],
                BudgetScenario.department_id == department.id
            ).first()

            if existing:
                print(f"⏭️  Scenario already exists: {scenario_data['scenario_name']}")
                created_scenarios.append(existing)
            else:
                scenario = BudgetScenario(**scenario_data)
                db.add(scenario)
                db.flush()
                created_scenarios.append(scenario)
                print(f"✅ Created scenario: {scenario_data['scenario_name']} (ID: {scenario.id})")

        # Create base version
        base_scenario = created_scenarios[0]  # Base scenario

        # Check if version already exists
        existing_version = db.query(BudgetVersion).filter(
            BudgetVersion.year == 2026,
            BudgetVersion.department_id == department.id,
            BudgetVersion.scenario_id == base_scenario.id
        ).first()

        if existing_version:
            print(f"⏭️  Version already exists: ID {existing_version.id}")
        else:
            version = BudgetVersion(
                year=2026,
                version_number=1,
                version_name="Первоначальная версия",
                department_id=department.id,
                scenario_id=base_scenario.id,
                status=BudgetVersionStatusEnum.DRAFT,
                created_by="admin",
                comments="Автоматически созданная тестовая версия",
                total_amount=Decimal("0"),
                total_capex=Decimal("0"),
                total_opex=Decimal("0"),
            )
            db.add(version)
            db.flush()
            print(f"✅ Created version: v1.0 (ID: {version.id})")

        db.commit()
        print("\n🎉 Seed data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_budget_2026()
