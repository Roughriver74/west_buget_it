#!/usr/bin/env python3
"""
Скрипт для очистки расходов за июль-декабрь 2025 и привязки всех заявок к IT отделу
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

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
from sqlalchemy import and_, extract
from app.db.session import SessionLocal
from app.db.models import Expense, Department


def main():
    """Основная функция"""
    db = SessionLocal()

    try:
        print("="*80)
        print("ОЧИСТКА РАСХОДОВ ЗА ИЮЛЬ-ДЕКАБРЬ 2025 И ПРИВЯЗКА К IT ОТДЕЛУ")
        print("="*80)

        # Найдем IT отдел
        it_department = db.query(Department).filter(
            Department.code == "WEST"
        ).first()

        if not it_department:
            print("✗ Ошибка: IT отдел (код WEST) не найден!")
            sys.exit(1)

        print(f"\n✓ Найден отдел: {it_department.name} (ID: {it_department.id}, код: {it_department.code})")

        # 1. Удаляем расходы за июль-декабрь 2025
        print("\n" + "="*80)
        print("ШАГ 1: Удаление расходов за июль-декабрь 2025")
        print("="*80)

        # Подсчитаем сколько будет удалено
        expenses_to_delete = db.query(Expense).filter(
            and_(
                extract('year', Expense.request_date) == 2025,
                extract('month', Expense.request_date) >= 7  # Июль и позже
            )
        ).all()

        if expenses_to_delete:
            print(f"\nНайдено расходов для удаления: {len(expenses_to_delete)}")

            # Показываем разбивку по месяцам
            months = {}
            for exp in expenses_to_delete:
                month = exp.request_date.month
                months[month] = months.get(month, 0) + 1

            month_names = {
                7: 'Июль', 8: 'Август', 9: 'Сентябрь',
                10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
            }

            print("\nРазбивка по месяцам:")
            for month in sorted(months.keys()):
                print(f"  {month_names.get(month, f'Месяц {month}')}: {months[month]} расходов")

            # Удаляем
            deleted_count = db.query(Expense).filter(
                and_(
                    extract('year', Expense.request_date) == 2025,
                    extract('month', Expense.request_date) >= 7
                )
            ).delete(synchronize_session=False)

            db.commit()
            print(f"\n✓ Удалено расходов: {deleted_count}")
        else:
            print("\nРасходы для удаления не найдены")

        # 2. Привязываем все заявки к IT отделу
        print("\n" + "="*80)
        print("ШАГ 2: Привязка всех заявок к IT отделу")
        print("="*80)

        # Подсчитаем сколько заявок будет обновлено
        expenses_to_update = db.query(Expense).filter(
            Expense.department_id != it_department.id
        ).all()

        if expenses_to_update:
            print(f"\nНайдено заявок для обновления: {len(expenses_to_update)}")

            # Обновляем
            updated_count = db.query(Expense).filter(
                Expense.department_id != it_department.id
            ).update(
                {Expense.department_id: it_department.id},
                synchronize_session=False
            )

            db.commit()
            print(f"✓ Обновлено заявок: {updated_count}")
        else:
            print("\nВсе заявки уже привязаны к IT отделу")

        # 3. Статистика после операций
        print("\n" + "="*80)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("="*80)

        total_expenses = db.query(Expense).count()
        it_expenses = db.query(Expense).filter(
            Expense.department_id == it_department.id
        ).count()

        print(f"\nВсего заявок в системе: {total_expenses}")
        print(f"Заявок в IT отделе: {it_expenses}")
        print(f"Заявок в других отделах: {total_expenses - it_expenses}")

        # Проверяем оставшиеся расходы за 2025
        expenses_2025 = db.query(Expense).filter(
            extract('year', Expense.request_date) == 2025
        ).count()
        print(f"\nВсего расходов за 2025 год: {expenses_2025}")

        # Разбивка по месяцам
        print("\nРасходы за 2025 год по месяцам:")
        for month in range(1, 13):
            count = db.query(Expense).filter(
                and_(
                    extract('year', Expense.request_date) == 2025,
                    extract('month', Expense.request_date) == month
                )
            ).count()
            month_names_full = [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]
            print(f"  {month_names_full[month-1]:12s}: {count:4d} расходов")

        print("\n" + "="*80)
        print("✓ ОПЕРАЦИИ ЗАВЕРШЕНЫ УСПЕШНО!")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
