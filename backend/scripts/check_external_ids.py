"""
Проверка - есть ли в БД записи с external_id_1c из ноябрьских данных
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction

db = SessionLocal()

try:
    # Эти external_id_1c мы видели в выводе
    november_ids = [
        "30670543-c11d-11f0-ad7f-74563c634acb",
        "2fdec760-b6dc-11f0-ad7f-74563c634acb",
        "3608d54a-b6dc-11f0-ad7f-74563c634acb",
        "eccb18eb-b6da-11f0-ad7f-74563c634acb",
        "c9ebb880-b6db-11f0-ad7f-74563c634acb"
    ]

    print("=" * 80)
    print("ПРОВЕРКА external_id_1c В БАЗЕ ДАННЫХ")
    print("=" * 80)

    for ext_id in november_ids:
        exists = db.query(BankTransaction).filter(
            BankTransaction.external_id_1c == ext_id
        ).first()

        if exists:
            print(f"✅ {ext_id[:36]} - НАЙДЕН (дата: {exists.transaction_date})")
        else:
            print(f"❌ {ext_id[:36]} - НЕ НАЙДЕН")

    # Проверим, сколько вообще ноябрьских записей в БД
    from datetime import date
    november_count = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= date(2025, 11, 1),
        BankTransaction.transaction_date <= date(2025, 11, 30)
    ).count()

    print(f"\n📊 Всего записей за ноябрь 2025 в БД: {november_count}")

    if november_count > 0:
        # Показать примеры
        examples = db.query(BankTransaction).filter(
            BankTransaction.transaction_date >= date(2025, 11, 1),
            BankTransaction.transaction_date <= date(2025, 11, 30)
        ).limit(5).all()

        print("\nПримеры:")
        for t in examples:
            print(f"  {t.transaction_date} | {t.transaction_type.value} | {t.amount} ₽ | {t.external_id_1c[:36] if t.external_id_1c else 'N/A'}")

finally:
    db.close()

print("\n" + "=" * 80)
print("ЗАВЕРШЕНО")
print("=" * 80)
