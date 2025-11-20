#!/usr/bin/env python3
"""
Проверка полной структуры Document_ЗаявкаНаРасходованиеДенежныхСредств
включая табличные части
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
print("🔍 ПОЛНАЯ СТРУКТУРА Document_ЗаявкаНаРасходованиеДенежныхСредств")
print("=" * 80)

print("\n1️⃣  Получение метаданных...")
try:
    response = requests.get(
        f"{ODATA_URL}/$metadata",
        auth=HTTPBasicAuth(ODATA_USER, ODATA_PASS),
        timeout=30
    )

    if response.status_code == 200:
        metadata = response.text
        print(f"✅ Метаданные получены ({len(metadata)} bytes)\n")

        lines = metadata.split('\n')

        # Ищем EntityType для Document_ЗаявкаНаРасходованиеДенежныхСредств
        in_entity = False
        entity_lines = []

        for line in lines:
            if 'EntityType' in line and 'Document_ЗаявкаНаРасходованиеДенежныхСредств"' in line:
                in_entity = True
                entity_lines.append(line)
                continue

            if in_entity:
                entity_lines.append(line)
                if '</EntityType>' in line:
                    break

        if entity_lines:
            print("✅ Найдена структура Document_ЗаявкаНаРасходованиеДенежныхСредств:")
            print("=" * 80)

            # Извлекаем все свойства
            properties = []
            table_parts = []

            for line in entity_lines:
                # Простые поля
                if '<Property' in line and 'Name=' in line and 'Type=' in line:
                    name_start = line.find('Name="') + 6
                    name_end = line.find('"', name_start)
                    field_name = line[name_start:name_end]

                    type_start = line.find('Type="') + 6
                    type_end = line.find('"', type_start)
                    field_type = line[type_start:type_end]

                    nullable = 'Nullable="false"' not in line

                    # Ищем табличные части
                    if 'Collection(' in field_type:
                        table_parts.append({
                            'name': field_name,
                            'type': field_type
                        })
                    else:
                        properties.append({
                            'name': field_name,
                            'type': field_type,
                            'nullable': nullable
                        })

            # Выводим простые поля
            print("\n📋 ПРОСТЫЕ ПОЛЯ:")
            print("-" * 80)

            # Группируем по типам
            key_fields = [p for p in properties if '_Key' in p['name']]
            date_fields = [p for p in properties if 'Дата' in p['name'] or 'Date' in p['name']]
            sum_fields = [p for p in properties if 'Сумма' in p['name'] or 'Amount' in p['name']]
            other_fields = [p for p in properties if p not in key_fields and p not in date_fields and p not in sum_fields]

            print("\n🔑 Ключевые поля (GUID ссылки):")
            for field in key_fields[:20]:  # Ограничим вывод
                nullable_mark = "?" if field['nullable'] else "!"
                print(f"   {nullable_mark} {field['name']:45s} ({field['type']})")

            print(f"\n   ... всего {len(key_fields)} ключевых полей")

            print("\n📅 Даты:")
            for field in date_fields:
                nullable_mark = "?" if field['nullable'] else "!"
                print(f"   {nullable_mark} {field['name']:45s} ({field['type']})")

            print("\n💰 Суммовые поля:")
            for field in sum_fields:
                nullable_mark = "?" if field['nullable'] else "!"
                print(f"   {nullable_mark} {field['name']:45s} ({field['type']})")

            # Выводим табличные части
            print("\n\n📊 ТАБЛИЧНЫЕ ЧАСТИ (Collection fields):")
            print("=" * 80)

            if table_parts:
                for tp in table_parts:
                    print(f"\n✅ {tp['name']}")
                    print(f"   Type: {tp['type']}")

                    # Пробуем найти структуру этой табличной части
                    # Извлекаем имя типа из Collection(...)
                    if 'Collection(' in tp['type']:
                        type_start = tp['type'].find('Collection(') + 11
                        type_end = tp['type'].find(')', type_start)
                        row_type = tp['type'][type_start:type_end]

                        print(f"   Row Type: {row_type}")

                        # Ищем ComplexType для этой табличной части
                        in_complex = False
                        complex_lines = []

                        for line in lines:
                            if f'ComplexType Name="{row_type.split(".")[-1]}"' in line:
                                in_complex = True
                                complex_lines.append(line)
                                continue

                            if in_complex:
                                complex_lines.append(line)
                                if '</ComplexType>' in line:
                                    break

                        if complex_lines:
                            print(f"   Структура:")
                            for line in complex_lines:
                                if '<Property' in line and 'Name=' in line:
                                    name_start = line.find('Name="') + 6
                                    name_end = line.find('"', name_start)
                                    col_name = line[name_start:name_end]

                                    type_start = line.find('Type="') + 6
                                    type_end = line.find('"', type_start)
                                    col_type = line[type_start:type_end]

                                    print(f"     - {col_name:40s} ({col_type})")

                # Ищем табличную часть связанную с файлами
                file_related = [tp for tp in table_parts if 'Файл' in tp['name'] or 'File' in tp['name'] or 'Документ' in tp['name']]

                if file_related:
                    print("\n\n🔍 ТАБЛИЧНЫЕ ЧАСТИ СВЯЗАННЫЕ С ФАЙЛАМИ/ДОКУМЕНТАМИ:")
                    print("=" * 80)
                    for tp in file_related:
                        print(f"   ✅ {tp['name']}")
                        print(f"      {tp['type']}")
                else:
                    print("\n\n❌ Табличные части связанные с файлами НЕ НАЙДЕНЫ")
            else:
                print("❌ Табличные части не найдены в документе")

        else:
            print("❌ Структура Document_ЗаявкаНаРасходованиеДенежныхСредств не найдена")

    else:
        print(f"❌ Ошибка: {response.status_code}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("АНАЛИЗ ЗАВЕРШЕН")
print("=" * 80)
