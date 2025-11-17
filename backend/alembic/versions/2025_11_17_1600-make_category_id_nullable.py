"""make category_id nullable in business_operation_mappings for auto-stubs

Revision ID: make_category_nullable
Revises: cdded28ddc42
Create Date: 2025-11-17 16:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'make_category_nullable'
down_revision: Union[str, None] = 'cdded28ddc42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make category_id nullable in business_operation_mappings
    op.alter_column('business_operation_mappings', 'category_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade() -> None:
    # Make category_id NOT NULL again (may fail if there are NULL values)
    op.alter_column('business_operation_mappings', 'category_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
