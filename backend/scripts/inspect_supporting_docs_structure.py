#!/usr/bin/env python3
"""
Проверка структуры табличной части ПодтверждающиеДокументы
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
print("🔍 СТРУКТУРА ТАБЛИЧНОЙ ЧАСТИ ПодтверждающиеДокументы")
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

        # Ищем ComplexType для ПодтверждающиеДокументы
        print("🔍 Поиск ComplexType для ПодтверждающиеДокументы...")
        print("=" * 80)

        in_complex = False
        complex_lines = []
        complex_name = None

        for line in lines:
            # Ищем ComplexType содержащий ПодтверждающиеДокументы
            if 'ComplexType' in line and 'ПодтверждающиеДокументы' in line and 'Name=' in line:
                in_complex = True
                complex_lines.append(line)

                # Извлекаем имя
                name_start = line.find('Name="') + 6
                name_end = line.find('"', name_start)
                complex_name = line[name_start:name_end]
                continue

            if in_complex:
                complex_lines.append(line)
                if '</ComplexType>' in line:
                    break

        if complex_lines and complex_name:
            print(f"✅ Найден ComplexType: {complex_name}\n")

            # Извлекаем поля
            fields = []
            for line in complex_lines:
                if '<Property' in line and 'Name=' in line and 'Type=' in line:
                    name_start = line.find('Name="') + 6
                    name_end = line.find('"', name_start)
                    field_name = line[name_start:name_end]

                    type_start = line.find('Type="') + 6
                    type_end = line.find('"', type_start)
                    field_type = line[type_start:type_end]

                    nullable = 'Nullable="false"' not in line

                    fields.append({
                        'name': field_name,
                        'type': field_type,
                        'nullable': nullable
                    })

            print("📋 ПОЛЯ ТАБЛИЧНОЙ ЧАСТИ:")
            print("-" * 80)

            required = [f for f in fields if not f['nullable']]
            optional = [f for f in fields if f['nullable']]

            if required:
                print("\n🔴 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (Nullable=false):")
                for f in required:
                    print(f"   ! {f['name']:45s} ({f['type']})")

            if optional:
                print("\n🟢 ОПЦИОНАЛЬНЫЕ ПОЛЯ (Nullable=true):")
                for f in optional:
                    print(f"   ? {f['name']:45s} ({f['type']})")

            # Ищем поля связанные с файлами
            file_fields = [f for f in fields if 'Файл' in f['name'] or 'File' in f['name'] or 'Документ' in f['name']]

            if file_fields:
                print("\n\n🔍 ПОЛЯ СВЯЗАННЫЕ С ФАЙЛАМИ/ДОКУМЕНТАМИ:")
                print("=" * 80)
                for f in file_fields:
                    nullable_mark = "?" if f['nullable'] else "!"
                    print(f"   {nullable_mark} {f['name']:45s} ({f['type']})")

            # Выводим полную структуру
            print("\n\n📄 ПОЛНАЯ СТРУКТУРА (XML):")
            print("=" * 80)
            for line in complex_lines[:30]:  # Первые 30 строк
                print(line.strip())

            if len(complex_lines) > 30:
                print(f"   ... ещё {len(complex_lines) - 30} строк")

        else:
            print("❌ ComplexType для ПодтверждающиеДокументы не найден")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("АНАЛИЗ ЗАВЕРШЕН")
print("=" * 80)
print("\n💡 ВОЗМОЖНЫЕ ДЕЙСТВИЯ:")
print("   1. Если есть поле для ссылки на Catalog_Файлы - использовать его")
print("   2. Если есть поле для прямого хранения файла - использовать его")
print("   3. Если нет подходящих полей - рассмотреть альтернативные подходы")
print()
