"""
Create Test Invoice for 1C Integration Testing

Создает тестовый invoice с данными контрагента, найденного в 1С
"""

import sys
import os
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from datetime import date, datetime
from decimal import Decimal

from app.db.session import SessionLocal
from app.db.models import ProcessedInvoice, User, Department

def create_test_invoice():
    """Создать тестовый invoice для проверки интеграции с 1С"""

    db = SessionLocal()

    try:
        # Get first user and department
        user = db.query(User).filter_by(is_active=True).first()
        dept = db.query(Department).filter_by(is_active=True).first()

        if not user or not dept:
            print("❌ Не найден активный пользователь или отдел")
            return None

        # Данные контрагента, найденного в 1С (ТРАСТ ТЕЛЕКОМ ООО)
        test_invoice = ProcessedInvoice(
            department_id=dept.id,

            # Файл (фиктивный)
            original_filename="test_invoice_trust_telecom.pdf",
            file_path="/tmp/test_invoice.pdf",
            file_size_kb=150,
            uploaded_by=user.id,
            uploaded_at=datetime.utcnow(),

            # OCR результаты
            ocr_text="Счет №ТТ-2025-001 от 31.10.2025\nТРАСТ ТЕЛЕКОМ ООО\nИНН: 7734640247...",
            ocr_confidence=Decimal("95.5"),

            # Распознанные данные счета
            invoice_number="ТТ-2025-001",
            invoice_date=date(2025, 10, 31),

            # Поставщик (ТРАСТ ТЕЛЕКОМ ООО - найден в 1С!)
            supplier_name="ТРАСТ ТЕЛЕКОМ ООО",
            supplier_inn="7734640247",
            supplier_kpp="773401001",
            supplier_bank_name="СБЕРБАНК",
            supplier_bik="044525225",
            supplier_account="40702810100000123456",

            # Суммы
            amount_without_vat=Decimal("1694.92"),
            vat_amount=Decimal("305.08"),
            total_amount=Decimal("2000.00"),

            # Назначение платежа
            payment_purpose="Оплата услуг связи за октябрь 2025 г. по счету №ТТ-2025-001",

            # Статус
            status="PROCESSED",
            processed_at=datetime.utcnow(),

            # Parsed data (JSON)
            parsed_data={
                "invoice_number": "ТТ-2025-001",
                "invoice_date": "2025-10-31",
                "supplier": {
                    "name": "ТРАСТ ТЕЛЕКОМ ООО",
                    "inn": "7734640247",
                    "kpp": "773401001"
                },
                "buyer": {
                    "name": "ВЕСТ ГРУПП ООО",
                    "inn": "7727563778",  # Этой организации нет в 1С (тестовый ИНН)
                    "kpp": "772701001"
                },
                "total_amount": 2000.00,
                "vat_amount": 305.08,
                "amount_without_vat": 1694.92,
                "items": [
                    {
                        "description": "Услуги связи интернет",
                        "quantity": 1,
                        "unit": "месяц",
                        "price": 2000.00,
                        "amount": 2000.00
                    }
                ]
            },

            # AI metadata
            ai_model_used="gpt-4o-mini",
            ai_processing_time_sec=Decimal("2.5"),

            # Category NOT SET (будем устанавливать через API)
            category_id=None,

            is_active=True
        )

        db.add(test_invoice)
        db.commit()
        db.refresh(test_invoice)

        print("=" * 80)
        print("✅ Тестовый invoice создан успешно!")
        print("=" * 80)
        print(f"ID: {test_invoice.id}")
        print(f"Number: {test_invoice.invoice_number}")
        print(f"Date: {test_invoice.invoice_date}")
        print(f"Supplier: {test_invoice.supplier_name}")
        print(f"Supplier INN: {test_invoice.supplier_inn}")
        print(f"Amount: {test_invoice.total_amount}")
        print(f"Payment Purpose: {test_invoice.payment_purpose}")
        print(f"Category: {test_invoice.category_id or 'NOT SET (нужно установить!)'}")
        print("=" * 80)
        print(f"\nТеперь можно запустить:")
        print(f"  python scripts/test_invoice_to_1c.py --invoice-id {test_invoice.id} --validate-only")

        return test_invoice.id

    except Exception as e:
        print(f"❌ Ошибка при создании invoice: {e}")
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    create_test_invoice()
