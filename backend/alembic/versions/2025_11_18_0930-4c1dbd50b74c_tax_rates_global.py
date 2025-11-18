"""tax_rates_global

Revision ID: 4c1dbd50b74c
Revises: b1d4321efea6
Create Date: 2025-11-18 09:30:18.353161+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1dbd50b74c'
down_revision: Union[str, None] = 'b1d4321efea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'tax_rates',
        'department_id',
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    # Backfill NULL department_id before making column NOT NULL again
    op.execute("""
        UPDATE tax_rates
        SET department_id = (
            SELECT id FROM departments ORDER BY id LIMIT 1
        )
        WHERE department_id IS NULL
    """)

    op.alter_column(
        'tax_rates',
        'department_id',
        existing_type=sa.Integer(),
        nullable=False
    )
