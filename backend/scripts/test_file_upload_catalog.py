#!/usr/bin/env python3
"""
Тест загрузки файла в Catalog_Файлы (правильный endpoint)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, timedelta
import base64

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("📎 ТЕСТ ЗАГРУЗКИ ФАЙЛА В Catalog_Файлы")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# 1. Получаем существующую заявку для владельца
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
TEST PDF FILE FOR 1C CATALOG_FILES UPLOAD
=========================================

This is a test file to verify that file upload to 1C Catalog_Files works correctly.

Document: Invoice Test
Date: %s
Size: Small test file

The file is uploaded using BASE64 encoding to 1C Catalog_Files.
""" % date.today().isoformat().encode()

test_filename = f"test_invoice_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"

print(f"✅ Файл подготовлен:")
print(f"   Имя: {test_filename}")
print(f"   Размер: {len(test_content)} bytes ({len(test_content) / 1024:.2f} KB)")
print(f"   Расширение: pdf")

# 3. Вариант 1: Попробуем загрузить через метод upload_attachment_base64
print(f"\n3️⃣  ВАРИАНТ 1: Загрузка через upload_attachment_base64...")
print(f"   Endpoint: Catalog_Файлы")
print(f"   Владелец (Ref_Key): {ref_key}")
print()

try:
    result = client.upload_attachment_base64(
        file_content=test_content,
        filename=test_filename,
        owner_guid=ref_key,
        file_extension="pdf",
        endpoint="Catalog_Файлы"
    )

    if result:
        print(f"\n✅ ВАРИАНТ 1 УСПЕШЕН!")
        print(f"\n📄 Response от 1С:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"\n⚠️  Вариант 1: файл не загружен (вернулся None)")

except Exception as e:
    print(f"\n❌ ВАРИАНТ 1 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

# 4. Вариант 2: Прямая отправка в Catalog_Файлы с минимальными полями
print(f"\n\n4️⃣  ВАРИАНТ 2: Прямая отправка POST в Catalog_Файлы...")
print(f"   Минимальный набор полей")
print()

try:
    base64_content = base64.b64encode(test_content).decode('utf-8')

    # Минимальная структура для Catalog_Файлы
    file_data = {
        "Description": test_filename,
        "ДвоичныеДанные": base64_content,
        "Расширение": "pdf"
    }

    print(f"📋 Отправляемые поля:")
    print(f"   Description: {test_filename}")
    print(f"   ДвоичныеДанные: [BASE64, {len(base64_content)} chars]")
    print(f"   Расширение: pdf")
    print()

    response = client._make_request(
        method='POST',
        endpoint="Catalog_Файлы",
        data=file_data
    )

    print(f"\n✅ ВАРИАНТ 2 УСПЕШЕН!")
    print(f"\n📄 Response от 1С:")
    import json
    print(json.dumps(response, ensure_ascii=False, indent=2))

except Exception as e:
    print(f"\n❌ ВАРИАНТ 2 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

# 5. Вариант 3: Попробуем Catalog_ВерсииФайлов (если есть поле ФайлХранилище_Base64Data)
print(f"\n\n5️⃣  ВАРИАНТ 3: Загрузка в Catalog_ВерсииФайлов...")
print(f"   Endpoint с поддержкой ФайлХранилище_Base64Data")
print()

try:
    base64_content = base64.b64encode(test_content).decode('utf-8')

    # Структура для Catalog_ВерсииФайлов
    version_data = {
        "Description": test_filename,
        "ФайлХранилище_Base64Data": base64_content,
        "Расширение": "pdf"
    }

    print(f"📋 Отправляемые поля:")
    print(f"   Description: {test_filename}")
    print(f"   ФайлХранилище_Base64Data: [BASE64, {len(base64_content)} chars]")
    print(f"   Расширение: pdf")
    print()

    response = client._make_request(
        method='POST',
        endpoint="Catalog_ВерсииФайлов",
        data=version_data
    )

    print(f"\n✅ ВАРИАНТ 3 УСПЕШЕН!")
    print(f"\n📄 Response от 1С:")
    import json
    print(json.dumps(response, ensure_ascii=False, indent=2))

except Exception as e:
    print(f"\n❌ ВАРИАНТ 3 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
print("\n💡 ВЫВОДЫ:")
print("   - Проверьте какой вариант сработал успешно")
print("   - Успешный вариант нужно использовать для загрузки файлов")
print("   - Возможно потребуется связать файл с владельцем отдельным запросом")
print()
