#!/usr/bin/env python3
"""
Seed script for Insurance Rates (2025 and 2026)

Загружает ставки страховых взносов для 2025 и 2026 годов
для всех департаментов.

Usage:
    python scripts/seed_insurance_rates_2025_2026.py
"""
import sys
import os
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import InsuranceRate, Department, TaxTypeEnum


def seed_insurance_rates(db: Session):
    """
    Загрузить ставки страховых взносов для 2025 и 2026 годов
    """
    print("🔄 Starting insurance rates seed...")

    # Get all departments
    departments = db.query(Department).filter(Department.is_active == True).all()

    if not departments:
        print("❌ No active departments found. Please create departments first.")
        return

    print(f"📊 Found {len(departments)} active departments")

    # ==================== Ставки 2025 (текущие) ====================
    rates_2025 = [
        {
            "rate_type": TaxTypeEnum.PENSION_FUND,
            "rate_percentage": Decimal("22.0"),
            "description": "Пенсионный фонд (ПФР) - стандартная ставка 2025",
            "legal_basis": "НК РФ ст. 425-426",
        },
        {
            "rate_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "rate_percentage": Decimal("5.1"),
            "description": "Медицинское страхование (ФОМС) - стандартная ставка 2025",
            "legal_basis": "НК РФ ст. 425",
        },
        {
            "rate_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "rate_percentage": Decimal("2.9"),
            "description": "Социальное страхование (ФСС) - стандартная ставка 2025",
            "legal_basis": "НК РФ ст. 425",
        },
        {
            "rate_type": TaxTypeEnum.INJURY_INSURANCE,
            "rate_percentage": Decimal("0.2"),
            "description": "Страхование от несчастных случаев - минимальный тариф",
            "legal_basis": "ФЗ-125 'Об обязательном социальном страховании'",
        },
    ]

    # ==================== Ставки 2026 (планируемые изменения) ====================
    rates_2026 = [
        {
            "rate_type": TaxTypeEnum.PENSION_FUND,
            "rate_percentage": Decimal("30.0"),
            "description": "Пенсионный фонд (ПФР) - ПОВЫШЕНИЕ с 22% до 30%",
            "legal_basis": "Планируемые изменения в НК РФ (проект)",
            "total_employer_burden": Decimal("39.7"),  # Общая нагрузка
        },
        {
            "rate_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "rate_percentage": Decimal("6.0"),
            "description": "Медицинское страхование (ФОМС) - ПОВЫШЕНИЕ с 5.1% до 6%",
            "legal_basis": "Планируемые изменения в НК РФ (проект)",
        },
        {
            "rate_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "rate_percentage": Decimal("3.5"),
            "description": "Социальное страхование (ФСС) - ПОВЫШЕНИЕ с 2.9% до 3.5%",
            "legal_basis": "Планируемые изменения в НК РФ (проект)",
        },
        {
            "rate_type": TaxTypeEnum.INJURY_INSURANCE,
            "rate_percentage": Decimal("0.2"),
            "description": "Страхование от несчастных случаев - без изменений",
            "legal_basis": "ФЗ-125 'Об обязательном социальном страховании'",
        },
    ]

    created_count = 0
    skipped_count = 0

    # Create rates for each department and year
    for department in departments:
        print(f"\n📁 Processing department: {department.name}")

        # 2025 rates
        for rate_data in rates_2025:
            # Check if rate already exists
            existing = db.query(InsuranceRate).filter(
                InsuranceRate.year == 2025,
                InsuranceRate.rate_type == rate_data["rate_type"],
                InsuranceRate.department_id == department.id,
            ).first()

            if existing:
                print(f"   ⏭️  {rate_data['rate_type'].value} 2025 - already exists")
                skipped_count += 1
                continue

            # Create new rate
            rate = InsuranceRate(
                year=2025,
                department_id=department.id,
                **rate_data
            )
            db.add(rate)
            created_count += 1
            print(f"   ✅ {rate_data['rate_type'].value} 2025 - {rate_data['rate_percentage']}%")

        # 2026 rates
        for rate_data in rates_2026:
            # Check if rate already exists
            existing = db.query(InsuranceRate).filter(
                InsuranceRate.year == 2026,
                InsuranceRate.rate_type == rate_data["rate_type"],
                InsuranceRate.department_id == department.id,
            ).first()

            if existing:
                print(f"   ⏭️  {rate_data['rate_type'].value} 2026 - already exists")
                skipped_count += 1
                continue

            # Create new rate
            rate = InsuranceRate(
                year=2026,
                department_id=department.id,
                **rate_data
            )
            db.add(rate)
            created_count += 1
            print(f"   ✅ {rate_data['rate_type'].value} 2026 - {rate_data['rate_percentage']}% (CHANGED)")

    # Commit all changes
    db.commit()

    print("\n" + "=" * 60)
    print(f"✅ Seed completed!")
    print(f"📊 Created: {created_count} rates")
    print(f"⏭️  Skipped: {skipped_count} rates (already exist)")
    print("=" * 60)

    # Summary
    print("\n📈 Summary of changes:")
    print("\n2025 (Current rates):")
    print("  • ПФР (Pension):     22.0%")
    print("  • ФОМС (Medical):     5.1%")
    print("  • ФСС (Social):       2.9%")
    print("  • НС (Injury):        0.2%")
    print("  • TOTAL:             30.2%")

    print("\n2026 (Planned changes):")
    print("  • ПФР (Pension):     30.0%  (+8.0 п.п.)  ⚠️")
    print("  • ФОМС (Medical):     6.0%  (+0.9 п.п.)  ⚠️")
    print("  • ФСС (Social):       3.5%  (+0.6 п.п.)  ⚠️")
    print("  • НС (Injury):        0.2%  (no change)")
    print("  • TOTAL:             39.7%  (+9.5 п.п.)  ⚠️")

    print("\n💰 Impact example (for 100,000 RUB salary):")
    print(f"  2025: {100000 * 0.302:,.0f} RUB insurance contributions")
    print(f"  2026: {100000 * 0.397:,.0f} RUB insurance contributions")
    print(f"  Increase: +{100000 * (0.397 - 0.302):,.0f} RUB (+{((0.397 - 0.302) / 0.302 * 100):.1f}%)")

    print("\n🎯 Next steps:")
    print("  1. Use API to view rates: GET /api/v1/payroll-scenarios/insurance-rates?year=2026")
    print("  2. Create scenarios: POST /api/v1/payroll-scenarios/scenarios")
    print("  3. Compare impact: GET /api/v1/payroll-scenarios/impact-analysis?base_year=2025&target_year=2026")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Insurance Rates Seed Script (2025 vs 2026)")
    print("=" * 60)

    db = SessionLocal()
    try:
        seed_insurance_rates(db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
