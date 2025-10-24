#!/usr/bin/env python3
"""
Скрипт для организации категорий в иерархию (группы)
"""

import sys
import os
from pathlib import Path

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, ExpenseTypeEnum

# Определяем иерархию категорий
CATEGORY_GROUPS = {
    "Лицензии и ПО": {
        "type": ExpenseTypeEnum.OPEX,
        "description": "Программное обеспечение и лицензии",
        "subcategories": [
            "1с(лицензии)",
            "Битрикс24(лицензии)",
            "Покупка ПО",
        ]
    },
    "Связь и коммуникации": {
        "type": ExpenseTypeEnum.OPEX,
        "description": "Телефония, интернет, интеграции",
        "subcategories": [
            "Интегарции телефонии чатов и пр",
            "Почтовый Сервер",
            "Связь (телефон/интернет)",
        ]
    },
    "Разработка и настройка": {
        "type": ExpenseTypeEnum.OPEX,
        "description": "Разработка, настройка систем",
        "subcategories": [
            "Битрикс 24(настройка)",
            "Битрикс 24 Разработка",
            "1с",
            "Аналитика данных",
            "Приложение визитов(разработка)",
            "Аутсорс",
        ]
    },
    "Обслуживание и ремонт": {
        "type": ExpenseTypeEnum.OPEX,
        "description": "Обслуживание, ремонт, расходные материалы",
        "subcategories": [
            "Ремонты и тех обслуживание",
            "Обслуживание оргтехники",
            "Заправка картриджей",
            "Расходные материалы",
        ]
    },
    "Серверы и хостинг": {
        "type": ExpenseTypeEnum.CAPEX,
        "description": "Серверное оборудование и хостинг",
        "subcategories": [
            "Сервер 1с",
            "Хостинг CRM",
            "Новая квартира для серверов",
        ]
    },
    "Техника офисов": {
        "type": ExpenseTypeEnum.CAPEX,
        "description": "Компьютерная техника и оборудование по офисам",
        "subcategories": [
            "Реновация техники",
            "Покупка принтеров и прочей орг техники(обновление)",
            "Техника Краснодар",
            "Техника Логистика",
            "Техника Склад",
            "Техника ВЭД",
            "Техника Юр. отдел",
            "Техника Москва",
            "Техника Сервис",
            "Техника ОП СПб",
            "Техника отдел маркетинга",
            "Техника",
        ]
    },
    "Прочие расходы": {
        "type": ExpenseTypeEnum.OPEX,
        "description": "Непредвиденные расходы и риски",
        "subcategories": [
            "Непредвиденные расходы и риски",
            "Непредвиденные расходы и риски¶",
        ]
    },
}


def organize_categories(db: Session):
    """Организовать категории в иерархию"""

    print(f"\n{'='*80}")
    print("ОРГАНИЗАЦИЯ КАТЕГОРИЙ В ИЕРАРХИЮ")
    print(f"{'='*80}\n")

    # Получаем все существующие категории
    existing_categories = {}
    for cat in db.query(BudgetCategory).all():
        existing_categories[cat.name] = cat

    print(f"📊 Найдено существующих категорий: {len(existing_categories)}")

    # Создаем группы и назначаем подкатегории
    groups_created = 0
    relationships_created = 0

    for group_name, group_info in CATEGORY_GROUPS.items():
        # Проверяем, существует ли группа
        if group_name in existing_categories:
            parent = existing_categories[group_name]
            print(f"  ✓ Группа '{group_name}' уже существует")
        else:
            # Создаем родительскую категорию (группу)
            parent = BudgetCategory(
                name=group_name,
                type=group_info["type"],
                description=group_info["description"],
                is_active=True,
                parent_id=None
            )
            db.add(parent)
            db.flush()  # Чтобы получить ID
            groups_created += 1
            print(f"  + Создана группа: {group_name} ({group_info['type'].value})")

        # Назначаем подкатегории
        for subcat_name in group_info["subcategories"]:
            if subcat_name in existing_categories:
                subcat = existing_categories[subcat_name]
                if subcat.parent_id != parent.id:
                    subcat.parent_id = parent.id
                    relationships_created += 1
                    print(f"    └─ {subcat_name}")
            else:
                print(f"    ⚠️  Подкатегория '{subcat_name}' не найдена")

    # Коммитим изменения
    db.commit()

    print(f"\n{'='*80}")
    print("✅ ИЕРАРХИЯ СОЗДАНА")
    print(f"{'='*80}\n")

    print(f"Создано групп: {groups_created}")
    print(f"Установлено связей: {relationships_created}")

    # Показываем финальную иерархию
    print(f"\n{'='*80}")
    print("ФИНАЛЬНАЯ СТРУКТУРА КАТЕГОРИЙ")
    print(f"{'='*80}\n")

    # Получаем все категории заново
    root_categories = db.query(BudgetCategory).filter(
        BudgetCategory.parent_id == None
    ).order_by(BudgetCategory.name).all()

    total_categories = 0
    for parent in root_categories:
        cat_type = "CAPEX" if parent.type == ExpenseTypeEnum.CAPEX else "OPEX"
        print(f"\n{parent.name} ({cat_type})")
        print(f"  {parent.description}")

        # Получаем подкатегории
        subcategories = db.query(BudgetCategory).filter(
            BudgetCategory.parent_id == parent.id
        ).order_by(BudgetCategory.name).all()

        if subcategories:
            print(f"  Подкатегорий: {len(subcategories)}")
            for subcat in subcategories:
                total_categories += 1
                print(f"    └─ {subcat.name}")
        else:
            total_categories += 1
            print(f"    (нет подкатегорий)")

    print(f"\n{'='*80}")
    print(f"Всего категорий в системе: {total_categories}")
    print(f"Групп верхнего уровня: {len(root_categories)}")
    print(f"{'='*80}\n")


def main():
    """Основная функция"""
    db = SessionLocal()

    try:
        organize_categories(db)
    except Exception as e:
        print(f"\n❌ Ошибка при организации: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
