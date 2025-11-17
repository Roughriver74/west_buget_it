"""
Прямая проверка - есть ли данные за ноябрь 2025 в 1С
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth

base_url = "http://10.10.100.77/trade/odata/standard.odata"
username = "odata.user"
password = "ak228Hu2hbs28"

print("=" * 80)
print("ПРОВЕРКА ДАННЫХ ЗА НОЯБРЬ 2025")
print("=" * 80)

entities = [
    ("Поступления", "Document_ПоступлениеБезналичныхДенежныхСредств"),
    ("Списания", "Document_СписаниеБезналичныхДенежныхСредств")
]

for name, entity in entities:
    print(f"\n{'=' * 80}")
    print(f"📊 {name}: {entity}")
    print("=" * 80)

    # year(Date) gt 2024
    print("\n1️⃣  Фильтр: year(Date) gt 2024")
    try:
        url = f"{base_url}/{entity}?$filter=year(Date) gt 2024&$top=10&$format=json"
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data.get('value', []))
            print(f"✅ Получено записей: {count}")
            if count > 0:
                dates = [item.get('Date', 'N/A') for item in data['value'][:5]]
                print(f"Даты первых 5 записей: {dates}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение: {e}")

    # year(Date) eq 2025 and month(Date) eq 11
    print("\n2️⃣  Фильтр: year(Date) eq 2025 and month(Date) eq 11")
    try:
        url = f"{base_url}/{entity}?$filter=year(Date) eq 2025 and month(Date) eq 11&$top=10&$format=json"
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data.get('value', []))
            print(f"✅ Получено записей за НОЯБРЬ 2025: {count}")
            if count > 0:
                print(f"\n📋 Первые записи:")
                for idx, item in enumerate(data['value'][:5], 1):
                    print(f"  {idx}. Date: {item.get('Date', 'N/A')} | Number: {item.get('Number', 'N/A')} | Ref_Key: {item.get('Ref_Key', 'N/A')[:36]}")
            else:
                print("⚠️  НЕТ ДАННЫХ за ноябрь 2025")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение: {e}")

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
