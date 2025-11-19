#!/usr/bin/env python
"""
Миграция данных кредитного портфеля из legacy БД (acme_fin_dwh) в текущую схему fin_*.

Использование:
    poetry run python backend/scripts/migrate_credit_portfolio.py \
        --legacy-url postgresql://user:pass@localhost:25432/acme_fin_dwh \
        --department-id 8

По умолчанию берет цель из настроек приложения (SessionLocal), а источник — из
переменной LEGACY_DATABASE_URL. Скрипт идемпотентен: повторный запуск обновит
существующие записи без дублей.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

debug_env = os.getenv("DEBUG")
if debug_env and debug_env.lower() not in ("true", "false", "1", "0", "yes", "no"):
    os.environ["DEBUG"] = "false"

from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import (
    FinBankAccount,
    FinContract,
    FinExpense,
    FinExpenseDetail,
    FinImportLog,
    FinOrganization,
    FinReceipt,
)
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

LEGACY_TABLES = [
    "organizations",
    "bank_accounts",
    "contracts",
    "receipts",
    "expenses",
    "expense_details",
    "import_logs",
]

DEFAULT_DEPARTMENT_ID = 8


@dataclass
class MigrationCounters:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    def __str__(self) -> str:
        return f"inserted={self.inserted}, updated={self.updated}, skipped={self.skipped}"


def load_source_tables(engine: Engine) -> Dict[str, Table]:
    metadata = MetaData()
    tables = {}
    for name in LEGACY_TABLES:
        tables[name] = Table(name, metadata, autoload_with=engine)
    return tables


def migrate_credit_portfolio(legacy_url: str, department_id: int) -> None:
    logger.info("Starting migration from legacy DB: %s", legacy_url)
    legacy_engine = create_engine(legacy_url)
    legacy_tables = load_source_tables(legacy_engine)

    org_id_map: Dict[int, int] = {}
    bank_id_map: Dict[int, int] = {}
    contract_id_map: Dict[int, int] = {}

    with legacy_engine.connect() as source_conn, SessionLocal() as target_session:
        migrate_organizations(
            source_conn, target_session, legacy_tables["organizations"], department_id, org_id_map
        )
        migrate_bank_accounts(
            source_conn,
            target_session,
            legacy_tables["bank_accounts"],
            department_id,
            org_id_map,
            bank_id_map,
        )
        migrate_contracts(
            source_conn,
            target_session,
            legacy_tables["contracts"],
            department_id,
            org_id_map,
            contract_id_map,
        )
        migrate_receipts(
            source_conn,
            target_session,
            legacy_tables["receipts"],
            department_id,
            org_id_map,
            bank_id_map,
            contract_id_map,
        )
        migrate_expenses(
            source_conn,
            target_session,
            legacy_tables["expenses"],
            department_id,
            org_id_map,
            bank_id_map,
            contract_id_map,
        )
        migrate_expense_details(
            source_conn,
            target_session,
            legacy_tables["expense_details"],
            department_id,
        )
        migrate_import_logs(
            source_conn,
            target_session,
            legacy_tables["import_logs"],
            department_id,
        )

    logger.info("Migration completed successfully")


def migrate_organizations(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
    org_id_map: Dict[int, int],
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {
            "name": row["name"],
            "department_id": department_id,
        }
        defaults = {
            "inn": row.get("inn"),
            "is_active": bool_or_default(row.get("is_active"), True),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        org = upsert(target_session, FinOrganization, filters, defaults, counters)
        org_id_map[row["id"]] = org.id

    target_session.commit()
    logger.info("Organizations: %s", counters)


def migrate_bank_accounts(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
    org_id_map: Dict[int, int],
    bank_id_map: Dict[int, int],
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {
            "account_number": row["account_number"],
            "department_id": department_id,
        }
        organization_id = org_id_map.get(row.get("organization_id"))
        defaults = {
            "bank_name": row.get("bank_name"),
            "organization_id": organization_id,
            "is_active": bool_or_default(row.get("is_active"), True),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        bank = upsert(target_session, FinBankAccount, filters, defaults, counters)
        bank_id_map[row["id"]] = bank.id

    target_session.commit()
    logger.info("Bank accounts: %s", counters)


def migrate_contracts(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
    org_id_map: Dict[int, int],
    contract_id_map: Dict[int, int],
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {
            "contract_number": row["contract_number"],
            "department_id": department_id,
        }
        defaults = {
            "contract_date": row.get("contract_date"),
            "contract_type": row.get("contract_type"),
            "counterparty": row.get("counterparty"),
            "organization_id": org_id_map.get(row.get("organization_id")),
            "is_active": bool_or_default(row.get("is_active"), True),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        contract = upsert(target_session, FinContract, filters, defaults, counters)
        contract_id_map[row["id"]] = contract.id

    target_session.commit()
    logger.info("Contracts: %s", counters)


def migrate_receipts(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
    org_id_map: Dict[int, int],
    bank_id_map: Dict[int, int],
    contract_id_map: Dict[int, int],
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {"operation_id": row["operation_id"], "department_id": department_id}
        organization_id = org_id_map.get(row.get("organization_id"))
        if organization_id is None:
            counters.skipped += 1
            logger.warning("Skip receipt %s: organization not found", row["operation_id"])
            continue
        defaults = {
            "department_id": department_id,
            "organization_id": organization_id,
            "bank_account_id": bank_id_map.get(row.get("bank_account_id")),
            "contract_id": contract_id_map.get(row.get("contract_id")),
            "operation_type": row.get("operation_type"),
            "accounting_account": row.get("accounting_account"),
            "document_number": row.get("document_number"),
            "document_date": row.get("document_date"),
            "payer": row.get("payer"),
            "payer_account": row.get("payer_account"),
            "settlement_account": row.get("settlement_account"),
            "contract_date": row.get("contract_date"),
            "currency": row.get("currency"),
            "amount": row.get("amount"),
            "commission": row.get("commission"),
            "payment_purpose": row.get("payment_purpose"),
            "responsible_person": row.get("responsible_person"),
            "comment": row.get("comment"),
            "is_active": True,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        upsert(target_session, FinReceipt, filters, defaults, counters)

    target_session.commit()
    logger.info("Receipts: %s", counters)


def migrate_expenses(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
    org_id_map: Dict[int, int],
    bank_id_map: Dict[int, int],
    contract_id_map: Dict[int, int],
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {"operation_id": row["operation_id"], "department_id": department_id}
        organization_id = org_id_map.get(row.get("organization_id"))
        if organization_id is None:
            counters.skipped += 1
            logger.warning("Skip expense %s: organization not found", row["operation_id"])
            continue
        defaults = {
            "department_id": department_id,
            "organization_id": organization_id,
            "bank_account_id": bank_id_map.get(row.get("bank_account_id")),
            "contract_id": contract_id_map.get(row.get("contract_id")),
            "operation_type": row.get("operation_type"),
            "accounting_account": row.get("accounting_account"),
            "document_number": row.get("document_number"),
            "document_date": row.get("document_date"),
            "recipient": row.get("recipient"),
            "recipient_account": row.get("recipient_account"),
            "debit_account": row.get("debit_account"),
            "contract_date": row.get("contract_date"),
            "currency": row.get("currency"),
            "amount": row.get("amount"),
            "expense_article": row.get("expense_article"),
            "payment_purpose": row.get("payment_purpose"),
            "responsible_person": row.get("responsible_person"),
            "comment": row.get("comment"),
            "tax_period": row.get("tax_period"),
            "unconfirmed_by_bank": bool_or_default(row.get("unconfirmed_by_bank"), False),
            "is_active": True,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        upsert(target_session, FinExpense, filters, defaults, counters)

    target_session.commit()
    logger.info("Expenses: %s", counters)


def migrate_expense_details(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {
            "expense_operation_id": row["expense_operation_id"],
            "department_id": department_id,
            "payment_type": row.get("payment_type"),
            "settlement_account": row.get("settlement_account"),
            "payment_amount": row.get("payment_amount"),
        }
        defaults = {
            "contract_number": row.get("contract_number"),
            "repayment_type": row.get("repayment_type"),
            "advance_account": row.get("advance_account"),
            "settlement_rate": row.get("settlement_rate"),
            "settlement_amount": row.get("settlement_amount"),
            "vat_amount": row.get("vat_amount"),
            "expense_amount": row.get("expense_amount"),
            "vat_in_expense": row.get("vat_in_expense"),
            "created_at": row.get("created_at"),
        }
        upsert(target_session, FinExpenseDetail, filters, defaults, counters)

    target_session.commit()
    logger.info("Expense details: %s", counters)


def migrate_import_logs(
    source_conn,
    target_session: Session,
    table: Table,
    department_id: int,
) -> None:
    counters = MigrationCounters()
    rows = source_conn.execute(select(table)).mappings()
    for row in rows:
        filters = {
            "department_id": department_id,
            "import_date": row.get("import_date"),
            "source_file": row.get("source_file"),
            "table_name": row.get("table_name"),
        }
        defaults = {
            "rows_inserted": row.get("rows_inserted", 0),
            "rows_updated": row.get("rows_updated", 0),
            "rows_failed": row.get("rows_failed", 0),
            "status": row.get("status"),
            "error_message": row.get("error_message"),
            "processed_by": row.get("processed_by"),
            "processing_time_seconds": row.get("processing_time_seconds"),
        }
        upsert(target_session, FinImportLog, filters, defaults, counters)

    target_session.commit()
    logger.info("Import logs: %s", counters)


def upsert(session: Session, model, filters: dict, defaults: dict, counters: MigrationCounters):
    instance = session.query(model).filter_by(**filters).one_or_none()
    if instance:
        for key, value in defaults.items():
            setattr(instance, key, value)
        counters.updated += 1
    else:
        params = {**filters, **defaults}
        instance = model(**params)
        session.add(instance)
        session.flush()
        counters.inserted += 1
    return instance


def bool_or_default(value: Optional[bool], default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "t", "1", "yes")
    return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Миграция данных кредитного портфеля из legacy БД.")
    parser.add_argument(
        "--legacy-url",
        default=os.getenv("LEGACY_DATABASE_URL"),
        help="Строка подключения к legacy БД (postgresql://user:pass@host:port/dbname)",
    )
    parser.add_argument(
        "--department-id",
        type=int,
        default=DEFAULT_DEPARTMENT_ID,
        help="ID отдела, к которому будут привязаны данные (default: 8)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Уровень логирования",
    )
    args = parser.parse_args()
    if not args.legacy_url:
        parser.error("Необходимо указать LEGACY_DATABASE_URL или параметр --legacy-url")
    return args


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s %(message)s")
    migrate_credit_portfolio(args.legacy_url, args.department_id)


if __name__ == "__main__":
    main()

