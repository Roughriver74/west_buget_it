"""
Script to import AI classifier categories into database
Creates budget categories from TransactionClassifier keyword dictionaries
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department, ExpenseTypeEnum
from app.services.transaction_classifier import TransactionClassifier


def import_categories_for_department(db: Session, department_id: int):
    """
    Import AI categories for specific department
    """
    print(f"\n=== Импорт категорий для отдела ID={department_id} ===\n")

    # Get department
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        print(f"❌ Отдел с ID={department_id} не найден")
        return 0, 0

    print(f"Отдел: {department.name}")

    classifier = TransactionClassifier(db)

    created = 0
    skipped = 0

    # OPEX categories
    print("\n--- OPEX категории ---")
    for category_name in classifier.OPEX_KEYWORDS.keys():
        # Check if category already exists
        existing = db.query(BudgetCategory).filter(
            BudgetCategory.name == category_name,
            BudgetCategory.department_id == department_id
        ).first()

        if existing:
            print(f"⏭️  Пропущена (уже существует): {category_name}")
            skipped += 1
            continue

        # Create new category
        category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.OPEX,
            description=f"Автоматически создана из AI классификатора. Ключевые слова: {', '.join(classifier.OPEX_KEYWORDS[category_name][:5])}",
            department_id=department_id,
            is_active=True
        )
        db.add(category)
        print(f"✅ Создана: {category_name}")
        created += 1

    # CAPEX categories
    print("\n--- CAPEX категории ---")
    for category_name in classifier.CAPEX_KEYWORDS.keys():
        # Check if category already exists
        existing = db.query(BudgetCategory).filter(
            BudgetCategory.name == category_name,
            BudgetCategory.department_id == department_id
        ).first()

        if existing:
            print(f"⏭️  Пропущена (уже существует): {category_name}")
            skipped += 1
            continue

        # Create new category
        category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.CAPEX,
            description=f"Автоматически создана из AI классификатора. Ключевые слова: {', '.join(classifier.CAPEX_KEYWORDS[category_name][:5])}",
            department_id=department_id,
            is_active=True
        )
        db.add(category)
        print(f"✅ Создана: {category_name}")
        created += 1

    # Tax categories (considered OPEX)
    print("\n--- Налоговые категории ---")
    for category_name in classifier.TAX_KEYWORDS.keys():
        # Check if category already exists
        existing = db.query(BudgetCategory).filter(
            BudgetCategory.name == category_name,
            BudgetCategory.department_id == department_id
        ).first()

        if existing:
            print(f"⏭️  Пропущена (уже существует): {category_name}")
            skipped += 1
            continue

        # Create new category
        category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.OPEX,  # Taxes are OPEX
            description=f"Автоматически создана из AI классификатора. Ключевые слова: {', '.join(classifier.TAX_KEYWORDS[category_name][:5])}",
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
    print("📊 Импорт категорий из AI классификатора в справочник")
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
        print("1. Импортировать для всех отделов")
        print("2. Выбрать конкретный отдел")

        choice = input("\nВаш выбор (1 или 2): ").strip()

        total_created = 0
        total_skipped = 0

        if choice == "1":
            # Import for all departments
            for dept in departments:
                created, skipped = import_categories_for_department(db, dept.id)
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
                created, skipped = import_categories_for_department(db, dept_id)
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
        print("📈 Итоги импорта:")
        print(f"   Создано новых категорий: {total_created}")
        print(f"   Пропущено (уже существуют): {total_skipped}")
        print("=" * 60)

        if total_created > 0:
            print("\n✅ Категории успешно импортированы!")
            print("   Теперь AI классификатор сможет их использовать.")
        else:
            print("\nℹ️  Все категории уже существуют в базе данных.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
