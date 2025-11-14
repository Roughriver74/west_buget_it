"""
Скрипт для удаления всех банковских транзакций (soft delete - is_active=False)
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import BankTransaction
from datetime import datetime


def delete_all_bank_transactions():
    """Удалить все банковские транзакции (soft delete)"""
    db = SessionLocal()
    try:
        # Получить все активные транзакции
        transactions = db.query(BankTransaction).filter(
            BankTransaction.is_active == True
        ).all()

        count = len(transactions)

        if count == 0:
            print("✅ Транзакций для удаления не найдено.")
            return

        print(f"⚠️  Найдено {count} активных транзакций.")
        print(f"🗑️  Удаление всех транзакций...")

        # Soft delete - устанавливаем is_active=False
        for tx in transactions:
            tx.is_active = False
            tx.updated_at = datetime.utcnow()

        db.commit()

        print(f"✅ Успешно удалено {count} транзакций (soft delete).")
        print(f"   Транзакции помечены как is_active=False и скрыты из UI.")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при удалении транзакций: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("УДАЛЕНИЕ ВСЕХ БАНКОВСКИХ ТРАНЗАКЦИЙ")
    print("=" * 60)

    # Запросить подтверждение
    confirm = input("\n⚠️  Вы уверены, что хотите удалить ВСЕ банковские транзакции? (yes/no): ")

    if confirm.lower() in ['yes', 'y', 'да']:
        delete_all_bank_transactions()
    else:
        print("❌ Операция отменена.")
