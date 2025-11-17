"""add 1c catalog sync fields to organizations and budget_categories

Revision ID: abc123def456
Revises: 6bad3b34ad66
Create Date: 2025-11-17 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, None] = '6bad3b34ad66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Add 1C integration fields to organizations ###
    op.add_column('organizations', sa.Column('ogrn', sa.String(length=20), nullable=True))
    op.add_column('organizations', sa.Column('prefix', sa.String(length=10), nullable=True))
    op.add_column('organizations', sa.Column('okpo', sa.String(length=20), nullable=True))
    op.add_column('organizations', sa.Column('status_1c', sa.String(length=50), nullable=True))

    # ### Add 1C integration fields to budget_categories ###
    op.add_column('budget_categories', sa.Column('external_id_1c', sa.String(length=100), nullable=True))
    op.add_column('budget_categories', sa.Column('code_1c', sa.String(length=50), nullable=True))
    op.add_column('budget_categories', sa.Column('is_folder', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('budget_categories', sa.Column('order_index', sa.Integer(), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_budget_categories_external_id_1c'), 'budget_categories', ['external_id_1c'], unique=False)
    op.create_index('idx_budget_category_external_id_1c_dept', 'budget_categories', ['external_id_1c', 'department_id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Drop indexes ###
    op.drop_index('idx_budget_category_external_id_1c_dept', table_name='budget_categories')
    op.drop_index(op.f('ix_budget_categories_external_id_1c'), table_name='budget_categories')

    # ### Drop 1C fields from budget_categories ###
    op.drop_column('budget_categories', 'order_index')
    op.drop_column('budget_categories', 'is_folder')
    op.drop_column('budget_categories', 'code_1c')
    op.drop_column('budget_categories', 'external_id_1c')

    # ### Drop 1C fields from organizations ###
    op.drop_column('organizations', 'status_1c')
    op.drop_column('organizations', 'okpo')
    op.drop_column('organizations', 'prefix')
    op.drop_column('organizations', 'ogrn')
    # ### end Alembic commands ###
