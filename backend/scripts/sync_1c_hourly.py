"""
Hourly 1C OData Sync - Last 24 Hours
Предназначен для запуска по расписанию (каждый час)
Загружает только новые данные за последние 24 часа, избегая дублей
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import create_1c_client_from_env
from app.services.bank_transaction_1c_import import BankTransaction1CImporter

# Настроить логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/evgenijsikunov/projects/acme/acme_buget_it/backend/logs/sync_hourly.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sync_hourly():
    """Синхронизация за последние 24 часа для всех активных отделов"""

    db: Session = SessionLocal()

    try:
        # Получить все активные отделы
        departments = db.query(Department).filter(Department.is_active == True).all()

        if not departments:
            logger.error("No active departments found!")
            return

        logger.info(f"Starting hourly sync for {len(departments)} departments")

        # Создать OData клиент
        client = create_1c_client_from_env()

        # Проверить подключение
        if not client.test_connection():
            logger.error("Failed to connect to 1C OData!")
            return

        # Период: последние 24 часа
        date_to = date.today()
        date_from = date_to - timedelta(days=1)

        logger.info(f"Sync period: {date_from} to {date_to}")

        # Счетчики для всех отделов
        total_fetched_all = 0
        total_processed_all = 0
        total_created_all = 0
        total_updated_all = 0
        total_skipped_all = 0
        total_auto_categorized_all = 0
        all_errors = []

        # Синхронизация для каждого отдела
        for dept in departments:
            logger.info(f"\n--- Syncing department: {dept.name} (ID: {dept.id}) ---")

            try:
                # Создать импортер
                importer = BankTransaction1CImporter(
                    db=db,
                    odata_client=client,
                    department_id=dept.id,
                    auto_classify=True  # Автоматическая классификация
                )

                # Импортировать данные
                result = importer.import_transactions(
                    date_from=date_from,
                    date_to=date_to
                )

                # Вывести результаты по отделу
                logger.info(f"Department {dept.name} results:")
                logger.info(f"  Fetched:          {result.total_fetched}")
                logger.info(f"  Processed:        {result.total_processed}")
                logger.info(f"  Created:          {result.created}")
                logger.info(f"  Updated:          {result.updated}")
                logger.info(f"  Skipped:          {result.skipped}")
                logger.info(f"  Auto-categorized: {result.auto_categorized}")

                if result.errors:
                    logger.warning(f"  Errors:           {len(result.errors)}")
                    for error in result.errors[:3]:
                        logger.warning(f"    - {error}")

                # Накопить статистику
                total_fetched_all += result.total_fetched
                total_processed_all += result.total_processed
                total_created_all += result.created
                total_updated_all += result.updated
                total_skipped_all += result.skipped
                total_auto_categorized_all += result.auto_categorized
                all_errors.extend(result.errors)

            except Exception as e:
                logger.error(f"Error syncing department {dept.name}: {str(e)}")
                all_errors.append(f"Department {dept.name}: {str(e)}")
                continue

        # Вывести общие результаты
        logger.info("\n" + "=" * 80)
        logger.info("HOURLY SYNC RESULTS - ALL DEPARTMENTS")
        logger.info("=" * 80)
        logger.info(f"Departments:        {len(departments)}")
        logger.info(f"Total fetched:      {total_fetched_all}")
        logger.info(f"Total processed:    {total_processed_all}")
        logger.info(f"Created:            {total_created_all}")
        logger.info(f"Updated:            {total_updated_all}")
        logger.info(f"Skipped:            {total_skipped_all}")
        logger.info(f"Auto-categorized:   {total_auto_categorized_all}")
        logger.info(f"Errors:             {len(all_errors)}")

        if all_errors:
            logger.warning("Errors occurred:")
            for error in all_errors[:10]:
                logger.warning(f"  - {error}")

        logger.info("=" * 80)

        if total_created_all > 0 or total_updated_all > 0:
            logger.info("✅ Hourly sync completed successfully with changes")
        else:
            logger.info("ℹ️  Hourly sync completed - no new transactions")

    except Exception as e:
        logger.error(f"Hourly sync failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == '__main__':
    sync_hourly()
