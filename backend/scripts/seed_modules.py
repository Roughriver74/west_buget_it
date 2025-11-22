#!/usr/bin/env python3
"""
Seed script for initial module data

This script creates all available modules and assigns BUDGET_CORE to all existing organizations
to ensure backward compatibility.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Module, OrganizationModule, Organization


# Module definitions
MODULES = [
    {
        "code": "BUDGET_CORE",
        "name": "Budget Core",
        "description": "Базовая функциональность: заявки на расход, бюджетирование, справочники, мультитенантность",
        "version": "1.0.0",
        "dependencies": [],
        "icon": "DollarOutlined",
        "sort_order": 1,
    },
    {
        "code": "AI_FORECAST",
        "name": "AI & Forecasting",
        "description": "AI-классификация транзакций, OCR счетов, автоматизация",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "RobotOutlined",
        "sort_order": 2,
    },
    {
        "code": "CREDIT_PORTFOLIO",
        "name": "Credit Portfolio Management",
        "description": "Управление кредитным портфелем, FTP авто-импорт, cash flow анализ",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "BankOutlined",
        "sort_order": 3,
    },
    {
        "code": "REVENUE_BUDGET",
        "name": "Revenue Budget",
        "description": "Планирование доходов, Customer LTV, сезонность, P&L отчеты",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "LineChartOutlined",
        "sort_order": 4,
    },
    {
        "code": "PAYROLL_KPI",
        "name": "Payroll & KPI System",
        "description": "Расширенное управление ФОТ, KPI сотрудников, бонусы по результатам",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "TeamOutlined",
        "sort_order": 5,
    },
    {
        "code": "HR_DEPARTMENT",
        "name": "HR Department (Timesheet)",
        "description": "Табель учета рабочего времени, управление рабочими часами сотрудников, интеграция с расчетом ЗП",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "ClockCircleOutlined",
        "sort_order": 6,
    },
    {
        "code": "INTEGRATIONS_1C",
        "name": "1C Integration",
        "description": "Интеграция с 1С через OData, синхронизация справочников, фоновые задачи",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "ApiOutlined",
        "sort_order": 7,
    },
    {
        "code": "FOUNDER_DASHBOARD",
        "name": "Founder Dashboard",
        "description": "Executive панель для руководителя, кросс-департментская аналитика",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "DashboardOutlined",
        "sort_order": 8,
    },
    {
        "code": "ADVANCED_ANALYTICS",
        "name": "Advanced Analytics",
        "description": "Продвинутая аналитика, прогнозирование, кастомные отчеты",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "BarChartOutlined",
        "sort_order": 9,
    },
    {
        "code": "MULTI_DEPARTMENT",
        "name": "Multi-Department",
        "description": "Расширенная мультитенантность, сводные отчеты по отделам",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE"],
        "icon": "ClusterOutlined",
        "sort_order": 10,
    },
    {
        "code": "INVOICE_PROCESSING",
        "name": "Invoice Processing (AI OCR)",
        "description": "Автоматическое распознавание счетов через OCR и GPT-4o, создание заявок на расход в 1С",
        "version": "1.0.0",
        "dependencies": ["BUDGET_CORE", "INTEGRATIONS_1C"],
        "icon": "FileTextOutlined",
        "sort_order": 11,
    },
]


def seed_modules(db: Session):
    """Create all modules in the database"""
    print("=" * 80)
    print("SEEDING MODULES")
    print("=" * 80)

    created_count = 0
    updated_count = 0

    for module_data in MODULES:
        # Check if module exists
        existing = db.query(Module).filter_by(code=module_data["code"]).first()

        if existing:
            # Update existing module
            for key, value in module_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            print(f"✓ Updated: {module_data['code']} - {module_data['name']}")
            updated_count += 1
        else:
            # Create new module
            module = Module(**module_data)
            db.add(module)
            print(f"✓ Created: {module_data['code']} - {module_data['name']}")
            created_count += 1

    db.commit()

    print(f"\nModules seeded: {created_count} created, {updated_count} updated")
    return created_count, updated_count


def assign_core_to_organizations(db: Session):
    """Assign BUDGET_CORE module to all existing organizations for backward compatibility"""
    print("\n" + "=" * 80)
    print("ASSIGNING BUDGET_CORE TO ORGANIZATIONS")
    print("=" * 80)

    # Get BUDGET_CORE module
    core_module = db.query(Module).filter_by(code="BUDGET_CORE").first()
    if not core_module:
        print("❌ ERROR: BUDGET_CORE module not found. Run seed_modules first.")
        return 0

    # Get all organizations
    organizations = db.query(Organization).filter_by(is_active=True).all()

    if not organizations:
        print("ℹ️  No organizations found. Skipping assignment.")
        return 0

    assigned_count = 0
    skipped_count = 0

    for org in organizations:
        # Check if already assigned
        existing = db.query(OrganizationModule).filter_by(
            organization_id=org.id,
            module_id=core_module.id
        ).first()

        if existing:
            print(f"  ⊙ Skipped: {org.name} (already has BUDGET_CORE)")
            skipped_count += 1
        else:
            # Assign BUDGET_CORE
            org_module = OrganizationModule(
                organization_id=org.id,
                module_id=core_module.id,
                enabled_at=datetime.utcnow(),
                expires_at=None,  # No expiration
                limits=None,
                is_active=True
            )
            db.add(org_module)
            print(f"  ✓ Assigned: {org.name}")
            assigned_count += 1

    db.commit()

    print(f"\nOrganizations processed: {assigned_count} assigned, {skipped_count} skipped")
    return assigned_count


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("MODULE SYSTEM SEED SCRIPT")
    print("=" * 80)
    print("This script will:")
    print("1. Create/update all module definitions")
    print("2. Assign BUDGET_CORE to all active organizations")
    print("=" * 80)

    # Confirm
    response = input("\nContinue? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    db = SessionLocal()
    try:
        # Seed modules
        created, updated = seed_modules(db)

        # Assign BUDGET_CORE to organizations
        assigned = assign_core_to_organizations(db)

        print("\n" + "=" * 80)
        print("✓ SEED COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Modules: {created} created, {updated} updated")
        print(f"Organizations: {assigned} assigned BUDGET_CORE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
