"""add_performance_indexes

Revision ID: f7g8h9i0j1k2
Revises: d4e5f6a7b8c9
Create Date: 2025-10-25 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add single column indexes
    op.create_index('ix_budget_categories_is_active', 'budget_categories', ['is_active'], unique=False)
    op.create_index('ix_contractors_is_active', 'contractors', ['is_active'], unique=False)
    op.create_index('ix_organizations_is_active', 'organizations', ['is_active'], unique=False)
    op.create_index('ix_expenses_category_id', 'expenses', ['category_id'], unique=False)
    op.create_index('ix_expenses_contractor_id', 'expenses', ['contractor_id'], unique=False)
    op.create_index('ix_expenses_organization_id', 'expenses', ['organization_id'], unique=False)
    op.create_index('ix_expenses_is_paid', 'expenses', ['is_paid'], unique=False)
    op.create_index('ix_expenses_is_closed', 'expenses', ['is_closed'], unique=False)
    op.create_index('ix_forecast_expenses_category_id', 'forecast_expenses', ['category_id'], unique=False)
    op.create_index('ix_forecast_expenses_contractor_id', 'forecast_expenses', ['contractor_id'], unique=False)
    op.create_index('ix_forecast_expenses_organization_id', 'forecast_expenses', ['organization_id'], unique=False)
    op.create_index('ix_budget_plans_category_id', 'budget_plans', ['category_id'], unique=False)

    # Add composite indexes for common query patterns
    op.create_index('idx_budget_category_dept_active', 'budget_categories', ['department_id', 'is_active'], unique=False)
    op.create_index('idx_contractor_dept_active', 'contractors', ['department_id', 'is_active'], unique=False)
    op.create_index('idx_organization_dept_active', 'organizations', ['department_id', 'is_active'], unique=False)
    op.create_index('idx_expense_dept_status', 'expenses', ['department_id', 'status'], unique=False)
    op.create_index('idx_expense_dept_date', 'expenses', ['department_id', 'request_date'], unique=False)
    op.create_index('idx_budget_plan_dept_year_month', 'budget_plans', ['department_id', 'year', 'month'], unique=False)


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index('idx_budget_plan_dept_year_month', table_name='budget_plans')
    op.drop_index('idx_expense_dept_date', table_name='expenses')
    op.drop_index('idx_expense_dept_status', table_name='expenses')
    op.drop_index('idx_organization_dept_active', table_name='organizations')
    op.drop_index('idx_contractor_dept_active', table_name='contractors')
    op.drop_index('idx_budget_category_dept_active', table_name='budget_categories')

    # Drop single column indexes
    op.drop_index('ix_budget_plans_category_id', table_name='budget_plans')
    op.drop_index('ix_forecast_expenses_organization_id', table_name='forecast_expenses')
    op.drop_index('ix_forecast_expenses_contractor_id', table_name='forecast_expenses')
    op.drop_index('ix_forecast_expenses_category_id', table_name='forecast_expenses')
    op.drop_index('ix_expenses_is_closed', table_name='expenses')
    op.drop_index('ix_expenses_is_paid', table_name='expenses')
    op.drop_index('ix_expenses_organization_id', table_name='expenses')
    op.drop_index('ix_expenses_contractor_id', table_name='expenses')
    op.drop_index('ix_expenses_category_id', table_name='expenses')
    op.drop_index('ix_organizations_is_active', table_name='organizations')
    op.drop_index('ix_contractors_is_active', table_name='contractors')
    op.drop_index('ix_budget_categories_is_active', table_name='budget_categories')
