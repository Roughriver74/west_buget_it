#!/usr/bin/env python3
"""
Тест: Создание файла через Catalog_ПапкиФайлов (папку)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, datetime
import base64

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("📁 ТЕСТ: СОЗДАНИЕ ФАЙЛА ЧЕРЕЗ ПАПКУ")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# 1. Получаем или создаем папку для файлов
print("\n1️⃣  Получение папок файлов...")

try:
    folders = client._make_request(
        method='GET',
        endpoint="Catalog_ПапкиФайлов",
        params={'$top': 10}
    )

    folder_list = folders.get('value', [])

    if folder_list:
        # Используем первую папку
        folder = folder_list[0]
        folder_ref = folder.get('Ref_Key')
        folder_name = folder.get('Description', 'Без названия')

        print(f"✅ Найдена папка: {folder_name}")
        print(f"   Ref_Key: {folder_ref}")
    else:
        # Создаем новую папку
        print("   Папки не найдены, создаем новую...")

        new_folder = {
            "Description": "IT Budget Manager - Вложения"
        }

        folder_response = client._make_request(
            method='POST',
            endpoint="Catalog_ПапкиФайлов",
            data=new_folder
        )

        folder_ref = folder_response.get('Ref_Key')
        print(f"✅ Создана папка: {folder_response.get('Description')}")
        print(f"   Ref_Key: {folder_ref}")

except Exception as e:
    print(f"❌ Ошибка работы с папками: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Создаем файл с владельцем = папка
print(f"\n2️⃣  Создание файла с владельцем = папка...")

try:
    test_content = b"TEST FILE CONTENT FOR 1C CATALOG_FILES WITH FOLDER OWNER"
    test_filename = f"test_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"
    base64_content = base64.b64encode(test_content).decode('utf-8')

    file_data = {
        "Description": test_filename,
        "ФайлХранилище_Base64Data": base64_content,
        "ФайлХранилище_Type": "application/pdf",
        "Расширение": "pdf",
        "Размер": len(test_content),
        "ДатаСоздания": datetime.now().isoformat(),
        "ВладелецФайла": folder_ref,  # ← ПАПКА КАК ВЛАДЕЛЕЦ
        "ВладелецФайла_Type": "StandardODATA.Catalog_ПапкиФайлов",
    }

    print(f"   Файл: {test_filename}")
    print(f"   Владелец (папка): {folder_ref}")
    print(f"   Размер: {len(test_content)} bytes")

    file_response = client._make_request(
        method='POST',
        endpoint="Catalog_Файлы",
        data=file_data
    )

    file_ref_key = file_response.get('Ref_Key')

    print(f"\n✅ ФАЙЛ УСПЕШНО СОЗДАН!")
    print(f"   Ref_Key: {file_ref_key}")
    print(f"\n🎉 Теперь этот файл можно привязать к заявке через ПодтверждающиеДокументы!")

except Exception as e:
    print(f"\n❌ Ошибка создания файла: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
