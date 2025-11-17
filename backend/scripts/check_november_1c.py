"""
Прямая проверка данных за ноябрь 2025 в 1C OData API
Точно повторяет запрос из Postman
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
import json

base_url = "http://10.10.100.77/trade/odata/standard.odata"
username = "odata.user"
password = "ak228Hu2hbs28"

# Сущности для проверки
entities = [
    "Document_ПоступлениеБезналичныхДенежныхСредств",  # Поступления
    "Document_СписаниеБезналичныхДенежныхСредств"      # Списания
]

print("=" * 80)
print("ПРОВЕРКА ДАННЫХ ЗА НОЯБРЬ 2025 В 1C ODATA")
print("=" * 80)

for entity in entities:
    print(f"\n{'=' * 80}")
    print(f"📊 Сущность: {entity}")
    print("=" * 80)

    # Запрос без фильтра (первые 5 записей)
    print("\n1️⃣  Запрос БЕЗ фильтра (первые 5 записей):")
    print("-" * 80)
    try:
        url = f"{base_url}/{entity}?$format=json&$top=5"
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
                print(f"Первая запись:")
                first = data['value'][0]
                print(f"  Date: {first.get('Date', 'N/A')}")
                print(f"  Number: {first.get('Number', 'N/A')}")
                print(f"  Ref_Key: {first.get('Ref_Key', 'N/A')[:50]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Исключение: {e}")

    # Запрос с фильтром по году (как в импортере)
    print("\n2️⃣  Запрос с фильтром: year(Date) gt 2024")
    print("-" * 80)
    try:
        url = f"{base_url}/{entity}"
        params = {
            '$format': 'json',
            '$top': 5,
            '$filter': 'year(Date) gt 2024'
        }
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data.get('value', []))
            print(f"✅ Получено записей: {count}")
            if count > 0:
                print(f"Первая запись:")
                first = data['value'][0]
                print(f"  Date: {first.get('Date', 'N/A')}")
                print(f"  Number: {first.get('Number', 'N/A')}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Исключение: {e}")

    # Запрос с фильтром по ноябрю 2025
    print("\n3️⃣  Запрос с фильтром: year(Date) eq 2025 and month(Date) eq 11")
    print("-" * 80)
    try:
        url = f"{base_url}/{entity}"
        params = {
            '$format': 'json',
            '$top': 10,
            '$filter': 'year(Date) eq 2025 and month(Date) eq 11'
        }
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data.get('value', []))
            print(f"✅ Получено записей за ноябрь 2025: {count}")
            if count > 0:
                print(f"\nПримеры записей:")
                for idx, item in enumerate(data['value'][:3], 1):
                    print(f"  {idx}. Date: {item.get('Date', 'N/A')} | Number: {item.get('Number', 'N/A')}")
            else:
                print("⚠️  Нет записей за ноябрь 2025")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Исключение: {e}")

    # Запрос с фильтром по диапазону дат (как в импортере)
    print("\n4️⃣  Запрос с фильтром: Date ge 2025-11-01 and Date le 2025-11-30")
    print("-" * 80)
    try:
        url = f"{base_url}/{entity}"
        params = {
            '$format': 'json',
            '$top': 10,
            '$filter': "Date ge datetime'2025-11-01T00:00:00' and Date le datetime'2025-11-30T23:59:59'"
        }
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data.get('value', []))
            print(f"✅ Получено записей: {count}")
            if count > 0:
                print(f"\nПримеры записей:")
                for idx, item in enumerate(data['value'][:3], 1):
                    print(f"  {idx}. Date: {item.get('Date', 'N/A')} | Number: {item.get('Number', 'N/A')}")
            else:
                print("⚠️  Нет записей за ноябрь 2025")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Исключение: {e}")

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
