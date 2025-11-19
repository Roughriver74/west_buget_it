"""
Debug pagination в OData client
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


def debug_pagination():
    """Debug pagination"""

    print("=" * 80)
    print("DEBUG PAGINATION")
    print("=" * 80)

    odata_client = OData1CClient(
        base_url=ODATA_1C_URL,
        username=ODATA_1C_USERNAME,
        password=ODATA_1C_PASSWORD
    )

    all_categories = []
    all_ref_keys = set()
    skip = 0
    batch_size = 100
    batch_num = 0

    while True:
        batch_num += 1
        print(f"\nБатч #{batch_num}: skip={skip}, top={batch_size}")

        batch = odata_client.get_cash_flow_categories(
            top=batch_size,
            skip=skip,
            include_folders=True
        )

        if not batch:
            print(f"  → Пустой батч, остановка")
            break

        print(f"  → Получено: {len(batch)} записей")

        # Проверить Ref_Key
        batch_ref_keys = set(cat.get('Ref_Key') for cat in batch)
        print(f"  → Уникальных Ref_Key в батче: {len(batch_ref_keys)}")

        # Проверить дубликаты
        duplicates = all_ref_keys & batch_ref_keys
        if duplicates:
            print(f"  ⚠️ ДУБЛИКАТЫ: {len(duplicates)} Ref_Key уже были загружены ранее!")
            for dup_key in list(duplicates)[:3]:
                cat = next(c for c in batch if c.get('Ref_Key') == dup_key)
                print(f"      - {cat.get('Description')} (Code: {cat.get('Code')})")

        all_categories.extend(batch)
        all_ref_keys.update(batch_ref_keys)

        print(f"  → Всего уникальных Ref_Key: {len(all_ref_keys)}")
        print(f"  → Всего записей: {len(all_categories)}")

        skip += batch_size

        if len(batch) < batch_size:
            print(f"  → Последний батч (размер < {batch_size}), остановка")
            break

        if skip > 10000:
            print(f"  → Защита от бесконечного цикла, остановка")
            break

    print(f"\n{'='*80}")
    print(f"ИТОГО:")
    print(f"  Всего записей загружено: {len(all_categories)}")
    print(f"  Уникальных Ref_Key: {len(all_ref_keys)}")
    print(f"  Дубликатов: {len(all_categories) - len(all_ref_keys)}")
    print(f"{'='*80}")


if __name__ == "__main__":
    debug_pagination()
