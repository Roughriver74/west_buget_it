#!/usr/bin/env python3
"""Скрипт для проверки импортированных данных"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Добавляем путь к проекту для импорта моделей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# Загружаем переменные окружения
env_path = project_root / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    os.environ.setdefault('DEBUG', 'False')
    os.environ.setdefault('SECRET_KEY', 'temporary-secret-key-for-import-script-only')
    os.environ.setdefault('DATABASE_URL', 'postgresql://budget_user:budget_pass@localhost:5432/budget_db')
    os.environ.setdefault('CORS_ORIGINS', '["http://localhost:3000"]')

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import (
    BudgetPlan, Expense, Employee, PayrollPlan, Department, BudgetCategory
)

def main():
    """Проверка импортированных данных"""
    db = SessionLocal()

    try:
        print("="*80)
        print("ПРОВЕРКА ИМПОРТИРОВАННЫХ ДАННЫХ")
        print("="*80)

        # Проверяем отдел
        dept_count = db.query(Department).filter(Department.code == "WEST").count()
        print(f"\nОтделы с кодом WEST: {dept_count}")

        # Проверяем категории бюджета
        category_count = db.query(BudgetCategory).count()
        print(f"Категорий бюджета: {category_count}")

        # Проверяем плановые данные бюджета
        budget_plan_count = db.query(BudgetPlan).filter(BudgetPlan.year == 2025).count()
        budget_plan_sum = db.query(func.sum(BudgetPlan.planned_amount)).filter(
            BudgetPlan.year == 2025
        ).scalar() or 0
        print(f"\nПлановые записи бюджета за 2025: {budget_plan_count}")
        print(f"Сумма планового бюджета за 2025: {budget_plan_sum:,.2f} руб.")

        # Проверяем фактические расходы
        expense_count = db.query(Expense).count()
        expense_sum = db.query(func.sum(Expense.amount)).scalar() or 0
        print(f"\nФактические расходы: {expense_count}")
        print(f"Сумма фактических расходов: {expense_sum:,.2f} руб.")

        # Проверяем сотрудников
        employee_count = db.query(Employee).count()
        print(f"\nСотрудников: {employee_count}")

        # Проверяем планы ФОТ
        payroll_plan_count = db.query(PayrollPlan).filter(PayrollPlan.year == 2025).count()
        payroll_plan_sum = db.query(func.sum(PayrollPlan.total_planned)).filter(
            PayrollPlan.year == 2025
        ).scalar() or 0
        print(f"\nПланы ФОТ за 2025: {payroll_plan_count}")
        print(f"Сумма планового ФОТ за 2025: {payroll_plan_sum:,.2f} руб.")

        # Детальная разбивка по месяцам для планового бюджета
        print(f"\n{'='*80}")
        print("ПЛАНОВЫЙ БЮДЖЕТ ПО МЕСЯЦАМ (2025)")
        print(f"{'='*80}")
        for month in range(1, 13):
            month_sum = db.query(func.sum(BudgetPlan.planned_amount)).filter(
                BudgetPlan.year == 2025,
                BudgetPlan.month == month
            ).scalar() or 0
            month_names = [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]
            print(f"{month_names[month-1]:12s}: {month_sum:>15,.2f} руб.")

        # Детальная разбивка по месяцам для ФОТ
        print(f"\n{'='*80}")
        print("ПЛАНОВЫЙ ФОТ ПО МЕСЯЦАМ (2025)")
        print(f"{'='*80}")
        for month in range(1, 13):
            month_sum = db.query(func.sum(PayrollPlan.total_planned)).filter(
                PayrollPlan.year == 2025,
                PayrollPlan.month == month
            ).scalar() or 0
            month_names = [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]
            print(f"{month_names[month-1]:12s}: {month_sum:>15,.2f} руб.")

        print(f"\n{'='*80}")
        print("✓ ПРОВЕРКА ЗАВЕРШЕНА")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n✗ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
