#!/usr/bin/env python3
"""
Создать тестовые данные по зарплатам за 2024 год

Копирует данные из 2025 в 2024 со снижением на 5%
для возможности сравнения сценариев.

Usage:
    cd backend
    DEBUG=true python scripts/create_2024_payroll_data.py
"""
import sys
import os
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import PayrollActual, Department


def create_2024_data(db: Session):
    """
    Создать тестовые данные за 2024 год на основе 2025
    """
    print("=" * 70)
    print("    СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ПО ЗАРПЛАТАМ ЗА 2024 ГОД")
    print("=" * 70)

    # Получить все записи за 2025
    records_2025 = db.query(PayrollActual).filter(
        PayrollActual.year == 2025
    ).all()

    if not records_2025:
        print("❌ Не найдено данных за 2025 год. Сначала создайте данные за 2025.")
        return

    print(f"\n📊 Найдено записей за 2025: {len(records_2025)}")

    # Проверить, есть ли уже данные за 2024
    existing_2024 = db.query(PayrollActual).filter(
        PayrollActual.year == 2024
    ).count()

    if existing_2024 > 0:
        print(f"\n⚠️  Внимание: уже есть {existing_2024} записей за 2024 год.")
        response = input("Удалить их и создать заново? (yes/no): ")
        if response.lower() != 'yes':
            print("Отменено.")
            return

        # Удалить существующие записи
        db.query(PayrollActual).filter(PayrollActual.year == 2024).delete()
        db.commit()
        print("✅ Удалены старые записи за 2024 год")

    # Создать данные за 2024 (снижение на 5% относительно 2025)
    created_count = 0

    print("\n🔄 Создание записей за 2024 год...")
    print("   (Зарплаты на 5% ниже, чем в 2025)")

    for record in records_2025:
        # Снизить зарплату на 5%
        new_base_salary = record.base_salary_paid * Decimal('0.95')
        new_other_payments = record.other_payments_paid * Decimal('0.95')
        new_total = new_base_salary + new_other_payments

        # Создать новую запись за 2024
        new_record = PayrollActual(
            year=2024,  # Изменить год
            month=record.month,
            employee_id=record.employee_id,
            department_id=record.department_id,
            base_salary_paid=new_base_salary,
            other_payments_paid=new_other_payments,
            total_paid=new_total,
            payment_date=None,  # Можно указать дату, если нужно
            expense_id=None,
            notes="Тестовые данные (скопировано из 2025, -5%)",
            monthly_bonus_paid=record.monthly_bonus_paid * Decimal('0.95'),
            quarterly_bonus_paid=record.quarterly_bonus_paid * Decimal('0.95'),
            annual_bonus_paid=record.annual_bonus_paid * Decimal('0.95'),
            income_tax_rate=record.income_tax_rate,
            income_tax_amount=record.income_tax_amount * Decimal('0.95'),
            social_tax_amount=record.social_tax_amount * Decimal('0.95'),
        )

        db.add(new_record)
        created_count += 1

        if created_count % 10 == 0:
            print(f"   ✅ Создано {created_count} записей...")

    # Commit all changes
    db.commit()

    print(f"\n✅ Создано записей за 2024: {created_count}")

    # Summary
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("=" * 70)

    # Calculate totals
    total_2024 = db.query(
        PayrollActual
    ).filter(
        PayrollActual.year == 2024
    ).count()

    total_salary_2024 = db.query(
        db.func.sum(PayrollActual.base_salary_paid)
    ).filter(
        PayrollActual.year == 2024
    ).scalar() or Decimal('0')

    total_salary_2025 = db.query(
        db.func.sum(PayrollActual.base_salary_paid)
    ).filter(
        PayrollActual.year == 2025
    ).scalar() or Decimal('0')

    print(f"\n2024 год:")
    print(f"  Записей: {total_2024}")
    print(f"  Общая зарплата: {float(total_salary_2024):,.0f} ₽")

    print(f"\n2025 год:")
    print(f"  Записей: {len(records_2025)}")
    print(f"  Общая зарплата: {float(total_salary_2025):,.0f} ₽")

    difference = total_salary_2025 - total_salary_2024
    difference_percent = (difference / total_salary_2024 * 100) if total_salary_2024 > 0 else 0

    print(f"\nРазница:")
    print(f"  {float(difference):,.0f} ₽ (+{float(difference_percent):.1f}%)")

    print("\n" + "=" * 70)
    print("🎯 СЛЕДУЮЩИЕ ШАГИ")
    print("=" * 70)
    print("\n1. Теперь можно создать сценарий:")
    print("   - Базовый год: 2024")
    print("   - Целевой год: 2025")
    print("   - Изменение штата: 0%")
    print("   - Изменение зарплат: 0%")
    print("\n2. Нажмите 'Рассчитать'")
    print("\n3. Система покажет:")
    print("   - Разницу в ФОТ между 2024 и 2025")
    print("   - Влияние изменения ставок страховых взносов")
    print("   - Рекомендации по оптимизации")
    print("\n" + "=" * 70)


def main():
    """Main entry point"""
    print()
    db = SessionLocal()
    try:
        create_2024_data(db)
        print("\n✅ Скрипт успешно выполнен!\n")
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
