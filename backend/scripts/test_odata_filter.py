"""
Тестирование разных способов передачи $filter параметра в OData запрос
Цель: найти способ, который работает как в Postman
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
import urllib.parse

base_url = "http://10.10.100.77/trade/odata/standard.odata"
username = "odata.user"
password = "ak228Hu2hbs28"
endpoint = "Document_ПоступлениеБезналичныхДенежныхСредств"

print("=" * 70)
print("ТЕСТИРОВАНИЕ $filter ПАРАМЕТРА")
print("=" * 70)

# Подход 1: Параметры через словарь (текущий подход)
print("\n1️⃣  Подход 1: Параметры через словарь")
print("-" * 70)
try:
    url = f"{base_url}/{endpoint}"
    params = {
        '$format': 'json',
        '$top': 1,
        '$filter': 'year(Date) gt 2024'
    }

    print(f"URL: {url}")
    print(f"Params: {params}")

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=10
    )

    print(f"Actual URL: {response.url}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Count: {len(data.get('value', []))}")
        if data.get('value'):
            print(f"First item date: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {e}")

# Подход 2: Параметры в URL (как в Postman)
print("\n2️⃣  Подход 2: Параметры встроены в URL")
print("-" * 70)
try:
    # Как в Postman
    url = f"{base_url}/{endpoint}?$top=1&$format=json&$filter=year(Date) gt 2024"

    print(f"URL: {url}")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Count: {len(data.get('value', []))}")
        if data.get('value'):
            print(f"First item date: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {e}")

# Подход 3: URL-encoded параметры
print("\n3️⃣  Подход 3: URL-encoded фильтр")
print("-" * 70)
try:
    url = f"{base_url}/{endpoint}"
    filter_value = urllib.parse.quote("year(Date) gt 2024")
    full_url = f"{url}?$top=1&$format=json&$filter={filter_value}"

    print(f"URL: {full_url}")

    response = requests.get(
        full_url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Count: {len(data.get('value', []))}")
        if data.get('value'):
            print(f"First item date: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {e}")

# Подход 4: Без кавычек в фильтре (если 1С их не любит)
print("\n4️⃣  Подход 4: Альтернативный синтаксис фильтра")
print("-" * 70)
try:
    url = f"{base_url}/{endpoint}"
    params = {
        '$format': 'json',
        '$top': 1,
        '$filter': 'Date gt 2024-12-31T00:00:00'  # ISO format
    }

    print(f"URL: {url}")
    print(f"Params: {params}")

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=10
    )

    print(f"Actual URL: {response.url}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Count: {len(data.get('value', []))}")
        if data.get('value'):
            print(f"First item date: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {e}")

# Подход 5: Без $filter вообще (проверка, что API работает)
print("\n5️⃣  Подход 5: Без фильтра (baseline)")
print("-" * 70)
try:
    url = f"{base_url}/{endpoint}"
    params = {
        '$format': 'json',
        '$top': 1
    }

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Count: {len(data.get('value', []))}")
        if data.get('value'):
            print(f"First item date: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 70)
print("ИТОГИ ТЕСТИРОВАНИЯ")
print("=" * 70)
