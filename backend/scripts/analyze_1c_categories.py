"""
Анализ категорий из 1С для выявления проблемных записей
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

from app.services.odata_1c_client import OData1CClient

# 1C OData credentials (hardcoded для тестирования)
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def analyze_1c_categories():
    """Анализ категорий из 1С"""

    print("=" * 80)
    print("АНАЛИЗ КАТЕГОРИЙ ИЗ 1С")
    print("=" * 80)

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

    # Загрузить ВСЕ категории
    print("\n2. Загрузка всех категорий из 1С...")

    all_categories = []
    batch_size = 100
    skip = 0

    while True:
        batch = odata_client.get_cash_flow_categories(
            top=batch_size,
            skip=skip,
            include_folders=True
        )

        if not batch:
            break

        all_categories.extend(batch)
        print(f"  Загружено: {len(all_categories)} категорий")

        skip += batch_size

        if len(batch) < batch_size:
            break

        # Защита от бесконечного цикла
        if skip > 10000:
            break

    total_count = len(all_categories)
    print(f"\n✅ Всего загружено: {total_count} категорий")

    # Анализ проблем
    print("\n3. Анализ проблемных записей:")
    print("=" * 80)

    # Пустой Ref_Key
    empty_ref_key = [
        cat for cat in all_categories
        if not cat.get("Ref_Key") or cat.get("Ref_Key") == "00000000-0000-0000-0000-000000000000"
    ]

    print(f"\n📊 Категорий с пустым Ref_Key: {len(empty_ref_key)}")
    if empty_ref_key:
        print("  Примеры:")
        for i, cat in enumerate(empty_ref_key[:5]):
            print(f"    - Code: {cat.get('Code', 'N/A')}, Description: {cat.get('Description', 'N/A')}")

    # Нет имени
    no_name = [
        cat for cat in all_categories
        if not (cat.get("Description") or cat.get("Наименование"))
    ]

    print(f"\n📊 Категорий без имени: {len(no_name)}")
    if no_name:
        print("  Примеры:")
        for i, cat in enumerate(no_name[:5]):
            print(f"    - Code: {cat.get('Code', 'N/A')}, Ref_Key: {cat.get('Ref_Key', 'N/A')[:8]}...")

    # Помечены на удаление
    deletion_mark = [
        cat for cat in all_categories
        if cat.get("DeletionMark", False)
    ]

    print(f"\n📊 Категорий с пометкой удаления: {len(deletion_mark)}")
    if deletion_mark:
        print("  Примеры:")
        for i, cat in enumerate(deletion_mark[:5]):
            print(f"    - {cat.get('Description', 'N/A')} (Code: {cat.get('Code', 'N/A')})")

    # Папки vs Элементы
    folders = [cat for cat in all_categories if cat.get("IsFolder", False)]
    items = [cat for cat in all_categories if not cat.get("IsFolder", False)]

    print(f"\n📁 Папок: {len(folders)}")
    print(f"📄 Элементов: {len(items)}")

    # Корневые элементы
    root_elements = [
        cat for cat in all_categories
        if not cat.get("Parent_Key") or cat.get("Parent_Key") == "00000000-0000-0000-0000-000000000000"
    ]

    print(f"\n🌳 Корневых элементов: {len(root_elements)}")

    # Валидные категории (которые будут созданы)
    valid_categories = [
        cat for cat in all_categories
        if (cat.get("Ref_Key") and cat.get("Ref_Key") != "00000000-0000-0000-0000-000000000000")
        and (cat.get("Description") or cat.get("Наименование"))
    ]

    print(f"\n✅ Валидных категорий (будут созданы): {len(valid_categories)}")

    # Проблемные категории
    problematic = total_count - len(valid_categories)
    print(f"⚠️  Проблемных категорий (будут пропущены): {problematic}")

    # Детальная разбивка
    print("\n4. Детальная разбивка:")
    print("=" * 80)

    print(f"Всего категорий в 1С: {total_count}")
    print(f"  └─ Валидные (Ref_Key + Name): {len(valid_categories)}")
    print(f"  └─ Пустой Ref_Key: {len(empty_ref_key)}")
    print(f"  └─ Нет имени: {len(no_name)}")
    print(f"  └─ С пометкой удаления: {len(deletion_mark)}")

    # Пересечения
    empty_ref_and_no_name = [
        cat for cat in all_categories
        if (not cat.get("Ref_Key") or cat.get("Ref_Key") == "00000000-0000-0000-0000-000000000000")
        and not (cat.get("Description") or cat.get("Наименование"))
    ]

    if empty_ref_and_no_name:
        print(f"\n⚠️  Категорий с пустым Ref_Key И без имени: {len(empty_ref_and_no_name)}")

    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЁН")
    print("=" * 80)


if __name__ == "__main__":
    analyze_1c_categories()
