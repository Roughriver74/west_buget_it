"""
Тестовый скрипт для импорта банковских операций из 1С через OData

Запуск:
    cd backend
    python scripts/test_1c_import.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.odata_1c_client import OData1CClient
from app.services.bank_transaction_1c_import import BankTransaction1CImporter


def main():
    """Тестовый импорт за небольшой период"""

    # Database session
    db: Session = SessionLocal()

    try:
        # 1. Create OData client
        print("Creating 1C OData client...")
        client = OData1CClient(
            base_url="http://10.10.100.77/trade/odata/standard.odata",
            username="odata.user",
            password="ak228Hu2hbs28"
        )

        # 2. Test connection
        print("Testing connection...")
        if not client.test_connection():
            print("ERROR: Connection failed!")
            return

        print("✅ Connection successful!")

        # 3. Test fetch receipts (small period)
        print("\n" + "="*60)
        print("Testing fetch receipts (June 16-17, 2020)...")
        print("="*60)

        receipts = client.get_bank_receipts(
            date_from=date(2020, 6, 16),
            date_to=date(2020, 6, 17),
            top=5
        )

        print(f"\nFetched {len(receipts)} receipts")

        if receipts:
            print("\nFirst receipt sample:")
            first = receipts[0]
            print(f"  Ref_Key: {first.get('Ref_Key')}")
            print(f"  Number: {first.get('Number')}")
            print(f"  Date: {first.get('Date')}")
            print(f"  Amount: {first.get('СуммаДокумента')}")
            print(f"  Purpose: {first.get('НазначениеПлатежа', '')[:50]}...")
            print(f"  Posted: {first.get('Posted')}")

        # 4. Test fetch payments
        print("\n" + "="*60)
        print("Testing fetch payments (June 18-19, 2020)...")
        print("="*60)

        payments = client.get_bank_payments(
            date_from=date(2020, 6, 18),
            date_to=date(2020, 6, 19),
            top=5
        )

        print(f"\nFetched {len(payments)} payments")

        if payments:
            print("\nFirst payment sample:")
            first = payments[0]
            print(f"  Ref_Key: {first.get('Ref_Key')}")
            print(f"  Number: {first.get('Number')}")
            print(f"  Date: {first.get('Date')}")
            print(f"  Amount: {first.get('СуммаДокумента')}")
            print(f"  Purpose: {first.get('НазначениеПлатежа', '')[:50]}...")
            print(f"  Posted: {first.get('Posted')}")

        # 5. Test import (за 2 дня, чтобы не перегрузить)
        print("\n" + "="*60)
        print("Testing import to database (June 16-17, 2020)...")
        print("="*60)

        # Спросим, хотим ли мы импортировать
        answer = input("\nDo you want to import transactions to database? (y/n): ")

        if answer.lower() == 'y':
            # Выбираем department_id
            department_id = input("Enter department_id (default: 1): ") or "1"
            department_id = int(department_id)

            # Create importer
            importer = BankTransaction1CImporter(
                db=db,
                odata_client=client,
                department_id=department_id,
                auto_classify=True  # Включаем AI классификацию
            )

            # Import transactions
            print(f"\nImporting for department {department_id}...")
            result = importer.import_transactions(
                date_from=date(2020, 6, 16),
                date_to=date(2020, 6, 17),
                batch_size=10
            )

            # Print results
            print("\n" + "="*60)
            print("IMPORT RESULTS:")
            print("="*60)
            print(f"Total fetched:      {result.total_fetched}")
            print(f"Total processed:    {result.total_processed}")
            print(f"Created:            {result.total_created}")
            print(f"Updated:            {result.total_updated}")
            print(f"Skipped:            {result.total_skipped}")
            print(f"Auto-categorized:   {result.auto_categorized}")
            print(f"Errors:             {len(result.errors)}")

            if result.errors:
                print("\nErrors:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")

            print("\n✅ Import completed!")
        else:
            print("\nSkipping import.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
