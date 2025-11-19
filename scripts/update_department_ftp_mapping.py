#!/usr/bin/env python3
"""
Скрипт для обновления сопоставления подразделения FTP для отдела ACME
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
    os.environ.setdefault('SECRET_KEY', 'temporary-secret-key-for-import-script-only')
    os.environ.setdefault('DATABASE_URL', 'postgresql://budget_user:budget_pass@localhost:5432/budget_db')
    os.environ.setdefault('CORS_ORIGINS', '["http://localhost:3000"]')

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department


def main():
    """Основная функция"""
    db = SessionLocal()

    try:
        print("="*80)
        print("ОБНОВЛЕНИЕ СОПОСТАВЛЕНИЯ FTP ДЛЯ ОТДЕЛА ACME")
        print("="*80)

        # Найдем отдел ACME
        department = db.query(Department).filter(
            Department.code == "ACME"
        ).first()

        if not department:
            print("✗ Ошибка: Отдел с кодом ACME не найден!")
            sys.exit(1)

        print(f"\n✓ Найден отдел:")
        print(f"  ID: {department.id}")
        print(f"  Название: {department.name}")
        print(f"  Код: {department.code}")
        print(f"  Текущее FTP сопоставление: {department.ftp_subdivision_name or 'не указано'}")

        # Обновляем поле ftp_subdivision_name
        new_subdivision_name = "(ДЕМО) IT"
        department.ftp_subdivision_name = new_subdivision_name

        db.commit()
        db.refresh(department)

        print(f"\n✓ Обновлено!")
        print(f"  Новое FTP сопоставление: {department.ftp_subdivision_name}")

        print("\n" + "="*80)
        print("✓ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("="*80)
        print("\nТеперь при импорте из FTP заявки с подразделением '(ДЕМО) IT'")
        print("будут автоматически привязываться к отделу ACME")

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
