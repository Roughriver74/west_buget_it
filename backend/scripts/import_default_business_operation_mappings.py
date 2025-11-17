#!/usr/bin/env python3
"""
Import default business operation mappings for automatic transaction categorization.

This script creates standard mappings between 1C business operations and budget categories.
Run this after setting up a new environment or department to enable automatic categorization.

Usage:
    python scripts/import_default_business_operation_mappings.py
    python scripts/import_default_business_operation_mappings.py --department-id 8
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    BusinessOperationMapping,
    BudgetCategory,
    Department,
    User,
    UserRoleEnum
)
from app.core.logging import log_info, log_error, log_warning
import argparse


# Default mappings for standard 1C business operations
DEFAULT_MAPPINGS = [
    # Зарплата и ФОТ (приоритет 100 - максимальный)
    {
        "business_operation": "ВыплатаЗарплаты",
        "category_names": ["ФОТ", "Зарплата"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Выплата зарплаты сотрудникам"
    },
    {
        "business_operation": "ВыплатаЗарплатыНаЛицевыеСчета",
        "category_names": ["ФОТ", "Зарплата"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Зарплата на карточные счета сотрудников"
    },
    {
        "business_operation": "ВыплатаЗарплатыПоЗарплатномуПроекту",
        "category_names": ["ФОТ", "Зарплата"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Зарплата по зарплатному проекту"
    },

    # Налоги и взносы (приоритет 100)
    {
        "business_operation": "ПеречислениеНДФЛ",
        "category_names": ["НДФЛ", "Налоги"],
        "priority": 100,
        "confidence": 0.99,
        "notes": "Перечисление НДФЛ в бюджет"
    },
    {
        "business_operation": "ПеречислениеНДС",
        "category_names": ["Налог НДС", "Налоги"],
        "priority": 100,
        "confidence": 0.99,
        "notes": "Перечисление НДС в бюджет"
    },
    {
        "business_operation": "ПеречислениеСтраховыхВзносов",
        "category_names": ["Страховые взносы", "Налоги"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Страховые взносы (ПФР, ФСС, ФФОМС)"
    },
    {
        "business_operation": "ПеречислениеВБюджет",
        "category_names": ["Налоги"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Прочие перечисления в бюджет"
    },

    # Банковские услуги (приоритет 100)
    {
        "business_operation": "КомиссияБанка",
        "category_names": ["Услуги банка", "Банковские услуги"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Комиссия банка за операции"
    },
    {
        "business_operation": "ОплатаБанковскихУслуг",
        "category_names": ["Услуги банка", "Банковские услуги"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Оплата услуг банка (РКО, переводы и т.д.)"
    },

    # Поставщики и клиенты (приоритет 100)
    {
        "business_operation": "ОплатаПоставщику",
        "category_names": ["Поставщики (расход)", "Закупки у поставщиков"],
        "priority": 100,
        "confidence": 0.69,  # Ниже уверенность, т.к. может быть разная номенклатура
        "notes": "Оплата поставщику за товары/услуги"
    },
    {
        "business_operation": "ПоступлениеОплатыОтКлиента",
        "category_names": ["Покупатели (приход)", "Реализация продукции"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Поступление оплаты от покупателя"
    },
    {
        "business_operation": "ПоступлениеОплатыПоПлатежнойКарте",
        "category_names": ["Покупатели (приход)", "Реализация продукции"],
        "priority": 100,
        "confidence": 0.98,
        "notes": "Оплата по платежной карте от покупателя"
    },

    # Подотчет (приоритет 95)
    {
        "business_operation": "ВыдачаДенежныхСредствВПодотчет",
        "category_names": ["Подотчет", "Хозяйственные расходы"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Выдача денег подотчетному лицу"
    },
    {
        "business_operation": "ВыдачаПодотчетномуЛицу",
        "category_names": ["Подотчет", "Хозяйственные расходы"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Выдача подотчетному лицу"
    },
    {
        "business_operation": "ПоступлениеОтПодотчетногоЛица",
        "category_names": ["Подотчет", "Хозяйственные расходы"],
        "priority": 95,
        "confidence": 0.95,
        "notes": "Возврат неиспользованных подотчетных средств"
    },
]


def get_or_create_admin_user(db: Session) -> User:
    """Get first ADMIN user for created_by field"""
    admin = db.query(User).filter(User.role == UserRoleEnum.ADMIN).first()
    if not admin:
        log_warning("No ADMIN user found, creating mappings without created_by")
        return None
    return admin


def import_mappings_for_department(
    db: Session,
    department: Department,
    admin_user: User = None
) -> dict:
    """
    Import default mappings for a specific department.

    Returns:
        dict with statistics (created, updated, skipped, errors)
    """
    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": []
    }

    log_info(f"\nProcessing department: {department.name} (ID: {department.id})")

    for mapping_data in DEFAULT_MAPPINGS:
        business_operation = mapping_data["business_operation"]
        category_names = mapping_data["category_names"]
        priority = mapping_data["priority"]
        confidence = mapping_data["confidence"]
        notes = mapping_data.get("notes", "")

        # Try to find matching category for this department
        category = None
        for cat_name in category_names:
            category = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == department.id,
                BudgetCategory.name == cat_name,
                BudgetCategory.is_active == True
            ).first()

            if category:
                log_info(f"  ✓ Found category '{cat_name}' for operation '{business_operation}'")
                break

        if not category:
            log_warning(
                f"  ⚠ No matching category found for '{business_operation}' "
                f"(tried: {', '.join(category_names)})"
            )
            stats["skipped"] += 1
            continue

        # Check if mapping already exists
        existing = db.query(BusinessOperationMapping).filter(
            BusinessOperationMapping.business_operation == business_operation,
            BusinessOperationMapping.department_id == department.id,
            BusinessOperationMapping.category_id == category.id
        ).first()

        if existing:
            # Update if needed
            updated = False
            if existing.priority != priority:
                existing.priority = priority
                updated = True
            if existing.confidence != confidence:
                existing.confidence = confidence
                updated = True
            if existing.notes != notes:
                existing.notes = notes
                updated = True
            if not existing.is_active:
                existing.is_active = True
                updated = True

            if updated:
                db.commit()
                log_info(f"  ↻ Updated mapping: {business_operation} → {category.name}")
                stats["updated"] += 1
            else:
                log_info(f"  = Skipped (already exists): {business_operation} → {category.name}")
                stats["skipped"] += 1
        else:
            # Create new mapping
            try:
                new_mapping = BusinessOperationMapping(
                    business_operation=business_operation,
                    category_id=category.id,
                    department_id=department.id,
                    priority=priority,
                    confidence=confidence,
                    notes=notes,
                    is_active=True,
                    created_by=admin_user.id if admin_user else None
                )
                db.add(new_mapping)
                db.commit()
                log_info(f"  + Created mapping: {business_operation} → {category.name}")
                stats["created"] += 1
            except Exception as e:
                db.rollback()
                error_msg = f"Error creating mapping {business_operation}: {str(e)}"
                log_error(error_msg)
                stats["errors"].append(error_msg)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Import default business operation mappings"
    )
    parser.add_argument(
        "--department-id",
        type=int,
        help="Import only for specific department ID (default: all departments)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update existing mappings"
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        # Get admin user for created_by field
        admin_user = get_or_create_admin_user(db)

        # Get departments to process
        if args.department_id:
            departments = db.query(Department).filter(
                Department.id == args.department_id,
                Department.is_active == True
            ).all()
            if not departments:
                log_error(f"Department with ID {args.department_id} not found or inactive")
                return 1
        else:
            departments = db.query(Department).filter(
                Department.is_active == True
            ).all()
            if not departments:
                log_error("No active departments found")
                return 1

        log_info(f"\n{'='*60}")
        log_info(f"Import Default Business Operation Mappings")
        log_info(f"{'='*60}")
        log_info(f"Processing {len(departments)} department(s)")
        log_info(f"Default mappings: {len(DEFAULT_MAPPINGS)} operations")

        # Process each department
        total_stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }

        for dept in departments:
            dept_stats = import_mappings_for_department(db, dept, admin_user)
            total_stats["created"] += dept_stats["created"]
            total_stats["updated"] += dept_stats["updated"]
            total_stats["skipped"] += dept_stats["skipped"]
            total_stats["errors"].extend(dept_stats["errors"])

        # Print summary
        log_info(f"\n{'='*60}")
        log_info(f"SUMMARY")
        log_info(f"{'='*60}")
        log_info(f"✓ Created:  {total_stats['created']}")
        log_info(f"↻ Updated:  {total_stats['updated']}")
        log_info(f"= Skipped:  {total_stats['skipped']}")
        log_info(f"✗ Errors:   {len(total_stats['errors'])}")

        if total_stats["errors"]:
            log_error("\nErrors:")
            for error in total_stats["errors"]:
                log_error(f"  - {error}")

        log_info(f"\n✅ Import completed successfully!")

        return 0

    except Exception as e:
        log_error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
