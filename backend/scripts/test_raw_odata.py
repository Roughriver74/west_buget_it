"""
Тест RAW OData запроса без клиентской фильтрации
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.odata_1c_client import OData1CClient

client = OData1CClient(
    base_url="http://10.10.100.77/trade/odata/standard.odata",
    username="odata.user",
    password="ak228Hu2hbs28"
)

print("=" * 80)
print("RAW ODATA ЗАПРОС (БЕЗ КЛИЕНТСКОЙ ФИЛЬТРАЦИИ)")
print("=" * 80)

# Построим URL вручную как в коде
entity = "Document_ПоступлениеБезналичныхДенежныхСредств"
url = f"{entity}?$top=10&$format=json&$skip=0&$filter=year(Date) gt 2024"

print(f"\n📊 URL: {url}")

# Выполним запрос напрямую
response = client._make_request(
    method='GET',
    endpoint=url,
    params=None
)

results = response.get('value', [])
print(f"✅ Получено из 1С: {len(results)} записей")

if results:
    print("\nПервые 5 записей (без клиентской фильтрации):")
    for idx, r in enumerate(results[:5], 1):
        print(f"  {idx}. Date: {r.get('Date', 'N/A')} | Number: {r.get('Number', 'N/A')} | Ref_Key: {r.get('Ref_Key', 'N/A')[:36]}")

    # Подсчитаем, сколько записей за ноябрь
    november_count = 0
    for r in results:
        date_str = r.get('Date', '')
        if '2025-11' in date_str:
            november_count += 1

    print(f"\n📊 Из них за ноябрь 2025: {november_count}")

    # Покажем распределение по месяцам
    from collections import Counter
    months = []
    for r in results:
        date_str = r.get('Date', '')
        if date_str and date_str.startswith('2025-'):
            month = date_str[:7]  # "2025-11"
            months.append(month)

    month_counts = Counter(months)
    print(f"\nРаспределение по месяцам (топ-10):")
    for month, count in month_counts.most_common(10):
        print(f"  {month}: {count} записей")

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
