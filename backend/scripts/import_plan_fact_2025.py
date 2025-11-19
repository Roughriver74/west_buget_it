#!/usr/bin/env python3
"""
Скрипт для импорта данных плана и факта на 2025 год из файла Планфакт2025.xlsx
Лист 1 - План
Лист 2 - Факт
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.models import BudgetCategory, BudgetPlan, Expense, Organization, Contractor, ExpenseTypeEnum, ExpenseStatusEnum, BudgetStatusEnum

# Маппинг месяцев
MONTH_MAPPING = {
    'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
    'май': 5, 'Май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
    'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
}


def get_or_create_category(db: Session, name: str) -> BudgetCategory:
    """Получить или создать категорию бюджета"""
    category = db.query(BudgetCategory).filter(BudgetCategory.name == name).first()

    if not category:
        # Определяем тип расхода по названию
        expense_type = ExpenseTypeEnum.CAPEX if any(word in name.lower() for word in [
            'техника', 'сервер', 'покупка', 'реновация', 'обновление'
        ]) else ExpenseTypeEnum.OPEX

        category = BudgetCategory(
            name=name,
            type=expense_type,
            description=f"Импортировано из Планфакт2025.xlsx",
            is_active=True
        )
        db.add(category)
        db.flush()
        print(f"✓ Создана категория: {name} ({expense_type})")

    return category


def get_or_create_organization(db: Session) -> Organization:
    """Получить или создать организацию по умолчанию"""
    org = db.query(Organization).filter(Organization.name == "ДЕМО ООО").first()
    if not org:
        org = Organization(
            name="ДЕМО ООО",
            legal_name="Общество с ограниченной ответственностью ДЕМО",
            is_active=True
        )
        db.add(org)
        db.flush()
    return org


def get_or_create_contractor(db: Session, name: str = "Общий") -> Contractor:
    """Получить или создать контрагента"""
    contractor = db.query(Contractor).filter(Contractor.name == name).first()
    if not contractor:
        contractor = Contractor(
            name=name,
            is_active=True
        )
        db.add(contractor)
        db.flush()
    return contractor


def import_budget_plan(db: Session, excel_file: str, year: int = 2025):
    """Импорт плана бюджета из первого листа Excel"""
    print(f"\n{'='*80}")
    print(f"ИМПОРТ ПЛАНА БЮДЖЕТА НА {year} ГОД")
    print(f"{'='*80}\n")

    # Читаем первый лист
    df = pd.read_excel(excel_file, sheet_name=0)

    # Удаляем строки-итоги
    df = df[~df['СТАТЬЯ'].str.contains('ИТОГО|общие затраты', case=False, na=False)]

    total_records = 0

    for idx, row in df.iterrows():
        category_name = row['СТАТЬЯ']

        if pd.isna(category_name):
            continue

        # Получаем или создаем категорию
        category = get_or_create_category(db, category_name)

        # Проходим по всем месяцам
        for month_name, amount in row[1:].items():
            if pd.notna(amount) and amount > 0:
                month_num = MONTH_MAPPING.get(month_name)
                if not month_num:
                    continue

                # Проверяем, есть ли уже запись
                existing = db.query(BudgetPlan).filter(
                    BudgetPlan.year == year,
                    BudgetPlan.month == month_num,
                    BudgetPlan.category_id == category.id
                ).first()

                if existing:
                    existing.planned_amount = Decimal(str(amount))
                    if category.type == ExpenseTypeEnum.CAPEX:
                        existing.capex_planned = Decimal(str(amount))
                        existing.opex_planned = Decimal('0')
                    else:
                        existing.opex_planned = Decimal(str(amount))
                        existing.capex_planned = Decimal('0')
                else:
                    budget_plan = BudgetPlan(
                        year=year,
                        month=month_num,
                        category_id=category.id,
                        planned_amount=Decimal(str(amount)),
                        capex_planned=Decimal(str(amount)) if category.type == ExpenseTypeEnum.CAPEX else Decimal('0'),
                        opex_planned=Decimal(str(amount)) if category.type == ExpenseTypeEnum.OPEX else Decimal('0'),
                        status=BudgetStatusEnum.APPROVED
                    )
                    db.add(budget_plan)

                total_records += 1

    db.commit()
    print(f"\n✅ Импортировано записей плана: {total_records}")


def import_actual_expenses(db: Session, excel_file: str, year: int = 2025):
    """Импорт фактических расходов из второго листа Excel"""
    print(f"\n{'='*80}")
    print(f"ИМПОРТ ФАКТИЧЕСКИХ РАСХОДОВ НА {year} ГОД")
    print(f"{'='*80}\n")

    # Читаем второй лист
    df = pd.read_excel(excel_file, sheet_name=1)

    # Удаляем строки-итоги
    df = df[~df['СТАТЬЯ'].str.contains('ИТОГО|общие затраты|МСК|КРД', case=False, na=False)]

    # Получаем организацию и контрагента
    organization = get_or_create_organization(db)
    contractor = get_or_create_contractor(db, "Импорт из Excel")

    total_records = 0

    for idx, row in df.iterrows():
        category_name = row['СТАТЬЯ']

        if pd.isna(category_name):
            continue

        # Получаем или создаем категорию
        category = get_or_create_category(db, category_name)

        # Проходим по всем месяцам
        for month_name, amount in row[1:].items():
            if pd.notna(amount) and amount > 0:
                month_num = MONTH_MAPPING.get(month_name)
                if not month_num:
                    continue

                # Создаем дату заявки (середина месяца)
                request_date = datetime(year, month_num, 15)
                payment_date = datetime(year, month_num, 28)

                # Генерируем номер заявки
                expense_number = f"IMP-{year}-{month_num:02d}-{category.id:03d}"

                # Проверяем, нет ли уже такой заявки
                existing = db.query(Expense).filter(
                    Expense.number == expense_number
                ).first()

                if not existing:
                    expense = Expense(
                        number=expense_number,
                        category_id=category.id,
                        contractor_id=contractor.id,
                        organization_id=organization.id,
                        amount=Decimal(str(amount)),
                        request_date=request_date,
                        payment_date=payment_date,
                        status=ExpenseStatusEnum.PAID,
                        is_paid=True,
                        is_closed=True,
                        comment=f"Импорт из Планфакт2025.xlsx ({month_name} {year})",
                        requester="Система"
                    )
                    db.add(expense)
                    total_records += 1

    db.commit()
    print(f"\n✅ Импортировано заявок на расходы: {total_records}")


def main():
    """Основная функция импорта"""
    # Путь к файлу
    excel_file = Path(__file__).parent.parent.parent / "Планфакт2025.xlsx"

    if not excel_file.exists():
        print(f"❌ Файл не найден: {excel_file}")
        sys.exit(1)

    print(f"\n📂 Импорт данных из: {excel_file}")

    # Создаем сессию БД
    db = SessionLocal()

    try:
        # 1. Импортируем план
        import_budget_plan(db, str(excel_file), 2025)

        # 2. Импортируем факт
        import_actual_expenses(db, str(excel_file), 2025)

        print(f"\n{'='*80}")
        print("✅ ИМПОРТ ЗАВЕРШЕН УСПЕШНО!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
