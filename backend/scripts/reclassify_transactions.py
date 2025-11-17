#!/usr/bin/env python
"""
Скрипт для повторной классификации банковских транзакций
с использованием business operation mappings
"""
import sys
import os
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BankTransaction, BusinessOperationMapping, BankTransactionStatusEnum
from app.services.transaction_classifier import TransactionClassifier


def reclassify_transactions(department_id: int, dry_run: bool = False):
    """
    Повторная классификация транзакций с использованием business operation mappings

    Args:
        department_id: ID отдела
        dry_run: Если True, только показываем что будет изменено, но не сохраняем
    """
    db = SessionLocal()
    try:
        # Получаем все транзакции без категорий или со статусом NEW/NEEDS_REVIEW
        query = db.query(BankTransaction).filter(
            BankTransaction.department_id == department_id,
            BankTransaction.business_operation.isnot(None),  # Есть business_operation
            BankTransaction.business_operation != '',
        ).filter(
            (BankTransaction.category_id.is_(None)) |  # Нет категории
            (BankTransaction.status.in_([
                BankTransactionStatusEnum.NEW,
                BankTransactionStatusEnum.NEEDS_REVIEW
            ]))
        )

        transactions = query.all()
        total_count = len(transactions)

        print(f"\n=== Найдено транзакций для классификации: {total_count} ===\n")

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
            print(f"[{i}/{total_count}] ID: {transaction.id}, Operation: {transaction.business_operation}")

            try:
                # Классифицируем
                category_id, confidence, reasoning = classifier.classify(
                    payment_purpose=transaction.payment_purpose or "",
                    counterparty_name=transaction.counterparty_name,
                    counterparty_inn=transaction.counterparty_inn,
                    amount=transaction.amount,
                    department_id=department_id,
                    transaction_type=transaction.transaction_type.value if transaction.transaction_type else None,
                    business_operation=transaction.business_operation
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
                            categorized_count += 1
                        else:
                            transaction.status = BankTransactionStatusEnum.NEEDS_REVIEW
                            transaction.suggested_category_id = category_id
                            print(f"   ⚠️  Предложена категория {category_id} (confidence: {confidence:.2%}) → NEEDS_REVIEW")
                            needs_review_count += 1
                    else:
                        print(f"   [DRY RUN] Категория {category_id} (confidence: {confidence:.2%})")
                        if confidence >= 0.9:
                            categorized_count += 1
                        else:
                            needs_review_count += 1
                else:
                    print(f"   ❌ Не удалось найти категорию")
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

    parser = argparse.ArgumentParser(description='Re-classify bank transactions using business operation mappings')
    parser.add_argument('--department-id', type=int, required=True, help='Department ID')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (do not save changes)')

    args = parser.parse_args()

    print(f"=== Повторная классификация транзакций для department_id={args.department_id} ===")
    if args.dry_run:
        print("⚠️  DRY RUN MODE - изменения не будут сохранены")

    reclassify_transactions(args.department_id, args.dry_run)
