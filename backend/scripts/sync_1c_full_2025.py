"""
Full 1C OData Sync - All 2025 Data
Загружает все данные с начала 2025 года
Использовать для первоначальной загрузки или полного обновления
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import create_1c_client_from_env
from app.services.bank_transaction_1c_import import BankTransaction1CImporter

# Настроить логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_full_2025():
    """Полная синхронизация всех данных за 2025 год"""

    db: Session = SessionLocal()

    try:
        # Найти отдел FIN
        fin_department = db.query(Department).filter_by(code="FIN").first()
        if not fin_department:
            logger.error("Department FIN not found!")
            return

        print("\n" + "=" * 80)
        print(f"FULL 2025 SYNC - Department: {fin_department.name}")
        print("=" * 80)

        # Создать OData клиент
        client = create_1c_client_from_env()

        # Проверить подключение
        if not client.test_connection():
            logger.error("Failed to connect to 1C OData!")
            return

        print("\n✅ Connected to 1C OData")

        # Период: весь 2025 год
        date_from = date(2025, 1, 1)
        date_to = date(2025, 12, 31)

        print(f"\n📅 Period: {date_from} to {date_to} (FULL YEAR 2025)")
        print(f"🏢 Department: {fin_department.name} (id={fin_department.id})")
        print(f"🤖 Auto-classify: enabled\n")

        # Создать импортер
        importer = BankTransaction1CImporter(
            db=db,
            odata_client=client,
            department_id=fin_department.id,
            auto_classify=True  # Автоматическая классификация
        )

        # Импортировать данные
        print("Starting import... (this may take several minutes)\n")

        result = importer.import_transactions(
            date_from=date_from,
            date_to=date_to
        )

        # Вывести результаты
        print("\n" + "=" * 80)
        print("FULL 2025 SYNC RESULTS")
        print("=" * 80)
        print(f"Total fetched:      {result.total_fetched}")
        print(f"Total processed:    {result.total_processed}")
        print(f"Created:            {result.created}")
        print(f"Updated:            {result.updated}")
        print(f"Skipped (duplicates): {result.skipped}")
        print(f"Auto-categorized:   {result.auto_categorized}")
        print(f"Errors:             {len(result.errors)}")

        if result.errors:
            print("\n⚠️  Errors occurred:")
            for i, error in enumerate(result.errors[:20], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 20:
                print(f"  ... and {len(result.errors) - 20} more errors")

        print("\n" + "=" * 80)
        print("✅ FULL 2025 SYNC COMPLETED")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Full 2025 sync failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    sync_full_2025()
