"""
Прямой тест OData клиента - что возвращается
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from app.services.odata_1c_client import OData1CClient

client = OData1CClient(
    base_url="http://10.10.100.77/trade/odata/standard.odata",
    username="odata.user",
    password="ak228Hu2hbs28"
)

print("=" * 80)
print("ТЕСТ ODATA КЛИЕНТА")
print("=" * 80)

# Получить поступления за ноябрь
print("\n📊 Запрос поступлений за ноябрь 2025...")
receipts = client.get_bank_receipts(
    date_from=date(2025, 11, 1),
    date_to=date(2025, 11, 30),
    top=10
)

print(f"✅ Получено: {len(receipts)} записей")
if receipts:
    print("\nПервые 3 записи:")
    for idx, r in enumerate(receipts[:3], 1):
        print(f"  {idx}. Date: {r.get('Date', 'N/A')} | Number: {r.get('Number', 'N/A')}")
else:
    print("❌ Нет записей!")

# Получить списания за ноябрь
print("\n📊 Запрос списаний за ноябрь 2025...")
payments = client.get_bank_payments(
    date_from=date(2025, 11, 1),
    date_to=date(2025, 11, 30),
    top=10
)

print(f"✅ Получено: {len(payments)} записей")
if payments:
    print("\nПервые 3 записи:")
    for idx, p in enumerate(payments[:3], 1):
        print(f"  {idx}. Date: {p.get('Date', 'N/A')} | Number: {p.get('Number', 'N/A')}")
else:
    print("❌ Нет записей!")

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
