#!/usr/bin/env python3
"""
Минимальный тест - попробуем создать заявку с минимумом полей
"""
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import date, datetime, timedelta

# 1C OData настройки
BASE_URL = "http://10.10.100.77/trade/odata/standard.odata"
USERNAME = "odata.user"
PASSWORD = "ak228Hu2hbs28"

# Текущая дата + 3 дня
today = datetime.now()
payment_date = today + timedelta(days=3)

# МИНИМАЛЬНЫЙ payload - только обязательные поля
payload = {
    "Date": today.strftime("%Y-%m-%dT00:00:00"),
    "Организация_Key": "72201a7e-7fef-11ef-ad66-74563c634acb",
    "ХозяйственнаяОперация": "ОплатаПоставщику",
    "СуммаДокумента": 50000,
    "Контрагент_Key": "f7289e62-5309-11ef-ad62-74563c634acb",
    "СтатьяДвиженияДенежныхСредств_Key": "fae1b6be-f347-11ef-ad72-74563c634acb",
    "ЖелательнаяДатаПлатежа": payment_date.strftime("%Y-%m-%dT00:00:00"),
    "НазначениеПлатежа": "Тест создания заявки",
    "РасшифровкаПлатежа": [
        {
            "LineNumber": 1,
            "СтатьяРасходов_Key": "fae1b6be-f347-11ef-ad72-74563c634acb",
            "Сумма": 50000
        }
    ]
}

print("=" * 80)
print("Тест 1: МИНИМАЛЬНЫЙ запрос (только обязательные поля)")
print("=" * 80)
print(f"\nPayload:")
print(json.dumps(payload, ensure_ascii=False, indent=2))

try:
    response = requests.post(
        f"{BASE_URL}/Document_ЗаявкаНаРасходованиеДенежныхСредств?$format=json",
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30
    )

    print(f"\n✅ Status Code: {response.status_code}")

    if response.status_code == 201:
        result = response.json()
        print(f"\n🎉 УСПЕХ! Заявка создана!")
        print(f"Ref_Key: {result.get('Ref_Key')}")
        print(f"Number: {result.get('Number')}")
    else:
        print(f"\n❌ ОШИБКА!")
        try:
            error_data = response.json()
            print(json.dumps(error_data, ensure_ascii=False, indent=2))
        except:
            print(response.text)

except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 80)

# Тест 2: С подразделением
payload_with_subdivision = payload.copy()
payload_with_subdivision["Подразделение_Key"] = "afc66ff1-4cea-11f0-ad78-74563c634acb"

print("\nТест 2: С подразделением")
print("=" * 80)

try:
    response2 = requests.post(
        f"{BASE_URL}/Document_ЗаявкаНаРасходованиеДенежныхСредств?$format=json",
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={"Content-Type": "application/json"},
        json=payload_with_subdivision,
        timeout=30
    )

    print(f"\n✅ Status Code: {response2.status_code}")

    if response2.status_code == 201:
        result = response2.json()
        print(f"\n🎉 УСПЕХ! Заявка с подразделением создана!")
        print(f"Ref_Key: {result.get('Ref_Key')}")
    else:
        print(f"\n❌ ОШИБКА!")
        try:
            error_data = response2.json()
            print(json.dumps(error_data, ensure_ascii=False, indent=2))
        except:
            print(response2.text)

except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 80)
