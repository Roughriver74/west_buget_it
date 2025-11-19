"""
Сравнение raw request vs OData client
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

import requests
from requests.auth import HTTPBasicAuth
from app.services.odata_1c_client import OData1CClient

# 1C OData credentials
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def compare_requests():
    """Сравнить raw request и OData client"""

    print("=" * 80)
    print("СРАВНЕНИЕ RAW REQUEST vs ODATA CLIENT")
    print("=" * 80)

    # ============== RAW REQUEST ==============
    print("\n1. RAW REQUEST (top=1000, no pagination)...")
    url = f"{ODATA_1C_URL}/Catalog_СтатьиДвиженияДенежныхСредств?$format=json&$filter=DeletionMark eq false&$top=1000"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(ODATA_1C_USERNAME, ODATA_1C_PASSWORD),
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        raw_categories = data.get('value', [])
        print(f"  ✅ Получено: {len(raw_categories)} категорий")

        # Поиск "Аутсорс"
        autsors_raw = [
            cat for cat in raw_categories
            if "аутсорс" in (cat.get("Description", "") or "").lower()
        ]

        if autsors_raw:
            print(f"  ✅ Найдено 'Аутсорс': {len(autsors_raw)}")
            for cat in autsors_raw:
                print(f"    - Code: {cat.get('Code')}, Description: {cat.get('Description')}")
                print(f"      Ref_Key: {cat.get('Ref_Key')}")
        else:
            print(f"  ❌ 'Аутсорс' не найден")
    else:
        print(f"  ❌ Ошибка: {response.status_code}")
        return

    # ============== ODATA CLIENT ==============
    print("\n2. ODATA CLIENT (pagination, top=100)...")
    odata_client = OData1CClient(
        base_url=ODATA_1C_URL,
        username=ODATA_1C_USERNAME,
        password=ODATA_1C_PASSWORD
    )

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
        skip += batch_size

        if len(batch) < batch_size:
            break

        if skip > 10000:
            break

    print(f"  ✅ Получено: {len(all_categories)} категорий")

    # Поиск "Аутсорс"
    autsors_odata = [
        cat for cat in all_categories
        if "аутсорс" in (cat.get("Description", "") or "").lower()
    ]

    if autsors_odata:
        print(f"  ✅ Найдено 'Аутсорс': {len(autsors_odata)}")
        for cat in autsors_odata:
            print(f"    - Code: {cat.get('Code')}, Description: {cat.get('Description')}")
            print(f"      Ref_Key: {cat.get('Ref_Key')}")
    else:
        print(f"  ❌ 'Аутсорс' не найден")

    # ============== СРАВНЕНИЕ ==============
    print("\n3. СРАВНЕНИЕ РЕЗУЛЬТАТОВ...")

    # Сравнить Ref_Key списки
    raw_keys = set(cat.get('Ref_Key') for cat in raw_categories)
    odata_keys = set(cat.get('Ref_Key') for cat in all_categories)

    print(f"  RAW request: {len(raw_keys)} уникальных Ref_Key")
    print(f"  OData client: {len(odata_keys)} уникальных Ref_Key")

    # Разница
    only_in_raw = raw_keys - odata_keys
    only_in_odata = odata_keys - raw_keys

    if only_in_raw:
        print(f"\n  ⚠️ Только в RAW ({len(only_in_raw)}):")
        for ref_key in list(only_in_raw)[:5]:
            cat = next(c for c in raw_categories if c.get('Ref_Key') == ref_key)
            print(f"    - {cat.get('Description')} (Code: {cat.get('Code')})")

    if only_in_odata:
        print(f"\n  ⚠️ Только в OData ({len(only_in_odata)}):")
        for ref_key in list(only_in_odata)[:5]:
            cat = next(c for c in all_categories if c.get('Ref_Key') == ref_key)
            print(f"    - {cat.get('Description')} (Code: {cat.get('Code')})")

    if not only_in_raw and not only_in_odata:
        print(f"\n  ✅ Результаты идентичны!")

    # Проверить "Аутсорс" в RAW
    if autsors_raw:
        autsors_ref = autsors_raw[0].get('Ref_Key')
        print(f"\n4. Проверка 'Аутсорс' (Ref_Key: {autsors_ref})...")

        if autsors_ref in raw_keys:
            print(f"  ✅ Есть в RAW request")
        else:
            print(f"  ❌ НЕТ в RAW request")

        if autsors_ref in odata_keys:
            print(f"  ✅ Есть в OData client")
        else:
            print(f"  ❌ НЕТ в OData client")

    print("\n" + "=" * 80)
    print("СРАВНЕНИЕ ЗАВЕРШЕНО")
    print("=" * 80)


if __name__ == "__main__":
    compare_requests()
