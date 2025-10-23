"""Add parent_id to budget_categories and status to budget_plans

Revision ID: add_parent_status
Revises: 21c6cd6d2f8b
Create Date: 2025-10-23 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_parent_status'
down_revision: Union[str, None] = '21c6cd6d2f8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create BudgetStatusEnum type
    op.execute("CREATE TYPE budgetstatusenum AS ENUM ('Черновик', 'Утвержден')")

    # Add parent_id to budget_categories for subcategories support
    op.add_column('budget_categories', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_budget_categories_parent_id'), 'budget_categories', ['parent_id'], unique=False)
    op.create_foreign_key('fk_budget_categories_parent_id', 'budget_categories', 'budget_categories', ['parent_id'], ['id'])

    # Add status to budget_plans
    op.add_column('budget_plans', sa.Column('status', sa.Enum('Черновик', 'Утвержден', name='budgetstatusenum'), nullable=False, server_default='Черновик'))
    op.create_index(op.f('ix_budget_plans_status'), 'budget_plans', ['status'], unique=False)


def downgrade() -> None:
    # Remove status from budget_plans
    op.drop_index(op.f('ix_budget_plans_status'), table_name='budget_plans')
    op.drop_column('budget_plans', 'status')

    # Remove parent_id from budget_categories
    op.drop_constraint('fk_budget_categories_parent_id', 'budget_categories', type_='foreignkey')
    op.drop_index(op.f('ix_budget_categories_parent_id'), table_name='budget_categories')
    op.drop_column('budget_categories', 'parent_id')

    # Drop BudgetStatusEnum type
    op.execute("DROP TYPE budgetstatusenum")
