#!/usr/bin/env python3
"""
Setup Modules for Development - Быстрая настройка модулей для разработки

Этот скрипт автоматически:
1. Применяет миграции БД
2. Загружает модули в БД
3. Включает ВСЕ модули для ВСЕХ организаций (только для dev!)
4. Показывает результат

Использование:
    python scripts/setup_modules_dev.py

Или с параметрами:
    python scripts/setup_modules_dev.py --org-id 1  # Только для организации 1
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import subprocess
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Module, OrganizationModule, Organization
from app.core.config import settings


def run_command(cmd: str, description: str):
    """Run shell command and show result"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=backend_path
        )
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} - УСПЕШНО")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stdout:
            print(f"Вывод: {e.stdout}")
        if e.stderr:
            print(f"Ошибки: {e.stderr}")
        return False


def setup_modules(db: Session, organization_id: int = None):
    """
    Setup modules for development

    Args:
        db: Database session
        organization_id: Optional - setup for specific org only
    """

    print("\n" + "="*60)
    print("🎯 НАСТРОЙКА МОДУЛЕЙ ДЛЯ РАЗРАБОТКИ")
    print("="*60)

    # Step 1: Check if modules exist
    modules = db.query(Module).all()

    if not modules:
        print("\n⚠️  Модули не найдены в БД!")
        print("Запускаем seed_modules.py...")

        # Run seed_modules.py
        success = run_command(
            "python scripts/seed_modules.py",
            "Загрузка модулей в БД"
        )

        if not success:
            print("\n❌ Не удалось загрузить модули. Проверьте ошибки выше.")
            return False

        # Reload modules
        modules = db.query(Module).all()

    print(f"\n✅ Найдено {len(modules)} модулей в БД:")
    for m in modules:
        print(f"   - {m.code}: {m.name}")

    # Step 2: Get organizations
    if organization_id:
        organizations = db.query(Organization).filter_by(id=organization_id).all()
        if not organizations:
            print(f"\n❌ Организация с ID {organization_id} не найдена!")
            return False
    else:
        organizations = db.query(Organization).all()

    if not organizations:
        print("\n❌ Организации не найдены в БД!")
        print("Создайте хотя бы одну организацию для продолжения.")
        return False

    print(f"\n✅ Найдено {len(organizations)} организаций:")
    for org in organizations:
        print(f"   - ID {org.id}: {org.short_name}")

    # Step 3: Enable all modules for all organizations
    print("\n" + "="*60)
    print("🔓 ВКЛЮЧЕНИЕ МОДУЛЕЙ")
    print("="*60)

    enabled_count = 0
    already_enabled_count = 0

    # Set expiration date far in the future for dev
    expires_at = datetime.utcnow() + timedelta(days=3650)  # 10 years

    for org in organizations:
        print(f"\n📦 Организация: {org.short_name} (ID: {org.id})")

        for module in modules:
            # Check if already enabled
            existing = db.query(OrganizationModule).filter_by(
                organization_id=org.id,
                module_id=module.id
            ).first()

            if existing:
                if existing.is_active:
                    print(f"   ✓ {module.code} - уже включен")
                    already_enabled_count += 1
                else:
                    # Reactivate
                    existing.is_active = True
                    existing.enabled_at = datetime.utcnow()
                    existing.expires_at = expires_at
                    db.commit()
                    print(f"   🔄 {module.code} - переактивирован")
                    enabled_count += 1
            else:
                # Create new
                org_module = OrganizationModule(
                    organization_id=org.id,
                    module_id=module.id,
                    is_active=True,
                    enabled_at=datetime.utcnow(),
                    expires_at=expires_at,
                    limits={}
                )
                db.add(org_module)
                db.commit()
                print(f"   ✅ {module.code} - включен")
                enabled_count += 1

    # Summary
    print("\n" + "="*60)
    print("📊 ИТОГИ")
    print("="*60)
    print(f"✅ Включено новых модулей: {enabled_count}")
    print(f"✓  Уже было включено: {already_enabled_count}")
    print(f"📦 Всего организаций: {len(organizations)}")
    print(f"🎛️  Всего модулей: {len(modules)}")

    # Show what's enabled per organization
    print("\n" + "="*60)
    print("📋 ВКЛЮЧЕННЫЕ МОДУЛИ ПО ОРГАНИЗАЦИЯМ")
    print("="*60)

    for org in organizations:
        enabled_modules = db.query(OrganizationModule).join(Module).filter(
            OrganizationModule.organization_id == org.id,
            OrganizationModule.is_active == True
        ).all()

        print(f"\n🏢 {org.short_name} (ID: {org.id}):")
        for om in enabled_modules:
            module = db.query(Module).get(om.module_id)
            expires = om.expires_at.strftime("%Y-%m-%d") if om.expires_at else "Бессрочно"
            print(f"   ✅ {module.code}: {module.name}")
            print(f"      Истекает: {expires}")

    print("\n" + "="*60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("="*60)
    print("\nТеперь можно:")
    print("1. Перезапустить backend: uvicorn app.main:app --reload")
    print("2. Перезапустить frontend: npm run dev")
    print("3. Обновить страницу в браузере (Ctrl+Shift+R)")
    print("\nВсе модули должны быть видны в меню!")

    return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup modules for development - включить все модули для всех организаций"
    )
    parser.add_argument(
        "--org-id",
        type=int,
        help="ID организации (если не указан - включит для всех)"
    )
    parser.add_argument(
        "--apply-migrations",
        action="store_true",
        help="Применить миграции перед setup"
    )

    args = parser.parse_args()

    # Step 0: Apply migrations if requested
    if args.apply_migrations:
        success = run_command(
            "alembic upgrade head",
            "Применение миграций БД"
        )
        if not success:
            print("\n❌ Не удалось применить миграции. Проверьте ошибки выше.")
            return

    # Setup modules
    db = SessionLocal()
    try:
        success = setup_modules(db, args.org_id)
        if success:
            print("\n✅ Успех! Модули настроены.")
        else:
            print("\n❌ Произошла ошибка при настройке.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
