"""
Синхронизация ноября 2025 с DEBUG логами
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import date
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Department
from app.services.odata_1c_client import OData1CClient
from app.services.bank_transaction_1c_import import BankTransaction1CImporter

# Включить DEBUG логи
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("СИНХРОНИЗАЦИЯ НОЯБРЯ 2025 (DEBUG)")
print("=" * 80)

db = SessionLocal()

try:
    # Найти отдел FIN
    fin_department = db.query(Department).filter_by(code="FIN").first()
    if not fin_department:
        print("❌ Отдел FIN не найден!")
        sys.exit(1)

    print(f"✅ Отдел: {fin_department.name} (id={fin_department.id})")

    # Создать OData client
    client = OData1CClient(
        base_url="http://10.10.100.77/trade/odata/standard.odata",
        username="odata.user",
        password="ak228Hu2hbs28"
    )

    print("\n" + "=" * 80)
    print("ЗАПУСК ИМПОРТА")
    print("=" * 80)

    # Создать импортер
    importer = BankTransaction1CImporter(
        db=db,
        odata_client=client,
        department_id=fin_department.id,
        auto_classify=True
    )

    # Импорт за ноябрь
    date_from = date(2025, 11, 1)
    date_to = date(2025, 11, 30)

    print(f"Период: {date_from} - {date_to}")

    result = importer.import_transactions(
        date_from=date_from,
        date_to=date_to
    )

    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print(f"Total fetched:      {result.total_fetched}")
    print(f"Total processed:    {result.total_processed}")
    print(f"Created:            {result.created}")
    print(f"Updated:            {result.updated}")
    print(f"Skipped:            {result.skipped}")
    print(f"Auto-categorized:   {result.auto_categorized}")
    print(f"Errors:             {len(result.errors)}")

    if result.errors:
        print("\nОшибки:")
        for error in result.errors[:10]:
            print(f"  - {error}")

finally:
    db.close()

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
