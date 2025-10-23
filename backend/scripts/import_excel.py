"""
Script to import data from Excel files into the database
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, Base
from app.db.models import (
    BudgetCategory,
    Contractor,
    Organization,
    Expense,
    BudgetPlan,
    ExpenseTypeEnum,
    ExpenseStatusEnum,
)


def create_tables():
    """Create all tables"""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def import_categories(db: Session):
    """Import budget categories"""
    print("\nImporting categories...")

    categories_data = [
        {"name": "Аутсорс", "type": ExpenseTypeEnum.OPEX, "description": "Аутсорсинг услуг"},
        {"name": "Техника", "type": ExpenseTypeEnum.CAPEX, "description": "Оборудование и техника"},
        {"name": "Покупка ПО", "type": ExpenseTypeEnum.OPEX, "description": "Покупка программного обеспечения"},
        {"name": "Интернет", "type": ExpenseTypeEnum.OPEX, "description": "Интернет и связь"},
        {"name": "Лицензии и ПО", "type": ExpenseTypeEnum.OPEX, "description": "Лицензии и программное обеспечение"},
        {"name": "Обслуживание", "type": ExpenseTypeEnum.OPEX, "description": "Обслуживание техники"},
        {"name": "Оборудование", "type": ExpenseTypeEnum.CAPEX, "description": "Оборудование и инфраструктура"},
    ]

    for cat_data in categories_data:
        existing = db.query(BudgetCategory).filter(BudgetCategory.name == cat_data["name"]).first()
        if not existing:
            category = BudgetCategory(**cat_data)
            db.add(category)
            print(f"  Added category: {cat_data['name']}")

    db.commit()
    print("Categories imported successfully!")


def import_organizations(db: Session):
    """Import organizations"""
    print("\nImporting organizations...")

    orgs_data = [
        {"name": "ВЕСТ ООО", "legal_name": "Общество с ограниченной ответственностью ВЕСТ"},
        {"name": "ВЕСТ ГРУПП ООО", "legal_name": "Общество с ограниченной ответственностью ВЕСТ ГРУПП"},
    ]

    for org_data in orgs_data:
        existing = db.query(Organization).filter(Organization.name == org_data["name"]).first()
        if not existing:
            organization = Organization(**org_data)
            db.add(organization)
            print(f"  Added organization: {org_data['name']}")

    db.commit()
    print("Organizations imported successfully!")


def import_expenses_from_excel(db: Session, file_path: str):
    """Import expenses from Excel file"""
    print(f"\nImporting expenses from {file_path}...")

    try:
        df = pd.read_excel(file_path)
        print(f"  Found {len(df)} rows in Excel")

        # Get category mapping
        categories = {cat.name: cat.id for cat in db.query(BudgetCategory).all()}

        # Get organization mapping
        organizations = {org.name: org.id for org in db.query(Organization).all()}

        # Status mapping
        status_mapping = {
            "Оплачена": ExpenseStatusEnum.PAID,
            "К оплате": ExpenseStatusEnum.PENDING,
            "Отклонена": ExpenseStatusEnum.REJECTED,
            "Закрыта": ExpenseStatusEnum.CLOSED,
        }

        imported = 0
        skipped = 0

        for idx, row in df.iterrows():
            try:
                # Check if expense already exists
                number = str(row.get("Номер", ""))
                if not number or number == "nan":
                    skipped += 1
                    continue

                existing = db.query(Expense).filter(Expense.number == number).first()
                if existing:
                    skipped += 1
                    continue

                # Get category
                category_name = str(row.get("Статья ДДС", ""))
                category_id = categories.get(category_name)
                if not category_id:
                    # Try to find or create category
                    print(f"  Warning: Category '{category_name}' not found, creating...")
                    new_cat = BudgetCategory(
                        name=category_name,
                        type=ExpenseTypeEnum.OPEX,
                        description=f"Auto-imported: {category_name}"
                    )
                    db.add(new_cat)
                    db.flush()
                    category_id = new_cat.id
                    categories[category_name] = category_id

                # Get organization
                org_name = str(row.get("Организация", ""))
                organization_id = organizations.get(org_name)
                if not organization_id:
                    # Use first organization as default
                    organization_id = list(organizations.values())[0]

                # Get or create contractor
                contractor_name = str(row.get("Получатель", ""))
                contractor = None
                if contractor_name and contractor_name != "nan":
                    contractor = db.query(Contractor).filter(Contractor.name == contractor_name).first()
                    if not contractor:
                        contractor = Contractor(name=contractor_name)
                        db.add(contractor)
                        db.flush()

                # Parse dates
                request_date = row.get("Дата заявки")
                if pd.isna(request_date):
                    request_date = datetime.now()
                elif isinstance(request_date, str):
                    request_date = pd.to_datetime(request_date, format="%d.%m.%Y", errors="coerce")
                    if pd.isna(request_date):
                        request_date = datetime.now()

                payment_date = row.get("Дата платежа")
                if not pd.isna(payment_date) and isinstance(payment_date, str):
                    payment_date = pd.to_datetime(payment_date, format="%d.%m.%Y", errors="coerce")
                else:
                    payment_date = None

                # Get amount
                amount = row.get("Сумма", 0)
                if pd.isna(amount):
                    amount = 0

                # Get status
                status_str = str(row.get("Статус", "Черновик"))
                status = status_mapping.get(status_str, ExpenseStatusEnum.DRAFT)

                # Create expense
                expense = Expense(
                    number=number,
                    category_id=category_id,
                    contractor_id=contractor.id if contractor else None,
                    organization_id=organization_id,
                    amount=Decimal(str(amount)),
                    request_date=request_date,
                    payment_date=payment_date,
                    status=status,
                    is_paid=(status == ExpenseStatusEnum.PAID),
                    is_closed=(str(row.get("Оплачена / Закрыта", "")) == "Да"),
                    comment=str(row.get("Комментарий", "")) if not pd.isna(row.get("Комментарий")) else None,
                    requester=str(row.get("Заявитель", "")) if not pd.isna(row.get("Заявитель")) else None,
                )

                db.add(expense)
                imported += 1

                if imported % 10 == 0:
                    db.commit()
                    print(f"  Imported {imported} expenses...")

            except Exception as e:
                print(f"  Error importing row {idx}: {e}")
                skipped += 1
                continue

        db.commit()
        print(f"\nExpenses import completed!")
        print(f"  Imported: {imported}")
        print(f"  Skipped: {skipped}")

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        db.rollback()


def main():
    """Main import function"""
    print("="*60)
    print("IT Budget Manager - Data Import Script")
    print("="*60)

    # Create database session
    db = SessionLocal()

    try:
        # Create tables
        create_tables()

        # Import reference data
        import_categories(db)
        import_organizations(db)

        # Import expenses
        expenses_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "заявки на расходы по дням.xlsx"
        )

        if os.path.exists(expenses_file):
            import_expenses_from_excel(db, expenses_file)
        else:
            print(f"\nWarning: Expenses file not found: {expenses_file}")

        print("\n" + "="*60)
        print("Import completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
