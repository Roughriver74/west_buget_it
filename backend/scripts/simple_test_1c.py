#!/usr/bin/env python3
"""
Простой тест 1С OData без зависимости от config
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, timedelta
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# 1C OData credentials
ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🧪 ТЕСТ 1С ODATA")
print("=" * 80)

# 1. Создание клиента
print("\n1️⃣  Создание клиента...")
print(f"   URL: {ODATA_URL}")
print(f"   User: {ODATA_USER}")

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)
print("✅ Клиент создан\n")

# 2. Проверка подключения
print("2️⃣  Проверка подключения...")
if client.test_connection():
    print("✅ Подключение успешно\n")
else:
    print("❌ Не удалось подключиться\n")
    sys.exit(1)

# 3. Получение организаций
print("3️⃣  Получение организаций...")
try:
    orgs = client.get_organizations(top=3)
    print(f"✅ Получено: {len(orgs)}")
    for org in orgs[:2]:
        print(f"   - {org.get('Description', 'N/A')} (ИНН: {org.get('ИНН', 'N/A')})")
    print()
except Exception as e:
    print(f"❌ Ошибка: {e}\n")

# 4. Получение категорий (статей ДДС)
print("4️⃣  Получение категорий (статей ДДС)...")
try:
    categories = client.get_cash_flow_categories(top=5)
    print(f"✅ Получено: {len(categories)}")
    for cat in categories[:3]:
        print(f"   - {cat.get('Description', 'N/A')}")
    print()
except Exception as e:
    print(f"❌ Ошибка: {e}\n")

# 5. Получение заявок
print("5️⃣  Получение заявок на расход...")
try:
    date_from = date.today() - timedelta(days=30)
    date_to = date.today()

    expenses = client.get_expense_requests(
        date_from=date_from,
        date_to=date_to,
        top=5,
        only_posted=False
    )

    print(f"✅ Получено: {len(expenses)}")
    for exp in expenses[:3]:
        print(f"   - №{exp.get('Number', 'N/A')}, "
              f"Сумма: {exp.get('СуммаДокумента', 0):.2f} руб., "
              f"Дата: {exp.get('Date', 'N/A')[:10]}")
    print()
except Exception as e:
    print(f"❌ Ошибка: {e}\n")

# 6. Тест создания заявки
print("6️⃣  Тест создания заявки...")
create_test = input("   Создать тестовую заявку? (y/n): ")

if create_test.lower() == 'y':
    try:
        if not orgs or not categories:
            print("❌ Нет данных для создания заявки\n")
        else:
            org_guid = orgs[0].get('Ref_Key')
            category_guid = categories[0].get('Ref_Key')

            print(f"\n   Организация: {orgs[0].get('Description')}")
            print(f"   Категория: {categories[0].get('Description')}")
            print(f"   Сумма: 1000.00 руб.\n")

            test_data = {
                "Дата": date.today().isoformat() + "T00:00:00",
                "Организация_Key": org_guid,
                "СуммаДокумента": 1000.00,
                "СтатьяДДС_Key": category_guid,
                "НазначениеПлатежа": "Тест из IT Budget Manager - quick_test",
                "ХозяйственнаяОперация": "ОплатаПоставщику"
            }

            response = client.create_expense_request(test_data)
            ref_key = response.get('Ref_Key')

            print(f"✅ Заявка создана!")
            print(f"   Ref_Key: {ref_key}\n")

            # 7. Тест загрузки файла
            print("7️⃣  Тест загрузки файла...")
            upload_test = input("   Загрузить тестовый файл? (y/n): ")

            if upload_test.lower() == 'y':
                test_content = b"PDF test content for 1C attachment upload"
                test_filename = "test_document.pdf"

                print(f"\n   Файл: {test_filename}")
                print(f"   Размер: {len(test_content)} bytes")
                print(f"   Владелец: {ref_key}\n")

                result = client.upload_attachment_base64(
                    file_content=test_content,
                    filename=test_filename,
                    owner_guid=ref_key,
                    file_extension="pdf"
                )

                if result:
                    print(f"✅ Файл загружен!")
                    print(f"   Response: {result}\n")
                else:
                    print("⚠️  Файл не загружен (проверьте логи)\n")

    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        import traceback
        traceback.print_exc()

print("=" * 80)
print("✅ ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
