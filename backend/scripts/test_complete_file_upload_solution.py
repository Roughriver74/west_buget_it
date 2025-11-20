#!/usr/bin/env python3
"""
ПОЛНОЕ РЕШЕНИЕ: Загрузка файла к заявке на расход через табличную часть

Алгоритм:
1. Создать файл в Catalog_Файлы (получить Ref_Key файла)
2. Обновить заявку, добавив запись в ПодтверждающиеДокументы с ссылкой на файл
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
print("📎 ПОЛНОЕ РЕШЕНИЕ: ЗАГРУЗКА ФАЙЛА К ЗАЯВКЕ НА РАСХОД")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# 1. Получаем существующую заявку
print("\n1️⃣  Получение заявки из 1С...")
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

print(f"✅ Найдена заявка:")
print(f"   Номер: {number}")
print(f"   Ref_Key: {ref_key}")

# 2. Создаем тестовый файл
print("\n2️⃣  Подготовка файла...")
test_content_str = f"""TEST INVOICE FILE FOR 1C EXPENSE REQUEST
Date: {date.today().isoformat()}
Expense Request: {number}

This is a test attachment for expense request via ПодтверждающиеДокументы tabular section.
"""
test_content = test_content_str.encode('utf-8')
test_filename = f"test_invoice_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"

print(f"✅ Файл: {test_filename} ({len(test_content)} bytes)")

# 3. ШАГ 1: Создаем файл в Catalog_Файлы
print(f"\n3️⃣  ШАГ 1: Создание файла в Catalog_Файлы...")

try:
    base64_content = base64.b64encode(test_content).decode('utf-8')

    # Создаем файл БЕЗ владельца (так как Document_ не поддерживается)
    file_data = {
        "Description": test_filename,
        "ФайлХранилище_Base64Data": base64_content,
        "ФайлХранилище_Type": "application/pdf",
        "Расширение": "pdf",
        "Размер": len(test_content),
        "ДатаСоздания": datetime.now().isoformat(),
        "ДатаМодификацииУниверсальная": datetime.now().isoformat(),
    }

    print(f"   Отправка POST в Catalog_Файлы...")

    file_response = client._make_request(
        method='POST',
        endpoint="Catalog_Файлы",
        data=file_data
    )

    file_ref_key = file_response.get('Ref_Key')

    print(f"\n✅ ШАГ 1 УСПЕШЕН!")
    print(f"   Файл создан в Catalog_Файлы")
    print(f"   Ref_Key файла: {file_ref_key}")

except Exception as e:
    print(f"\n❌ ШАГ 1 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. ШАГ 2: Обновляем заявку, добавляя запись в ПодтверждающиеДокументы
print(f"\n4️⃣  ШАГ 2: Добавление записи в ПодтверждающиеДокументы...")

try:
    # Получаем текущие ПодтверждающиеДокументы из заявки
    current_docs = expense.get('ПодтверждающиеДокументы', [])

    print(f"   Текущих документов: {len(current_docs)}")

    # Добавляем новую запись
    new_doc = {
        "LineNumber": len(current_docs) + 1,
        "ВидДокумента": "Счет",
        "Номер": test_filename,
        "Дата": datetime.now().isoformat(),
        "Сумма": expense.get('СуммаДокумента', 0),
        "Файл": file_ref_key,  # ← ССЫЛКА НА ФАЙЛ
        "Файл_Type": "StandardODATA.Catalog_Файлы"  # ← ТИП ССЫЛКИ
    }

    updated_docs = current_docs + [new_doc]

    # Обновляем заявку
    update_data = {
        "ПодтверждающиеДокументы": updated_docs
    }

    print(f"\n   Отправка PATCH к заявке {ref_key}...")
    print(f"   Добавляем документ:")
    print(f"     ВидДокумента: Счет")
    print(f"     Номер: {test_filename}")
    print(f"     Файл: {file_ref_key}")
    print(f"     Файл_Type: StandardODATA.Catalog_Файлы")

    # PATCH запрос для обновления заявки
    import requests
    from requests.auth import HTTPBasicAuth
    from urllib.parse import urlparse, quote

    parsed = urlparse(client.base_url)
    endpoint_encoded = quote(f"Document_ЗаявкаНаРасходованиеДенежныхСредств(guid'{ref_key}')", safe='()\'')
    full_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/{endpoint_encoded}?$format=json"

    response = requests.patch(
        full_url,
        json=update_data,
        auth=HTTPBasicAuth(client.username, client.password),
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    if response.status_code in [200, 201, 204]:
        print(f"\n✅ ШАГ 2 УСПЕШЕН!")
        print(f"   Файл успешно прикреплен к заявке!")
        print(f"\n🎉 ПОЛНЫЙ УСПЕХ!")
        print(f"\n📋 Итог:")
        print(f"   ✅ Файл создан в Catalog_Файлы (Ref_Key: {file_ref_key})")
        print(f"   ✅ Файл привязан к заявке {number} через ПодтверждающиеДокументы")
        print(f"   ✅ Теперь файл доступен в 1С в составе заявки")

    else:
        print(f"\n❌ ШАГ 2 ОШИБКА: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ ШАГ 2 ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
