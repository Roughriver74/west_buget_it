"""
Классификация импортированных банковских транзакций за ноябрь 2025
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction, BankTransactionStatusEnum
from app.services.transaction_classifier import TransactionClassifier


def classify_transactions():
    """
    Применить AI классификацию ко всем транзакциям со статусом NEW
    """
    db: Session = SessionLocal()

    try:
        # Создать классификатор
        classifier = TransactionClassifier(db)

        # Получить все транзакции за ноябрь 2025 со статусом NEW
        transactions = db.query(BankTransaction).filter(
            BankTransaction.transaction_year == 2025,
            BankTransaction.transaction_month == 11,
            BankTransaction.status == BankTransactionStatusEnum.NEW,
            BankTransaction.is_active == True
        ).all()

        print(f"Найдено {len(transactions)} транзакций для классификации")
        print()

        categorized_count = 0
        needs_review_count = 0
        failed_count = 0

        for i, transaction in enumerate(transactions, 1):
            if i % 100 == 0:
                print(f"Обработано {i}/{len(transactions)} транзакций...")

            try:
                # Классифицировать транзакцию
                category_id, confidence, reasoning = classifier.classify(
                    payment_purpose=transaction.payment_purpose,
                    counterparty_name=transaction.counterparty_name,
                    counterparty_inn=transaction.counterparty_inn,
                    amount=transaction.amount,
                    department_id=transaction.department_id
                )

                if category_id:
                    # Автоматически назначаем категорию при высокой уверенности
                    if confidence >= 0.9:
                        transaction.category_id = category_id
                        transaction.category_confidence = Decimal(str(confidence))
                        transaction.status = BankTransactionStatusEnum.CATEGORIZED
                        categorized_count += 1
                    else:
                        # Предлагаем категорию для ручной проверки
                        transaction.suggested_category_id = category_id
                        transaction.category_confidence = Decimal(str(confidence))
                        transaction.status = BankTransactionStatusEnum.NEEDS_REVIEW
                        needs_review_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                print(f"Ошибка при классификации транзакции {transaction.id}: {e}")
                failed_count += 1
                continue

        # Сохранить изменения
        db.commit()

        print()
        print("=" * 70)
        print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ:")
        print("=" * 70)
        print(f"Всего обработано:           {len(transactions)}")
        print(f"Автоматически категорировано: {categorized_count}")
        print(f"Требуют ручной проверки:    {needs_review_count}")
        print(f"Не удалось классифицировать: {failed_count}")
        print()

        # Показать примеры категоризованных транзакций
        print("Примеры автоматически категоризованных транзакций:")
        print("-" * 70)

        categorized = db.query(BankTransaction).filter(
            BankTransaction.transaction_year == 2025,
            BankTransaction.transaction_month == 11,
            BankTransaction.status == BankTransactionStatusEnum.CATEGORIZED,
            BankTransaction.category_id.isnot(None)
        ).limit(5).all()

        for t in categorized:
            print(f"{t.transaction_date} | {t.amount:>12} | {t.category_rel.name if t.category_rel else 'N/A'}")
            print(f"  {t.payment_purpose[:80]}")
            print()

    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      AI Classification - November 2025 Transactions               ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    classify_transactions()
