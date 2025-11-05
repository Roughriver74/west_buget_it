#!/usr/bin/env python3
"""
Импорт подготовленных данных склада в базу данных
ВАЖНО: Этот скрипт нужно запускать на сервере после копирования подготовленных файлов
"""
import sys
import argparse
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

# Добавляем путь к модулям приложения
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import BudgetPlan, BudgetPlanDetail, BudgetCategory, Department, User
from app.schemas.budget import BudgetTypeEnum
from datetime import datetime

def get_or_create_budget_category(db: Session, name: str, budget_type: str, department_id: int):
    """Получить или создать категорию бюджета"""
    category = db.query(BudgetCategory).filter(
        BudgetCategory.name == name,
        BudgetCategory.department_id == department_id
    ).first()

    if not category:
        category = BudgetCategory(
            name=name,
            budget_type=budget_type,
            department_id=department_id,
            is_active=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        print(f"  ✅ Создана категория: {name} ({budget_type})")
    else:
        print(f"  ℹ️  Категория уже существует: {name}")

    return category

def get_or_create_budget_plan(db: Session, year: int, department_id: int):
    """Получить или создать бюджетный план"""
    plan = db.query(BudgetPlan).filter(
        BudgetPlan.year == year,
        BudgetPlan.department_id == department_id
    ).first()

    if not plan:
        plan = BudgetPlan(
            year=year,
            department_id=department_id,
            status='DRAFT',
            created_at=datetime.utcnow()
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        print(f"  ✅ Создан бюджетный план на {year} год")
    else:
        print(f"  ℹ️  Бюджетный план на {year} год уже существует (ID: {plan.id})")

    return plan

def import_warehouse_expenses(file_path: str, department_id: int):
    """
    Импорт бюджета по расходам склада
    """
    print(f"\n{'='*80}")
    print(f"ИМПОРТ БЮДЖЕТА ПО РАСХОДАМ СКЛАДА")
    print(f"{'='*80}\n")

    # Читаем подготовленный файл
    df = pd.read_excel(file_path)
    print(f"📁 Загружено {len(df)} записей из файла\n")
    print("Структура данных:")
    print(df.head().to_string())

    db = SessionLocal()
    try:
        # Получаем отдел
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            print(f"\n❌ Отдел с ID {department_id} не найден")
            print("Доступные отделы:")
            departments = db.query(Department).all()
            for dept in departments:
                print(f"  - ID {dept.id}: {dept.name}")
            return

        print(f"\n✅ Отдел: {department.name} (ID: {department_id})\n")

        # Получаем или создаем бюджетный план
        year = df['Год'].iloc[0]
        budget_plan = get_or_create_budget_plan(db, year, department_id)

        # Обрабатываем каждую запись
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            category_name = row['Категория']
            expense_type = row['Тип расходов']
            month = row['Месяц']
            amount = row['Плановая сумма']
            justification = str(row.get('Обоснование', '')) if pd.notna(row.get('Обоснование')) else ''

            # Получаем или создаем категорию
            category = get_or_create_budget_category(db, category_name, expense_type, department_id)

            # Проверяем, есть ли уже запись
            existing = db.query(BudgetPlanDetail).filter(
                BudgetPlanDetail.budget_plan_id == budget_plan.id,
                BudgetPlanDetail.category_id == category.id,
                BudgetPlanDetail.month == month
            ).first()

            if existing:
                # Обновляем существующую запись
                existing.planned_amount = amount
                existing.justification = justification
                updated_count += 1
            else:
                # Создаем новую запись
                detail = BudgetPlanDetail(
                    budget_plan_id=budget_plan.id,
                    category_id=category.id,
                    month=month,
                    planned_amount=amount,
                    actual_amount=0,
                    justification=justification,
                    department_id=department_id
                )
                db.add(detail)
                imported_count += 1

            if (idx + 1) % 50 == 0:
                db.commit()
                print(f"  ⏳ Обработано {idx + 1}/{len(df)} записей...")

        db.commit()

        print(f"\n{'='*80}")
        print(f"✅ ИМПОРТ ЗАВЕРШЕН")
        print(f"{'='*80}\n")
        print(f"📊 Статистика:")
        print(f"  - Создано новых записей: {imported_count}")
        print(f"  - Обновлено записей: {updated_count}")
        print(f"  - Пропущено: {skipped_count}")
        print(f"  - Всего обработано: {len(df)}")

    except Exception as e:
        print(f"\n❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Импорт данных склада в базу данных')
    parser.add_argument('--file', required=True, help='Путь к подготовленному Excel файлу')
    parser.add_argument('--department-id', type=int, required=True, help='ID отдела склада')
    parser.add_argument('--type', choices=['expenses', 'payroll'], default='expenses',
                        help='Тип данных для импорта')

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    if args.type == 'expenses':
        import_warehouse_expenses(str(file_path), args.department_id)
    else:
        print(f"❌ Импорт типа '{args.type}' пока не реализован")

if __name__ == "__main__":
    main()
