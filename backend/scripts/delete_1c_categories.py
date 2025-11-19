"""
Скрипт для удаления всех категорий бюджета с 1C UID (external_id_1c)
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
from app.db.models import BudgetCategory, Department, ProcessedInvoice


def delete_1c_categories(department_id: int):
    """
    Удалить все категории с external_id_1c для указанного отдела

    Args:
        department_id: ID отдела
    """

    print("=" * 80)
    print("УДАЛЕНИЕ КАТЕГОРИЙ С 1C UID")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Проверить департамент
        department = db.query(Department).filter(Department.id == department_id).first()

        if not department:
            print(f"❌ Департамент с ID {department_id} не найден")
            return

        print(f"\n✅ Департамент: {department.name} (ID: {department.id})")

        # Подсчитать категории с external_id_1c
        categories_with_1c = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department_id,
            BudgetCategory.external_id_1c.isnot(None)
        ).all()

        total_count = len(categories_with_1c)

        if total_count == 0:
            print("\n✅ Нет категорий с 1C UID для удаления")
            return

        print(f"\n📊 Найдено категорий с 1C UID: {total_count}")

        # Показать примеры
        print("\nПримеры категорий для удаления:")
        for i, cat in enumerate(categories_with_1c[:5]):
            folder_icon = "📁" if cat.is_folder else "📄"
            print(f"  {folder_icon} {cat.name} (Code: {cat.code_1c}, UID: {cat.external_id_1c[:8]}...)")

        if total_count > 5:
            print(f"  ... и ещё {total_count - 5} категорий")

        # Подтверждение
        print(f"\n⚠️  ВНИМАНИЕ: Будет удалено {total_count} категорий!")
        confirm = input("Продолжить? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("\n❌ Отменено пользователем")
            return

        # Шаг 1: Обнулить ссылки в processed_invoices
        print(f"\n1️⃣  Обнуление ссылок в обработанных счетах...")

        category_ids = [cat.id for cat in categories_with_1c]

        affected_invoices = db.query(ProcessedInvoice).filter(
            ProcessedInvoice.category_id.in_(category_ids)
        ).count()

        if affected_invoices > 0:
            print(f"  📊 Найдено счетов со ссылками на категории: {affected_invoices}")

            db.query(ProcessedInvoice).filter(
                ProcessedInvoice.category_id.in_(category_ids)
            ).update(
                {"category_id": None},
                synchronize_session=False
            )

            db.flush()
            print(f"  ✅ Ссылки обнулены")
        else:
            print(f"  ✅ Нет ссылок для обнуления")

        # Шаг 2: Удалить категории
        print(f"\n2️⃣  Удаление категорий...")

        deleted_count = 0
        for cat in categories_with_1c:
            try:
                db.delete(cat)
                deleted_count += 1

                if deleted_count % 50 == 0:
                    db.flush()
                    print(f"  Удалено: {deleted_count}/{total_count}")

            except Exception as e:
                print(f"  ⚠️  Ошибка при удалении {cat.name}: {e}")

        # Коммит
        db.commit()
        print(f"\n✅ Успешно удалено {deleted_count} категорий с 1C UID")

        # Проверить результат
        remaining = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department_id,
            BudgetCategory.external_id_1c.isnot(None)
        ).count()

        total_remaining = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department_id
        ).count()

        print(f"\n📊 После удаления:")
        print(f"  Категорий с 1C UID: {remaining}")
        print(f"  Всего категорий: {total_remaining}")

        print("\n" + "=" * 80)
        print("УДАЛЕНИЕ ЗАВЕРШЕНО!")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def delete_all_departments():
    """Удалить категории с 1C UID для всех департаментов"""

    print("=" * 80)
    print("УДАЛЕНИЕ КАТЕГОРИЙ С 1C UID ДЛЯ ВСЕХ ОТДЕЛОВ")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Получить все департаменты
        departments = db.query(Department).all()

        if not departments:
            print("❌ Департаменты не найдены")
            return

        print(f"\nНайдено департаментов: {len(departments)}")
        for dept in departments:
            print(f"  - {dept.name} (ID: {dept.id})")

        # Подтверждение
        confirm = input("\n⚠️  Удалить категории с 1C UID из ВСЕХ отделов? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("\n❌ Отменено")
            return

        # Удалить для каждого департамента
        for dept in departments:
            print(f"\n{'='*80}")
            print(f"Обработка отдела: {dept.name}")
            print(f"{'='*80}")

            categories_with_1c = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == dept.id,
                BudgetCategory.external_id_1c.isnot(None)
            ).all()

            if not categories_with_1c:
                print(f"  ✅ Нет категорий с 1C UID")
                continue

            print(f"  📊 Найдено: {len(categories_with_1c)} категорий")

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

            # Удалить категории
            deleted_count = 0
            for cat in categories_with_1c:
                try:
                    db.delete(cat)
                    deleted_count += 1
                except Exception as e:
                    print(f"    ⚠️  Ошибка: {e}")

            db.flush()
            print(f"  ✅ Удалено: {deleted_count}")

        # Коммит всех изменений
        db.commit()
        print("\n✅ Удаление завершено для всех отделов!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Удаление категорий с 1C UID")
    parser.add_argument(
        "--department-id",
        type=int,
        help="ID отдела (если не указан, удаляются из всех отделов)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Удалить из всех отделов без интерактивного подтверждения"
    )

    args = parser.parse_args()

    if args.department_id:
        delete_1c_categories(args.department_id)
    else:
        delete_all_departments()
