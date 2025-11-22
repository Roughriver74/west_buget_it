#!/usr/bin/env python3
"""
Тест загрузки файла в Catalog_Файлы с правильной структурой полей
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, timedelta, datetime
import base64

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("📎 ТЕСТ ЗАГРУЗКИ ФАЙЛА В Catalog_Файлы (ПРАВИЛЬНАЯ СТРУКТУРА)")
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
test_content_str = f"""
TEST PDF FILE FOR 1C CATALOG_FILES UPLOAD - CORRECT STRUCTURE
==============================================================

This is a test file to verify that file upload to 1C Catalog_Files works
correctly with proper field structure including FileStorage_Type.

Document: Invoice Test
Date: {date.today().isoformat()}
Size: Small test file

The file is uploaded using BASE64 encoding to 1C Catalog_Files.
"""
test_content = test_content_str.encode('utf-8')

test_filename = f"test_invoice_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"

print(f"✅ Файл подготовлен:")
print(f"   Имя: {test_filename}")
print(f"   Размер: {len(test_content)} bytes ({len(test_content) / 1024:.2f} KB)")
print(f"   Расширение: pdf")

# 3. Загрузка с правильной структурой
print(f"\n3️⃣  Загрузка файла в Catalog_Файлы...")
print(f"   Endpoint: Catalog_Файлы")
print()

try:
    base64_content = base64.b64encode(test_content).decode('utf-8')

    # ПРАВИЛЬНАЯ структура для Catalog_Файлы
    # Ключевое отличие: добавляем ФайлХранилище_Type!
    file_data = {
        "Description": test_filename,
        "ФайлХранилище_Base64Data": base64_content,
        "ФайлХранилище_Type": "application/pdf",  # ← ОБЯЗАТЕЛЬНОЕ ПОЛЕ для binary!
        "Расширение": "pdf",
        "Размер": len(test_content),
        "ДатаСоздания": datetime.now().isoformat(),
        "ДатаМодификацииУниверсальная": datetime.now().isoformat(),
        # "ВладелецФайла": ref_key,  # Попробуем без владельца сначала
        "ТипХраненияФайла": "ВТомахНаДиске"
    }

    print(f"📋 Отправляемые поля:")
    print(f"   Description: {test_filename}")
    print(f"   ФайлХранилище_Base64Data: [BASE64, {len(base64_content)} chars]")
    print(f"   ФайлХранилище_Type: application/pdf ← ОБЯЗАТЕЛЬНОЕ!")
    print(f"   Расширение: pdf")
    print(f"   Размер: {len(test_content)} bytes")
    print(f"   ТипХраненияФайла: ВТомахНаДиске")
    print()

    response = client._make_request(
        method='POST',
        endpoint="Catalog_Файлы",
        data=file_data
    )

    print(f"\n✅ ФАЙЛ УСПЕШНО ЗАГРУЖЕН В 1С!")
    print(f"\n📄 Response от 1С:")
    import json
    print(json.dumps(response, ensure_ascii=False, indent=2))

    file_ref_key = response.get('Ref_Key')
    print(f"\n🎉 УСПЕХ!")
    print(f"   Ref_Key файла: {file_ref_key}")
    print(f"   Теперь можно связать файл с владельцем (заявкой)")

except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

# 4. Вариант 2: Попробуем с указанием владельца
print(f"\n\n4️⃣  ВАРИАНТ 2: С указанием владельца файла...")
print(f"   ВладелецФайла: {ref_key}")
print()

try:
    base64_content = base64.b64encode(test_content).decode('utf-8')

    file_data_with_owner = {
        "Description": f"{test_filename}_with_owner",
        "ФайлХранилище_Base64Data": base64_content,
        "ФайлХранилище_Type": "application/pdf",
        "Расширение": "pdf",
        "Размер": len(test_content),
        "ДатаСоздания": datetime.now().isoformat(),
        "ДатаМодификацииУниверсальная": datetime.now().isoformat(),
        "ВладелецФайла": ref_key,  # Указываем владельца
        "ВладелецФайла_Type": "StandardODATA.Document_ЗаявкаНаРасходованиеДенежныхСредств",
        "ТипХраненияФайла": "ВТомахНаДиске"
    }

    print(f"📋 Отправляемые поля (с владельцем):")
    print(f"   Description: {test_filename}_with_owner")
    print(f"   ФайлХранилище_Base64Data: [BASE64, {len(base64_content)} chars]")
    print(f"   ФайлХранилище_Type: application/pdf")
    print(f"   ВладелецФайла: {ref_key}")
    print(f"   ВладелецФайла_Type: StandardODATA.Document_ЗаявкаНаРасходованиеДенежныхСредств")
    print()

    response = client._make_request(
        method='POST',
        endpoint="Catalog_Файлы",
        data=file_data_with_owner
    )

    print(f"\n✅ ВАРИАНТ 2 УСПЕШЕН!")
    print(f"\n📄 Response от 1С:")
    import json
    print(json.dumps(response, ensure_ascii=False, indent=2))

    file_ref_key = response.get('Ref_Key')
    print(f"\n🎉 ФАЙЛ ЗАГРУЖЕН И СВЯЗАН С ЗАЯВКОЙ!")
    print(f"   Ref_Key файла: {file_ref_key}")
    print(f"   Владелец: Заявка {number}")

except Exception as e:
    print(f"\n❌ ВАРИАНТ 2 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
print("\n💡 ВЫВОДЫ:")
print("   ✅ Для binary полей ОБЯЗАТЕЛЬНО указывать _Type поле!")
print("   ✅ ФайлХранилище_Base64Data требует ФайлХранилище_Type")
print("   ✅ Для привязки к владельцу нужны ВладелецФайла и ВладелецФайла_Type")
print()
