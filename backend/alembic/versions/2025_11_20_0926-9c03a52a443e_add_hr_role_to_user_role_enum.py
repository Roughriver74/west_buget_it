"""add_hr_role_to_user_role_enum

Revision ID: 9c03a52a443e
Revises: 02f520978e61
Create Date: 2025-11-20 09:26:02.398368+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c03a52a443e'
down_revision: Union[str, None] = '02f520978e61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'HR' value to userroleenum (after ACCOUNTANT, before USER)
    # PostgreSQL enum ALTER TYPE doesn't support AFTER clause, so we just add at the end
    op.execute("ALTER TYPE userroleenum ADD VALUE IF NOT EXISTS 'HR'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly
    # Manual database intervention would be required to remove the enum value
    pass
