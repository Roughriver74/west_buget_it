#!/usr/bin/env python3
"""
Скрипт для проверки корректности плана в БД и сверки с Excel
"""

import sys
import os
from pathlib import Path
import pandas as pd
from decimal import Decimal

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import BudgetPlan, BudgetCategory
from sqlalchemy import func

def verify_plan():
    """Проверить корректность плана"""

    db = SessionLocal()

    print(f"\n{'='*80}")
    print("СВЕРКА ПЛАНА С EXCEL")
    print(f"{'='*80}\n")

    # Читаем Excel
    excel_path = Path(__file__).parent.parent.parent / 'Планфакт2025.xlsx'
    df_plan = pd.read_excel(excel_path, sheet_name=0)

    print(f"📄 Читаем Excel: {excel_path}")

    # Маппинг месяцев
    MONTH_MAPPING = {
        'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
        'май': 5, 'Май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
        'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
    }

    # Получаем все категории
    categories = {cat.name: cat for cat in db.query(BudgetCategory).all()}

    issues = []
    correct = []

    # Проверяем каждую категорию из Excel
    for idx, row in df_plan.iterrows():
        category_name = row['СТАТЬЯ']

        if pd.isna(category_name):
            continue

        # Пропускаем итоговые строки
        if category_name in ['ИТОГО', 'общие затраты на технику', 'МСК', 'КРД', 'ИТОГО без МСК и КРД']:
            continue

        # Проверяем, есть ли категория в БД
        if category_name not in categories:
            issues.append(f"❌ Категория '{category_name}' из Excel НЕ НАЙДЕНА в БД")
            continue

        category = categories[category_name]

        # Проверяем план по месяцам
        for col in df_plan.columns[1:]:
            if col not in MONTH_MAPPING:
                continue

            month_num = MONTH_MAPPING[col]
            excel_value = row[col]

            if pd.isna(excel_value) or excel_value == 0:
                continue

            # Получаем значение из БД
            db_plan = db.query(BudgetPlan).filter(
                BudgetPlan.year == 2025,
                BudgetPlan.month == month_num,
                BudgetPlan.category_id == category.id
            ).first()

            if not db_plan:
                issues.append(
                    f"❌ {category_name} / {col}: в Excel {excel_value:,.0f}, в БД НЕТ ЗАПИСИ"
                )
            elif float(db_plan.planned_amount) != float(excel_value):
                issues.append(
                    f"⚠️  {category_name} / {col}: в Excel {excel_value:,.0f}, в БД {float(db_plan.planned_amount):,.0f}"
                )
            else:
                correct.append(f"✓ {category_name} / {col}: {excel_value:,.0f}")

    # Выводим результаты
    print(f"\n{'='*80}")
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print(f"{'='*80}\n")

    print(f"✅ Совпадений: {len(correct)}")
    print(f"❌ Несоответствий: {len(issues)}")

    if issues:
        print(f"\n{'='*80}")
        print("НАЙДЕННЫЕ ПРОБЛЕМЫ:")
        print(f"{'='*80}\n")

        for issue in issues[:20]:  # Показываем первые 20
            print(f"  {issue}")

        if len(issues) > 20:
            print(f"\n  ... и еще {len(issues) - 20} проблем")

    # Проверяем общую сумму
    print(f"\n{'='*80}")
    print("ОБЩИЕ СУММЫ:")
    print(f"{'='*80}\n")

    # Сумма из БД
    db_total = db.query(func.sum(BudgetPlan.planned_amount)).filter(
        BudgetPlan.year == 2025
    ).scalar() or 0

    # Сумма из Excel
    excel_total = 0
    for idx, row in df_plan.iterrows():
        category_name = row['СТАТЬЯ']
        if pd.isna(category_name) or category_name in ['ИТОГО', 'общие затраты на технику', 'МСК', 'КРД', 'ИТОГО без МСК и КРД']:
            continue

        for col in df_plan.columns[1:]:
            if col in MONTH_MAPPING:
                val = row[col]
                if pd.notna(val):
                    excel_total += float(val)

    print(f"Сумма в БД:    {db_total:20,.2f} руб")
    print(f"Сумма в Excel: {excel_total:20,.2f} руб")
    print(f"Разница:       {abs(db_total - excel_total):20,.2f} руб")

    db.close()

    return len(issues) == 0


def main():
    """Основная функция"""
    try:
        if verify_plan():
            print("\n✅ Все данные совпадают!")
            sys.exit(0)
        else:
            print("\n⚠️  Найдены несоответствия")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
