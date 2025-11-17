"""
Test Invoice to 1C Integration

Тестовый скрипт для проверки интеграции создания заявок на расход в 1С из счетов.

Usage:
    python scripts/test_invoice_to_1c.py --invoice-id 1 --department-id 1
    python scripts/test_invoice_to_1c.py --invoice-id 1 --validate-only
    python scripts/test_invoice_to_1c.py --test-connection
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import argparse
import logging
from typing import Optional
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import ProcessedInvoice, BudgetCategory, User, Department
from app.services.odata_1c_client import OData1CClient
from app.services.invoice_to_1c_converter import InvoiceTo1CConverter, InvoiceValidationError

# OData 1C settings
ODATA_1C_URL = os.getenv('ODATA_1C_URL', 'http://10.10.100.77/trade/odata/standard.odata')
ODATA_1C_USERNAME = os.getenv('ODATA_1C_USERNAME', 'odata.user')
ODATA_1C_PASSWORD = os.getenv('ODATA_1C_PASSWORD', 'ak228Hu2hbs28')

# Custom authorization token (from working curl example)
# TODO: Remove after testing, use regular username/password
CUSTOM_AUTH_TOKEN = "Basic 0KjQuNC60YPQvdC+0LLQlTohUUFaMndzeA=="

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_1c_connection() -> bool:
    """Test 1C OData connection"""
    logger.info("=" * 80)
    logger.info("TEST 1: 1C OData Connection")
    logger.info("=" * 80)

    try:
        client = OData1CClient(
            base_url=ODATA_1C_URL,
            custom_auth_token=CUSTOM_AUTH_TOKEN
        )

        logger.info(f"URL: {ODATA_1C_URL}")
        logger.info(f"Using custom auth token: {CUSTOM_AUTH_TOKEN[:20]}...")

        if client.test_connection():
            logger.info("✅ 1C connection successful")
            return True
        else:
            logger.error("❌ 1C connection failed")
            return False

    except Exception as e:
        logger.error(f"❌ Connection error: {e}", exc_info=True)
        return False


def test_contractor_search(inn: str) -> Optional[dict]:
    """Test contractor search by INN"""
    logger.info("=" * 80)
    logger.info(f"TEST 2: Search Contractor by INN: {inn}")
    logger.info("=" * 80)

    try:
        client = OData1CClient(
            base_url=ODATA_1C_URL,
            custom_auth_token=CUSTOM_AUTH_TOKEN
        )
        result = client.get_counterparty_by_inn(inn)

        if result:
            logger.info("✅ Contractor found:")
            logger.info(f"  Ref_Key: {result.get('Ref_Key')}")
            logger.info(f"  Description: {result.get('Description')}")
            logger.info(f"  ИНН: {result.get('ИНН')}")
            return result
        else:
            logger.warning(f"⚠️ Contractor with INN {inn} not found in 1C")
            return None

    except Exception as e:
        logger.error(f"❌ Error searching contractor: {e}", exc_info=True)
        return None


def test_organization_search(inn: str) -> Optional[dict]:
    """Test organization search by INN"""
    logger.info("=" * 80)
    logger.info(f"TEST 3: Search Organization by INN: {inn}")
    logger.info("=" * 80)

    try:
        client = OData1CClient(
            base_url=ODATA_1C_URL,
            custom_auth_token=CUSTOM_AUTH_TOKEN
        )
        result = client.get_organization_by_inn(inn)

        if result:
            logger.info("✅ Organization found:")
            logger.info(f"  Ref_Key: {result.get('Ref_Key')}")
            logger.info(f"  Description: {result.get('Description')}")
            logger.info(f"  ИНН: {result.get('ИНН')}")
            return result
        else:
            logger.warning(f"⚠️ Organization with INN {inn} not found in 1C")
            return None

    except Exception as e:
        logger.error(f"❌ Error searching organization: {e}", exc_info=True)
        return None


def test_category_sync(db: Session, department_id: int) -> bool:
    """Test if budget categories are synced with 1C"""
    logger.info("=" * 80)
    logger.info("TEST 4: Check Budget Categories Sync")
    logger.info("=" * 80)

    try:
        # Check categories with external_id_1c
        synced_categories = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == department_id,
            BudgetCategory.external_id_1c.isnot(None),
            BudgetCategory.is_active == True,
            BudgetCategory.is_folder == False
        ).all()

        if synced_categories:
            logger.info(f"✅ Found {len(synced_categories)} synced categories:")
            for cat in synced_categories[:5]:  # Show first 5
                logger.info(f"  - {cat.name} (external_id_1c: {cat.external_id_1c[:20]}...)")
            if len(synced_categories) > 5:
                logger.info(f"  ... and {len(synced_categories) - 5} more")
            return True
        else:
            logger.error("❌ No synced categories found!")
            logger.error("Run: POST /api/v1/sync-1c/categories/sync to sync categories")
            return False

    except Exception as e:
        logger.error(f"❌ Error checking categories: {e}", exc_info=True)
        return False


def test_invoice_validation(db: Session, invoice_id: int) -> bool:
    """Test invoice validation"""
    logger.info("=" * 80)
    logger.info(f"TEST 5: Validate Invoice #{invoice_id}")
    logger.info("=" * 80)

    try:
        # Get invoice
        invoice = db.query(ProcessedInvoice).filter_by(id=invoice_id).first()

        if not invoice:
            logger.error(f"❌ Invoice #{invoice_id} not found")
            return False

        logger.info(f"Invoice: {invoice.invoice_number or 'N/A'}")
        logger.info(f"Date: {invoice.invoice_date or 'N/A'}")
        logger.info(f"Amount: {invoice.total_amount or 'N/A'}")
        logger.info(f"Supplier: {invoice.supplier_name or 'N/A'}")
        logger.info(f"Supplier INN: {invoice.supplier_inn or 'N/A'}")
        logger.info(f"Category ID: {invoice.category_id or 'NOT SET'}")

        # Create converter
        client = OData1CClient(
            base_url=ODATA_1C_URL,
            custom_auth_token=CUSTOM_AUTH_TOKEN
        )
        converter = InvoiceTo1CConverter(db=db, odata_client=client)

        # Validate
        result = converter.validate_invoice_for_1c(invoice)

        logger.info("\n" + "=" * 40)
        logger.info("VALIDATION RESULT:")
        logger.info("=" * 40)

        if result.is_valid:
            logger.info("✅ Validation PASSED")
        else:
            logger.error("❌ Validation FAILED")

        if result.errors:
            logger.error("\nErrors:")
            for error in result.errors:
                logger.error(f"  ❌ {error}")

        if result.warnings:
            logger.warning("\nWarnings:")
            for warning in result.warnings:
                logger.warning(f"  ⚠️ {warning}")

        if result.counterparty_guid:
            logger.info(f"\n✅ Counterparty: {result.counterparty_name}")
            logger.info(f"   GUID: {result.counterparty_guid}")

        if result.organization_guid:
            logger.info(f"\n✅ Organization: {result.organization_name}")
            logger.info(f"   GUID: {result.organization_guid}")

        if result.cash_flow_category_guid:
            logger.info(f"\n✅ Cash Flow Category: {result.cash_flow_category_name}")
            logger.info(f"   GUID: {result.cash_flow_category_guid}")

        return result.is_valid

    except Exception as e:
        logger.error(f"❌ Validation error: {e}", exc_info=True)
        return False


def test_invoice_creation(db: Session, invoice_id: int, upload_attachment: bool = True) -> bool:
    """Test creating expense request in 1C"""
    logger.info("=" * 80)
    logger.info(f"TEST 6: Create Expense Request in 1C for Invoice #{invoice_id}")
    logger.info("=" * 80)

    try:
        # Get invoice
        invoice = db.query(ProcessedInvoice).filter_by(id=invoice_id).first()

        if not invoice:
            logger.error(f"❌ Invoice #{invoice_id} not found")
            return False

        # Check if already created
        if invoice.external_id_1c:
            logger.warning(f"⚠️ Invoice already has external_id_1c: {invoice.external_id_1c}")
            logger.warning("Skipping creation to avoid duplicate")
            return False

        # Create converter
        client = OData1CClient(
            base_url=ODATA_1C_URL,
            custom_auth_token=CUSTOM_AUTH_TOKEN
        )
        converter = InvoiceTo1CConverter(db=db, odata_client=client)

        # Create expense request
        logger.info("Creating expense request in 1C...")
        ref_key = converter.create_expense_request_in_1c(
            invoice=invoice,
            upload_attachment=upload_attachment
        )

        logger.info("\n" + "=" * 40)
        logger.info("✅ EXPENSE REQUEST CREATED!")
        logger.info("=" * 40)
        logger.info(f"Ref_Key (GUID): {ref_key}")
        logger.info(f"Invoice #{invoice.id} updated with external_id_1c")

        if upload_attachment:
            logger.info(f"File uploaded: {invoice.file_name or 'N/A'}")

        return True

    except InvoiceValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Creation error: {e}", exc_info=True)
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Invoice to 1C Integration')
    parser.add_argument('--invoice-id', type=int, help='Invoice ID to test')
    parser.add_argument('--department-id', type=int, default=1, help='Department ID (default: 1)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, do not create')
    parser.add_argument('--test-connection', action='store_true', help='Only test 1C connection')
    parser.add_argument('--no-attachment', action='store_true', help='Do not upload attachment')
    parser.add_argument('--test-inn', help='Test search by INN (format: supplier_inn/buyer_inn)')

    args = parser.parse_args()

    db = SessionLocal()

    try:
        # Test 1: Connection
        logger.info("\n")
        if not test_1c_connection():
            logger.error("❌ Cannot proceed without 1C connection")
            return 1

        # Test 2-3: INN search (if provided)
        if args.test_inn:
            logger.info("\n")
            if '/' in args.test_inn:
                supplier_inn, buyer_inn = args.test_inn.split('/')
                test_contractor_search(supplier_inn)
                logger.info("\n")
                test_organization_search(buyer_inn)
            else:
                test_contractor_search(args.test_inn)

        # Exit if only connection test
        if args.test_connection:
            return 0

        # Test 4: Category sync
        logger.info("\n")
        if not test_category_sync(db, args.department_id):
            logger.error("❌ Categories not synced. Please sync first.")
            return 1

        # Test 5-6: Invoice validation and creation
        if args.invoice_id:
            logger.info("\n")
            if not test_invoice_validation(db, args.invoice_id):
                logger.error("❌ Validation failed. Fix errors before creating.")
                return 1

            if not args.validate_only:
                logger.info("\n")
                upload_attachment = not args.no_attachment
                if test_invoice_creation(db, args.invoice_id, upload_attachment):
                    logger.info("\n✅ ALL TESTS PASSED!")
                    return 0
                else:
                    logger.error("\n❌ CREATION FAILED")
                    return 1
            else:
                logger.info("\n✅ VALIDATION PASSED (skipping creation)")
                return 0
        else:
            logger.info("\n✅ CONNECTION AND SYNC TESTS PASSED")
            logger.info("Use --invoice-id to test specific invoice")
            return 0

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
