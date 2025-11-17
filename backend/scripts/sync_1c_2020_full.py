"""
Синхронизация всех банковских операций из 1С за 2020 год
Загрузка для отдела Финансы (FIN)

Запуск: python scripts/sync_1c_2020_full.py
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
    Синхронизация всех банковских операций за 2020 год
    Отдел: Финансы (FIN)
    """

    db: Session = SessionLocal()

    try:
        # Найти отдел Финансы
        fin_department = db.query(Department).filter(Department.code == "FIN").first()

        if not fin_department:
            print("❌ ERROR: Department 'FIN' not found!")
            return

        print(f"✅ Department: {fin_department.name} (id={fin_department.id})")

        # Создать OData клиент
        print("Creating 1C OData client...")
        client = OData1CClient(
            base_url="http://10.10.100.77/trade/odata/standard.odata",
            username="odata.user",
            password="ak228Hu2hbs28"
        )

        # Тест подключения
        if not client.test_connection():
            print("❌ ERROR: Connection failed!")
            return

        print("✅ Connection successful!\n")

        # Параметры синхронизации - ВСЕ 2020 год
        date_from = date(2020, 1, 1)
        date_to = date(2020, 12, 31)

        print("=" * 70)
        print(f"🔄 FULL SYNCHRONIZATION FOR 2020")
        print("=" * 70)
        print(f"Department: {fin_department.name} (id={fin_department.id})")
        print(f"Period: {date_from} to {date_to}")
        print(f"Auto-classify: enabled")
        print(f"Batch size: 500 (optimized for full year)")
        print()

        # Создать импортер
        importer = BankTransaction1CImporter(
            db=db,
            odata_client=client,
            department_id=fin_department.id,
            auto_classify=True
        )

        # Импортировать транзакции
        print("Starting import...")
        print("This may take several minutes for a full year of data...")
        print()

        result = importer.import_transactions(
            date_from=date_from,
            date_to=date_to,
            batch_size=500  # Больший батч для производительности
        )

        # Показать результаты
        print("\n" + "=" * 70)
        print("✅ SYNCHRONIZATION COMPLETED")
        print("=" * 70)
        print(f"📊 Statistics:")
        print(f"   Total fetched:      {result.total_fetched}")
        print(f"   Total processed:    {result.total_processed}")
        print(f"   Created:            {result.total_created}")
        print(f"   Updated:            {result.total_updated}")
        print(f"   Skipped:            {result.total_skipped}")
        print(f"   Auto-categorized:   {result.auto_categorized}")
        print(f"   Errors:             {len(result.errors)}")

        if result.auto_categorized > 0:
            percentage = (result.auto_categorized / result.total_processed * 100) if result.total_processed > 0 else 0
            print(f"\n🤖 AI Classification: {percentage:.1f}% auto-categorized")

        if result.errors:
            print(f"\n⚠️  Errors ({len(result.errors)}):")
            for i, error in enumerate(result.errors[:5], 1):
                print(f"   {i}. {error}")
            if len(result.errors) > 5:
                print(f"   ... and {len(result.errors) - 5} more errors")

        print("\n" + "=" * 70)

        # Статистика по месяцам
        from sqlalchemy import func, extract
        from app.db.models import BankTransaction

        print("\n📅 Monthly Breakdown:")
        monthly_stats = db.query(
            extract('month', BankTransaction.transaction_date).label('month'),
            func.count(BankTransaction.id).label('count'),
            func.sum(BankTransaction.amount).label('total_amount')
        ).filter(
            BankTransaction.department_id == fin_department.id,
            BankTransaction.transaction_date >= date_from,
            BankTransaction.transaction_date <= date_to
        ).group_by('month').order_by('month').all()

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        for month_num, count, total in monthly_stats:
            month_name = months[int(month_num) - 1]
            total_rub = float(total) if total else 0
            print(f"   {month_name} 2020: {count:4d} transactions, {total_rub:,.2f}₽")

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
║      1C OData Full Synchronization - 2020                         ║
║      Department: Финансы (FIN)                                    ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    main()
