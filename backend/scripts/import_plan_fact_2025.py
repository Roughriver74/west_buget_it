#!/usr/bin/env python3
"""
Скрипт для импорта данных План/Факт 2025 из Excel в базу данных
"""
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, BudgetPlan, Expense, ExpenseStatusEnum, Organization, BudgetStatusEnum
from decimal import Decimal


# Маппинг названий из Excel в категории БД
CATEGORY_MAPPING = {
    'Покупка ПО': 'Покупка ПО',
    'Аутсорс': 'Аутсорс',
    'Техника': 'Техника',
    'Лицензии и ПО': 'Лицензии и ПО',
    'Интернет': 'Интернет',
    'Обслуживание': 'Обслуживание',
    'Оборудование': 'Оборудование',
}

MONTHS = {
    'январь': 1,
    'февраль': 2,
    'март': 3,
    'апрель': 4,
    'май': 5,
    'Май': 5,  # На листе "факт" май с большой буквы
    'июнь': 6,
    'июль': 7,
    'август': 8,
    'сентябрь': 9,
    'октябрь': 10,
    'ноябрь': 11,
    'декабрь': 12,
}


def get_or_create_organization(db: Session) -> Organization:
    """Получить или создать организацию по умолчанию"""
    org = db.query(Organization).filter(Organization.name == 'ВЕСТ ООО').first()
    if not org:
        org = Organization(name='ВЕСТ ООО', legal_name='ВЕСТ ООО', is_active=True)
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


def get_category_by_name(db: Session, name: str) -> BudgetCategory | None:
    """Найти категорию по имени"""
    # Пытаемся найти точное соответствие
    category = db.query(BudgetCategory).filter(
        BudgetCategory.name == name,
        BudgetCategory.is_active == True
    ).first()

    if not category:
        # Пытаемся найти по частичному совпадению
        category = db.query(BudgetCategory).filter(
            BudgetCategory.name.ilike(f'%{name}%'),
            BudgetCategory.is_active == True
        ).first()

    return category


def import_plan_data(db: Session, file_path: str):
    """Импорт плановых данных"""
    print("📊 Импорт плановых данных...")

    df = pd.read_excel(file_path, sheet_name='План')

    # Находим строки с основными категориями (те, где есть номер)
    main_categories = df[df['Unnamed: 0'].notna()]

    imported_count = 0
    skipped_count = 0

    for _, row in main_categories.iterrows():
        category_name = str(row['СТАТЬЯ']).strip()

        # Пропускаем пустые строки
        if pd.isna(category_name) or category_name == 'nan':
            continue

        # Ищем категорию в БД
        db_category = get_category_by_name(db, category_name)

        if not db_category:
            print(f"  ⚠️  Категория '{category_name}' не найдена в БД, пропускаем")
            skipped_count += 1
            continue

        print(f"  ✓ Обрабатываем: {category_name} (ID: {db_category.id})")

        # Импортируем данные по месяцам
        for month_name, month_num in MONTHS.items():
            if month_name not in df.columns:
                continue

            amount = row[month_name]

            # Пропускаем пустые значения
            if pd.isna(amount) or amount == 0:
                continue

            # Вычисляем CAPEX и OPEX
            capex = float(amount) if db_category.type.value == 'CAPEX' else 0
            opex = float(amount) if db_category.type.value == 'OPEX' else 0

            # Используем raw SQL чтобы обойти проблему с enum
            # Проверяем существующую запись
            check_sql = text("""
                SELECT id FROM budget_plans
                WHERE year = :year AND month = :month AND category_id = :category_id
            """)
            existing = db.execute(check_sql, {
                'year': 2025,
                'month': month_num,
                'category_id': db_category.id
            }).fetchone()

            if existing:
                # Обновляем существующую запись
                update_sql = text("""
                    UPDATE budget_plans
                    SET planned_amount = :amount,
                        capex_planned = :capex,
                        opex_planned = :opex,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)
                db.execute(update_sql, {
                    'amount': float(amount),
                    'capex': capex,
                    'opex': opex,
                    'id': existing[0]
                })
                print(f"    📝 Обновлён {month_name}: {amount:,.0f} руб.")
            else:
                # Создаём новую запись с явным указанием статуса на русском
                insert_sql = text("""
                    INSERT INTO budget_plans
                    (year, month, category_id, planned_amount, capex_planned, opex_planned, status, created_at, updated_at)
                    VALUES
                    (:year, :month, :category_id, :amount, :capex, :opex, 'Черновик'::budgetstatusenum, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
                db.execute(insert_sql, {
                    'year': 2025,
                    'month': month_num,
                    'category_id': db_category.id,
                    'amount': float(amount),
                    'capex': capex,
                    'opex': opex
                })
                print(f"    ➕ Создан {month_name}: {amount:,.0f} руб.")

            imported_count += 1

    db.commit()
    print(f"\n✅ Импортировано: {imported_count} записей плана")
    print(f"⚠️  Пропущено: {skipped_count} категорий\n")


def import_fact_data(db: Session, file_path: str):
    """Импорт фактических данных (только итоговые суммы по месяцам)"""
    print("📊 Импорт фактических данных...")
    print("ℹ️  Примечание: импортируются только итоговые суммы по категориям\n")

    df = pd.read_excel(file_path, sheet_name='факт')

    # Находим строки с основными категориями
    main_categories = df[df['Unnamed: 0'].notna()]

    org = get_or_create_organization(db)
    imported_count = 0
    skipped_count = 0

    for _, row in main_categories.iterrows():
        category_name = str(row['СТАТЬЯ']).strip()

        # Пропускаем пустые строки
        if pd.isna(category_name) or category_name == 'nan':
            continue

        # Ищем категорию в БД
        db_category = get_category_by_name(db, category_name)

        if not db_category:
            print(f"  ⚠️  Категория '{category_name}' не найдена в БД, пропускаем")
            skipped_count += 1
            continue

        print(f"  ✓ Обрабатываем: {category_name} (ID: {db_category.id})")

        # Импортируем итоговые суммы за год
        total_amount = row.get('ИТОГО ')

        if pd.notna(total_amount) and total_amount > 0:
            # Информационный вывод
            print(f"    ℹ️  Итоговая сумма за год: {total_amount:,.2f} руб.")
            print(f"    💡 Детальный импорт расходов можно сделать отдельным скриптом")
            imported_count += 1

    print(f"\n✅ Обработано: {imported_count} категорий с фактическими данными")
    print(f"⚠️  Пропущено: {skipped_count} категорий")
    print(f"\n💡 Для импорта детальных заявок используйте скрипт import_expenses.py\n")


def main():
    """Основная функция"""
    file_path = '/Users/evgenijsikunov/projects/west/west_buget_it/Планфакт2025.xlsx'

    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    print("=" * 70)
    print("📥 ИМПОРТ ДАННЫХ ПЛАН/ФАКТ 2025")
    print("=" * 70)
    print(f"Файл: {file_path}\n")

    db = SessionLocal()

    try:
        # Импортируем плановые данные
        import_plan_data(db, file_path)

        # Импортируем фактические данные
        import_fact_data(db, file_path)

        print("=" * 70)
        print("✅ ИМПОРТ ЗАВЕРШЁН УСПЕШНО!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == '__main__':
    main()
