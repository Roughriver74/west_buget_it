"""add is_baseline field to budget_versions

Revision ID: d5e6f7g8h9i0
Revises: c4d5e6f7g8h9
Create Date: 2025-10-28 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd5e6f7g8h9i0'
down_revision = 'c4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_baseline column
    op.add_column(
        'budget_versions',
        sa.Column('is_baseline', sa.Boolean(), nullable=False, server_default='false')
    )

    # Create index for faster baseline lookups
    op.create_index(
        'idx_budget_version_baseline',
        'budget_versions',
        ['department_id', 'year', 'is_baseline']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_budget_version_baseline', table_name='budget_versions')

    # Drop column
    op.drop_column('budget_versions', 'is_baseline')
