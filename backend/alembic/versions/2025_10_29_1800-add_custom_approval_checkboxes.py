"""add custom approval checkboxes to budget_version

Revision ID: 4f5a6b7c8d9e
Revises: 93e38b6e59d4
Create Date: 2025-10-29 18:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f5a6b7c8d9e'
down_revision: Union[str, None] = '93e38b6e59d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add approval checkbox columns as nullable first
    op.add_column('budget_versions', sa.Column('manager_approved', sa.Boolean(), nullable=True))
    op.add_column('budget_versions', sa.Column('manager_approved_at', sa.DateTime(), nullable=True))
    op.add_column('budget_versions', sa.Column('cfo_approved', sa.Boolean(), nullable=True))
    op.add_column('budget_versions', sa.Column('cfo_approved_at', sa.DateTime(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder1_approved', sa.Boolean(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder1_approved_at', sa.DateTime(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder2_approved', sa.Boolean(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder2_approved_at', sa.DateTime(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder3_approved', sa.Boolean(), nullable=True))
    op.add_column('budget_versions', sa.Column('founder3_approved_at', sa.DateTime(), nullable=True))

    # Set default value False for existing rows
    op.execute("""
        UPDATE budget_versions
        SET manager_approved = FALSE,
            cfo_approved = FALSE,
            founder1_approved = FALSE,
            founder2_approved = FALSE,
            founder3_approved = FALSE
        WHERE manager_approved IS NULL
    """)

    # Now make boolean columns NOT NULL
    op.alter_column('budget_versions', 'manager_approved', nullable=False)
    op.alter_column('budget_versions', 'cfo_approved', nullable=False)
    op.alter_column('budget_versions', 'founder1_approved', nullable=False)
    op.alter_column('budget_versions', 'founder2_approved', nullable=False)
    op.alter_column('budget_versions', 'founder3_approved', nullable=False)


def downgrade() -> None:
    op.drop_column('budget_versions', 'manager_approved')
    op.drop_column('budget_versions', 'manager_approved_at')
    op.drop_column('budget_versions', 'cfo_approved')
    op.drop_column('budget_versions', 'cfo_approved_at')
    op.drop_column('budget_versions', 'founder1_approved')
    op.drop_column('budget_versions', 'founder1_approved_at')
    op.drop_column('budget_versions', 'founder2_approved')
    op.drop_column('budget_versions', 'founder2_approved_at')
    op.drop_column('budget_versions', 'founder3_approved')
    op.drop_column('budget_versions', 'founder3_approved_at')
