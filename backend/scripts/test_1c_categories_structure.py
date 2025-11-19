"""
Тестовый скрипт для проверки структуры категорий из 1С
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.odata_1c_client import OData1CClient
from app.core.config import settings
import json


def test_categories_structure():
    """Тест структуры данных категорий из 1С"""

    print("=" * 80)
    print("ТЕСТ СТРУКТУРЫ КАТЕГОРИЙ ИЗ 1С")
    print("=" * 80)

    # Создать OData клиент
    client = OData1CClient(
        base_url=settings.ODATA_1C_URL,
        username=settings.ODATA_1C_USERNAME,
        password=settings.ODATA_1C_PASSWORD
    )

    # Проверить подключение
    print("\n1. Проверка подключения к 1С OData...")
    if not client.test_connection():
        print("❌ Не удалось подключиться к 1С")
        return
    print("✅ Подключение успешно")

    # Получить категории (включая папки)
    print("\n2. Получение категорий из 1С (первые 10 записей)...")
    try:
        categories = client.get_cash_flow_categories(
            top=10,
            skip=0,
            include_folders=True
        )

        if not categories:
            print("❌ Категории не найдены")
            return

        print(f"✅ Получено {len(categories)} категорий")

        # Вывести структуру первой категории
        print("\n3. Структура данных первой категории:")
        print("=" * 80)
        first_cat = categories[0]
        print(json.dumps(first_cat, indent=2, ensure_ascii=False, default=str))

        # Проверить наличие ключевых полей
        print("\n4. Проверка ключевых полей:")
        print("=" * 80)

        key_fields = [
            "Ref_Key",
            "Code",
            "Description",
            "IsFolder",
            "Parent_Key",  # Поле для родителя
            "Родитель_Key",  # Альтернативное название
            "DeletionMark",
            "Наименование",
            "Код"
        ]

        for field in key_fields:
            exists = field in first_cat
            value = first_cat.get(field, "N/A")
            status = "✅" if exists else "❌"
            print(f"{status} {field:20} = {value}")

        # Вывести все доступные поля
        print("\n5. Все доступные поля в категории:")
        print("=" * 80)
        for key in sorted(first_cat.keys()):
            print(f"  - {key}")

        # Найти папки и элементы
        print("\n6. Анализ типов категорий:")
        print("=" * 80)
        folders = [c for c in categories if c.get('IsFolder', False)]
        items = [c for c in categories if not c.get('IsFolder', False)]

        print(f"Папок (IsFolder=true): {len(folders)}")
        print(f"Элементов (IsFolder=false): {len(items)}")

        if folders:
            print("\nПример папки:")
            folder = folders[0]
            print(f"  Код: {folder.get('Code', 'N/A')}")
            print(f"  Наименование: {folder.get('Description', 'N/A')}")
            print(f"  Ref_Key: {folder.get('Ref_Key', 'N/A')}")

            # Проверить поле родителя
            parent_key = folder.get('Parent_Key') or folder.get('Родитель_Key')
            print(f"  Parent_Key: {parent_key if parent_key else 'N/A (корневой элемент)'}")

        if items:
            print("\nПример элемента:")
            item = items[0]
            print(f"  Код: {item.get('Code', 'N/A')}")
            print(f"  Наименование: {item.get('Description', 'N/A')}")
            print(f"  Ref_Key: {item.get('Ref_Key', 'N/A')}")

            # Проверить поле родителя
            parent_key = item.get('Parent_Key') or item.get('Родитель_Key')
            print(f"  Parent_Key: {parent_key if parent_key else 'N/A (корневой элемент)'}")

        # Получить больше записей для проверки общего количества
        print("\n7. Проверка общего количества категорий:")
        print("=" * 80)

        total_count = 0
        batch_size = 100
        max_batches = 20  # Максимум 2000 записей

        for batch_num in range(max_batches):
            skip = batch_num * batch_size
            batch = client.get_cash_flow_categories(
                top=batch_size,
                skip=skip,
                include_folders=True
            )

            if not batch:
                break

            total_count += len(batch)
            print(f"  Batch {batch_num + 1}: {len(batch)} категорий (skip={skip})")

            if len(batch) < batch_size:
                break

        print(f"\n✅ Всего категорий в 1С: {total_count}")

    except Exception as e:
        print(f"❌ Ошибка при получении категорий: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЁН")
    print("=" * 80)


if __name__ == "__main__":
    test_categories_structure()
