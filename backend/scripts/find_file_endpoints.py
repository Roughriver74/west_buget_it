#!/usr/bin/env python3
"""
Поиск доступных endpoints для работы с файлами в 1С
"""
import requests
from requests.auth import HTTPBasicAuth

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🔍 ПОИСК ENDPOINTS ДЛЯ ФАЙЛОВ В 1С ODATA")
print("=" * 80)

print(f"\nURL: {ODATA_URL}")
print(f"User: {ODATA_USER}\n")

# Получаем метаданные
print("Получение метаданных из 1С...")
try:
    response = requests.get(
        f"{ODATA_URL}/$metadata",
        auth=HTTPBasicAuth(ODATA_USER, ODATA_PASS),
        timeout=30
    )

    if response.status_code == 200:
        metadata = response.text

        print(f"✅ Метаданные получены ({len(metadata)} bytes)\n")

        # Ищем все что содержит слово "Файл"
        print("🔍 Endpoints содержащие 'Файл':")
        print("=" * 80)

        lines_with_file = [line for line in metadata.split('\n') if 'Файл' in line or 'File' in line]

        if lines_with_file:
            for line in lines_with_file[:50]:  # Первые 50 строк
                print(line.strip())
        else:
            print("❌ Не найдено endpoints с 'Файл' или 'File'")

        # Ищем EntitySet (доступные коллекции)
        print("\n\n🔍 Доступные EntitySet (коллекции):")
        print("=" * 80)

        entity_sets = []
        for line in metadata.split('\n'):
            if 'EntitySet' in line and 'Name=' in line:
                # Извлекаем имя EntitySet
                start = line.find('Name="') + 6
                end = line.find('"', start)
                if start > 5 and end > start:
                    entity_name = line[start:end]
                    entity_sets.append(entity_name)

        # Группируем по категориям
        catalogs = [e for e in entity_sets if e.startswith('Catalog_')]
        documents = [e for e in entity_sets if e.startswith('Document_')]
        registers = [e for e in entity_sets if e.startswith('InformationRegister_') or e.startswith('AccumulationRegister_')]

        print(f"\n📂 Справочники (Catalogs): {len(catalogs)}")
        file_catalogs = [c for c in catalogs if 'Файл' in c or 'File' in c or 'Хранилище' in c or 'Storage' in c]
        if file_catalogs:
            for cat in file_catalogs:
                print(f"   - {cat}")
        else:
            print("   (нет связанных с файлами)")

        print(f"\n📋 Документы (Documents): {len(documents)}")
        file_documents = [d for d in documents if 'Файл' in d or 'File' in d]
        if file_documents:
            for doc in file_documents:
                print(f"   - {doc}")
        else:
            print("   (нет связанных с файлами)")

        print(f"\n📊 Регистры (Registers): {len(registers)}")
        file_registers = [r for r in registers if 'Файл' in r or 'File' in r or 'Присоединенн' in r or 'Attach' in r]
        if file_registers:
            for reg in file_registers:
                print(f"   - {reg}")
        else:
            print("   (нет связанных с файлами)")

        # Проверяем конкретные варианты
        print("\n\n✅ Проверка конкретных endpoints:")
        print("=" * 80)

        endpoints_to_check = [
            "Catalog_ХранилищеФайлов",
            "Catalog_ПрисоединенныеФайлы",
            "InformationRegister_ПрисоединенныеФайлы",
            "Catalog_Files",
            "InformationRegister_Files"
        ]

        for endpoint in endpoints_to_check:
            exists = endpoint in entity_sets
            status = "✅ Существует" if exists else "❌ Не найден"
            print(f"{endpoint:50s} {status}")

    else:
        print(f"❌ Ошибка: {response.status_code} {response.reason}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n" + "=" * 80)
