"""
Debug OData client response - проверка что именно возвращается
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


def debug_odata_response():
    """Debug OData client response"""

    print("=" * 80)
    print("DEBUG ODATA CLIENT RESPONSE")
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

    # Получить первые 100 категорий
    print("\n2. Получение первых 100 категорий через OData client...")
    batch = odata_client.get_cash_flow_categories(
        top=100,
        skip=0,
        include_folders=True
    )

    print(f"✅ Получено: {len(batch)} категорий")

    # Поиск "Аутсорс"
    print("\n3. Поиск 'Аутсорс' в первом батче...")
    for cat in batch:
        description = cat.get("Description", "") or cat.get("Наименование", "")
        if "аутсорс" in description.lower():
            print(f"✅ НАЙДЕНО:")
            print(f"  Description: {cat.get('Description')}")
            print(f"  Code: {cat.get('Code')}")
            print(f"  Ref_Key: {cat.get('Ref_Key')}")
            print(f"  DeletionMark: {cat.get('DeletionMark')}")
            return

    print("❌ НЕ найдено в первом батче")

    # Проверить все батчи
    print("\n4. Проверка всех батчей...")
    all_categories = []
    skip = 0
    batch_size = 100

    while True:
        batch = odata_client.get_cash_flow_categories(
            top=batch_size,
            skip=skip,
            include_folders=True
        )

        if not batch:
            break

        all_categories.extend(batch)

        # Поиск в текущем батче
        for cat in batch:
            description = cat.get("Description", "") or cat.get("Наименование", "")
            if "аутсорс" in description.lower():
                print(f"\n✅ НАЙДЕНО в батче #{skip // batch_size + 1}:")
                print(f"  Description: {cat.get('Description')}")
                print(f"  Code: {cat.get('Code')}")
                print(f"  Ref_Key: {cat.get('Ref_Key')}")
                print(f"  DeletionMark: {cat.get('DeletionMark')}")
                print(f"  Batch start index: {skip}")
                break

        skip += batch_size

        if len(batch) < batch_size:
            break

        if skip > 10000:
            break

    print(f"\n5. Всего категорий загружено: {len(all_categories)}")

    # Поиск "Аутсорс" во всех категориях
    found = False
    for cat in all_categories:
        description = cat.get("Description", "") or cat.get("Наименование", "")
        if "аутсорс" in description.lower():
            print(f"\n✅ ИТОГО: 'Аутсорс' найден во всех категориях")
            found = True
            break

    if not found:
        print(f"\n❌ ИТОГО: 'Аутсорс' НЕ найден во всех {len(all_categories)} категориях")

        # Показать примеры категорий для проверки
        print(f"\nПримеры категорий (первые 10):")
        for i, cat in enumerate(all_categories[:10], 1):
            print(f"  {i}. {cat.get('Description', 'N/A')} (Code: {cat.get('Code', 'N/A')})")

    print("\n" + "=" * 80)
    print("DEBUG ЗАВЕРШЁН")
    print("=" * 80)


if __name__ == "__main__":
    debug_odata_response()
