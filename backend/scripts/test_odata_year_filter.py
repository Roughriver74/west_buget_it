"""
Тестирование разных вариантов year(Date) фильтра для 1C OData
Цель: найти правильный синтаксис согласно документации
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

print("=" * 80)
print("ТЕСТИРОВАНИЕ year(Date) ФИЛЬТРА ДЛЯ 1C OData")
print("=" * 80)

# Вариант 1: Как в текущем коде (фильтр после других параметров)
print("\n1️⃣  Вариант 1: Фильтр после $top и $format")
print("-" * 80)
try:
    url = f"{base_url}/{endpoint}?$top=5&$format=json&$filter=year(Date) gt 2024"
    print(f"URL: {url}")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Получено: {len(data.get('value', []))} записей")
        if data.get('value'):
            print(f"Первая запись: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Вариант 2: Фильтр ПЕРВЫМ параметром
print("\n2️⃣  Вариант 2: Фильтр первым параметром")
print("-" * 80)
try:
    url = f"{base_url}/{endpoint}?$filter=year(Date) gt 2024&$top=5&$format=json"
    print(f"URL: {url}")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Получено: {len(data.get('value', []))} записей")
        if data.get('value'):
            print(f"Первая запись: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Вариант 3: С URL-кодированием скобок
print("\n3️⃣  Вариант 3: С URL-кодированием скобок")
print("-" * 80)
try:
    filter_value = "year%28Date%29%20gt%202024"  # year(Date) gt 2024 в URL encoding
    url = f"{base_url}/{endpoint}?$filter={filter_value}&$top=5&$format=json"
    print(f"URL: {url}")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Получено: {len(data.get('value', []))} записей")
        if data.get('value'):
            print(f"Первая запись: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Вариант 4: Через params словарь (requests сам закодирует)
print("\n4️⃣  Вариант 4: Через params словарь")
print("-" * 80)
try:
    url = f"{base_url}/{endpoint}"
    params = {
        '$filter': 'year(Date) gt 2024',
        '$top': 5,
        '$format': 'json'
    }
    print(f"URL base: {url}")
    print(f"Params: {params}")

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    print(f"Actual URL: {response.url}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Получено: {len(data.get('value', []))} записей")
        if data.get('value'):
            print(f"Первая запись: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Вариант 5: Попробуем другую функцию - month и year отдельно
print("\n5️⃣  Вариант 5: Альтернативный синтаксис - month и year отдельно")
print("-" * 80)
try:
    url = f"{base_url}/{endpoint}?$filter=year(Date) eq 2025 and month(Date) ge 10&$top=5&$format=json"
    print(f"URL: {url}")

    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        headers={'Accept': 'application/json'},
        timeout=30
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Получено: {len(data.get('value', []))} записей")
        if data.get('value'):
            print(f"Первая запись: {data['value'][0].get('Date', 'N/A')}")
    else:
        print(f"❌ FAILED: {response.text[:300]}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Вариант 6: Попробуем сущность регистра вместо документа
print("\n6️⃣  Вариант 6: Проверим регистр накопления (если есть)")
print("-" * 80)
alt_entities = [
    "AccumulationRegister_ДвижениеДенежныхСредств",
    "InformationRegister_ДвижениеДенежныхСредств",
    "Document_BankStatement"
]

for alt_entity in alt_entities:
    try:
        url = f"{base_url}/{alt_entity}?$top=1&$format=json"
        print(f"\n  Проверка: {alt_entity}")

        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            headers={'Accept': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Существует! Записей в примере: {len(data.get('value', []))}")

            # Попробуем с фильтром
            url_filtered = f"{base_url}/{alt_entity}?$filter=year(Date) gt 2024&$top=5&$format=json"
            response2 = requests.get(
                url_filtered,
                auth=HTTPBasicAuth(username, password),
                headers={'Accept': 'application/json'},
                timeout=10
            )

            if response2.status_code == 200:
                data2 = response2.json()
                print(f"  ✅ Фильтр работает! Записей с фильтром: {len(data2.get('value', []))}")
            else:
                print(f"  ❌ Фильтр не работает: {response2.status_code}")
        else:
            print(f"  ❌ Сущность не найдена")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

print("\n" + "=" * 80)
print("ИТОГИ ТЕСТИРОВАНИЯ")
print("=" * 80)
