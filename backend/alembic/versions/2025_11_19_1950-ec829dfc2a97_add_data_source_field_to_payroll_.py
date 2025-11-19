"""add data_source field to payroll_scenarios

Revision ID: ec829dfc2a97
Revises: a5f8c9d3e1b2
Create Date: 2025-11-19 19:50:41.513197+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec829dfc2a97'
down_revision: Union[str, None] = 'a5f8c9d3e1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first
    op.execute("CREATE TYPE payrolldatasourceenum AS ENUM ('EMPLOYEES', 'ACTUAL', 'PLAN')")
    # Add data_source field to payroll_scenarios table with default value
    op.add_column('payroll_scenarios', sa.Column('data_source', sa.Enum('EMPLOYEES', 'ACTUAL', 'PLAN', name='payrolldatasourceenum'), nullable=False, server_default='EMPLOYEES'))
    # Remove server_default after column is created
    op.alter_column('payroll_scenarios', 'data_source', server_default=None)


def downgrade() -> None:
    op.drop_column('payroll_scenarios', 'data_source')
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS payrolldatasourceenum")
