"""add_accountant_requester_roles

Revision ID: b1d4321efea6
Revises: b631c554e247
Create Date: 2025-11-18 09:16:12.082915+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1d4321efea6'
down_revision: Union[str, None] = 'b631c554e247'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ACCOUNTANT role
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'userroleenum'
                AND e.enumlabel = 'ACCOUNTANT'
            ) THEN
                ALTER TYPE userroleenum ADD VALUE 'ACCOUNTANT';
            END IF;
        END
        $$;
        """
    )

    # Add REQUESTER role
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'userroleenum'
                AND e.enumlabel = 'REQUESTER'
            ) THEN
                ALTER TYPE userroleenum ADD VALUE 'REQUESTER';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Reassign roles before removing enum values
    op.execute("UPDATE users SET role = 'MANAGER' WHERE role = 'ACCOUNTANT'")
    op.execute("UPDATE users SET role = 'USER' WHERE role = 'REQUESTER'")

    # Recreate enum without ACCOUNTANT and REQUESTER
    op.execute("ALTER TYPE userroleenum RENAME TO userroleenum_old")
    op.execute("CREATE TYPE userroleenum AS ENUM ('ADMIN', 'FOUNDER', 'MANAGER', 'USER')")
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN role
        TYPE userroleenum
        USING role::text::userroleenum
        """
    )
    op.execute("DROP TYPE userroleenum_old")
