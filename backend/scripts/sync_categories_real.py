"""
Реальная синхронизация категорий из 1С через API
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
from app.db.models import Department
from app.services.odata_1c_client import OData1CClient
from app.services.category_1c_sync import Category1CSync
# 1C OData credentials
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def sync_categories_real():
    """Реальная синхронизация категорий из 1С"""

    print("=" * 80)
    print("РЕАЛЬНАЯ СИНХРОНИЗАЦИЯ КАТЕГОРИЙ ИЗ 1С")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Получить Финансовый департамент
        fin_dept = db.query(Department).filter(
            Department.name == "Финансы"
        ).first()

        if not fin_dept:
            print("❌ Финансовый отдел не найден!")
            return

        print(f"\nДепартамент: {fin_dept.name} (ID: {fin_dept.id})")

        # Создать OData клиент
        odata_client = OData1CClient(
            base_url=ODATA_1C_URL,
            username=ODATA_1C_USERNAME,
            password=ODATA_1C_PASSWORD
        )

        # Проверить подключение
        print("\n1. Проверка подключения к 1С...")
        if not odata_client.test_connection():
            print("❌ Не удалось подключиться к 1С")
            return
        print("✅ Подключение успешно")

        # Создать sync сервис
        print("\n2. Создание sync service...")
        sync_service = Category1CSync(
            db=db,
            odata_client=odata_client,
            department_id=fin_dept.id
        )

        # Запустить синхронизацию
        print("\n3. Запуск синхронизации (batch_size=1000)...")
        result = sync_service.sync_categories(
            batch_size=1000,
            include_folders=True
        )

        # Вывести результаты
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
        print("=" * 80)
        print(f"\n✅ Всего получено из 1С: {result.total_fetched}")
        print(f"✅ Всего обработано: {result.total_processed}")
        print(f"✅ Создано: {result.created}")
        print(f"✅ Обновлено: {result.updated}")
        print(f"⏭️  Пропущено: {result.skipped}")

        if result.errors:
            print(f"\n❌ Ошибок: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")

        # Проверить Аутсорс
        print("\n" + "=" * 80)
        print("ПРОВЕРКА КАТЕГОРИИ \"Аутсорс\"")
        print("=" * 80)

        from app.db.models import BudgetCategory

        autsors = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == fin_dept.id,
            BudgetCategory.external_id_1c.isnot(None),
            BudgetCategory.name.ilike('%аутсорс%')
        ).all()

        if autsors:
            print(f"\n✅ Найдено {len(autsors)} категорий:")
            for cat in autsors:
                print(f"\n  ID: {cat.id}")
                print(f"  Name: {cat.name}")
                print(f"  Code 1C: {cat.code_1c}")
                print(f"  External ID 1C: {cat.external_id_1c}")
        else:
            print("\n❌ Категория \"Аутсорс\" НЕ НАЙДЕНА после синхронизации!")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)


if __name__ == "__main__":
    sync_categories_real()
