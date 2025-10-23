#!/usr/bin/env python3
"""Initialize database with seed data"""

import sys
sys.path.insert(0, '/home/user/west_buget_it/backend')

from datetime import datetime
from app.db.session import SessionLocal, engine
from app.db.models import BudgetCategory, Organization, Base

def seed_database():
    """Seed database with initial data"""

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_categories = db.query(BudgetCategory).count()
        if existing_categories > 0:
            print(f"Database already has {existing_categories} categories. Skipping seed.")
            return

        # Add categories
        categories = [
            BudgetCategory(
                name="Аутсорс",
                type="OPEX",
                description="Услуги внешних специалистов и компаний",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Лицензии",
                type="OPEX",
                description="Программное обеспечение и лицензии",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Оборудование",
                type="CAPEX",
                description="Компьютеры, серверы и другое оборудование",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Облачные сервисы",
                type="OPEX",
                description="AWS, Azure, Google Cloud и другие облачные платформы",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Обучение",
                type="OPEX",
                description="Курсы и обучение сотрудников",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="ЗП IT персонала",
                type="OPEX",
                description="Заработная плата IT специалистов",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Серверы",
                type="CAPEX",
                description="Физические серверы",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Сетевое оборудование",
                type="CAPEX",
                description="Коммутаторы, маршрутизаторы, точки доступа",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Хостинг",
                type="OPEX",
                description="Хостинг веб-сайтов и приложений",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            BudgetCategory(
                name="Прочее",
                type="OPEX",
                description="Другие расходы",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
        ]

        db.add_all(categories)
        db.flush()

        print(f"✅ Added {len(categories)} categories")

        # Add organizations
        organizations = [
            Organization(
                name="ВЕСТ ООО",
                legal_name="Общество с ограниченной ответственностью ВЕСТ",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Organization(
                name="ВЕСТ ГРУПП ООО",
                legal_name="Общество с ограниченной ответственностью ВЕСТ ГРУПП",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
        ]

        db.add_all(organizations)
        db.commit()

        print(f"✅ Added {len(organizations)} organizations")
        print("\n✅ Database seeded successfully!")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
