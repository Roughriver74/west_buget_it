"""
Автоматическая синхронизация справочников из 1С (без интерактивного ввода)

Использование:
    python sync_1c_catalogs_auto.py --department-id 2 --all
    python sync_1c_catalogs_auto.py --department-id 2 --orgs
    python sync_1c_catalogs_auto.py --department-id 2 --cats
"""

import sys
import os
import argparse
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
    parser = argparse.ArgumentParser(description='Синхронизация справочников из 1С')
    parser.add_argument('--department-id', type=int, required=True, help='ID отдела')
    parser.add_argument('--all', action='store_true', help='Синхронизировать всё')
    parser.add_argument('--orgs', action='store_true', help='Только организации')
    parser.add_argument('--cats', action='store_true', help='Только категории')

    args = parser.parse_args()

    # Determine what to sync
    if args.all:
        sync_orgs = True
        sync_cats = True
    elif args.orgs:
        sync_orgs = True
        sync_cats = False
    elif args.cats:
        sync_orgs = False
        sync_cats = True
    else:
        print("❌ Укажите что синхронизировать: --all, --orgs или --cats")
        return 1

    print("\n" + "="*80)
    print("1C CATALOGS SYNCHRONIZATION (AUTO)")
    print("="*80)

    # Create database session
    db = SessionLocal()

    try:
        # Get department
        department = db.query(Department).filter_by(id=args.department_id).first()
        if not department:
            print(f"❌ ОШИБКА: Отдел с ID {args.department_id} не найден")
            return 1

        print(f"\nОтдел: [{department.code}] {department.name}")

        # Create 1C OData client
        print("Создание клиента 1C OData...")
        odata_client = create_1c_client_from_env()

        # Test connection
        print("Проверка подключения к 1C...")
        if not odata_client.test_connection():
            print("❌ ОШИБКА: Не удалось подключиться к 1C OData")
            return 1

        print("✅ Подключение успешно")

        # Perform synchronization
        print("\n" + "="*80)
        print("НАЧАЛО СИНХРОНИЗАЦИИ")
        print("="*80)

        if sync_orgs:
            print("\n📦 Синхронизация организаций...")
        if sync_cats:
            print("\n📋 Синхронизация категорий бюджета...")

        results = sync_all_catalogs_from_1c(
            db=db,
            odata_client=odata_client,
            department_id=department.id,
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
                for error in org_result.errors[:5]:
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
                for error in cat_result.errors[:5]:
                    print(f"    - {error}")
            print(f"  Статус: {'✅ УСПЕХ' if cat_result.success else '❌ ОШИБКА'}")

        print("\n" + "="*80)
        print("СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА")
        print("="*80)

        return 0

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
