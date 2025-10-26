#!/usr/bin/env python3
"""
Скрипт для проверки связей всех данных с отделами
Проверяет что все записи в системе привязаны к отделам
"""

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
    os.environ.setdefault('SECRET_KEY', 'temporary-secret-key-for-verification-script')
    os.environ.setdefault('DATABASE_URL', 'postgresql://budget_user:budget_pass@localhost:5432/budget_db')
    os.environ.setdefault('CORS_ORIGINS', '["http://localhost:3000"]')

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    Department, BudgetCategory, Contractor, Organization,
    Expense, ForecastExpense, BudgetPlan, Employee,
    PayrollPlan, PayrollActual, AuditLog, User
)


def verify_entity_department_associations(db: Session, entity_class, entity_name: str):
    """Проверка связей сущности с отделами"""
    print(f"\n{'='*80}")
    print(f"Проверка: {entity_name}")
    print(f"{'='*80}")

    # Общее количество записей
    total_count = db.query(func.count(entity_class.id)).scalar()
    print(f"Всего записей: {total_count}")

    if total_count == 0:
        print("✓ Записей нет")
        return True

    # Записи с department_id
    with_dept_count = db.query(func.count(entity_class.id)).filter(
        entity_class.department_id.isnot(None)
    ).scalar()

    # Записи без department_id
    without_dept_count = db.query(func.count(entity_class.id)).filter(
        entity_class.department_id.is_(None)
    ).scalar()

    print(f"С привязкой к отделу: {with_dept_count}")
    print(f"Без привязки к отделу: {without_dept_count}")

    # Проверка наличия невалидных department_id
    invalid_dept = db.query(entity_class).filter(
        entity_class.department_id.isnot(None),
        ~db.query(Department.id).filter(Department.id == entity_class.department_id).exists()
    ).count()

    if invalid_dept > 0:
        print(f"⚠ ВНИМАНИЕ: {invalid_dept} записей с несуществующим department_id!")

    # Статистика по отделам
    if with_dept_count > 0:
        print("\nРаспределение по отделам:")
        dept_stats = db.query(
            Department.name,
            Department.code,
            func.count(entity_class.id).label('count')
        ).join(
            entity_class, entity_class.department_id == Department.id
        ).group_by(
            Department.id, Department.name, Department.code
        ).all()

        for dept_name, dept_code, count in dept_stats:
            print(f"  - {dept_name} ({dept_code}): {count} записей")

    # Результат проверки
    if without_dept_count == 0 and invalid_dept == 0:
        print(f"\n✓ ВСЕ ЗАПИСИ ПРИВЯЗАНЫ К ОТДЕЛАМ")
        return True
    else:
        print(f"\n✗ ЕСТЬ ПРОБЛЕМЫ С ПРИВЯЗКОЙ К ОТДЕЛАМ")
        return False


def main():
    """Основная функция"""
    db = SessionLocal()

    try:
        print("="*80)
        print("ПРОВЕРКА ПРИВЯЗКИ ВСЕХ ДАННЫХ К ОТДЕЛАМ")
        print("="*80)

        # Проверяем наличие отделов
        dept_count = db.query(func.count(Department.id)).scalar()
        active_dept_count = db.query(func.count(Department.id)).filter(
            Department.is_active == True
        ).scalar()

        print(f"\nОтделов в системе: {dept_count}")
        print(f"Активных отделов: {active_dept_count}")

        if dept_count == 0:
            print("\n✗ ОШИБКА: В системе нет отделов!")
            sys.exit(1)

        # Список отделов
        print("\nСписок отделов:")
        departments = db.query(Department).all()
        for dept in departments:
            status = "✓ Активен" if dept.is_active else "✗ Неактивен"
            ftp_mapping = f" | FTP: {dept.ftp_subdivision_name}" if dept.ftp_subdivision_name else ""
            print(f"  {status} - {dept.name} ({dept.code}){ftp_mapping}")

        # Проверяем все сущности с department_id
        entities_to_check = [
            (BudgetCategory, "Категории бюджета"),
            (Contractor, "Контрагенты"),
            (Organization, "Организации"),
            (Expense, "Заявки на расход"),
            (ForecastExpense, "Прогнозные расходы"),
            (BudgetPlan, "Планы бюджета"),
            (Employee, "Сотрудники"),
            (PayrollPlan, "Планы по ФОТ"),
            (PayrollActual, "Фактический ФОТ"),
        ]

        all_ok = True
        for entity_class, entity_name in entities_to_check:
            result = verify_entity_department_associations(db, entity_class, entity_name)
            all_ok = all_ok and result

        # AuditLog особый случай - department_id может быть NULL
        print(f"\n{'='*80}")
        print("Проверка: Журнал аудита (может не иметь department_id)")
        print(f"{'='*80}")
        total_audit = db.query(func.count(AuditLog.id)).scalar()
        with_dept_audit = db.query(func.count(AuditLog.id)).filter(
            AuditLog.department_id.isnot(None)
        ).scalar()
        print(f"Всего записей: {total_audit}")
        print(f"С привязкой к отделу: {with_dept_audit}")
        print(f"Без привязки к отделу: {total_audit - with_dept_audit}")
        print("ℹ Для записей аудита отдел необязателен")

        # Проверяем пользователей
        print(f"\n{'='*80}")
        print("Проверка: Пользователи")
        print(f"{'='*80}")
        total_users = db.query(func.count(User.id)).scalar()
        with_dept_users = db.query(func.count(User.id)).filter(
            User.department_id.isnot(None)
        ).scalar()
        print(f"Всего пользователей: {total_users}")
        print(f"С привязкой к отделу: {with_dept_users}")
        print(f"Без привязки к отделу: {total_users - with_dept_users}")

        if with_dept_users < total_users:
            print("\n⚠ ВНИМАНИЕ: Есть пользователи без привязки к отделу!")
            print("Они могут иметь доступ ко всем данным (роль ADMIN)")

        # Итоговый результат
        print("\n" + "="*80)
        if all_ok:
            print("✓ ВСЕ ДАННЫЕ КОРРЕКТНО ПРИВЯЗАНЫ К ОТДЕЛАМ")
            print("✓ МУЛЬТИТЕНАНТНОСТЬ НАСТРОЕНА ПРАВИЛЬНО")
        else:
            print("✗ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С ПРИВЯЗКОЙ К ОТДЕЛАМ")
            print("✗ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ДАННЫХ")
        print("="*80)

        return 0 if all_ok else 1

    except Exception as e:
        print(f"\n✗ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
