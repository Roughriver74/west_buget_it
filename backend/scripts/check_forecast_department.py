"""Check and update department_id in forecast_expenses table"""
import os
from sqlalchemy import create_engine, text

# Direct database URL
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://budget_user:budget_pass@localhost:54329/it_budget_db'
)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check current state
    result = conn.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(department_id) as with_dept,
            COUNT(*) - COUNT(department_id) as without_dept
        FROM forecast_expenses
    """))
    row = result.fetchone()

    print(f"\n=== Forecast Expenses Department Status ===")
    print(f"Total records: {row[0]}")
    print(f"With department_id: {row[1]}")
    print(f"Without department_id (NULL): {row[2]}")

    # Show sample records
    result = conn.execute(text("""
        SELECT id, department_id, category_id, amount, forecast_date
        FROM forecast_expenses
        LIMIT 5
    """))

    print(f"\n=== Sample Records ===")
    for row in result:
        print(f"ID: {row[0]}, Department: {row[1]}, Category: {row[2]}, Amount: {row[3]}, Date: {row[4]}")

    # If there are records without department_id, update them
    result = conn.execute(text("""
        SELECT COUNT(*) FROM forecast_expenses WHERE department_id IS NULL
    """))
    null_count = result.scalar()

    if null_count > 0:
        print(f"\n=== Updating {null_count} records without department_id ===")
        conn.execute(text("""
            UPDATE forecast_expenses
            SET department_id = 2
            WHERE department_id IS NULL
        """))
        conn.commit()
        print("✓ Updated all records to department_id=2 (IT Отдел ACME)")
    else:
        print("\n✓ All records have department_id assigned")

print("\n=== Check Complete ===\n")
