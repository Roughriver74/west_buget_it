#!/usr/bin/env python3
"""
Тест создания заявки с правильной структурой полей
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🧪 ТЕСТ СОЗДАНИЯ ЗАЯВКИ С ПРАВИЛЬНОЙ СТРУКТУРОЙ")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# 1. GUID валюты RUB (из анализа существующих заявок)
print("\n1️⃣  Валюта RUB...")
RUB_CURRENCY_GUID = "f04b98ee-b430-11ea-a43c-b42e994e04d3"
print(f"✅ Используется GUID валюты RUB: {RUB_CURRENCY_GUID}")

# 2. Получаем организацию
print("\n2️⃣  Получение организации...")
orgs = client.get_organizations(top=3)
if not orgs:
    print("❌ Организации не найдены")
    sys.exit(1)

org = orgs[0]
print(f"✅ Организация: {org.get('Description')}")
print(f"   GUID: {org.get('Ref_Key')}")

# 3. Получаем категорию (статью ДДС)
print("\n3️⃣  Получение категории...")
categories = client.get_cash_flow_categories(top=10)
if not categories:
    print("❌ Категории не найдены")
    sys.exit(1)

# Берем не архивную категорию
category = None
for cat in categories:
    desc = cat.get('Description', '')
    if 'архив' not in desc.lower() and 'выбирать' not in desc.lower():
        category = cat
        break

if not category:
    category = categories[0]

print(f"✅ Категория: {category.get('Description')}")
print(f"   GUID: {category.get('Ref_Key')}")

# 4. Создаем заявку с правильными полями
print("\n4️⃣  Создание заявки...")
print(f"\n📋 Параметры:")
print(f"   Организация: {org.get('Description')}")
print(f"   Валюта: RUB (GUID: {RUB_CURRENCY_GUID})")
print(f"   Категория: {category.get('Description')}")
print(f"   Сумма: 1000.00 руб.")
print(f"   Дата: {date.today()}")

# Правильная структура данных (на основе анализа)
test_data = {
    "Дата": date.today().isoformat() + "T00:00:00",
    "Организация_Key": org.get('Ref_Key'),
    "Валюта_Key": RUB_CURRENCY_GUID,
    "СуммаДокумента": 1000.00,
    "СтатьяДвиженияДенежныхСредств_Key": category.get('Ref_Key'),  # Правильное поле!
    "НазначениеПлатежа": "Тест из IT Budget Manager - проверка корректной структуры",
    "ДатаПлатежа": date.today().isoformat() + "T00:00:00",
    "ХозяйственнаяОперация": "ОплатаПоставщику"
}

print(f"\n✉️  Отправка запроса...\n")

try:
    response = client.create_expense_request(test_data)
    ref_key = response.get('Ref_Key')

    print(f"✅ ЗАЯВКА УСПЕШНО СОЗДАНА!")
    print(f"   Ref_Key: {ref_key}")
    print(f"   Номер: {response.get('Number', 'N/A')}")

    # 5. Тест загрузки файла
    print("\n5️⃣  Тест загрузки файла к заявке...")
    upload_test = input("   Загрузить тестовый файл? (y/n): ")

    if upload_test.lower() == 'y':
        test_content = b"Test PDF content for 1C OData attachment upload verification"
        test_filename = f"test_attachment_{date.today().strftime('%Y%m%d')}.pdf"

        print(f"\n   📎 Параметры загрузки:")
        print(f"   Файл: {test_filename}")
        print(f"   Размер: {len(test_content)} bytes")
        print(f"   Владелец (Ref_Key): {ref_key}")
        print()

        result = client.upload_attachment_base64(
            file_content=test_content,
            filename=test_filename,
            owner_guid=ref_key,
            file_extension="pdf"
        )

        if result:
            print(f"\n✅ ФАЙЛ УСПЕШНО ЗАГРУЖЕН!")
            print(f"   Response: {result}")
        else:
            print(f"\n⚠️  Файл не загружен (проверьте логи)")

except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
