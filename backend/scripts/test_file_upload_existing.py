#!/usr/bin/env python3
"""
Тест загрузки файла к существующей заявке
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, timedelta

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("📎 ТЕСТ ЗАГРУЗКИ ФАЙЛА К СУЩЕСТВУЮЩЕЙ ЗАЯВКЕ В 1С")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# 1. Получаем существующую заявку
print("\n1️⃣  Получение последней заявки из 1С...")
expenses = client.get_expense_requests(
    date_from=date.today() - timedelta(days=60),
    date_to=date.today(),
    top=5,
    only_posted=False
)

if not expenses:
    print("❌ Заявки не найдены")
    sys.exit(1)

expense = expenses[0]
ref_key = expense.get('Ref_Key')
number = expense.get('Number')
amount = expense.get('СуммаДокумента', 0)
expense_date = expense.get('Date', '')[:10]

print(f"✅ Найдена заявка:")
print(f"   Номер: {number}")
print(f"   Дата: {expense_date}")
print(f"   Сумма: {amount:.2f} руб.")
print(f"   Ref_Key: {ref_key}")

# 2. Создаем тестовый файл
print("\n2️⃣  Подготовка тестового файла...")
test_content = b"""
TEST PDF FILE FOR 1C ODATA ATTACHMENT UPLOAD
=============================================

This is a test file to verify that file upload to 1C via OData works correctly.

Document: Invoice Test
Date: %s
Size: Small test file

The file is uploaded using BASE64 encoding to 1C expense request document.
""" % date.today().isoformat().encode()

test_filename = f"test_invoice_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"

print(f"✅ Файл подготовлен:")
print(f"   Имя: {test_filename}")
print(f"   Размер: {len(test_content)} bytes ({len(test_content) / 1024:.2f} KB)")
print(f"   Расширение: pdf")

# 3. Загрузка файла
print(f"\n3️⃣  Загрузка файла в 1С...")
print(f"   Владелец (Ref_Key): {ref_key}")
print(f"   Endpoint: InformationRegister_ПрисоединенныеФайлы")
print()

try:
    result = client.upload_attachment_base64(
        file_content=test_content,
        filename=test_filename,
        owner_guid=ref_key,
        file_extension="pdf"
    )

    if result:
        print(f"\n✅ ФАЙЛ УСПЕШНО ЗАГРУЖЕН В 1С!")
        print(f"\n📄 Response от 1С:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print(f"\n🎉 УСПЕХ! Загрузка файлов через OData работает корректно!")

    else:
        print(f"\n⚠️  Файл не загружен (вернулся None)")
        print(f"   Возможные причины:")
        print(f"   - Endpoint InformationRegister_ПрисоединенныеФайлы не существует")
        print(f"   - Недостаточно прав для загрузки файлов")
        print(f"   - Неправильная структура данных")

except Exception as e:
    print(f"\n❌ ОШИБКА ПРИ ЗАГРУЗКЕ:")
    print(f"   {e}")
    print(f"\n📋 Детали ошибки:")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
