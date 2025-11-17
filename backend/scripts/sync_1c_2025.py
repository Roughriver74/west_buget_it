"""
Синхронизация банковских операций из 1С за 2025 год
Автоматическая загрузка данных для отдела Финансы (FIN)

Запуск: python scripts/sync_1c_2025.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import OData1CClient
from app.services.bank_transaction_1c_import import BankTransaction1CImporter


def main():
    """
    Синхронизация банковских операций из 1С за 2025 год
    Загрузка для отдела Финансы (FIN, id=8)
    """

    db: Session = SessionLocal()

    try:
        # Найти отдел Финансы
        fin_department = db.query(Department).filter(Department.code == "FIN").first()

        if not fin_department:
            print("❌ ERROR: Department 'FIN' not found!")
            print("Available departments:")
            departments = db.query(Department).all()
            for dept in departments:
                print(f"  - {dept.code}: {dept.name} (id={dept.id})")
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

        # Параметры синхронизации
        date_from = date(2025, 1, 1)
        date_to = date(2025, 12, 31)

        print("=" * 70)
        print(f"Starting synchronization for {fin_department.name}")
        print("=" * 70)
        print(f"Period: {date_from} to {date_to}")
        print(f"Department ID: {fin_department.id}")
        print(f"Auto-classify: enabled")
        print()

        # Создать импортер
        importer = BankTransaction1CImporter(
            db=db,
            odata_client=client,
            department_id=fin_department.id,
            auto_classify=True  # Включаем AI классификацию
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
            for i, error in enumerate(result.errors[:10], 1):  # Показать первые 10 ошибок
                print(f"  {i}. {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")
            print()

        if result.total_created > 0 or result.total_updated > 0:
            print("✅ Synchronization completed successfully!")

            # Статистика по категориям
            if result.auto_categorized > 0:
                percentage = (result.auto_categorized / result.total_processed * 100) if result.total_processed > 0 else 0
                print(f"\n📊 AI Classification: {percentage:.1f}% transactions auto-categorized")
        else:
            print("⚠️  No new transactions were imported")
            print("Possible reasons:")
            print("  - All transactions for this period already exist")
            print("  - No transactions in 1C for this period")
            print("  - Date range filter excluded all records")

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
║      1C OData Synchronization - 2025 Year                         ║
║      Department: Финансы (FIN)                                    ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    main()
