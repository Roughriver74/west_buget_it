#!/usr/bin/env python3
"""
Анализ структуры заявок на расход в 1С
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odata_1c_client import OData1CClient
from datetime import date, timedelta
import json

ODATA_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_USER = "odata.user"
ODATA_PASS = "ak228Hu2hbs28"

print("=" * 80)
print("🔍 АНАЛИЗ СТРУКТУРЫ ЗАЯВОК НА РАСХОД В 1С")
print("=" * 80)

client = OData1CClient(
    base_url=ODATA_URL,
    username=ODATA_USER,
    password=ODATA_PASS
)

# Получаем последнюю заявку
print("\nПолучение последних заявок...")
expenses = client.get_expense_requests(
    date_from=date.today() - timedelta(days=60),
    date_to=date.today(),
    top=5,
    only_posted=False
)

if expenses:
    print(f"✅ Получено заявок: {len(expenses)}\n")

    # Анализируем первую заявку
    expense = expenses[0]

    print(f"📋 Заявка №{expense.get('Number', 'N/A')}")
    print(f"   Дата: {expense.get('Date', 'N/A')}")
    print(f"   Сумма: {expense.get('СуммаДокумента', 0)} руб.")
    print(f"   Posted: {expense.get('Posted', False)}")
    print("\n" + "=" * 80)
    print("ПОЛНАЯ СТРУКТУРА ДОКУМЕНТА:")
    print("=" * 80)

    # Выводим все поля
    for key, value in sorted(expense.items()):
        if value is not None and value != '':
            # Форматируем значение
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)

            # Обрезаем длинные значения
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."

            print(f"{key:40s}: {value_str}")

    print("\n" + "=" * 80)
    print("КЛЮЧЕВЫЕ ПОЛЯ ДЛЯ СОЗДАНИЯ ЗАЯВКИ:")
    print("=" * 80)

    # Выделяем ключевые поля
    key_fields = [
        'Дата', 'Организация_Key', 'Получатель_Key', 'СуммаДокумента',
        'Валюта_Key', 'СтатьяДДС_Key', 'НазначениеПлатежа',
        'ДатаПлатежа', 'ХозяйственнаяОперация', 'ВидОперации',
        'СчетОрганизации', 'БанковскийСчет_Key', 'БанковскийСчетПолучателя_Key',
        'Подразделение_Key'
    ]

    for field in key_fields:
        value = expense.get(field)
        if value is not None and value != '':
            print(f"{field:40s}: {value}")

    # Проверяем какие GUID поля присутствуют
    print("\n" + "=" * 80)
    print("GUID ПОЛЯ (ссылки на справочники):")
    print("=" * 80)

    for key, value in expense.items():
        if '_Key' in key and value:
            print(f"{key:40s}: {value}")

else:
    print("❌ Заявки не найдены")

print("\n" + "=" * 80)
