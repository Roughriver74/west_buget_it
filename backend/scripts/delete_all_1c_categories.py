"""
Удалить все категории с external_id_1c из ВСЕХ департаментов
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
from app.db.models import BudgetCategory, Department, ProcessedInvoice, BusinessOperationMapping


def delete_all_1c_categories():
    """Удалить все категории с external_id_1c из всех департаментов"""

    print("=" * 80)
    print("УДАЛЕНИЕ ВСЕХ КАТЕГОРИЙ С 1C UID")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Получить все департаменты
        departments = db.query(Department).all()

        print(f"\nНайдено департаментов: {len(departments)}")

        grand_total = 0

        for dept in departments:
            print(f"\n{'='*80}")
            print(f"Департамент: {dept.name} (ID: {dept.id})")
            print(f"{'='*80}")

            # Найти все категории с 1C UID
            categories_with_1c = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == dept.id,
                BudgetCategory.external_id_1c.isnot(None)
            ).all()

            if not categories_with_1c:
                print(f"  ✅ Нет категорий с 1C UID")
                continue

            total_count = len(categories_with_1c)
            print(f"  📊 Найдено: {total_count} категорий с 1C UID")

            # Обнулить ссылки в processed_invoices
            category_ids = [cat.id for cat in categories_with_1c]

            affected_invoices = db.query(ProcessedInvoice).filter(
                ProcessedInvoice.category_id.in_(category_ids)
            ).count()

            if affected_invoices > 0:
                print(f"  📊 Обнуление ссылок в {affected_invoices} счетах...")
                db.query(ProcessedInvoice).filter(
                    ProcessedInvoice.category_id.in_(category_ids)
                ).update(
                    {"category_id": None},
                    synchronize_session=False
                )
                db.flush()
                print(f"  ✅ Ссылки в счетах обнулены")

            # Обнулить ссылки в business_operation_mappings
            affected_mappings = db.query(BusinessOperationMapping).filter(
                BusinessOperationMapping.category_id.in_(category_ids)
            ).count()

            if affected_mappings > 0:
                print(f"  📊 Обнуление ссылок в {affected_mappings} маппингах...")
                db.query(BusinessOperationMapping).filter(
                    BusinessOperationMapping.category_id.in_(category_ids)
                ).update(
                    {"category_id": None},
                    synchronize_session=False
                )
                db.flush()
                print(f"  ✅ Ссылки в маппингах обнулены")

            # Удалить категории
            deleted_count = 0
            for cat in categories_with_1c:
                try:
                    db.delete(cat)
                    deleted_count += 1

                    if deleted_count % 50 == 0:
                        db.flush()
                        print(f"  ⏳ Удалено: {deleted_count}/{total_count}")

                except Exception as e:
                    print(f"    ⚠️  Ошибка при удалении {cat.name}: {e}")

            db.commit()
            grand_total += deleted_count

            print(f"  ✅ Удалено: {deleted_count} категорий")

        print(f"\n{'='*80}")
        print(f"ИТОГО УДАЛЕНО: {grand_total} категорий")
        print(f"{'='*80}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Подтверждение
    print("\n⚠️  ВНИМАНИЕ: Будут удалены ВСЕ категории с 1C UID из ВСЕХ департаментов!")
    confirm = input("Продолжить? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("\n❌ Отменено пользователем")
    else:
        delete_all_1c_categories()
