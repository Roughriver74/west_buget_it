"""
Script to load test data for Credit Portfolio module.
Inserts sample data into fin_organizations, fin_bank_accounts, fin_contracts,
fin_receipts, fin_expenses, and fin_expense_details tables.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import (
    Department,
    FinOrganization,
    FinBankAccount,
    FinContract,
    FinReceipt,
    FinExpense,
    FinExpenseDetail,
)


def create_test_data(db: Session, department_id: int):
    """Create comprehensive test data for credit portfolio analytics."""

    print(f"Creating test data for department_id={department_id}")

    # 1. Create Organizations
    print("Creating organizations...")
    organizations = []
    org_data = [
        {"name": "ПАО Сбербанк", "inn": "7707083893"},
        {"name": "ВТБ (ПАО)", "inn": "7702070139"},
        {"name": "АО 'Альфа-Банк'", "inn": "7728168971"},
    ]

    for data in org_data:
        org = FinOrganization(
            name=data["name"],
            inn=data["inn"],
            is_active=True,
            department_id=department_id,
        )
        db.add(org)
        organizations.append(org)

    db.commit()
    print(f"Created {len(organizations)} organizations")

    # 2. Create Bank Accounts
    print("Creating bank accounts...")
    bank_accounts = []
    bank_names = ["Сбербанк", "ВТБ", "Альфа-Банк"]
    for i, org in enumerate(organizations, 1):
        account = FinBankAccount(
            account_number=f"4070281000000000{i:04d}",
            bank_name=bank_names[i-1],
            is_active=True,
            department_id=department_id,
        )
        db.add(account)
        bank_accounts.append(account)

    db.commit()
    print(f"Created {len(bank_accounts)} bank accounts")

    # 3. Create Contracts
    print("Creating contracts...")
    contracts = []
    contract_data = [
        {
            "number": "КД-001/2023",
            "date": "2023-01-15",
            "type": "Кредитный договор",
            "counterparty": "ПАО Сбербанк",
        },
        {
            "number": "КД-002/2023",
            "date": "2023-06-20",
            "type": "Кредитный договор",
            "counterparty": "ВТБ (ПАО)",
        },
        {
            "number": "КД-003/2024",
            "date": "2024-01-10",
            "type": "Кредитный договор",
            "counterparty": "АО 'Альфа-Банк'",
        },
    ]

    for data in contract_data:
        contract = FinContract(
            contract_number=data["number"],
            contract_date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            contract_type=data["type"],
            counterparty=data["counterparty"],
            is_active=True,
            department_id=department_id,
        )
        db.add(contract)
        contracts.append(contract)

    db.commit()
    print(f"Created {len(contracts)} contracts")

    # 4. Create Receipts (Credit inflows - получение кредитов)
    print("Creating receipts...")
    receipts = []

    # Contract 1 (Сбербанк) - 2023
    receipt_dates_2023 = [
        ("2023-02-01", 5000000),  # 5M initial
        ("2023-07-01", 3000000),  # 3M additional
    ]

    for date_str, amount in receipt_dates_2023:
        receipt = FinReceipt(
            operation_id=f"RCP-{date_str}-001",
            organization_id=organizations[0].id,
            bank_account_id=bank_accounts[0].id,
            contract_id=contracts[0].id,
            operation_type="Получение кредита",
            document_number=f"ПП-{date_str}",
            document_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
            payer=organizations[0].name,
            payment_purpose=f"Предоставление кредита по договору {contracts[0].contract_number}",
            currency="RUB",
            amount=Decimal(str(amount)),
            is_active=True,
            department_id=department_id,
        )
        db.add(receipt)
        receipts.append(receipt)

    # Contract 2 (ВТБ) - 2023
    receipt = FinReceipt(
        operation_id="RCP-2023-08-01-002",
        organization_id=organizations[1].id,
        bank_account_id=bank_accounts[1].id,
        contract_id=contracts[1].id,
        operation_type="Получение кредита",
        document_number="ПП-2023-08-01",
        document_date=datetime.strptime("2023-08-01", "%Y-%m-%d").date(),
        payer=organizations[1].name,
        payment_purpose=f"Предоставление кредита по договору {contracts[1].contract_number}",
        currency="RUB",
        amount=Decimal("4000000"),
        is_active=True,
        department_id=department_id,
    )
    db.add(receipt)
    receipts.append(receipt)

    # Contract 3 (Альфа-Банк) - 2024
    receipt_dates_2024 = [
        ("2024-02-01", 6000000),  # 6M initial
        ("2024-08-01", 2000000),  # 2M additional
    ]

    for date_str, amount in receipt_dates_2024:
        receipt = FinReceipt(
            operation_id=f"RCP-{date_str}-003",
            organization_id=organizations[2].id,
            bank_account_id=bank_accounts[2].id,
            contract_id=contracts[2].id,
            operation_type="Получение кредита",
            document_number=f"ПП-{date_str}",
            document_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
            payer=organizations[2].name,
            payment_purpose=f"Предоставление кредита по договору {contracts[2].contract_number}",
            currency="RUB",
            amount=Decimal(str(amount)),
            is_active=True,
            department_id=department_id,
        )
        db.add(receipt)
        receipts.append(receipt)

    # 2025 data
    receipt = FinReceipt(
        operation_id="RCP-2025-01-15-001",
        organization_id=organizations[0].id,
        bank_account_id=bank_accounts[0].id,
        contract_id=contracts[0].id,
        operation_type="Получение кредита",
        document_number="ПП-2025-01-15",
        document_date=datetime.strptime("2025-01-15", "%Y-%m-%d").date(),
        payer=organizations[0].name,
        payment_purpose=f"Предоставление кредита по договору {contracts[0].contract_number}",
        currency="RUB",
        amount=Decimal("3500000"),
        is_active=True,
        department_id=department_id,
    )
    db.add(receipt)
    receipts.append(receipt)

    db.commit()
    print(f"Created {len(receipts)} receipts")

    # 5. Create Expenses (Credit payments - погашение кредитов)
    print("Creating expenses...")
    expenses = []

    # Contract 1 - Monthly payments 2023
    start_date = datetime(2023, 3, 1)
    for month in range(10):  # 10 months of 2023
        payment_date = start_date + timedelta(days=30 * month)
        expense = FinExpense(
            operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-001",
            organization_id=organizations[0].id,
            bank_account_id=bank_accounts[0].id,
            contract_id=contracts[0].id,
            operation_type="Погашение кредита",
            document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
            document_date=payment_date.date(),
            recipient=organizations[0].name,
            payment_purpose=f"Погашение кредита по договору {contracts[0].contract_number}",
            currency="RUB",
            amount=Decimal("450000"),  # Total payment
            expense_article="Погашение кредитов",
            unconfirmed_by_bank=False,
            is_active=True,
            department_id=department_id,
        )
        db.add(expense)
        expenses.append(expense)

    # Contract 1 - Monthly payments 2024
    start_date = datetime(2024, 1, 1)
    for month in range(12):  # 12 months of 2024
        payment_date = start_date + timedelta(days=30 * month)
        expense = FinExpense(
            operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-001",
            organization_id=organizations[0].id,
            bank_account_id=bank_accounts[0].id,
            contract_id=contracts[0].id,
            operation_type="Погашение кредита",
            document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
            document_date=payment_date.date(),
            recipient=organizations[0].name,
            payment_purpose=f"Погашение кредита по договору {contracts[0].contract_number}",
            currency="RUB",
            amount=Decimal("420000"),  # Reduced payment
            expense_article="Погашение кредитов",
            unconfirmed_by_bank=False,
            is_active=True,
            department_id=department_id,
        )
        db.add(expense)
        expenses.append(expense)

    # Contract 2 - Monthly payments 2023
    start_date = datetime(2023, 9, 1)
    for month in range(4):  # 4 months of 2023
        payment_date = start_date + timedelta(days=30 * month)
        expense = FinExpense(
            operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-002",
            organization_id=organizations[1].id,
            bank_account_id=bank_accounts[1].id,
            contract_id=contracts[1].id,
            operation_type="Погашение кредита",
            document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
            document_date=payment_date.date(),
            recipient=organizations[1].name,
            payment_purpose=f"Погашение кредита по договору {contracts[1].contract_number}",
            currency="RUB",
            amount=Decimal("380000"),
            expense_article="Погашение кредитов",
            unconfirmed_by_bank=False,
            is_active=True,
            department_id=department_id,
        )
        db.add(expense)
        expenses.append(expense)

    # Contract 2 - Monthly payments 2024
    start_date = datetime(2024, 1, 1)
    for month in range(12):
        payment_date = start_date + timedelta(days=30 * month)
        expense = FinExpense(
            operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-002",
            organization_id=organizations[1].id,
            bank_account_id=bank_accounts[1].id,
            contract_id=contracts[1].id,
            operation_type="Погашение кредита",
            document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
            document_date=payment_date.date(),
            recipient=organizations[1].name,
            payment_purpose=f"Погашение кредита по договору {contracts[1].contract_number}",
            currency="RUB",
            amount=Decimal("360000"),
            expense_article="Погашение кредитов",
            unconfirmed_by_bank=False,
            is_active=True,
            department_id=department_id,
        )
        db.add(expense)
        expenses.append(expense)

    # Contract 3 - Monthly payments 2024
    start_date = datetime(2024, 3, 1)
    for month in range(10):
        payment_date = start_date + timedelta(days=30 * month)
        expense = FinExpense(
            operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-003",
            organization_id=organizations[2].id,
            bank_account_id=bank_accounts[2].id,
            contract_id=contracts[2].id,
            operation_type="Погашение кредита",
            document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
            document_date=payment_date.date(),
            recipient=organizations[2].name,
            payment_purpose=f"Погашение кредита по договору {contracts[2].contract_number}",
            currency="RUB",
            amount=Decimal("500000"),
            expense_article="Погашение кредитов",
            unconfirmed_by_bank=False,
            is_active=True,
            department_id=department_id,
        )
        db.add(expense)
        expenses.append(expense)

    # 2025 payments
    start_date = datetime(2025, 1, 1)
    for month in range(3):  # January to March 2025
        for contract_idx, org in enumerate(organizations):
            payment_date = start_date + timedelta(days=30 * month)
            amounts = [400000, 350000, 480000]  # Different amounts per org
            expense = FinExpense(
                operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-{contract_idx+1:03d}",
                organization_id=org.id,
                bank_account_id=bank_accounts[contract_idx].id,
                contract_id=contracts[contract_idx].id,
                operation_type="Погашение кредита",
                document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}-{contract_idx+1}",
                document_date=payment_date.date(),
                recipient=org.name,
                payment_purpose=f"Погашение кредита по договору {contracts[contract_idx].contract_number}",
                currency="RUB",
                amount=Decimal(str(amounts[contract_idx])),
                expense_article="Погашение кредитов",
                unconfirmed_by_bank=False,
                is_active=True,
                department_id=department_id,
            )
            db.add(expense)
            expenses.append(expense)

    db.commit()
    print(f"Created {len(expenses)} expenses")

    # 6. Create Expense Details (Principal and Interest breakdown)
    print("Creating expense details...")
    details_count = 0

    for expense in expenses:
        # Calculate principal and interest (typically 70-80% principal, 20-30% interest)
        total = float(expense.amount)
        principal_ratio = 0.75  # 75% principal
        interest_ratio = 0.25   # 25% interest

        # Principal payment
        detail_principal = FinExpenseDetail(
            expense_operation_id=expense.operation_id,
            payment_type="тело",
            payment_amount=Decimal(str(total * principal_ratio)),
            settlement_amount=Decimal(str(total * principal_ratio)),
            expense_amount=Decimal(str(total * principal_ratio)),
            department_id=department_id,
        )
        db.add(detail_principal)
        details_count += 1

        # Interest payment
        detail_interest = FinExpenseDetail(
            expense_operation_id=expense.operation_id,
            payment_type="проценты",
            payment_amount=Decimal(str(total * interest_ratio)),
            settlement_amount=Decimal(str(total * interest_ratio)),
            expense_amount=Decimal(str(total * interest_ratio)),
            department_id=department_id,
        )
        db.add(detail_interest)
        details_count += 1

    db.commit()
    print(f"Created {details_count} expense details")

    print("\n" + "="*60)
    print("Test data creation completed successfully!")
    print("="*60)
    print(f"Organizations: {len(organizations)}")
    print(f"Bank Accounts: {len(bank_accounts)}")
    print(f"Contracts: {len(contracts)}")
    print(f"Receipts: {len(receipts)}")
    print(f"Expenses: {len(expenses)}")
    print(f"Expense Details: {details_count}")
    print("="*60)


def main():
    """Main function to run the script."""
    db = SessionLocal()

    try:
        # Get first department
        department = db.query(Department).first()

        if not department:
            print("ERROR: No departments found in database!")
            print("Please create a department first.")
            return

        print(f"Using department: {department.name} (ID: {department.id})")

        # Check if test data already exists
        existing_orgs = db.query(FinOrganization).filter(
            FinOrganization.department_id == department.id
        ).count()

        if existing_orgs > 0:
            response = input(
                f"Found {existing_orgs} existing organizations for this department. "
                "Delete and recreate test data? (yes/no): "
            )
            if response.lower() != 'yes':
                print("Aborted.")
                return

            # Delete existing data
            print("Deleting existing credit portfolio data...")
            db.query(FinExpenseDetail).filter(
                FinExpenseDetail.department_id == department.id
            ).delete()
            db.query(FinExpense).filter(
                FinExpense.department_id == department.id
            ).delete()
            db.query(FinReceipt).filter(
                FinReceipt.department_id == department.id
            ).delete()
            db.query(FinContract).filter(
                FinContract.department_id == department.id
            ).delete()
            db.query(FinBankAccount).filter(
                FinBankAccount.department_id == department.id
            ).delete()
            db.query(FinOrganization).filter(
                FinOrganization.department_id == department.id
            ).delete()
            db.commit()
            print("Deleted existing data.")

        # Create test data
        create_test_data(db, department.id)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
