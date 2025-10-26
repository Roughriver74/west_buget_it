#!/usr/bin/env python3
"""
Скрипт для импорта данных план-факт за 2025 год из Excel файла.
Импортирует:
1. План (лист "План") -> BudgetPlan
2. Факт (лист "факт") -> Expense
3. ФОТ (лист "ВЕСТ") -> PayrollPlan
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from dotenv import load_dotenv

# Добавляем путь к проекту для импорта моделей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# Загружаем переменные окружения из backend/.env
env_path = project_root / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠️  Предупреждение: Файл .env не найден по пути {env_path}")
    print("Используем стандартные переменные окружения")
    # Устанавливаем минимально необходимые переменные
    os.environ.setdefault('DEBUG', 'False')
    os.environ.setdefault('SECRET_KEY', 'temporary-secret-key-for-import-script-only')
    os.environ.setdefault('DATABASE_URL', 'postgresql://budget_user:budget_pass@localhost:5432/budget_db')
    os.environ.setdefault('CORS_ORIGINS', '["http://localhost:3000"]')

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models import (
    Department, BudgetCategory, Expense, BudgetPlan,
    Employee, PayrollPlan, Organization, Contractor,
    ExpenseTypeEnum, ExpenseStatusEnum, BudgetStatusEnum, EmployeeStatusEnum
)


# Константы
EXCEL_FILE = project_root / "xls" / "Планфакт2025.xlsx"
YEAR = 2025
DEFAULT_DEPARTMENT_CODE = "WEST"  # Код отдела по умолчанию


# Маппинг названий месяцев
MONTH_MAPPING = {
    'январь': 1, 'янв': 1,
    'февраль': 2, 'февр': 2,
    'март': 3,
    'апрель': 4,
    'май': 5,
    'июнь': 6,
    'июль': 7,
    'август': 8, 'авг': 8,
    'сентябрь': 9, 'сент': 9,
    'октябрь': 10, 'окт': 10,
    'ноябрь': 11, 'нояб': 11,
    'декабрь': 12, 'дек': 12
}


def get_or_create_department(db: Session, code: str = DEFAULT_DEPARTMENT_CODE) -> Department:
    """Получить или создать отдел"""
    # Ищем отдел по коду
    dept = db.query(Department).filter(Department.code == code).first()

    if dept:
        print(f"✓ Найден существующий отдел: {dept.name} (код: {dept.code}, id: {dept.id})")
        return dept

    # Если отдел не найден, создаем новый
    dept = Department(
        code=code,
        name=f"Отдел {code}",
        description=f"Отдел {code} - автоматически создан при импорте",
        is_active=True
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    print(f"✓ Создан отдел: {dept.name} (код: {dept.code}, id: {dept.id})")
    return dept


def get_or_create_category(db: Session, name: str, dept_id: int,
                           category_type: ExpenseTypeEnum = ExpenseTypeEnum.OPEX) -> BudgetCategory:
    """Получить или создать категорию бюджета"""
    # Ищем категорию с таким названием в этом отделе
    category = db.query(BudgetCategory).filter(
        BudgetCategory.name == name,
        BudgetCategory.department_id == dept_id
    ).first()

    if not category:
        category = BudgetCategory(
            name=name,
            type=category_type,
            department_id=dept_id,
            is_active=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        print(f"  ✓ Создана категория: {name}")

    return category


def get_or_create_organization(db: Session, name: str, dept_id: int) -> Organization:
    """Получить или создать организацию"""
    # Сначала ищем по имени (т.к. у модели есть unique индекс на name)
    org = db.query(Organization).filter(
        Organization.name == name
    ).first()

    if org:
        # Если организация существует, но принадлежит другому отделу,
        # обновляем её отдел
        if org.department_id != dept_id:
            org.department_id = dept_id
            db.commit()
            db.refresh(org)
            print(f"  ✓ Обновлен отдел для организации: {name}")
        return org

    # Если организация не существует, создаем новую
    org = Organization(
        name=name,
        legal_name=name,
        department_id=dept_id,
        is_active=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    print(f"  ✓ Создана организация: {name}")

    return org


def get_or_create_employee(db: Session, full_name: str, dept_id: int,
                           base_salary: Decimal = Decimal('0')) -> Employee:
    """Получить или создать сотрудника"""
    employee = db.query(Employee).filter(
        Employee.full_name == full_name,
        Employee.department_id == dept_id
    ).first()

    if not employee:
        employee = Employee(
            full_name=full_name,
            position="Сотрудник",
            department_id=dept_id,
            base_salary=base_salary,
            status=EmployeeStatusEnum.ACTIVE,
            hire_date=date(YEAR, 1, 1)
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        print(f"  ✓ Создан сотрудник: {full_name}")

    return employee


def import_budget_plan(db: Session, excel_file: Path, dept: Department):
    """Импорт плановых данных бюджета из листа 'План'"""
    print("\n" + "="*80)
    print("ИМПОРТ ПЛАНОВЫХ ДАННЫХ (лист 'План')")
    print("="*80)

    # Читаем лист
    df = pd.read_excel(excel_file, sheet_name='План')

    # Удаляем существующие планы для этого отдела и года
    db.query(BudgetPlan).filter(
        BudgetPlan.department_id == dept.id,
        BudgetPlan.year == YEAR
    ).delete()
    db.commit()

    imported_count = 0

    # Обрабатываем каждую строку
    for idx, row in df.iterrows():
        category_name = row['СТАТЬЯ']

        # Пропускаем пустые строки
        if pd.isna(category_name) or str(category_name).strip() == '':
            continue

        category_name = str(category_name).strip()

        # Получаем или создаем категорию
        category = get_or_create_category(db, category_name, dept.id)

        # Обрабатываем каждый месяц
        for col_name in df.columns[1:]:  # Пропускаем первый столбец (СТАТЬЯ)
            month_name = col_name.lower()
            month = MONTH_MAPPING.get(month_name)

            if not month:
                continue

            amount = row[col_name]

            # Пропускаем пустые значения
            if pd.isna(amount) or amount == 0:
                continue

            amount = Decimal(str(amount))

            # Создаем запись плана
            budget_plan = BudgetPlan(
                year=YEAR,
                month=month,
                department_id=dept.id,
                category_id=category.id,
                planned_amount=amount,
                opex_planned=amount if category.type == ExpenseTypeEnum.OPEX else Decimal('0'),
                capex_planned=amount if category.type == ExpenseTypeEnum.CAPEX else Decimal('0'),
                status=BudgetStatusEnum.APPROVED
            )
            db.add(budget_plan)
            imported_count += 1

    db.commit()
    print(f"\n✓ Импортировано {imported_count} записей плана бюджета")


def import_expenses(db: Session, excel_file: Path, dept: Department):
    """Импорт фактических расходов из листа 'факт'"""
    print("\n" + "="*80)
    print("ИМПОРТ ФАКТИЧЕСКИХ РАСХОДОВ (лист 'факт')")
    print("="*80)

    # Читаем лист
    df = pd.read_excel(excel_file, sheet_name='факт')

    # Получаем или создаем организацию по умолчанию
    org = get_or_create_organization(db, "ВЕСТ ООО", dept.id)

    imported_count = 0

    # Обрабатываем каждую строку
    for idx, row in df.iterrows():
        category_name = row['СТАТЬЯ']

        # Пропускаем пустые строки
        if pd.isna(category_name) or str(category_name).strip() == '':
            continue

        category_name = str(category_name).strip()

        # Получаем или создаем категорию
        category = get_or_create_category(db, category_name, dept.id)

        # Обрабатываем каждый месяц
        for col_name in df.columns[1:]:  # Пропускаем первый столбец (СТАТЬЯ)
            month_name = col_name.lower()
            month = MONTH_MAPPING.get(month_name)

            if not month:
                continue

            amount = row[col_name]

            # Пропускаем пустые значения
            if pd.isna(amount) or amount == 0:
                continue

            amount = Decimal(str(amount))

            # Создаем запись расхода
            # Генерируем уникальный номер
            expense_number = f"IMP-{YEAR}-{month:02d}-{category.id}-{idx}"

            # Проверяем, не существует ли уже такая запись
            existing = db.query(Expense).filter(
                Expense.number == expense_number,
                Expense.department_id == dept.id
            ).first()

            if existing:
                continue

            expense = Expense(
                number=expense_number,
                department_id=dept.id,
                category_id=category.id,
                organization_id=org.id,
                amount=amount,
                request_date=datetime(YEAR, month, 15),  # Середина месяца
                payment_date=datetime(YEAR, month, 20),  # Конец месяца
                status=ExpenseStatusEnum.PAID,
                is_paid=True,
                is_closed=True,
                comment=f"Импортировано из файла Планфакт2025.xlsx (лист 'факт')"
            )
            db.add(expense)
            imported_count += 1

    db.commit()
    print(f"\n✓ Импортировано {imported_count} записей расходов")


def import_payroll(db: Session, excel_file: Path, dept: Department):
    """Импорт ФОТ из листа 'ВЕСТ'"""
    print("\n" + "="*80)
    print("ИМПОРТ ФОТ (лист 'ВЕСТ')")
    print("="*80)

    # Читаем лист
    df = pd.read_excel(excel_file, sheet_name='ВЕСТ')

    # Удаляем существующие планы ФОТ для этого отдела и года
    db.query(PayrollPlan).filter(
        PayrollPlan.department_id == dept.id,
        PayrollPlan.year == YEAR
    ).delete()
    db.commit()

    imported_count = 0

    # Обрабатываем каждую строку (сотрудника)
    for idx, row in df.iterrows():
        full_name = row['ФИО']

        # Пропускаем пустые строки
        if pd.isna(full_name) or str(full_name).strip() == '':
            continue

        full_name = str(full_name).strip()

        # Обрабатываем каждый месяц
        for col_name in df.columns[1:]:  # Пропускаем первый столбец (ФИО)
            month_name = col_name.lower()
            month = MONTH_MAPPING.get(month_name)

            if not month:
                continue

            salary = row[col_name]

            # Пропускаем пустые значения
            if pd.isna(salary):
                salary = 0

            salary = Decimal(str(salary))

            # Получаем или создаем сотрудника
            employee = get_or_create_employee(db, full_name, dept.id, salary)

            # Создаем запись плана ФОТ
            payroll_plan = PayrollPlan(
                year=YEAR,
                month=month,
                employee_id=employee.id,
                department_id=dept.id,
                base_salary=salary,
                bonus=Decimal('0'),
                other_payments=Decimal('0'),
                total_planned=salary
            )
            db.add(payroll_plan)
            imported_count += 1

    db.commit()
    print(f"\n✓ Импортировано {imported_count} записей ФОТ")


def main():
    """Основная функция"""
    print("="*80)
    print(f"ИМПОРТ ДАННЫХ ИЗ {EXCEL_FILE.name}")
    print("="*80)

    # Проверяем наличие файла
    if not EXCEL_FILE.exists():
        print(f"✗ Ошибка: Файл {EXCEL_FILE} не найден!")
        sys.exit(1)

    # Создаем сессию БД
    db = SessionLocal()

    try:
        # Получаем или создаем отдел
        dept = get_or_create_department(db, DEFAULT_DEPARTMENT_CODE)

        # Импортируем данные
        import_budget_plan(db, EXCEL_FILE, dept)
        import_expenses(db, EXCEL_FILE, dept)
        import_payroll(db, EXCEL_FILE, dept)

        print("\n" + "="*80)
        print("✓ ИМПОРТ ЗАВЕРШЕН УСПЕШНО!")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
