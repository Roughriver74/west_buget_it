#!/usr/bin/env python3
"""
Актуальные ставки страховых взносов для РФ (2024-2026)

Загружает реальные ставки страховых взносов для всех департаментов:
- 2024: Действующие ставки (раздельные)
- 2025: Единый тариф страховых взносов (ЕТВ)
- 2026: Прогноз (сохранение ЕТВ)

Usage:
    cd backend
    python scripts/seed_insurance_rates_actual.py
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
    Загрузить актуальные ставки страховых взносов для РФ
    """
    print("🔄 Загрузка актуальных ставок страховых взносов для РФ...")
    print("=" * 70)

    # Get all departments
    departments = db.query(Department).filter(Department.is_active == True).all()

    if not departments:
        print("❌ Не найдено активных департаментов. Создайте департаменты сначала.")
        return

    print(f"📊 Найдено департаментов: {len(departments)}")

    # ==================== 2024 год (ДЕЙСТВУЮЩИЕ СТАВКИ) ====================
    # До 01.01.2025 действуют раздельные тарифы
    rates_2024 = [
        {
            "rate_type": TaxTypeEnum.PENSION_FUND,
            "rate_percentage": Decimal("22.0"),
            "threshold_amount": Decimal("1917000"),  # База 2024: 1,917 млн руб
            "rate_above_threshold": Decimal("10.0"),
            "description": "ПФР - 22% (в пределах базы), 10% (свыше базы)",
            "legal_basis": "НК РФ ст. 425-426, действует до 31.12.2024",
        },
        {
            "rate_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "rate_percentage": Decimal("5.1"),
            "description": "ФОМС - 5.1% (без ограничения по базе)",
            "legal_basis": "НК РФ ст. 425, действует до 31.12.2024",
        },
        {
            "rate_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "rate_percentage": Decimal("2.9"),
            "threshold_amount": Decimal("1032000"),  # База 2024: 1,032 млн руб
            "rate_above_threshold": Decimal("0.0"),
            "description": "ФСС - 2.9% (в пределах базы), 0% (свыше базы)",
            "legal_basis": "НК РФ ст. 425, действует до 31.12.2024",
        },
        {
            "rate_type": TaxTypeEnum.INJURY_INSURANCE,
            "rate_percentage": Decimal("0.2"),
            "description": "Травматизм - 0.2% (минимальный тариф, I класс риска)",
            "legal_basis": "ФЗ-125 'Об обязательном социальном страховании от НС и ПЗ'",
        },
    ]

    # ==================== 2025 год (ЕДИНЫЙ ТАРИФ ВЗНОСОВ - ЕТВ) ====================
    # С 01.01.2025 вводится единый тариф страховых взносов (ЕТВ)
    rates_2025 = [
        {
            "rate_type": TaxTypeEnum.PENSION_FUND,
            "rate_percentage": Decimal("30.0"),  # ЕТВ включает ПФР+ФОМС+ФСС
            "threshold_amount": Decimal("2225000"),  # База 2025: ~2,225 млн руб (прогноз)
            "rate_above_threshold": Decimal("15.1"),
            "description": "ЕДИНЫЙ ТАРИФ ВЗНОСОВ (ЕТВ) - 30% в пределах базы, 15.1% свыше",
            "legal_basis": "НК РФ ст. 425 (ред. от 31.07.2023 №389-ФЗ), с 01.01.2025",
            "total_employer_burden": Decimal("30.0"),
        },
        {
            "rate_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "rate_percentage": Decimal("0.0"),  # Включен в ЕТВ
            "description": "Включен в Единый тариф взносов (ЕТВ)",
            "legal_basis": "НК РФ ст. 425, отменен с 01.01.2025",
        },
        {
            "rate_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "rate_percentage": Decimal("0.0"),  # Включен в ЕТВ
            "description": "Включен в Единый тариф взносов (ЕТВ)",
            "legal_basis": "НК РФ ст. 425, отменен с 01.01.2025",
        },
        {
            "rate_type": TaxTypeEnum.INJURY_INSURANCE,
            "rate_percentage": Decimal("0.2"),
            "description": "Травматизм - 0.2% (остается отдельным взносом)",
            "legal_basis": "ФЗ-125, не входит в ЕТВ",
        },
    ]

    # ==================== 2026 год (ПРОГНОЗ - СОХРАНЕНИЕ ЕТВ) ====================
    rates_2026 = [
        {
            "rate_type": TaxTypeEnum.PENSION_FUND,
            "rate_percentage": Decimal("30.0"),
            "threshold_amount": Decimal("2400000"),  # Прогноз базы 2026
            "rate_above_threshold": Decimal("15.1"),
            "description": "ЕДИНЫЙ ТАРИФ ВЗНОСОВ (ЕТВ) - прогноз сохранения 30%",
            "legal_basis": "НК РФ ст. 425 (прогноз без изменений)",
            "total_employer_burden": Decimal("30.0"),
        },
        {
            "rate_type": TaxTypeEnum.MEDICAL_INSURANCE,
            "rate_percentage": Decimal("0.0"),
            "description": "Включен в Единый тариф взносов (ЕТВ)",
            "legal_basis": "НК РФ ст. 425",
        },
        {
            "rate_type": TaxTypeEnum.SOCIAL_INSURANCE,
            "rate_percentage": Decimal("0.0"),
            "description": "Включен в Единый тариф взносов (ЕТВ)",
            "legal_basis": "НК РФ ст. 425",
        },
        {
            "rate_type": TaxTypeEnum.INJURY_INSURANCE,
            "rate_percentage": Decimal("0.2"),
            "description": "Травматизм - 0.2% (прогноз без изменений)",
            "legal_basis": "ФЗ-125",
        },
    ]

    created_count = 0
    updated_count = 0
    skipped_count = 0

    # Create/update rates for each department and year
    for department in departments:
        print(f"\n📁 Департамент: {department.name} (ID: {department.id})")

        # 2024 rates
        print("   📅 2024 год:")
        for rate_data in rates_2024:
            existing = db.query(InsuranceRate).filter(
                InsuranceRate.year == 2024,
                InsuranceRate.rate_type == rate_data["rate_type"],
                InsuranceRate.department_id == department.id,
            ).first()

            if existing:
                # Update existing
                for key, value in rate_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"      🔄 {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (обновлено)")
            else:
                # Create new
                rate = InsuranceRate(
                    year=2024,
                    department_id=department.id,
                    is_active=True,
                    **rate_data
                )
                db.add(rate)
                created_count += 1
                print(f"      ✅ {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (создано)")

        # 2025 rates
        print("   📅 2025 год (ЕТВ):")
        for rate_data in rates_2025:
            existing = db.query(InsuranceRate).filter(
                InsuranceRate.year == 2025,
                InsuranceRate.rate_type == rate_data["rate_type"],
                InsuranceRate.department_id == department.id,
            ).first()

            if existing:
                for key, value in rate_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"      🔄 {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (обновлено)")
            else:
                rate = InsuranceRate(
                    year=2025,
                    department_id=department.id,
                    is_active=True,
                    **rate_data
                )
                db.add(rate)
                created_count += 1
                print(f"      ✅ {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (создано)")

        # 2026 rates
        print("   📅 2026 год (прогноз):")
        for rate_data in rates_2026:
            existing = db.query(InsuranceRate).filter(
                InsuranceRate.year == 2026,
                InsuranceRate.rate_type == rate_data["rate_type"],
                InsuranceRate.department_id == department.id,
            ).first()

            if existing:
                for key, value in rate_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"      🔄 {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (обновлено)")
            else:
                rate = InsuranceRate(
                    year=2026,
                    department_id=department.id,
                    is_active=True,
                    **rate_data
                )
                db.add(rate)
                created_count += 1
                print(f"      ✅ {rate_data['rate_type'].value}: {rate_data['rate_percentage']}% (создано)")

    # Commit all changes
    db.commit()

    print("\n" + "=" * 70)
    print(f"✅ Загрузка завершена!")
    print(f"   Создано:    {created_count} записей")
    print(f"   Обновлено:  {updated_count} записей")
    print(f"   Пропущено:  {skipped_count} записей")
    print("=" * 70)

    # Summary
    print("\n📊 ИТОГОВАЯ СВОДКА ПО СТАВКАМ:")
    print("\n" + "=" * 70)
    print("2024 год (ДЕЙСТВУЮЩИЕ, раздельные тарифы)")
    print("=" * 70)
    print("  ПФР (Pension Fund):          22.0% (до 1,917 млн), 10% (свыше)")
    print("  ФОМС (Medical Insurance):     5.1% (без ограничения)")
    print("  ФСС (Social Insurance):       2.9% (до 1,032 млн), 0% (свыше)")
    print("  Травматизм (Injury):          0.2%")
    print("  ──────────────────────────────────────")
    print("  ИТОГО (стандартная нагрузка): 30.2%")

    print("\n" + "=" * 70)
    print("2025 год (ЕДИНЫЙ ТАРИФ ВЗНОСОВ - ЕТВ)")
    print("=" * 70)
    print("  🆕 ЕТВ (Единый тариф):        30.0% (до ~2,225 млн), 15.1% (свыше)")
    print("     └─ Включает: ПФР + ФОМС + ФСС")
    print("  Травматизм (отдельно):         0.2%")
    print("  ──────────────────────────────────────")
    print("  ИТОГО:                        30.2%")
    print("\n  ⚠️  Упрощение: вместо 3 взносов теперь ОДИН тариф!")

    print("\n" + "=" * 70)
    print("2026 год (ПРОГНОЗ)")
    print("=" * 70)
    print("  ЕТВ (Единый тариф):           30.0% (прогноз без изменений)")
    print("  Травматизм:                    0.2%")
    print("  ──────────────────────────────────────")
    print("  ИТОГО:                        30.2%")

    print("\n💰 ПРИМЕР РАСЧЕТА для зарплаты 100,000 руб/мес:")
    print("=" * 70)
    print("2024: 100,000 × 30.2% = 30,200 руб/мес страховых взносов")
    print("2025: 100,000 × 30.2% = 30,200 руб/мес (тот же размер, но ЕТВ)")
    print("2026: 100,000 × 30.2% = 30,200 руб/мес (прогноз)")
    print("\n✅ Ставки остаются стабильными 30.2%, меняется только механизм учета")

    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("=" * 70)
    print("1. Проверить данные в UI:")
    print("   → Откройте: http://localhost:5173/payroll-scenarios")
    print("\n2. Посмотреть ставки через API:")
    print("   → GET /api/v1/payroll-scenarios/insurance-rates?year=2025")
    print("\n3. Сравнить влияние между годами:")
    print("   → GET /api/v1/payroll-scenarios/impact-analysis?base_year=2024&target_year=2025")
    print("\n4. Создать сценарий:")
    print("   → POST /api/v1/payroll-scenarios/scenarios")
    print("   → Укажите base_year=2024, target_year=2025")
    print("\n5. Рассчитать сценарий:")
    print("   → POST /api/v1/payroll-scenarios/scenarios/{id}/calculate")
    print("=" * 70)


def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("    ЗАГРУЗКА АКТУАЛЬНЫХ СТАВОК СТРАХОВЫХ ВЗНОСОВ РФ (2024-2026)")
    print("=" * 70)

    db = SessionLocal()
    try:
        seed_insurance_rates(db)
        print("\n✅ Скрипт успешно выполнен!")
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
