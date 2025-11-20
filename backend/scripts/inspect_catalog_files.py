#!/usr/bin/env python3
"""
Проверка структуры Catalog_Файлы через метаданные 1С
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
import xml.etree.ElementTree as ET

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🔍 ПРОВЕРКА СТРУКТУРЫ Catalog_Файлы")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

print("\n1️⃣  Получение метаданных из 1С...")
try:
    import requests
    from requests.auth import HTTPBasicAuth

    response = requests.get(
        f"{ODATA_URL}/$metadata",
        auth=HTTPBasicAuth(ODATA_USER, ODATA_PASS),
        timeout=30
    )

    if response.status_code == 200:
        metadata = response.text
        print(f"✅ Метаданные получены ({len(metadata)} bytes)\n")

        # Ищем EntityType для Catalog_Файлы
        print("🔍 Поиск EntityType для Catalog_Файлы...")
        print("=" * 80)

        lines = metadata.split('\n')
        in_catalog_files = False
        catalog_files_lines = []

        for i, line in enumerate(lines):
            # Начало нужного EntityType
            if 'EntityType' in line and 'Catalog_Файлы' in line:
                in_catalog_files = True
                catalog_files_lines.append(line)
                continue

            # Собираем строки внутри EntityType
            if in_catalog_files:
                catalog_files_lines.append(line)
                # Конец EntityType
                if '</EntityType>' in line:
                    break

        if catalog_files_lines:
            print("✅ Найдена структура Catalog_Файлы:")
            print()
            for line in catalog_files_lines:
                print(line.strip())

            # Извлекаем все Property поля
            print("\n\n📋 СПИСОК ПОЛЕЙ Catalog_Файлы:")
            print("=" * 80)

            properties = []
            for line in catalog_files_lines:
                if '<Property' in line and 'Name=' in line:
                    # Извлекаем имя поля
                    name_start = line.find('Name="') + 6
                    name_end = line.find('"', name_start)
                    field_name = line[name_start:name_end]

                    # Извлекаем тип
                    type_start = line.find('Type="') + 6
                    type_end = line.find('"', type_start)
                    field_type = line[type_start:type_end]

                    # Проверяем Nullable
                    nullable = 'Nullable="false"' not in line

                    properties.append({
                        'name': field_name,
                        'type': field_type,
                        'nullable': nullable
                    })

            # Разделяем на обязательные и опциональные
            required_fields = [p for p in properties if not p['nullable']]
            optional_fields = [p for p in properties if p['nullable']]

            print("\n🔴 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (Nullable=false):")
            for field in required_fields:
                print(f"   - {field['name']:40s} ({field['type']})")

            print("\n🟢 ОПЦИОНАЛЬНЫЕ ПОЛЯ (Nullable=true):")
            for field in optional_fields:
                print(f"   - {field['name']:40s} ({field['type']})")

        else:
            print("❌ EntityType для Catalog_Файлы не найден")

        # Также ищем Catalog_ВерсииФайлов
        print("\n\n" + "=" * 80)
        print("🔍 Поиск EntityType для Catalog_ВерсииФайлов...")
        print("=" * 80)

        in_catalog_versions = False
        catalog_versions_lines = []

        for i, line in enumerate(lines):
            if 'EntityType' in line and 'Catalog_ВерсииФайлов' in line:
                in_catalog_versions = True
                catalog_versions_lines.append(line)
                continue

            if in_catalog_versions:
                catalog_versions_lines.append(line)
                if '</EntityType>' in line:
                    break

        if catalog_versions_lines:
            print("✅ Найдена структура Catalog_ВерсииФайлов:")
            print()

            # Извлекаем поля
            properties_v = []
            for line in catalog_versions_lines:
                if '<Property' in line and 'Name=' in line:
                    name_start = line.find('Name="') + 6
                    name_end = line.find('"', name_start)
                    field_name = line[name_start:name_end]

                    type_start = line.find('Type="') + 6
                    type_end = line.find('"', type_start)
                    field_type = line[type_start:type_end]

                    nullable = 'Nullable="false"' not in line

                    properties_v.append({
                        'name': field_name,
                        'type': field_type,
                        'nullable': nullable
                    })

            required_v = [p for p in properties_v if not p['nullable']]
            optional_v = [p for p in properties_v if p['nullable']]

            print("\n🔴 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:")
            for field in required_v:
                print(f"   - {field['name']:40s} ({field['type']})")

            print("\n🟢 ОПЦИОНАЛЬНЫЕ ПОЛЯ:")
            for field in optional_v:
                print(f"   - {field['name']:40s} ({field['type']})")

    else:
        print(f"❌ Ошибка получения метаданных: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("АНАЛИЗ ЗАВЕРШЕН")
print("=" * 80)
