"""
Проверка данных за ноябрь 2025
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction, BankTransactionTypeEnum
from datetime import date, timedelta
from sqlalchemy import func

db = SessionLocal()

try:
    print("=" * 80)
    print("ПРОВЕРКА ДАННЫХ ЗА НОЯБРЬ 2025")
    print("=" * 80)

    # Ноябрь 2025
    nov_start = date(2025, 11, 1)
    nov_end = date(2025, 11, 30)

    # Всего за ноябрь
    nov_total = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= nov_start,
        BankTransaction.transaction_date <= nov_end
    ).count()

    print(f"\nВсего транзакций за ноябрь 2025: {nov_total}")

    # По типам
    nov_credit = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= nov_start,
        BankTransaction.transaction_date <= nov_end,
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT
    ).count()

    nov_debit = db.query(BankTransaction).filter(
        BankTransaction.transaction_date >= nov_start,
        BankTransaction.transaction_date <= nov_end,
        BankTransaction.transaction_type == BankTransactionTypeEnum.DEBIT
    ).count()

    print(f"CREDIT (приход): {nov_credit}")
    print(f"DEBIT (расход): {nov_debit}")

    # Проверим диапазон дат в БД
    print("\n" + "=" * 80)
    print("ДИАПАЗОН ДАТ В БАЗЕ ДАННЫХ")
    print("=" * 80)

    min_date = db.query(func.min(BankTransaction.transaction_date)).scalar()
    max_date = db.query(func.max(BankTransaction.transaction_date)).scalar()

    print(f"Минимальная дата: {min_date}")
    print(f"Максимальная дата: {max_date}")

    # Транзакции по месяцам 2025 года
    print("\n" + "=" * 80)
    print("РАСПРЕДЕЛЕНИЕ ПО МЕСЯЦАМ 2025 ГОДА")
    print("=" * 80)

    for month in range(1, 13):
        month_start = date(2025, month, 1)
        if month == 12:
            month_end = date(2025, 12, 31)
        else:
            month_end = date(2025, month + 1, 1) - timedelta(days=1)

        count = db.query(BankTransaction).filter(
            BankTransaction.transaction_date >= month_start,
            BankTransaction.transaction_date <= month_end
        ).count()

        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

        if count > 0:
            print(f"{month_names[month-1]:12s}: {count:6d} транзакций")

finally:
    db.close()
