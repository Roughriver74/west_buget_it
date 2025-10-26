#!/usr/bin/env python3
"""
Скрипт для проверки сопоставления FTP
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
        print("ПРОВЕРКА СОПОСТАВЛЕНИЯ FTP")
        print("="*80)

        # Получаем все активные отделы
        departments = db.query(Department).filter(
            Department.is_active == True
        ).all()

        print(f"\nНайдено активных отделов: {len(departments)}\n")

        for dept in departments:
            print(f"Отдел: {dept.name} (код: {dept.code})")
            print(f"  ID: {dept.id}")
            print(f"  FTP Подразделение: {dept.ftp_subdivision_name or 'не указано'}")
            print()

        # Проверяем конкретное сопоставление для "(ВЕСТ) IT"
        print("="*80)
        print("ПОИСК ОТДЕЛА ПО FTP ПОДРАЗДЕЛЕНИЮ '(ВЕСТ) IT'")
        print("="*80)

        subdivision_name = "(ВЕСТ) IT"

        # Точное совпадение
        dept = db.query(Department).filter(
            Department.ftp_subdivision_name == subdivision_name,
            Department.is_active == True
        ).first()

        if dept:
            print(f"\n✓ Найден отдел по точному совпадению:")
            print(f"  Название: {dept.name}")
            print(f"  Код: {dept.code}")
            print(f"  ID: {dept.id}")
            print(f"  FTP Подразделение: {dept.ftp_subdivision_name}")
        else:
            print(f"\n✗ Отдел не найден для подразделения '{subdivision_name}'")

        print("\n" + "="*80)
        print("✓ ПРОВЕРКА ЗАВЕРШЕНА")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
