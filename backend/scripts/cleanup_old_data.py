#!/usr/bin/env python3
"""
Скрипт для очистки старых данных и сохранения только импортированных из Планфакт2025.xlsx
"""

import sys
import os
from pathlib import Path

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetPlan, Expense, BudgetCategory

def cleanup_data(db: Session):
    """Очистить старые данные, оставить только импортированные"""

    print(f"\n{'='*80}")
    print("АНАЛИЗ ДАННЫХ ПЕРЕД ОЧИСТКОЙ")
    print(f"{'='*80}\n")

    # Проверяем текущее состояние
    total_expenses = db.query(Expense).count()
    imported_expenses = db.query(Expense).filter(
        Expense.number.like('IMP-2025-%')
    ).count()
    old_expenses = total_expenses - imported_expenses

    total_plans = db.query(BudgetPlan).count()
    plans_2025 = db.query(BudgetPlan).filter(BudgetPlan.year == 2025).count()
    old_plans = total_plans - plans_2025

    total_categories = db.query(BudgetCategory).count()
    imported_categories = db.query(BudgetCategory).filter(
        BudgetCategory.description.like('%Импортировано из Планфакт2025.xlsx%')
    ).count()
    old_categories = total_categories - imported_categories

    print(f"📊 Текущее состояние:")
    print(f"  Всего заявок: {total_expenses}")
    print(f"    - Импортированных (IMP-2025-*): {imported_expenses}")
    print(f"    - Старых данных: {old_expenses}")
    print(f"\n  Всего записей плана: {total_plans}")
    print(f"    - За 2025 год: {plans_2025}")
    print(f"    - Старых данных: {old_plans}")
    print(f"\n  Всего категорий: {total_categories}")
    print(f"    - Импортированных: {imported_categories}")
    print(f"    - Старых: {old_categories}")

    # Показываем примеры старых данных
    print(f"\n{'='*80}")
    print("ПРИМЕРЫ СТАРЫХ ДАННЫХ (будут удалены):")
    print(f"{'='*80}\n")

    old_expense_examples = db.query(Expense).filter(
        ~Expense.number.like('IMP-2025-%')
    ).limit(5).all()

    if old_expense_examples:
        print("Старые заявки:")
        for exp in old_expense_examples:
            print(f"  - {exp.number}: {exp.amount} руб, {exp.requester}, {exp.created_at}")

    # Подтверждение
    print(f"\n{'='*80}")
    print("⚠️  ВНИМАНИЕ!")
    print(f"{'='*80}")
    print(f"\nБудет удалено:")
    print(f"  - {old_expenses} старых заявок")
    print(f"  - {old_plans} старых записей плана")
    print(f"  - {old_categories} старых категорий")
    print(f"\nОстанется:")
    print(f"  - {imported_expenses} заявок из Excel")
    print(f"  - {plans_2025} записей плана на 2025")
    print(f"  - {imported_categories} категорий из Excel")

    response = input(f"\nПродолжить? (yes/no): ")

    if response.lower() != 'yes':
        print("\n❌ Очистка отменена")
        return

    print(f"\n{'='*80}")
    print("НАЧАЛО ОЧИСТКИ")
    print(f"{'='*80}\n")

    # 1. Удаляем старые заявки (не импортированные из Excel)
    deleted_expenses = db.query(Expense).filter(
        ~Expense.number.like('IMP-2025-%')
    ).delete(synchronize_session=False)
    print(f"✓ Удалено старых заявок: {deleted_expenses}")

    # 2. Удаляем старые записи плана (не 2025 год)
    deleted_plans = db.query(BudgetPlan).filter(
        BudgetPlan.year != 2025
    ).delete(synchronize_session=False)
    print(f"✓ Удалено старых записей плана: {deleted_plans}")

    # 3. Удаляем старые категории (не импортированные)
    # Но сначала проверим, не используются ли они в оставшихся записях
    imported_cat_ids = [cat.id for cat in db.query(BudgetCategory).filter(
        BudgetCategory.description.like('%Импортировано из Планфакт2025.xlsx%')
    ).all()]

    # Находим категории, которые используются в импортированных данных
    used_categories_in_expenses = {exp.category_id for exp in db.query(Expense).all()}
    used_categories_in_plans = {plan.category_id for plan in db.query(BudgetPlan).all()}
    used_categories = used_categories_in_expenses | used_categories_in_plans

    # Удаляем только неиспользуемые категории
    categories_to_delete = db.query(BudgetCategory).filter(
        ~BudgetCategory.id.in_(used_categories)
    ).all()

    deleted_categories = 0
    for cat in categories_to_delete:
        db.delete(cat)
        deleted_categories += 1

    print(f"✓ Удалено неиспользуемых категорий: {deleted_categories}")

    # Коммитим изменения
    db.commit()

    print(f"\n{'='*80}")
    print("✅ ОЧИСТКА ЗАВЕРШЕНА")
    print(f"{'='*80}\n")

    # Финальная статистика
    final_expenses = db.query(Expense).count()
    final_plans = db.query(BudgetPlan).count()
    final_categories = db.query(BudgetCategory).count()

    print(f"📊 Итоговое состояние:")
    print(f"  Заявок: {final_expenses}")
    print(f"  Записей плана: {final_plans}")
    print(f"  Категорий: {final_categories}")

    # Показываем распределение по месяцам
    print(f"\n{'='*80}")
    print("РАСПРЕДЕЛЕНИЕ ПО МЕСЯЦАМ (2025)")
    print(f"{'='*80}\n")

    from sqlalchemy import func, extract

    monthly_stats = db.query(
        extract('month', Expense.request_date).label('month'),
        func.count(Expense.id).label('count'),
        func.sum(Expense.amount).label('total')
    ).filter(
        extract('year', Expense.request_date) == 2025
    ).group_by('month').order_by('month').all()

    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

    for stat in monthly_stats:
        month_name = months[int(stat.month) - 1]
        print(f"  {month_name} 2025: {stat.count} заявок на {stat.total:,.2f} руб")

    print(f"\n✅ Все старые данные удалены, остались только данные из Планфакт2025.xlsx")


def main():
    """Основная функция"""
    db = SessionLocal()

    try:
        cleanup_data(db)
    except Exception as e:
        print(f"\n❌ Ошибка при очистке: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
