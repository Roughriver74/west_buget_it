"""add SUBMITTED action to approval log enum

Revision ID: c4d5e6f7g8h9
Revises: dc3a59754bb0
Create Date: 2025-10-28 10:10:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c4d5e6f7g8h9'
down_revision = 'dc3a59754bb0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approvalactionenum AS ENUM ('APPROVED', 'REJECTED', 'REVISION_REQUESTED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Add SUBMITTED value if it doesn't exist
    # Note: ADD VALUE IF NOT EXISTS requires PostgreSQL 9.1+
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE approvalactionenum ADD VALUE IF NOT EXISTS 'SUBMITTED';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Downgrade requires recreating the enum without SUBMITTED
    op.execute("UPDATE budget_approval_log SET action = 'REVISION_REQUESTED' WHERE action = 'SUBMITTED'")
    op.execute("ALTER TYPE approvalactionenum RENAME TO approvalactionenum_old")
    op.execute("CREATE TYPE approvalactionenum AS ENUM ('APPROVED', 'REJECTED', 'REVISION_REQUESTED')")
    op.execute(
        """
        ALTER TABLE budget_approval_log
        ALTER COLUMN action
        TYPE approvalactionenum
        USING action::text::approvalactionenum
        """
    )
    op.execute("DROP TYPE approvalactionenum_old")
