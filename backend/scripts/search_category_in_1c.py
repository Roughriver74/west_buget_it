"""
Поиск конкретной категории в 1С
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

from app.services.odata_1c_client import OData1CClient

# 1C OData credentials
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def search_category(search_text: str):
    """Поиск категории по названию"""

    print("=" * 80)
    print(f"ПОИСК КАТЕГОРИИ: '{search_text}'")
    print("=" * 80)

    # Создать OData клиент
    odata_client = OData1CClient(
        base_url=ODATA_1C_URL,
        username=ODATA_1C_USERNAME,
        password=ODATA_1C_PASSWORD
    )

    # Проверить подключение
    print("\n1. Проверка подключения...")
    if not odata_client.test_connection():
        print("❌ Не удалось подключиться к 1С")
        return
    print("✅ Подключение успешно")

    # Поиск по всем записям (С ФИЛЬТРОМ DeletionMark=false)
    print(f"\n2. Поиск категории '{search_text}' (только активные)...")

    all_categories = []
    skip = 0
    found_categories = []

    while True:
        try:
            # Используем default top=1000 из OData клиента
            batch = odata_client.get_cash_flow_categories(
                skip=skip,
                include_folders=True
            )

            if not batch:
                break

            all_categories.extend(batch)

            # Искать в текущем батче
            for cat in batch:
                description = cat.get("Description", "") or cat.get("Наименование", "")
                if search_text.lower() in description.lower():
                    found_categories.append(cat)

            print(f"  Обработано: {len(all_categories)} категорий, найдено: {len(found_categories)}")

            if len(batch) < 1000:
                # Получили меньше чем максимум - это последний батч
                break

            skip += 1000

            # Защита
            if skip > 10000:
                break

        except Exception as e:
            print(f"❌ Ошибка при получении данных: {e}")
            break

    print(f"\n3. Результаты поиска:")
    print("=" * 80)

    if not found_categories:
        print(f"❌ Категория '{search_text}' НЕ НАЙДЕНА")
        print(f"\n📊 Всего загружено категорий из 1С: {len(all_categories)}")

        # Показать похожие категории
        print(f"\nПохожие категории (содержат '{search_text[:3]}'):")
        similar = [
            cat for cat in all_categories
            if search_text[:3].lower() in (cat.get("Description", "") or cat.get("Наименование", "")).lower()
        ]
        for cat in similar[:10]:
            print(f"  - {cat.get('Description', 'N/A')} (Code: {cat.get('Code', 'N/A')})")
    else:
        print(f"✅ Найдено {len(found_categories)} совпадений:")
        print()

        for i, cat in enumerate(found_categories, 1):
            print(f"Совпадение #{i}:")
            print(f"  Наименование: {cat.get('Description', 'N/A')}")
            print(f"  Код: {cat.get('Code', 'N/A')}")
            print(f"  Ref_Key: {cat.get('Ref_Key', 'N/A')}")
            print(f"  IsFolder: {cat.get('IsFolder', False)}")
            print(f"  Parent_Key: {cat.get('Parent_Key', 'N/A')}")
            print(f"  DeletionMark: {cat.get('DeletionMark', False)}")

            # Показать все поля
            print(f"\n  Все поля:")
            for key, value in cat.items():
                if key not in ["Description", "Code", "Ref_Key", "IsFolder", "Parent_Key", "DeletionMark"]:
                    print(f"    {key}: {value}")
            print()

    print("=" * 80)
    print("ПОИСК ЗАВЕРШЁН")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Поиск категории в 1С")
    parser.add_argument("search", type=str, help="Текст для поиска (например: 'Аутсорс')")

    args = parser.parse_args()
    search_category(args.search)
