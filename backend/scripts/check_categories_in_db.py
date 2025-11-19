"""
Проверка категорий в БД
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department


def check_categories_in_db():
    """Проверка категорий в БД"""

    print("=" * 80)
    print("ПРОВЕРКА КАТЕГОРИЙ В БД")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Получить все департаменты
        departments = db.query(Department).all()

        for dept in departments:
            print(f"\n{'='*80}")
            print(f"Департамент: {dept.name} (ID: {dept.id})")
            print(f"{'='*80}")

            # Всего категорий
            total = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == dept.id
            ).count()

            # С external_id_1c
            with_1c_uid = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == dept.id,
                BudgetCategory.external_id_1c.isnot(None)
            ).count()

            # Без external_id_1c
            without_1c_uid = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == dept.id,
                BudgetCategory.external_id_1c.is_(None)
            ).count()

            print(f"📊 Всего категорий: {total}")
            print(f"  └─ С 1C UID: {with_1c_uid}")
            print(f"  └─ Без 1C UID: {without_1c_uid}")

            # Папки и элементы с 1C UID
            if with_1c_uid > 0:
                folders = db.query(BudgetCategory).filter(
                    BudgetCategory.department_id == dept.id,
                    BudgetCategory.external_id_1c.isnot(None),
                    BudgetCategory.is_folder == True
                ).count()

                items = db.query(BudgetCategory).filter(
                    BudgetCategory.department_id == dept.id,
                    BudgetCategory.external_id_1c.isnot(None),
                    BudgetCategory.is_folder == False
                ).count()

                print(f"\n  С 1C UID:")
                print(f"    📁 Папок: {folders}")
                print(f"    📄 Элементов: {items}")

            # Показать примеры категорий с 1C UID
            if with_1c_uid > 0:
                print(f"\n  Примеры категорий с 1C UID:")
                examples = db.query(BudgetCategory).filter(
                    BudgetCategory.department_id == dept.id,
                    BudgetCategory.external_id_1c.isnot(None)
                ).limit(5).all()

                for cat in examples:
                    folder_icon = "📁" if cat.is_folder else "📄"
                    parent_info = f" → parent_id={cat.parent_id}" if cat.parent_id else ""
                    print(f"    {folder_icon} {cat.name} (Code: {cat.code_1c}){parent_info}")

        print("\n" + "=" * 80)
        print("ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    check_categories_in_db()
