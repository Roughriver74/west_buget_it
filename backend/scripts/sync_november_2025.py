"""
Синхронизация банковских операций из 1С за ноябрь 2025
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import OData1CClient
from app.services.bank_transaction_1c_import import BankTransaction1CImporter


def main():
    """
    Синхронизация за ноябрь 2025
    """
    db: Session = SessionLocal()

    try:
        # Найти отдел Финансы
        fin_department = db.query(Department).filter(Department.code == "FIN").first()

        if not fin_department:
            print("❌ ERROR: Department 'FIN' not found!")
            return

        print(f"✅ Found department: {fin_department.name} (id={fin_department.id})")
        print()

        # Создать OData клиент
        print("Creating 1C OData client...")
        client = OData1CClient(
            base_url="http://10.10.100.77/trade/odata/standard.odata",
            username="odata.user",
            password="ak228Hu2hbs28"
        )

        # Тест подключения
        print("Testing connection...")
        if not client.test_connection():
            print("❌ ERROR: Connection failed!")
            return

        print("✅ Connection successful!\n")

        # Параметры синхронизации - НОЯБРЬ 2025
        date_from = date(2025, 11, 1)
        date_to = date(2025, 11, 30)

        print("=" * 70)
        print(f"Starting synchronization for {fin_department.name}")
        print("=" * 70)
        print(f"Period: {date_from} to {date_to} (NOVEMBER 2025)")
        print(f"Department ID: {fin_department.id}")
        print(f"Auto-classify: enabled")
        print()

        # Создать импортер
        importer = BankTransaction1CImporter(
            db=db,
            odata_client=client,
            department_id=fin_department.id,
            auto_classify=True
        )

        # Импортировать транзакции
        result = importer.import_transactions(
            date_from=date_from,
            date_to=date_to,
            batch_size=100
        )

        # Показать результаты
        print("\n" + "=" * 70)
        print("SYNCHRONIZATION RESULTS:")
        print("=" * 70)
        print(f"Total fetched:      {result.total_fetched}")
        print(f"Total processed:    {result.total_processed}")
        print(f"Created:            {result.total_created}")
        print(f"Updated:            {result.total_updated}")
        print(f"Skipped:            {result.total_skipped}")
        print(f"Auto-categorized:   {result.auto_categorized}")
        print(f"Errors:             {len(result.errors)}")
        print()

        if result.errors:
            print("⚠️  Errors:")
            for i, error in enumerate(result.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")
            print()

        if result.total_created > 0 or result.total_updated > 0:
            print("✅ Synchronization completed successfully!")
            print(f"\n📊 Imported {result.total_created + result.total_updated} transactions for November 2025")
        else:
            print("⚠️  No new transactions were imported")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      1C OData Synchronization - November 2025                     ║
║      Department: Финансы (FIN)                                    ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    main()
