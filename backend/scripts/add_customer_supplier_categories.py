"""
Script to add default categories for customers (income) and suppliers (expense)
Required by TZ: Уточнение тз транзакций.md
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department, ExpenseTypeEnum


def add_customer_supplier_categories(db: Session, department_id: int):
    """
    Add customer/supplier categories for specific department
    """
    print(f"\n=== Добавление категорий для отдела ID={department_id} ===\n")

    # Get department
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        print(f"❌ Отдел с ID={department_id} не найден")
        return 0, 0

    print(f"Отдел: {department.name}")

    created = 0
    skipped = 0

    # Category 1: Покупатели (приход) - Income from customers
    category_name = "Покупатели (приход)"
    existing = db.query(BudgetCategory).filter(
        BudgetCategory.name == category_name,
        BudgetCategory.department_id == department_id
    ).first()

    if existing:
        print(f"⏭️  Пропущена (уже существует): {category_name}")
        skipped += 1
    else:
        category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.OPEX,  # Revenue category
            description="Доходы от покупателей (CREDIT транзакции). Автоматически создана для категоризации поступлений.",
            department_id=department_id,
            is_active=True
        )
        db.add(category)
        print(f"✅ Создана: {category_name}")
        created += 1

    # Category 2: Поставщики (расход) - Expenses to suppliers
    category_name = "Поставщики (расход)"
    existing = db.query(BudgetCategory).filter(
        BudgetCategory.name == category_name,
        BudgetCategory.department_id == department_id
    ).first()

    if existing:
        print(f"⏭️  Пропущена (уже существует): {category_name}")
        skipped += 1
    else:
        category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.OPEX,  # Operating expense
            description="Расходы на поставщиков (DEBIT транзакции). Автоматически создана для категоризации расходов.",
            department_id=department_id,
            is_active=True
        )
        db.add(category)
        print(f"✅ Создана: {category_name}")
        created += 1

    db.commit()

    return created, skipped


def main():
    """
    Main function
    """
    print("=" * 60)
    print("📊 Добавление категорий Покупатели/Поставщики")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Get all departments
        departments = db.query(Department).filter(Department.is_active == True).all()

        if not departments:
            print("❌ Нет активных отделов в базе данных")
            return

        print(f"\nНайдено отделов: {len(departments)}")
        print("\nВыберите опцию:")
        print("1. Добавить для всех отделов")
        print("2. Выбрать конкретный отдел")

        choice = input("\nВаш выбор (1 или 2): ").strip()

        total_created = 0
        total_skipped = 0

        if choice == "1":
            # Add for all departments
            for dept in departments:
                created, skipped = add_customer_supplier_categories(db, dept.id)
                total_created += created
                total_skipped += skipped

        elif choice == "2":
            # Show departments list
            print("\nДоступные отделы:")
            for dept in departments:
                print(f"  {dept.id}. {dept.name}")

            dept_id = input("\nВведите ID отдела: ").strip()

            try:
                dept_id = int(dept_id)
                created, skipped = add_customer_supplier_categories(db, dept_id)
                total_created += created
                total_skipped += skipped
            except ValueError:
                print("❌ Некорректный ID отдела")
                return

        else:
            print("❌ Некорректный выбор")
            return

        # Summary
        print("\n" + "=" * 60)
        print("📈 Итоги:")
        print(f"   Создано новых категорий: {total_created}")
        print(f"   Пропущено (уже существуют): {total_skipped}")
        print("=" * 60)

        if total_created > 0:
            print("\n✅ Категории успешно добавлены!")
            print("   Теперь они доступны для категоризации транзакций.")
        else:
            print("\nℹ️  Категории уже существуют в базе данных.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
