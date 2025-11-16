"""
Script to clean and reset credit portfolio data for a specific department.
Usage: python scripts/clean_credit_data.py --department-id 8
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
import argparse


def clean_credit_data(department_id: int, dry_run: bool = False):
    """Clean all credit portfolio data for specified department"""

    engine = create_engine(str(settings.DATABASE_URL))

    tables = [
        'fin_expense_details',  # Delete first (has FK to fin_expenses)
        'fin_expenses',
        'fin_receipts',
        'fin_contracts',
        'fin_bank_accounts',
        'fin_organizations',
        'fin_import_logs'
    ]

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            print(f"\n{'DRY RUN - ' if dry_run else ''}Cleaning credit portfolio data for department {department_id}...\n")

            total_deleted = 0

            for table in tables:
                # Count records
                count_query = text(f"SELECT COUNT(*) FROM {table} WHERE department_id = :dept_id")
                count = conn.execute(count_query, {"dept_id": department_id}).scalar()

                print(f"📊 {table}: {count} records")

                if not dry_run and count > 0:
                    # Delete records
                    delete_query = text(f"DELETE FROM {table} WHERE department_id = :dept_id")
                    result = conn.execute(delete_query, {"dept_id": department_id})
                    deleted = result.rowcount
                    total_deleted += deleted
                    print(f"   ✅ Deleted {deleted} records")

            print(f"\n{'[DRY RUN] Would delete' if dry_run else 'Total deleted'}: {total_deleted} records\n")

            if dry_run:
                print("⚠️  This was a dry run. No changes were made.")
                print("   Run without --dry-run to actually delete data.\n")
                trans.rollback()
            else:
                # Commit transaction
                trans.commit()
                print("✅ All data cleaned successfully!\n")

                # Refresh materialized views
                print("🔄 Refreshing materialized views...")
                with engine.connect() as refresh_conn:
                    refresh_conn.execute(text("REFRESH MATERIALIZED VIEW mv_contract_totals"))
                    refresh_conn.commit()
                print("✅ Materialized views refreshed!\n")

        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error: {e}\n")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean credit portfolio data for a department")
    parser.add_argument("--department-id", type=int, required=True, help="Department ID to clean")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")

    args = parser.parse_args()

    # Confirmation
    if not args.dry_run:
        print(f"\n⚠️  WARNING: This will DELETE all credit portfolio data for department {args.department_id}!")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)

    clean_credit_data(args.department_id, args.dry_run)
