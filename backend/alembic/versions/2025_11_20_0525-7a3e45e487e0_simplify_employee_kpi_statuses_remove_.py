"""simplify_employee_kpi_statuses_remove_in_progress

Revision ID: 7a3e45e487e0
Revises: 477726141e8b
Create Date: 2025-11-20 05:25:17.708547+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3e45e487e0'
down_revision: Union[str, None] = '477726141e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Update existing IN_PROGRESS records to DRAFT
    # This ensures no data loss and maintains workflow continuity
    op.execute("""
        UPDATE employee_kpis
        SET status = 'DRAFT'
        WHERE status = 'IN_PROGRESS'
    """)

    # Step 2: Drop the default constraint temporarily
    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status DROP DEFAULT;
    """)

    # Step 3: Alter the enum type to remove IN_PROGRESS
    # PostgreSQL requires creating a new enum type and converting the column
    op.execute("""
        ALTER TYPE employeekpistatusenum RENAME TO employeekpistatusenum_old;
    """)

    op.execute("""
        CREATE TYPE employeekpistatusenum AS ENUM (
            'DRAFT',
            'UNDER_REVIEW',
            'APPROVED',
            'REJECTED'
        );
    """)

    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status TYPE employeekpistatusenum
        USING status::text::employeekpistatusenum;
    """)

    op.execute("""
        DROP TYPE employeekpistatusenum_old;
    """)

    # Step 4: Restore the default (DRAFT is still a valid value)
    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status SET DEFAULT 'DRAFT'::employeekpistatusenum;
    """)


def downgrade() -> None:
    # Drop the default constraint temporarily
    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status DROP DEFAULT;
    """)

    # Recreate the old enum with IN_PROGRESS
    op.execute("""
        ALTER TYPE employeekpistatusenum RENAME TO employeekpistatusenum_new;
    """)

    op.execute("""
        CREATE TYPE employeekpistatusenum AS ENUM (
            'DRAFT',
            'IN_PROGRESS',
            'UNDER_REVIEW',
            'APPROVED',
            'REJECTED'
        );
    """)

    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status TYPE employeekpistatusenum
        USING status::text::employeekpistatusenum;
    """)

    op.execute("""
        DROP TYPE employeekpistatusenum_new;
    """)

    # Restore the default
    op.execute("""
        ALTER TABLE employee_kpis
        ALTER COLUMN status SET DEFAULT 'DRAFT'::employeekpistatusenum;
    """)

    # Note: We don't restore IN_PROGRESS records as they were converted to DRAFT
    # Manual data migration would be needed if exact rollback is required
