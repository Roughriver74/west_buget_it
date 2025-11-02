#!/usr/bin/env python3
"""
Скрипт для импорта бюджетных планов в систему планирования (BudgetVersion + BudgetPlanDetail)
Импортирует данные из Excel файла в формате:
- Категория | Тип | Январь | Февраль | ... | Декабрь | Обоснование

Использование:
    python scripts/import_budget_version.py <file.xlsx> --year 2026 --department-id 1 --version-name "План v1"
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import argparse

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import (
    BudgetCategory,
    BudgetVersion,
    BudgetPlanDetail,
    BudgetScenario,
    BudgetVersionStatusEnum,
    BudgetScenarioTypeEnum,
    ExpenseTypeEnum,
    CalculationMethodEnum,
)


MONTH_COLUMNS = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]


def get_or_create_scenario(
    db: Session,
    year: int,
    department_id: int,
    scenario_name: str = None
) -> BudgetScenario:
    """Получить или создать базовый сценарий"""
    scenario = db.query(BudgetScenario).filter(
        BudgetScenario.year == year,
        BudgetScenario.department_id == department_id,
        BudgetScenario.scenario_type == BudgetScenarioTypeEnum.BASE
    ).first()

    if not scenario:
        scenario = BudgetScenario(
            year=year,
            scenario_name=scenario_name or f"Базовый сценарий {year}",
            scenario_type=BudgetScenarioTypeEnum.BASE,
            department_id=department_id,
            description=f"Автоматически создан при импорте",
            is_active=True,
            created_by="import_script"
        )
        db.add(scenario)
        db.flush()
        print(f"✓ Создан сценарий: {scenario.scenario_name}")

    return scenario


def create_budget_version(
    db: Session,
    year: int,
    department_id: int,
    version_name: str,
    scenario_id: int = None
) -> BudgetVersion:
    """Создать новую версию бюджета"""
    # Получаем следующий номер версии
    max_version = db.query(BudgetVersion).filter(
        BudgetVersion.year == year,
        BudgetVersion.department_id == department_id
    ).count()

    version = BudgetVersion(
        year=year,
        version_number=max_version + 1,
        version_name=version_name,
        department_id=department_id,
        scenario_id=scenario_id,
        status=BudgetVersionStatusEnum.DRAFT,
        created_by="import_script",
        total_amount=Decimal("0"),
        total_capex=Decimal("0"),
        total_opex=Decimal("0")
    )
    db.add(version)
    db.flush()
    print(f"✓ Создана версия: {version.version_name} (v{version.version_number})")

    return version


def get_categories(db: Session, department_id: int) -> dict:
    """Получить все активные категории для отдела"""
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.department_id == department_id,
        BudgetCategory.is_active == True
    ).all()

    return {cat.name: cat for cat in categories}


def recalculate_version_totals(db: Session, version: BudgetVersion) -> None:
    """Пересчитать итоговые суммы версии"""
    from sqlalchemy import func, select

    # Subquery для определения родительских категорий
    parent_categories_subq = (
        select(BudgetCategory.parent_id)
        .where(BudgetCategory.parent_id.isnot(None))
        .distinct()
        .subquery()
    )

    # Суммируем только листовые категории
    totals = (
        db.query(
            func.coalesce(func.sum(BudgetPlanDetail.planned_amount), 0).label("amount"),
            BudgetPlanDetail.type,
        )
        .join(BudgetCategory, BudgetPlanDetail.category_id == BudgetCategory.id)
        .filter(
            BudgetPlanDetail.version_id == version.id,
            ~BudgetCategory.id.in_(parent_categories_subq)
        )
        .group_by(BudgetPlanDetail.type)
        .all()
    )

    total_amount = Decimal("0")
    total_capex = Decimal("0")
    total_opex = Decimal("0")

    for amount, detail_type in totals:
        amount = Decimal(amount)
        total_amount += amount
        if detail_type == ExpenseTypeEnum.CAPEX:
            total_capex += amount
        else:
            total_opex += amount

    version.total_amount = total_amount
    version.total_capex = total_capex
    version.total_opex = total_opex
    db.flush()


def import_from_excel(
    db: Session,
    excel_file: str,
    year: int,
    department_id: int,
    version_name: str,
    scenario_name: str = None
) -> BudgetVersion:
    """Импорт данных из Excel в систему планирования"""
    print(f"\n{'='*80}")
    print(f"ИМПОРТ БЮДЖЕТНОГО ПЛАНА")
    print(f"{'='*80}\n")
    print(f"Файл: {excel_file}")
    print(f"Год: {year}")
    print(f"Отдел ID: {department_id}")
    print(f"Название версии: {version_name}\n")

    # Читаем Excel
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return None

    # Проверяем наличие обязательных колонок
    required_columns = ['Категория', 'Тип']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
        print(f"Доступные колонки: {', '.join(df.columns)}")
        return None

    # Получаем или создаем сценарий
    scenario = get_or_create_scenario(db, year, department_id, scenario_name)

    # Создаем новую версию
    version = create_budget_version(db, year, department_id, version_name, scenario.id)

    # Получаем категории
    categories = get_categories(db, department_id)
    if not categories:
        print(f"❌ Нет активных категорий для отдела {department_id}")
        return None

    print(f"✓ Найдено категорий: {len(categories)}\n")

    # Импортируем данные
    created_count = 0
    errors = []

    for index, row in df.iterrows():
        try:
            category_name = str(row['Категория']).strip()
            type_val = str(row['Тип']).strip().upper()

            if not category_name or category_name == 'nan':
                continue

            if type_val not in ['OPEX', 'CAPEX']:
                errors.append(f"Строка {index + 2}: Тип должен быть OPEX или CAPEX, найдено: {type_val}")
                continue

            # Находим категорию
            category = categories.get(category_name)
            if not category:
                errors.append(f"Строка {index + 2}: Категория '{category_name}' не найдена")
                continue

            # Получаем обоснование если есть
            justification = None
            if 'Обоснование' in df.columns:
                just_val = row.get('Обоснование')
                if pd.notna(just_val):
                    justification = str(just_val).strip()

            # Импортируем данные по месяцам
            for month_idx, month_name in enumerate(MONTH_COLUMNS, start=1):
                if month_name not in df.columns:
                    continue

                amount_val = row.get(month_name)
                if pd.isna(amount_val):
                    amount = Decimal("0")
                else:
                    try:
                        amount = Decimal(str(amount_val))
                    except:
                        errors.append(f"Строка {index + 2}, {month_name}: Неверный формат суммы")
                        continue

                # Создаем запись
                detail = BudgetPlanDetail(
                    version_id=version.id,
                    month=month_idx,
                    category_id=category.id,
                    planned_amount=amount,
                    type=type_val,
                    justification=justification,
                    calculation_method=CalculationMethodEnum.MANUAL
                )
                db.add(detail)
                created_count += 1

        except Exception as e:
            errors.append(f"Строка {index + 2}: {str(e)}")

    # Сохраняем изменения
    db.commit()

    # Пересчитываем итоги
    recalculate_version_totals(db, version)
    db.commit()

    # Выводим результаты
    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТЫ ИМПОРТА")
    print(f"{'='*80}\n")
    print(f"✓ Создано записей: {created_count}")
    print(f"✓ Итого сумма: {version.total_amount:,.2f} ₽")
    print(f"  - CAPEX: {version.total_capex:,.2f} ₽")
    print(f"  - OPEX: {version.total_opex:,.2f} ₽")
    print(f"✓ Версия ID: {version.id}")

    if errors:
        print(f"\n⚠️  Ошибок: {len(errors)}")
        for error in errors[:10]:  # Показываем первые 10 ошибок
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... и еще {len(errors) - 10} ошибок")

    print()
    return version


def main():
    parser = argparse.ArgumentParser(
        description='Импорт бюджетного плана из Excel в систему планирования'
    )
    parser.add_argument('file', help='Путь к Excel файлу')
    parser.add_argument('--year', type=int, required=True, help='Год планирования')
    parser.add_argument('--department-id', type=int, required=True, help='ID отдела')
    parser.add_argument('--version-name', required=True, help='Название версии')
    parser.add_argument('--scenario-name', help='Название сценария (опционально)')

    args = parser.parse_args()

    # Проверяем существование файла
    if not os.path.exists(args.file):
        print(f"❌ Файл не найден: {args.file}")
        sys.exit(1)

    # Создаем сессию БД
    db = SessionLocal()

    try:
        version = import_from_excel(
            db=db,
            excel_file=args.file,
            year=args.year,
            department_id=args.department_id,
            version_name=args.version_name,
            scenario_name=args.scenario_name
        )

        if version:
            print(f"\n✓ Импорт завершен успешно!")
            print(f"  Версия ID: {version.id}")
            print(f"  Статус: {version.status.value}")
        else:
            print(f"\n❌ Импорт не удался")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
