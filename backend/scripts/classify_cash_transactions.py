#!/usr/bin/env python
"""
Скрипт для классификации CASH транзакций (без business_operation)
Использует payment_purpose и исторические данные
"""
import sys
import os
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction, BankTransactionStatusEnum
from app.services.transaction_classifier import TransactionClassifier


def classify_cash_transactions(department_id: int, dry_run: bool = False):
    """
    Классификация CASH транзакций (без business_operation)
    """
    db = SessionLocal()
    try:
        # Получаем транзакции БЕЗ business_operation (в основном CASH)
        query = db.query(BankTransaction).filter(
            BankTransaction.department_id == department_id,
            (BankTransaction.business_operation.is_(None)) |
            (BankTransaction.business_operation == ''),
            BankTransaction.category_id.is_(None),  # Без категории
            BankTransaction.status == BankTransactionStatusEnum.NEW
        )

        transactions = query.all()
        total_count = len(transactions)

        print(f"\n=== Найдено транзакций без business_operation: {total_count} ===\n")

        if total_count == 0:
            print("✅ Все транзакции уже классифицированы")
            return

        # Создаем классификатор
        classifier = TransactionClassifier(db, department_id)

        # Статистика
        categorized_count = 0
        needs_review_count = 0
        failed_count = 0

        # Обрабатываем каждую транзакцию
        for i, transaction in enumerate(transactions, 1):
            print(f"[{i}/{total_count}] ID: {transaction.id}, Source: {transaction.payment_source}, Amount: {transaction.amount}")

            try:
                # Классифицируем
                category_id, confidence, reasoning = classifier.classify(
                    payment_purpose=transaction.payment_purpose or "",
                    counterparty_name=transaction.counterparty_name,
                    counterparty_inn=transaction.counterparty_inn,
                    amount=transaction.amount,
                    department_id=department_id,
                    transaction_type=transaction.transaction_type.value if transaction.transaction_type else None,
                    business_operation=None  # Нет business_operation
                )

                if category_id:
                    # Обновляем транзакцию
                    if not dry_run:
                        transaction.category_id = category_id
                        transaction.category_confidence = confidence

                        # Статус зависит от confidence
                        if confidence >= 0.9:
                            transaction.status = BankTransactionStatusEnum.CATEGORIZED
                            print(f"   ✅ Категория {category_id} (confidence: {confidence:.2%}) → CATEGORIZED")
                            print(f"      Причина: {reasoning}")
                            categorized_count += 1
                        else:
                            transaction.status = BankTransactionStatusEnum.NEEDS_REVIEW
                            transaction.suggested_category_id = category_id
                            print(f"   ⚠️  Предложена категория {category_id} (confidence: {confidence:.2%}) → NEEDS_REVIEW")
                            print(f"      Причина: {reasoning}")
                            needs_review_count += 1
                    else:
                        print(f"   [DRY RUN] Категория {category_id} (confidence: {confidence:.2%})")
                        print(f"      Причина: {reasoning}")
                        if confidence >= 0.9:
                            categorized_count += 1
                        else:
                            needs_review_count += 1
                else:
                    print(f"   ❌ Не удалось найти категорию: {reasoning}")
                    failed_count += 1

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                failed_count += 1

        # Сохраняем изменения
        if not dry_run:
            db.commit()
            print(f"\n✅ Изменения сохранены в базу данных")
        else:
            print(f"\n⚠️  DRY RUN - изменения НЕ сохранены")

        # Итоговая статистика
        print(f"\n=== ИТОГО ===")
        print(f"Всего обработано: {total_count}")
        print(f"Категоризировано автоматически: {categorized_count}")
        print(f"Требует проверки: {needs_review_count}")
        print(f"Не удалось классифицировать: {failed_count}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Classify CASH transactions (without business_operation)')
    parser.add_argument('--department-id', type=int, required=True, help='Department ID')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (do not save changes)')

    args = parser.parse_args()

    print(f"=== Классификация транзакций без business_operation для department_id={args.department_id} ===")
    if args.dry_run:
        print("⚠️  DRY RUN MODE - изменения не будут сохранены")

    classify_cash_transactions(args.department_id, args.dry_run)
