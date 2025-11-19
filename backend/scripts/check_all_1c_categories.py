"""
Проверка ВСЕХ категорий в 1С (включая помеченные на удаление)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

import requests
from requests.auth import HTTPBasicAuth
import json

# 1C OData credentials
ODATA_1C_URL = "http://10.10.100.77/trade/odata/standard.odata"
ODATA_1C_USERNAME = "odata.user"
ODATA_1C_PASSWORD = "ak228Hu2hbs28"


def check_all_categories():
    """Проверить ВСЕ категории, включая помеченные на удаление"""

    print("=" * 80)
    print("ПРОВЕРКА ВСЕХ КАТЕГОРИЙ В 1С (включая удалённые)")
    print("=" * 80)

    # Вариант 1: Без фильтра
    print("\n1. Запрос без фильтра...")
    url1 = f"{ODATA_1C_URL}/Catalog_СтатьиДвиженияДенежныхСредств?$format=json&$top=1000"

    try:
        response = requests.get(
            url1,
            auth=HTTPBasicAuth(ODATA_1C_USERNAME, ODATA_1C_PASSWORD),
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            categories = data.get('value', [])
            print(f"  ✅ Получено: {len(categories)} категорий")

            # Поиск "Аутсорс"
            autsors_cats = [
                cat for cat in categories
                if "аутсорс" in (cat.get("Description", "") or "").lower()
            ]

            if autsors_cats:
                print(f"\n  ✅ Найдено 'Аутсорс': {len(autsors_cats)}")
                for cat in autsors_cats:
                    print(f"    - {cat.get('Description')} (Code: {cat.get('Code')}, DeletionMark: {cat.get('DeletionMark')})")
            else:
                print(f"\n  ❌ 'Аутсорс' не найден")

            # Статистика по DeletionMark
            deleted = [c for c in categories if c.get('DeletionMark', False)]
            active = [c for c in categories if not c.get('DeletionMark', False)]

            print(f"\n  Статистика:")
            print(f"    Активных: {len(active)}")
            print(f"    Помеченных на удаление: {len(deleted)}")

            if deleted:
                print(f"\n  Примеры помеченных на удаление:")
                for cat in deleted[:5]:
                    print(f"    - {cat.get('Description', 'N/A')} (Code: {cat.get('Code', 'N/A')})")

        else:
            print(f"  ❌ Ошибка: {response.status_code}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

    # Вариант 2: С явным указанием DeletionMark=false
    print("\n2. Запрос с фильтром DeletionMark eq false...")
    url2 = f"{ODATA_1C_URL}/Catalog_СтатьиДвиженияДенежныхСредств?$format=json&$filter=DeletionMark eq false&$top=1000"

    try:
        response = requests.get(
            url2,
            auth=HTTPBasicAuth(ODATA_1C_USERNAME, ODATA_1C_PASSWORD),
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            categories = data.get('value', [])
            print(f"  ✅ Получено: {len(categories)} категорий (только активные)")

            # Поиск "Аутсорс"
            autsors_cats = [
                cat for cat in categories
                if "аутсорс" in (cat.get("Description", "") or "").lower()
            ]

            if autsors_cats:
                print(f"  ✅ Найдено 'Аутсорс': {len(autsors_cats)}")
            else:
                print(f"  ❌ 'Аутсорс' не найден среди активных")
        else:
            print(f"  ❌ Ошибка: {response.status_code}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

    # Вариант 3: Поиск через $search (если поддерживается)
    print("\n3. Попытка поиска через содержимое...")
    url3 = f"{ODATA_1C_URL}/Catalog_СтатьиДвиженияДенежныхСредств?$format=json&$filter=substringof('Аутсорс',Description)&$top=100"

    try:
        response = requests.get(
            url3,
            auth=HTTPBasicAuth(ODATA_1C_USERNAME, ODATA_1C_PASSWORD),
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            categories = data.get('value', [])
            print(f"  ✅ Найдено через substringof: {len(categories)}")

            for cat in categories:
                print(f"    - {cat.get('Description')} (Code: {cat.get('Code')}, DeletionMark: {cat.get('DeletionMark')})")
        else:
            print(f"  ⚠️ substringof не поддерживается (status: {response.status_code})")

    except Exception as e:
        print(f"  ⚠️ substringof не поддерживается: {e}")

    print("\n" + "=" * 80)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80)


if __name__ == "__main__":
    check_all_categories()
