"""add_budget_scenarios_tables

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2025-10-24 17:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create budget_scenarios table
    op.create_table('budget_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_budget', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('budget_change_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budget_scenarios_id'), 'budget_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_budget_scenarios_name'), 'budget_scenarios', ['name'], unique=False)
    op.create_index(op.f('ix_budget_scenarios_year'), 'budget_scenarios', ['year'], unique=False)

    # Create budget_scenario_items table
    op.create_table('budget_scenario_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('category_type', sa.Enum('OPEX', 'CAPEX', name='budgetcategorytypeenum'), nullable=False),
        sa.Column('category_name', sa.String(length=255), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('priority', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='budgetpriorityenum'), nullable=False),
        sa.Column('change_from_previous', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scenario_id'], ['budget_scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budget_scenario_items_category_type'), 'budget_scenario_items', ['category_type'], unique=False)
    op.create_index(op.f('ix_budget_scenario_items_id'), 'budget_scenario_items', ['id'], unique=False)
    op.create_index(op.f('ix_budget_scenario_items_scenario_id'), 'budget_scenario_items', ['scenario_id'], unique=False)


def downgrade() -> None:
    # Drop budget_scenario_items table
    op.drop_index(op.f('ix_budget_scenario_items_scenario_id'), table_name='budget_scenario_items')
    op.drop_index(op.f('ix_budget_scenario_items_id'), table_name='budget_scenario_items')
    op.drop_index(op.f('ix_budget_scenario_items_category_type'), table_name='budget_scenario_items')
    op.drop_table('budget_scenario_items')

    # Drop budget_scenarios table
    op.drop_index(op.f('ix_budget_scenarios_year'), table_name='budget_scenarios')
    op.drop_index(op.f('ix_budget_scenarios_name'), table_name='budget_scenarios')
    op.drop_index(op.f('ix_budget_scenarios_id'), table_name='budget_scenarios')
    op.drop_table('budget_scenarios')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS budgetcategorytypeenum')
    op.execute('DROP TYPE IF EXISTS budgetpriorityenum')
