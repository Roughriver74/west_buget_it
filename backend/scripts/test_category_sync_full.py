"""
Тестовый скрипт для полной синхронизации категорий из 1С с иерархией
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ["DEBUG"] = "False"  # Fix validation error

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department
from app.services.odata_1c_client import OData1CClient
from app.services.category_1c_sync import Category1CSync
# from app.core.config import settings

# 1C OData credentials (hardcoded для тестирования)
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def print_category_tree(db: Session, department_id: int, parent_id: int = None, level: int = 0):
    """
    Рекурсивно вывести дерево категорий

    Args:
        db: Database session
        department_id: ID отдела
        parent_id: ID родительской категории (None для корневых)
        level: Уровень вложенности (для отступов)
    """
    # Получить категории с данным parent_id
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.department_id == department_id,
        BudgetCategory.parent_id == parent_id
    ).order_by(BudgetCategory.order_index, BudgetCategory.code_1c).all()

    for cat in categories:
        indent = "  " * level
        folder_icon = "📁" if cat.is_folder else "📄"
        print(f"{indent}{folder_icon} {cat.name} (Code: {cat.code_1c}, Type: {cat.type})")

        # Рекурсивно вывести дочерние категории
        if cat.is_folder:
            print_category_tree(db, department_id, cat.id, level + 1)


def test_category_sync_full():
    """Тестовая синхронизация всех категорий с иерархией"""

    print("=" * 80)
    print("ТЕСТ ПОЛНОЙ СИНХРОНИЗАЦИИ КАТЕГОРИЙ ИЗ 1С С ИЕРАРХИЕЙ")
    print("=" * 80)

    db: Session = SessionLocal()

    try:
        # Получить первый департамент
        department = db.query(Department).first()

        if not department:
            print("❌ Департаменты не найдены в базе. Создайте хотя бы один департамент.")
            return

        print(f"\n✅ Используем департамент: {department.name} (ID: {department.id})")

        # Создать OData клиент
        odata_client = OData1CClient(
            base_url=ODATA_1C_URL,
            username=ODATA_1C_USERNAME,
            password=ODATA_1C_PASSWORD
        )

        # Проверить подключение
        print("\n1. Проверка подключения к 1С OData...")
        if not odata_client.test_connection():
            print("❌ Не удалось подключиться к 1С")
            return
        print("✅ Подключение успешно")

        # Подсчитать текущие категории в БД
        print("\n2. Текущее состояние БД:")
        current_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id
        ).count()
        print(f"  Категорий в БД: {current_count}")

        # Создать сервис синхронизации
        sync_service = Category1CSync(
            db=db,
            odata_client=odata_client,
            department_id=department.id
        )

        # Запустить синхронизацию
        print("\n3. Запуск синхронизации (включая папки и иерархию)...")
        print("-" * 80)

        result = sync_service.sync_categories(
            batch_size=100,
            include_folders=True  # Включаем папки
        )

        print("-" * 80)
        print("\n4. Результаты синхронизации:")
        print(f"  ✅ Всего получено из 1С: {result.total_fetched}")
        print(f"  ✅ Обработано: {result.total_processed}")
        print(f"  ✅ Создано: {result.total_created}")
        print(f"  ✅ Обновлено: {result.total_updated}")
        print(f"  ✅ Пропущено: {result.total_skipped}")
        print(f"  📊 Статус: {'SUCCESS' if result.success else 'FAILED'}")

        if result.errors:
            print(f"\n  ⚠️ Ошибки ({len(result.errors)}):")
            for error in result.errors[:5]:  # Показать первые 5
                print(f"    - {error}")
            if len(result.errors) > 5:
                print(f"    ... и ещё {len(result.errors) - 5} ошибок")

        # Подсчитать результаты в БД
        print("\n5. Состояние БД после синхронизации:")
        total_categories = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id
        ).count()

        folders_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.is_folder == True
        ).count()

        items_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.is_folder == False
        ).count()

        root_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.parent_id == None
        ).count()

        with_parent_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.parent_id != None
        ).count()

        print(f"  📊 Всего категорий: {total_categories}")
        print(f"  📁 Папок: {folders_count}")
        print(f"  📄 Элементов: {items_count}")
        print(f"  🌳 Корневых элементов: {root_count}")
        print(f"  🔗 С родителями: {with_parent_count}")

        # Вывести дерево категорий (первые 50 для краткости)
        print("\n6. Дерево категорий (корневые элементы):")
        print("-" * 80)
        print_category_tree(db, department.id, parent_id=None, level=0)

        # Примеры иерархических связей
        print("\n7. Примеры иерархических связей:")
        print("-" * 80)

        # Найти категории с родителями
        categories_with_parents = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department.id,
            BudgetCategory.parent_id != None
        ).limit(5).all()

        for cat in categories_with_parents:
            parent = db.query(BudgetCategory).get(cat.parent_id)
            print(f"  '{cat.name}' → родитель: '{parent.name if parent else 'N/A'}'")

        print("\n" + "=" * 80)
        print("ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_category_sync_full()
