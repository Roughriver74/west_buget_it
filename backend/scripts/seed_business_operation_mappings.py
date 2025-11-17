"""
Seed Business Operation Mappings

Скрипт для заполнения таблицы business_operation_mappings начальными данными.
Создаёт базовые маппинги хозяйственных операций из 1С на категории бюджета.

Запуск:
    python scripts/seed_business_operation_mappings.py --department-id 1

Или для всех отделов:
    python scripts/seed_business_operation_mappings.py --all-departments
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import argparse
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import (
    BusinessOperationMapping,
    BudgetCategory,
    Department,
    User
)


# Базовые маппинги (операция → название категории)
# Это начальный набор, который можно настроить для каждого отдела
BASE_MAPPINGS = {
    # === ПОСТУПЛЕНИЯ (CREDIT) ===
    "ПоступлениеОплатыОтКлиента": {
        "category_names": ["Выручка от клиентов", "Доход от продаж", "Клиенты"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Оплата от клиента/покупателя"
    },
    "ПоступлениеОплатыПоПлатежнойКарте": {
        "category_names": ["Выручка от клиентов", "Доход от продаж", "Клиенты"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Оплата по платежной карте"
    },
    "ПоступлениеОтПодотчетногоЛица": {
        "category_names": ["Возврат подотчетных средств", "Подотчетные средства", "Подотчет"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Возврат подотчетных средств"
    },
    "ВозвратОтПоставщика": {
        "category_names": ["Возврат от поставщика", "Возвраты"],
        "priority": 90,
        "confidence": 0.95,
        "notes": "Возврат товаров/средств от поставщика"
    },
    "ПолучениеКредитаЗайма": {
        "category_names": ["Получение кредита", "Кредиты", "Займы"],
        "priority": 90,
        "confidence": 0.98,
        "notes": "Получение кредита или займа"
    },

    # === СПИСАНИЯ (DEBIT) ===
    # Зарплата
    "ВыплатаЗарплатыНаЛицевыеСчета": {
        "category_names": ["Зарплата", "Оплата труда", "ФОТ"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Выплата зарплаты на лицевые счета"
    },
    "ВыплатаЗарплатыПоЗарплатномуПроекту": {
        "category_names": ["Зарплата", "Оплата труда", "ФОТ"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Выплата зарплаты через зарплатный проект"
    },
    "ВыплатаЗарплаты": {
        "category_names": ["Зарплата", "Оплата труда", "ФОТ"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Общая выплата зарплаты"
    },
    "ВыплатаПособий": {
        "category_names": ["Пособия и компенсации", "Социальные выплаты", "Компенсации"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Больничные, отпускные, пособия"
    },

    # Налоги
    "ПеречислениеВБюджет": {
        "category_names": ["Налоги и сборы", "Налоги", "Бюджетные платежи"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Общее перечисление в бюджет (налоги)"
    },
    "ПеречислениеНДС": {
        "category_names": ["НДС", "Налоги и сборы", "Налоги"],
        "priority": 100,
        "confidence": 0.99,
        "notes": "Перечисление НДС"
    },
    "ПеречислениеНДФЛ": {
        "category_names": ["НДФЛ", "Налоги и сборы", "Налоги"],
        "priority": 100,
        "confidence": 0.99,
        "notes": "Перечисление НДФЛ"
    },
    "ПеречислениеСтраховыхВзносов": {
        "category_names": ["Страховые взносы", "Налоги и сборы", "Взносы"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "ПФР, ФСС, ФФОМС"
    },

    # Закупки
    "ОплатаПоставщику": {
        "category_names": ["Закупки у поставщиков", "Оплата поставщикам", "Закупки"],
        "priority": 90,
        "confidence": 0.95,
        "notes": "Оплата товаров/услуг поставщику"
    },
    "ПредоплатаПоставщику": {
        "category_names": ["Предоплата поставщикам", "Авансы поставщикам", "Закупки"],
        "priority": 90,
        "confidence": 0.95,
        "notes": "Авансы и предоплаты поставщикам"
    },
    "ОплатаТоваровУслуг": {
        "category_names": ["Закупки у поставщиков", "Оплата поставщикам", "Закупки"],
        "priority": 85,
        "confidence": 0.90,
        "notes": "Общая оплата товаров/услуг"
    },

    # Подотчет
    "ВыдачаПодотчетномуЛицу": {
        "category_names": ["Выдача подотчетных средств", "Подотчетные средства", "Подотчет"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Выдача денег подотчетному лицу"
    },
    "ВыдачаДенежныхСредствВПодотчет": {
        "category_names": ["Выдача подотчетных средств", "Подотчетные средства", "Подотчет"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Выдача в подотчет"
    },

    # Кредиты
    "ВозвратКредитаЗайма": {
        "category_names": ["Возврат кредита", "Кредиты", "Погашение кредитов"],
        "priority": 95,
        "confidence": 0.98,
        "notes": "Погашение кредита/займа"
    },
    "УплатаПроцентовПоКредиту": {
        "category_names": ["Проценты по кредитам", "Кредиты", "Банковские проценты"],
        "priority": 95,
        "confidence": 0.98,
        "notes": "Уплата процентов по кредиту"
    },

    # Внутренние переводы
    "ОплатаДенежныхСредствВДругуюОрганизацию": {
        "category_names": ["Внутренние переводы", "Внутригрупповые расчеты"],
        "priority": 90,
        "confidence": 0.95,
        "notes": "Перевод между своими организациями"
    },
    "ПеречислениеВДругуюОрганизацию": {
        "category_names": ["Внутренние переводы", "Внутригрупповые расчеты"],
        "priority": 90,
        "confidence": 0.95,
        "notes": "Перевод в другую свою организацию"
    },

    # Комиссии банка
    "КомиссияБанка": {
        "category_names": ["Комиссии банка", "Банковские услуги", "Услуги банка"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Комиссия банка за операции"
    },
    "ОплатаБанковскихУслуг": {
        "category_names": ["Комиссии банка", "Банковские услуги", "Услуги банка"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Оплата банковского обслуживания"
    },

    # Прочее
    "ПрочееСписание": {
        "category_names": ["Прочие расходы", "Прочие операции"],
        "priority": 50,
        "confidence": 0.70,
        "notes": "Прочие списания"
    },
    "ПрочаяОперация": {
        "category_names": ["Прочие расходы", "Прочие операции"],
        "priority": 50,
        "confidence": 0.70,
        "notes": "Прочие операции"
    },
}


def find_category_by_names(db: Session, department_id: int, category_names: list) -> int | None:
    """
    Найти категорию по списку возможных названий

    Args:
        db: Database session
        department_id: ID отдела
        category_names: Список возможных названий категории

    Returns:
        category_id или None
    """
    for name in category_names:
        category = (
            db.query(BudgetCategory)
            .filter(
                BudgetCategory.name.ilike(f"%{name}%"),
                BudgetCategory.department_id == department_id,
                BudgetCategory.is_active == True
            )
            .first()
        )
        if category:
            return category.id

    return None


def seed_mappings_for_department(db: Session, department_id: int, user_id: int | None = None):
    """
    Заполнить маппинги для указанного отдела

    Args:
        db: Database session
        department_id: ID отдела
        user_id: ID пользователя (для created_by)
    """
    print(f"\n=== Seeding mappings for department_id={department_id} ===\n")

    created_count = 0
    skipped_count = 0
    not_found_count = 0

    for business_operation, config in BASE_MAPPINGS.items():
        # Проверить, существует ли уже маппинг
        existing = (
            db.query(BusinessOperationMapping)
            .filter(
                BusinessOperationMapping.business_operation == business_operation,
                BusinessOperationMapping.department_id == department_id
            )
            .first()
        )

        if existing:
            print(f"⏭️  SKIP: {business_operation} (already exists)")
            skipped_count += 1
            continue

        # Найти категорию по списку названий
        category_id = find_category_by_names(db, department_id, config["category_names"])

        if not category_id:
            print(f"❌ NOT FOUND: {business_operation} → no matching category for {config['category_names']}")
            not_found_count += 1
            continue

        # Создать маппинг
        mapping = BusinessOperationMapping(
            business_operation=business_operation,
            category_id=category_id,
            priority=config["priority"],
            confidence=Decimal(str(config["confidence"])),
            notes=config["notes"],
            department_id=department_id,
            created_by=user_id
        )
        db.add(mapping)
        created_count += 1
        print(f"✅ CREATED: {business_operation} → category_id={category_id} ({config['category_names'][0]})")

    db.commit()

    print(f"\n=== Summary for department_id={department_id} ===")
    print(f"✅ Created: {created_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Not found: {not_found_count}")
    print(f"📊 Total: {created_count + skipped_count + not_found_count}")


def main():
    parser = argparse.ArgumentParser(description="Seed business operation mappings")
    parser.add_argument("--department-id", type=int, help="Department ID to seed mappings for")
    parser.add_argument("--all-departments", action="store_true", help="Seed for all departments")
    parser.add_argument("--user-id", type=int, help="User ID for created_by field (optional)")

    args = parser.parse_args()

    if not args.department_id and not args.all_departments:
        print("❌ Error: specify --department-id or --all-departments")
        sys.exit(1)

    db = SessionLocal()

    try:
        if args.all_departments:
            # Получить все отделы
            departments = db.query(Department).filter(Department.is_active == True).all()
            print(f"Found {len(departments)} active departments")

            for dept in departments:
                seed_mappings_for_department(db, dept.id, args.user_id)

        else:
            # Проверить, существует ли отдел
            dept = db.query(Department).filter(Department.id == args.department_id).first()
            if not dept:
                print(f"❌ Error: Department with id={args.department_id} not found")
                sys.exit(1)

            seed_mappings_for_department(db, args.department_id, args.user_id)

        print("\n✅ Seeding completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
