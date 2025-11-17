"""
Скрипт для синхронизации справочников из 1С

Синхронизирует:
- Catalog_Организации → Organizations
- Catalog_СтатьиДвиженияДенежныхСредств → BudgetCategories
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import create_1c_client_from_env
from app.services.catalog_1c_sync import sync_all_catalogs_from_1c


def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("1C CATALOGS SYNCHRONIZATION")
    print("="*80)

    # Create database session
    db = SessionLocal()

    try:
        # Create 1C OData client
        print("\n1. Создание клиента 1C OData...")
        odata_client = create_1c_client_from_env()

        # Test connection
        print("2. Проверка подключения к 1C...")
        if not odata_client.test_connection():
            print("❌ ОШИБКА: Не удалось подключиться к 1C OData")
            return

        print("✅ Подключение успешно")

        # Get department
        print("\n3. Выбор отдела...")
        departments = db.query(Department).all()

        if not departments:
            print("❌ ОШИБКА: Нет отделов в базе данных")
            return

        print("\nДоступные отделы:")
        for i, dept in enumerate(departments, 1):
            print(f"  {i}. [{dept.code}] {dept.name}")

        dept_choice = input(f"\nВыберите отдел (1-{len(departments)}): ")
        try:
            dept_index = int(dept_choice) - 1
            if dept_index < 0 or dept_index >= len(departments):
                raise ValueError()
            selected_dept = departments[dept_index]
        except (ValueError, IndexError):
            print("❌ ОШИБКА: Неверный выбор отдела")
            return

        print(f"\n✅ Выбран отдел: [{selected_dept.code}] {selected_dept.name}")

        # Ask what to sync
        print("\n4. Что синхронизировать?")
        print("  1. Организации (Catalog_Организации)")
        print("  2. Категории бюджета (Catalog_СтатьиДвиженияДенежныхСредств)")
        print("  3. Всё")

        sync_choice = input("\nВыберите (1-3): ")

        sync_orgs = sync_choice in ["1", "3"]
        sync_cats = sync_choice in ["2", "3"]

        if not sync_orgs and not sync_cats:
            print("❌ ОШИБКА: Неверный выбор")
            return

        # Perform synchronization
        print("\n" + "="*80)
        print("НАЧАЛО СИНХРОНИЗАЦИИ")
        print("="*80)

        results = sync_all_catalogs_from_1c(
            db=db,
            odata_client=odata_client,
            department_id=selected_dept.id,
            sync_organizations=sync_orgs,
            sync_categories=sync_cats
        )

        # Print results
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
        print("="*80)

        if 'organizations' in results:
            org_result = results['organizations']
            print("\n📊 ОРГАНИЗАЦИИ:")
            print(f"  Получено из 1С: {org_result.total_fetched}")
            print(f"  Обработано: {org_result.total_processed}")
            print(f"  Создано: {org_result.total_created}")
            print(f"  Обновлено: {org_result.total_updated}")
            print(f"  Пропущено: {org_result.total_skipped}")
            if org_result.errors:
                print(f"  ⚠️  Ошибки: {len(org_result.errors)}")
                for error in org_result.errors[:5]:  # Show first 5 errors
                    print(f"    - {error}")
            print(f"  Статус: {'✅ УСПЕХ' if org_result.success else '❌ ОШИБКА'}")

        if 'budget_categories' in results:
            cat_result = results['budget_categories']
            print("\n📊 КАТЕГОРИИ БЮДЖЕТА:")
            print(f"  Получено из 1С: {cat_result.total_fetched}")
            print(f"  Обработано: {cat_result.total_processed}")
            print(f"  Создано: {cat_result.total_created}")
            print(f"  Обновлено: {cat_result.total_updated}")
            print(f"  Пропущено: {cat_result.total_skipped}")
            if cat_result.errors:
                print(f"  ⚠️  Ошибки: {len(cat_result.errors)}")
                for error in cat_result.errors[:5]:  # Show first 5 errors
                    print(f"    - {error}")
            print(f"  Статус: {'✅ УСПЕХ' if cat_result.success else '❌ ОШИБКА'}")

        print("\n" + "="*80)
        print("СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА")
        print("="*80)

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()
