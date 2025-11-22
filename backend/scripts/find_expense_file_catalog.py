#!/usr/bin/env python3
"""
Поиск специального catalog для файлов заявок на расход
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from requests.auth import HTTPBasicAuth

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🔍 ПОИСК CATALOG ДЛЯ ФАЙЛОВ ЗАЯВОК НА РАСХОД")
print("=" * 80)

print("\n1️⃣  Получение метаданных из 1С...")
try:
    response = requests.get(
        f"{ODATA_URL}/$metadata",
        auth=HTTPBasicAuth(ODATA_USER, ODATA_PASS),
        timeout=30
    )

    if response.status_code == 200:
        metadata = response.text
        print(f"✅ Метаданные получены ({len(metadata)} bytes)\n")

        # Ищем все EntityType содержащие "Файл" и "Заявка"/"Расход"
        print("🔍 Поиск EntityType с 'Файл' и 'Заявка'/'Расход':")
        print("=" * 80)

        lines = metadata.split('\n')

        found_types = []
        for i, line in enumerate(lines):
            if 'EntityType' in line and 'Name=' in line:
                # Извлекаем имя EntityType
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                entity_name = line[name_start:name_end]

                # Ищем связанные с файлами и заявками/расходами
                if ('Файл' in entity_name or 'File' in entity_name) and \
                   ('Заявка' in entity_name or 'Расход' in entity_name or 'Денеж' in entity_name):
                    found_types.append(entity_name)

        if found_types:
            print(f"✅ Найдено {len(found_types)} EntityType:")
            for entity_name in found_types:
                print(f"   - {entity_name}")
        else:
            print("❌ Не найдено EntityType с 'Файл' и 'Заявка'/'Расход'")

        # Также попробуем найти все EntityType с "ПрисоединенныеФайлы"
        print("\n\n🔍 Поиск EntityType с 'ПрисоединенныеФайлы':")
        print("=" * 80)

        attached_files_types = []
        for i, line in enumerate(lines):
            if 'EntityType' in line and 'Name=' in line:
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                entity_name = line[name_start:name_end]

                if 'ПрисоединенныеФайлы' in entity_name or 'AttachedFiles' in entity_name:
                    attached_files_types.append(entity_name)

        if attached_files_types:
            print(f"✅ Найдено {len(attached_files_types)} EntityType:")
            for entity_name in attached_files_types:
                print(f"   - {entity_name}")
        else:
            print("❌ Не найдено EntityType с 'ПрисоединенныеФайлы'")

        # Попробуем найти EntitySet (доступные endpoints)
        print("\n\n🔍 Поиск EntitySet с 'Заявка' в названии:")
        print("=" * 80)

        expense_entity_sets = []
        for i, line in enumerate(lines):
            if 'EntitySet' in line and 'Name=' in line:
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                entity_name = line[name_start:name_end]

                if 'Заявка' in entity_name or 'Расход' in entity_name or 'Денеж' in entity_name:
                    expense_entity_sets.append(entity_name)

        if expense_entity_sets:
            print(f"✅ Найдено {len(expense_entity_sets)} EntitySet:")
            for entity_name in expense_entity_sets:
                print(f"   - {entity_name}")
        else:
            print("❌ Не найдено EntitySet с 'Заявка'")

        # Все Catalog_ содержащие "Файл"
        print("\n\n🔍 Все Catalog_ с 'Файл':")
        print("=" * 80)

        file_catalogs = []
        for i, line in enumerate(lines):
            if 'EntitySet' in line and 'Name=' in line:
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                entity_name = line[name_start:name_end]

                if entity_name.startswith('Catalog_') and 'Файл' in entity_name:
                    file_catalogs.append(entity_name)

        if file_catalogs:
            print(f"✅ Найдено {len(file_catalogs)} Catalog:")
            for entity_name in sorted(file_catalogs):
                print(f"   - {entity_name}")
        else:
            print("❌ Не найдено Catalog с 'Файл'")

        # Проверим конкретный catalog для заявок
        print("\n\n✅ Проверка конкретных вариантов:")
        print("=" * 80)

        possible_catalogs = [
            "Catalog_ЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы",
            "Catalog_ДокументЗаявкаНаРасходованиеДенежныхСредствПрисоединенныеФайлы",
            "Document_ЗаявкаНаРасходованиеДенежныхСредств_ПрисоединенныеФайлы",
            "InformationRegister_ПрисоединенныеФайлыЗаявок",
        ]

        entity_sets = []
        for i, line in enumerate(lines):
            if 'EntitySet' in line and 'Name=' in line:
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                entity_name = line[name_start:name_end]
                entity_sets.append(entity_name)

        for catalog_name in possible_catalogs:
            exists = catalog_name in entity_sets
            status = "✅ Существует" if exists else "❌ Не найден"
            print(f"{catalog_name:70s} {status}")

    else:
        print(f"❌ Ошибка: {response.status_code} {response.reason}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("АНАЛИЗ ЗАВЕРШЕН")
print("=" * 80)
