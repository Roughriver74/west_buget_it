"""
Автоматический тестовый импорт банковских операций из 1С через OData
Запуск: python scripts/test_1c_import_auto.py
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
    """Автоматический тестовый импорт (без интерактивных запросов)"""

    db: Session = SessionLocal()

    try:
        # 1. Создать OData клиент
        print("Creating 1C OData client...")
        client = OData1CClient(
            base_url="http://10.10.100.77/trade/odata/standard.odata",
            username="odata.user",
            password="ak228Hu2hbs28"
        )

        # 2. Тест подключения
        print("Testing connection...")
        if not client.test_connection():
            print("ERROR: Connection failed!")
            return

        print("✅ Connection successful!\n")

        # 3. Получить тестовые данные
        print("=" * 60)
        print("Fetching test data (June 16-17, 2020)...")
        print("=" * 60)

        receipts = client.get_bank_receipts(
            date_from=date(2020, 6, 16),
            date_to=date(2020, 6, 17),
            top=5
        )

        payments = client.get_bank_payments(
            date_from=date(2020, 6, 16),
            date_to=date(2020, 6, 17),
            top=5
        )

        print(f"\nFetched {len(receipts)} receipts")
        print(f"Fetched {len(payments)} payments")

        if not receipts and not payments:
            print("\n⚠️  No data found for this period")
            return

        # 4. Показать примеры
        if receipts:
            print("\n📥 First receipt sample:")
            first = receipts[0]
            print(f"  Ref_Key: {first.get('Ref_Key')}")
            print(f"  Number: {first.get('Number')}")
            print(f"  Date: {first.get('Date')}")
            print(f"  Amount: {first.get('СуммаДокумента')}")
            print(f"  Purpose: {first.get('НазначениеПлатежа', '')[:60]}...")

        if payments:
            print("\n📤 First payment sample:")
            first = payments[0]
            print(f"  Ref_Key: {first.get('Ref_Key')}")
            print(f"  Number: {first.get('Number')}")
            print(f"  Date: {first.get('Date')}")
            print(f"  Amount: {first.get('СуммаДокумента')}")
            print(f"  Purpose: {first.get('НазначениеПлатежа', '')[:60]}...")

        # 5. Импорт в БД
        print("\n" + "=" * 60)
        print("Starting import to database...")
        print("=" * 60)

        # Используем department_id=1 для теста
        department_id = 1

        importer = BankTransaction1CImporter(
            db=db,
            odata_client=client,
            department_id=department_id,
            auto_classify=True  # Включаем AI классификацию
        )

        # Импортировать транзакции
        print(f"\nImporting for department {department_id}...")
        result = importer.import_transactions(
            date_from=date(2020, 6, 16),
            date_to=date(2020, 6, 17),
            batch_size=10
        )

        # Показать результаты
        print("\n" + "=" * 60)
        print("IMPORT RESULTS:")
        print("=" * 60)
        print(f"Total fetched:      {result.total_fetched}")
        print(f"Total processed:    {result.total_processed}")
        print(f"Created:            {result.total_created}")
        print(f"Updated:            {result.total_updated}")
        print(f"Skipped:            {result.total_skipped}")
        print(f"Auto-categorized:   {result.auto_categorized}")
        print(f"Errors:             {len(result.errors)}")

        if result.errors:
            print("\n⚠️  Errors:")
            for error in result.errors[:5]:  # Показать первые 5 ошибок
                print(f"  - {error}")

        if result.total_created > 0 or result.total_updated > 0:
            print("\n✅ Import completed successfully!")
        else:
            print("\n⚠️  No new transactions were imported (possibly duplicates)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
