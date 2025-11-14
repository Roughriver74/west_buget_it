"""add FOUNDER role to UserRoleEnum

Revision ID: add_founder_role_001
Revises: add_category_002
Create Date: 2025-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_founder_role_001'
down_revision: Union[str, None] = 'add_category_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add FOUNDER value to UserRoleEnum if it doesn't exist
    # Note: ADD VALUE IF NOT EXISTS requires PostgreSQL 9.1+
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE userroleenum ADD VALUE IF NOT EXISTS 'FOUNDER';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    # Downgrade requires recreating the enum without FOUNDER
    # First, update any users with FOUNDER role to MANAGER role
    op.execute("UPDATE users SET role = 'MANAGER' WHERE role = 'FOUNDER'")

    # Rename old enum type
    op.execute("ALTER TYPE userroleenum RENAME TO userroleenum_old")

    # Create new enum without FOUNDER
    op.execute("CREATE TYPE userroleenum AS ENUM ('ADMIN', 'MANAGER', 'USER')")

    # Update users table to use new enum
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN role
        TYPE userroleenum
        USING role::text::userroleenum
        """
    )

    # Drop old enum type
    op.execute("DROP TYPE userroleenum_old")
