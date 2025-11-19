"""
Проверить категории через API
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix validation error
os.environ["DEBUG"] = "False"

import requests
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department


def check_categories_api():
    """Проверить категории через API"""

    print("=" * 80)
    print("ПРОВЕРКА КАТЕГОРИЙ ЧЕРЕЗ API")
    print("=" * 80)

    # 1. Получить токен
    print("\n1. Получение токена...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={"username": "admin", "password": "admin"}
    )

    if login_response.status_code != 200:
        print(f"❌ Ошибка логина: {login_response.status_code}")
        return

    token = login_response.json()["access_token"]
    print("✅ Токен получен")

    # 2. Проверить категории для финансового отдела
    print("\n2. Запрос категорий для финансового отдела (ID: 8)...")

    headers = {"Authorization": f"Bearer {token}"}

    # Запрос БЕЗ department_id (все категории)
    response_all = requests.get(
        "http://localhost:8000/api/v1/categories/?limit=1000",
        headers=headers
    )

    if response_all.status_code == 200:
        all_categories = response_all.json()
        print(f"✅ Всего категорий (без фильтра): {len(all_categories)}")

        # Группировка по департаментам
        by_dept = {}
        with_1c = 0
        for cat in all_categories:
            dept_id = cat.get("department_id")
            if dept_id not in by_dept:
                by_dept[dept_id] = 0
            by_dept[dept_id] += 1

            if cat.get("external_id_1c"):
                with_1c += 1

        print(f"\nРаспределение по департаментам:")
        for dept_id, count in sorted(by_dept.items()):
            print(f"  Department {dept_id}: {count} категорий")

        print(f"\nС 1C UID: {with_1c}")
    else:
        print(f"❌ Ошибка: {response_all.status_code}")
        print(response_all.text)

    # 3. Запрос С department_id=8
    print(f"\n3. Запрос категорий С фильтром department_id=8...")
    response_fin = requests.get(
        "http://localhost:8000/api/v1/categories/?department_id=8&limit=1000",
        headers=headers
    )

    if response_fin.status_code == 200:
        fin_categories = response_fin.json()
        print(f"✅ Категорий для финансового отдела: {len(fin_categories)}")

        with_1c = sum(1 for cat in fin_categories if cat.get("external_id_1c"))
        print(f"С 1C UID: {with_1c}")

        # Найти Аутсорс
        autsors = [cat for cat in fin_categories if "аутсорс" in cat.get("name", "").lower()]
        if autsors:
            print(f"\n✅ Найдено {len(autsors)} категорий 'Аутсорс':")
            for cat in autsors:
                print(f"  - {cat['name']} (ID: {cat['id']}, Code: {cat.get('code_1c')})")
        else:
            print("\n❌ 'Аутсорс' не найден в API ответе")
    else:
        print(f"❌ Ошибка: {response_fin.status_code}")
        print(response_fin.text)

    # 4. Сравнение с БД
    print(f"\n4. Сравнение с базой данных...")
    db: Session = SessionLocal()

    try:
        db_count = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == 8,
            BudgetCategory.external_id_1c.isnot(None)
        ).count()

        print(f"В БД (department_id=8, с 1C UID): {db_count}")

        if response_fin.status_code == 200:
            api_count = sum(1 for cat in fin_categories if cat.get("external_id_1c"))
            print(f"Через API (department_id=8, с 1C UID): {api_count}")

            if db_count != api_count:
                print(f"\n⚠️ РАСХОЖДЕНИЕ: БД={db_count}, API={api_count}")
            else:
                print(f"\n✅ Данные совпадают!")
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80)


if __name__ == "__main__":
    check_categories_api()
