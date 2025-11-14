"""
Data importer with UPSERT logic for loading credit portfolio XLSX data into PostgreSQL
Адаптировано для west_buget_it из west_fin с поддержкой multi-tenancy
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path
import time

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import (
    FinOrganization,
    FinBankAccount,
    FinContract,
    FinReceipt,
    FinExpense,
    FinExpenseDetail,
    FinImportLog
)
from app.services.credit_portfolio_parser import CreditPortfolioParser

logger = logging.getLogger(__name__)


class CreditPortfolioImporter:
    """Importer for credit portfolio data with UPSERT capabilities and multi-tenancy support"""

    def __init__(self, db_session: Session, department_id: int):
        """
        Initialize importer

        Args:
            db_session: Database session
            department_id: Department ID for multi-tenancy isolation
        """
        self.db = db_session
        self.department_id = department_id
        self.parser = CreditPortfolioParser()

        # Cache for reference data to avoid repeated DB queries
        self._org_cache = {}
        self._bank_cache = {}
        self._contract_cache = {}

    def get_or_create_organization(self, org_name: str) -> int:
        """Get or create organization and return its ID"""
        if not org_name:
            return None

        cache_key = f"{org_name}_{self.department_id}"
        if cache_key in self._org_cache:
            return self._org_cache[cache_key]

        org = (
            self.db.query(FinOrganization)
            .filter(
                FinOrganization.name == org_name,
                FinOrganization.department_id == self.department_id
            )
            .first()
        )

        if not org:
            org = FinOrganization(
                name=org_name,
                department_id=self.department_id,
                is_active=True
            )
            self.db.add(org)
            self.db.flush()
            logger.info(f"✓ Created new organization: {org_name} (dept_id={self.department_id})")

        self._org_cache[cache_key] = org.id
        return org.id

    def get_or_create_bank_account(self, account_number: str, org_name: str = None) -> int:
        """Get or create bank account and return its ID"""
        if not account_number:
            return None

        cache_key = f"{account_number}_{self.department_id}"
        if cache_key in self._bank_cache:
            return self._bank_cache[cache_key]

        bank = (
            self.db.query(FinBankAccount)
            .filter(
                FinBankAccount.account_number == account_number,
                FinBankAccount.department_id == self.department_id
            )
            .first()
        )

        if not bank:
            bank = FinBankAccount(
                account_number=account_number,
                department_id=self.department_id,
                is_active=True
            )
            self.db.add(bank)
            self.db.flush()
            logger.info(f"✓ Created new bank account: {account_number} (dept_id={self.department_id})")

        self._bank_cache[cache_key] = bank.id
        return bank.id

    def get_or_create_contract(
        self,
        contract_number: str,
        contract_date: datetime = None,
        org_name: str = None
    ) -> int:
        """Get or create contract and return its ID"""
        if not contract_number:
            return None

        cache_key = f"{contract_number}_{self.department_id}"
        if cache_key in self._contract_cache:
            return self._contract_cache[cache_key]

        contract = (
            self.db.query(FinContract)
            .filter(
                FinContract.contract_number == contract_number,
                FinContract.department_id == self.department_id
            )
            .first()
        )

        if not contract:
            # Try to get organization ID if org_name provided
            org_id = None
            if org_name:
                org_id = self.get_or_create_organization(org_name)

            contract = FinContract(
                contract_number=contract_number,
                contract_date=contract_date,
                organization_id=org_id,
                department_id=self.department_id,
                is_active=True
            )
            self.db.add(contract)
            self.db.flush()
            logger.info(f"✓ Created new contract: {contract_number} (dept_id={self.department_id})")

        self._contract_cache[cache_key] = contract.id
        return contract.id

    def upsert_receipts(self, records: List[Dict]) -> Tuple[int, int, int]:
        """
        Insert or update receipt records
        Auto-creates organizations, bank accounts, and contracts if they don't exist

        Args:
            records: List of receipt dictionaries

        Returns:
            Tuple[int, int, int]: (inserted, updated, failed)
        """
        inserted = 0
        updated = 0
        failed = 0

        for record in records:
            try:
                # Add department_id
                record['department_id'] = self.department_id

                # Auto-create organization, bank account, and contract; populate foreign keys
                org_name = record.get('organization')
                bank_account = record.get('bank_account')
                contract_number = record.get('contract_number')
                contract_date = record.get('contract_date')

                if org_name:
                    record['organization_id'] = self.get_or_create_organization(org_name)

                if bank_account:
                    record['bank_account_id'] = self.get_or_create_bank_account(bank_account, org_name)

                if contract_number:
                    record['contract_id'] = self.get_or_create_contract(
                        contract_number,
                        contract_date,
                        org_name
                    )

                # Remove denormalized fields (use FK only)
                record.pop('organization', None)
                record.pop('bank_account', None)
                record.pop('contract_number', None)

                stmt = insert(FinReceipt).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['operation_id', 'department_id'],
                    set_={
                        key: value
                        for key, value in record.items()
                        if key not in ['operation_id', 'department_id']
                    }
                )

                result = self.db.execute(stmt)

                if result.rowcount > 0:
                    inserted += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error upserting receipt {record.get('operation_id')}: {e}")
                failed += 1

        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing receipts: {e}")
            self.db.rollback()
            return 0, 0, len(records)

        logger.info(f"Receipts: {inserted} inserted, {updated} updated, {failed} failed")
        return inserted, updated, failed

    def upsert_expenses(self, records: List[Dict]) -> Tuple[int, int, int]:
        """
        Insert or update expense records
        Auto-creates organizations, bank accounts, and contracts if they don't exist

        Args:
            records: List of expense dictionaries

        Returns:
            Tuple[int, int, int]: (inserted, updated, failed)
        """
        inserted = 0
        updated = 0
        failed = 0

        for record in records:
            try:
                # Add department_id
                record['department_id'] = self.department_id

                # Auto-create organization, bank account, and contract; populate foreign keys
                org_name = record.get('organization')
                bank_account = record.get('bank_account')
                contract_number = record.get('contract_number')
                contract_date = record.get('contract_date')

                if org_name:
                    record['organization_id'] = self.get_or_create_organization(org_name)

                if bank_account:
                    record['bank_account_id'] = self.get_or_create_bank_account(bank_account, org_name)

                if contract_number:
                    record['contract_id'] = self.get_or_create_contract(contract_number, contract_date, org_name)

                # Remove denormalized fields (use FK only)
                record.pop('organization', None)
                record.pop('bank_account', None)
                record.pop('contract_number', None)

                stmt = insert(FinExpense).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['operation_id', 'department_id'],
                    set_={
                        key: value
                        for key, value in record.items()
                        if key not in ['operation_id', 'department_id']
                    }
                )

                result = self.db.execute(stmt)

                if result.rowcount > 0:
                    inserted += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error upserting expense {record.get('operation_id')}: {e}")
                failed += 1

        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing expenses: {e}")
            self.db.rollback()
            return 0, 0, len(records)

        logger.info(f"Expenses: {inserted} inserted, {updated} updated, {failed} failed")
        return inserted, updated, failed

    def insert_expense_details(self, records: List[Dict], source_file: str = None) -> Tuple[int, int]:
        """
        Insert expense detail records

        Args:
            records: List of expense detail dictionaries
            source_file: Optional source file name for error reporting

        Returns:
            Tuple[int, int]: (inserted, failed)
        """
        inserted = 0
        failed = 0
        skipped = 0
        missing_ids = []

        # Get all existing expense operation IDs for validation (within department)
        existing_expense_ids = set(
            row[0]
            for row in self.db.query(FinExpense.operation_id)
            .filter(FinExpense.department_id == self.department_id)
            .all()
        )

        for record in records:
            # Add department_id
            record['department_id'] = self.department_id

            # Check if referenced expense exists
            expense_op_id = record.get('expense_operation_id')
            if expense_op_id not in existing_expense_ids:
                logger.warning(
                    f"Skipping detail: expense_operation_id '{expense_op_id}' "
                    f"not found in expenses table (dept_id={self.department_id})"
                )
                missing_ids.append(expense_op_id)
                skipped += 1
                failed += 1
                continue

            try:
                # Simple insert for expense details
                detail = FinExpenseDetail(**record)
                self.db.add(detail)
                inserted += 1

            except Exception as e:
                logger.error(
                    f"Error inserting detail for "
                    f"{record.get('expense_operation_id')}: {e}"
                )
                failed += 1

        try:
            self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing expense details: {e}")
            self.db.rollback()
            return 0, len(records)

        logger.info(
            f"Expense details: {inserted} inserted, {failed} failed "
            f"({skipped} skipped due to missing expense records)"
        )
        return inserted, failed

    def log_import(
        self,
        source_file: str,
        table_name: str,
        rows_inserted: int,
        rows_updated: int,
        rows_failed: int,
        status: str,
        error_message: str = None,
        processing_time: float = 0.0
    ):
        """Log import operation to database"""
        try:
            log = FinImportLog(
                source_file=source_file,
                table_name=table_name,
                rows_inserted=rows_inserted,
                rows_updated=rows_updated,
                rows_failed=rows_failed,
                status=status,
                error_message=error_message,
                processed_by="auto_importer",
                processing_time_seconds=round(processing_time, 2),
                department_id=self.department_id
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging import: {e}")
            self.db.rollback()

    def import_file(self, file_path: str) -> bool:
        """
        Import a single XLSX file

        Args:
            file_path: Path to XLSX file

        Returns:
            bool: True if import successful, False otherwise
        """
        filename = Path(file_path).name
        start_time = time.time()

        logger.info(f"Starting import of: {filename} (dept_id={self.department_id})")

        try:
            # Parse file
            file_type, records = self.parser.parse_file(file_path)

            if file_type is None or not records:
                logger.warning(f"No records parsed from {filename}")
                self.log_import(
                    filename, "unknown", 0, 0, 0,
                    "failed", "No records parsed",
                    time.time() - start_time
                )
                return False

            # Import based on file type
            if file_type == "receipt":
                inserted, updated, failed = self.upsert_receipts(records)
                table_name = "fin_receipts"

            elif file_type == "expense":
                inserted, updated, failed = self.upsert_expenses(records)
                table_name = "fin_expenses"

            elif file_type == "detail":
                inserted, failed = self.insert_expense_details(records, source_file=filename)
                updated = 0
                table_name = "fin_expense_details"

            else:
                logger.error(f"Unknown file type: {file_type}")
                return False

            # Determine status
            if failed == 0:
                status = "success"
            elif inserted + updated > 0:
                status = "partial"
            else:
                status = "failed"

            # Log import
            self.log_import(
                filename, table_name,
                inserted, updated, failed,
                status, None,
                time.time() - start_time
            )

            logger.info(
                f"✓ Import completed: {filename} "
                f"({inserted} inserted, {updated} updated, {failed} failed)"
            )

            return status in ["success", "partial"]

        except Exception as e:
            logger.error(f"Error importing {filename}: {e}")
            self.log_import(
                filename, "unknown", 0, 0, 0,
                "failed", str(e),
                time.time() - start_time
            )
            return False

    def import_files(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Import multiple XLSX files

        Args:
            file_paths: List of file paths

        Returns:
            Dict[str, int]: Summary of import results
        """
        summary = {
            "total": len(file_paths),
            "success": 0,
            "failed": 0
        }

        for file_path in file_paths:
            if self.import_file(file_path):
                summary["success"] += 1
            else:
                summary["failed"] += 1

        logger.info(
            f"Import summary: {summary['success']}/{summary['total']} files imported "
            f"(dept_id={self.department_id})"
        )

        return summary
