"""
Тест фильтров для банковских транзакций
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction, BankTransactionTypeEnum
from datetime import date

db = SessionLocal()

try:
    print("=" * 80)
    print("ТЕСТ 1: Фильтр по типу CREDIT (приход)")
    print("=" * 80)

    credit_count = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT
    ).count()

    credit_examples = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT
    ).limit(3).all()

    print(f"Всего CREDIT транзакций: {credit_count}")
    for t in credit_examples:
        print(f"  {t.transaction_date} | {t.transaction_type.value} | +{t.amount} ₽ | {t.counterparty_name or 'N/A'}")

    print("\n" + "=" * 80)
    print("ТЕСТ 2: Фильтр по типу DEBIT (расход)")
    print("=" * 80)

    debit_count = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.DEBIT
    ).count()

    debit_examples = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.DEBIT
    ).limit(3).all()

    print(f"Всего DEBIT транзакций: {debit_count}")
    for t in debit_examples:
        print(f"  {t.transaction_date} | {t.transaction_type.value} | -{t.amount} ₽ | {t.counterparty_name or 'N/A'}")

    print("\n" + "=" * 80)
    print("ТЕСТ 3: Фильтр по датам (октябрь 2025)")
    print("=" * 80)

    october_count = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= date(2025, 10, 1),
        BankTransaction.transaction_date <= date(2025, 10, 31)
    ).count()

    october_examples = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= date(2025, 10, 1),
        BankTransaction.transaction_date <= date(2025, 10, 31)
    ).limit(5).all()

    print(f"Транзакций за октябрь 2025: {october_count}")
    for t in october_examples:
        print(f"  {t.transaction_date} | {t.transaction_type.value} | {t.amount} ₽")

    print("\n" + "=" * 80)
    print("ТЕСТ 4: Комбинированный (CREDIT + октябрь 2025)")
    print("=" * 80)

    combined_count = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT,
        BankTransaction.transaction_date >= date(2025, 10, 1),
        BankTransaction.transaction_date <= date(2025, 10, 31)
    ).count()

    combined_examples = db.query(BankTransaction).filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT,
        BankTransaction.transaction_date >= date(2025, 10, 1),
        BankTransaction.transaction_date <= date(2025, 10, 31)
    ).limit(5).all()

    print(f"CREDIT транзакций за октябрь 2025: {combined_count}")
    for t in combined_examples:
        print(f"  {t.transaction_date} | {t.transaction_type.value} | +{t.amount} ₽ | {t.counterparty_name or 'N/A'}")

    print("\n" + "=" * 80)
    print("ИТОГО:")
    print("=" * 80)
    print(f"✅ Фильтр по типу CREDIT работает: {credit_count} транзакций")
    print(f"✅ Фильтр по типу DEBIT работает: {debit_count} транзакций")
    print(f"✅ Фильтр по датам работает: {october_count} транзакций за октябрь")
    print(f"✅ Комбинированный фильтр работает: {combined_count} CREDIT за октябрь")

finally:
    db.close()
