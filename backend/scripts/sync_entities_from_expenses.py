"""
Скрипт для синхронизации контрагентов и организаций из заявок в справочники
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import Expense, Contractor, Organization

# Создаем подключение к БД
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def sync_contractors():
    """Синхронизация контрагентов из заявок"""
    db = SessionLocal()

    try:
        # Получаем все уникальные названия контрагентов из заявок
        expenses = db.query(Expense).filter(
            Expense.contractor_name.isnot(None),
            Expense.contractor_name != ''
        ).all()

        # Группируем по названию
        contractor_names = {}
        for expense in expenses:
            name = expense.contractor_name.strip()
            if name and name not in contractor_names:
                contractor_names[name] = expense

        print(f"Найдено уникальных контрагентов в заявках: {len(contractor_names)}")

        created_count = 0
        skipped_count = 0

        for name, sample_expense in contractor_names.items():
            # Проверяем, существует ли контрагент
            existing = db.query(Contractor).filter(Contractor.name == name).first()

            if not existing:
                # Создаем нового контрагента
                contractor = Contractor(
                    name=name,
                    inn=sample_expense.contractor_inn,
                    description=f"Автоматически создан из заявок",
                    is_active=True
                )
                db.add(contractor)
                created_count += 1
                print(f"  + Создан контрагент: {name}")
            else:
                skipped_count += 1

        db.commit()
        print(f"\nСоздано контрагентов: {created_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")

        # Связываем заявки с контрагентами
        link_expenses_to_contractors(db)

    except Exception as e:
        print(f"Ошибка при синхронизации контрагентов: {e}")
        db.rollback()
    finally:
        db.close()


def sync_organizations():
    """Синхронизация организаций из заявок"""
    db = SessionLocal()

    try:
        # Получаем все уникальные названия организаций из заявок
        expenses = db.query(Expense).filter(
            Expense.organization_name.isnot(None),
            Expense.organization_name != ''
        ).all()

        # Группируем по названию
        org_names = {}
        for expense in expenses:
            name = expense.organization_name.strip()
            if name and name not in org_names:
                org_names[name] = expense

        print(f"\nНайдено уникальных организаций в заявках: {len(org_names)}")

        created_count = 0
        skipped_count = 0

        for name, sample_expense in org_names.items():
            # Проверяем, существует ли организация
            existing = db.query(Organization).filter(Organization.name == name).first()

            if not existing:
                # Создаем новую организацию
                organization = Organization(
                    name=name,
                    description=f"Автоматически создана из заявок",
                    is_active=True
                )
                db.add(organization)
                created_count += 1
                print(f"  + Создана организация: {name}")
            else:
                skipped_count += 1

        db.commit()
        print(f"\nСоздано организаций: {created_count}")
        print(f"Пропущено (уже существуют): {skipped_count}")

        # Связываем заявки с организациями
        link_expenses_to_organizations(db)

    except Exception as e:
        print(f"Ошибка при синхронизации организаций: {e}")
        db.rollback()
    finally:
        db.close()


def link_expenses_to_contractors(db):
    """Связываем заявки с ID контрагентов"""
    print("\nСвязывание заявок с контрагентами...")

    expenses = db.query(Expense).filter(
        Expense.contractor_id.is_(None),
        Expense.contractor_name.isnot(None)
    ).all()

    linked_count = 0

    for expense in expenses:
        contractor = db.query(Contractor).filter(
            Contractor.name == expense.contractor_name.strip()
        ).first()

        if contractor:
            expense.contractor_id = contractor.id
            linked_count += 1

    db.commit()
    print(f"Связано заявок с контрагентами: {linked_count}")


def link_expenses_to_organizations(db):
    """Связываем заявки с ID организаций"""
    print("\nСвязывание заявок с организациями...")

    expenses = db.query(Expense).filter(
        Expense.organization_id.is_(None),
        Expense.organization_name.isnot(None)
    ).all()

    linked_count = 0

    for expense in expenses:
        organization = db.query(Organization).filter(
            Organization.name == expense.organization_name.strip()
        ).first()

        if organization:
            expense.organization_id = organization.id
            linked_count += 1

    db.commit()
    print(f"Связано заявок с организациями: {linked_count}")


if __name__ == "__main__":
    print("=" * 60)
    print("Синхронизация контрагентов и организаций из заявок")
    print("=" * 60)

    sync_contractors()
    sync_organizations()

    print("\n" + "=" * 60)
    print("Синхронизация завершена!")
    print("=" * 60)
