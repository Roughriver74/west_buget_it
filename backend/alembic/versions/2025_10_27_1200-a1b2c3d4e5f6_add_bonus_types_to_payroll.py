"""add bonus types to payroll

Revision ID: a1b2c3d4e5f6
Revises: 39fcb0613cd9
Create Date: 2025-10-27 12:00:00.000000

Description:
    Adds support for different types of bonuses (monthly, quarterly, annual)
    to Employee, PayrollPlan, and PayrollActual models.

    Changes:
    - Employee: add monthly_bonus_base, quarterly_bonus_base, annual_bonus_base
    - PayrollPlan: replace bonus with monthly_bonus, quarterly_bonus, annual_bonus
    - PayrollActual: replace bonus_paid with monthly_bonus_paid, quarterly_bonus_paid, annual_bonus_paid

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '39fcb0613cd9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Employee table: add bonus base rates ###
    op.add_column('employees', sa.Column('monthly_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('employees', sa.Column('quarterly_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('employees', sa.Column('annual_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))

    # ### PayrollPlan table: add specific bonus types ###
    # Add new columns
    op.add_column('payroll_plans', sa.Column('monthly_bonus', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('payroll_plans', sa.Column('quarterly_bonus', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('payroll_plans', sa.Column('annual_bonus', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))

    # Migrate data: copy bonus -> monthly_bonus
    op.execute("""
        UPDATE payroll_plans
        SET monthly_bonus = bonus
        WHERE bonus IS NOT NULL AND bonus > 0
    """)

    # Drop old column
    op.drop_column('payroll_plans', 'bonus')

    # ### PayrollActual table: add specific bonus types ###
    # Add new columns
    op.add_column('payroll_actuals', sa.Column('monthly_bonus_paid', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('payroll_actuals', sa.Column('quarterly_bonus_paid', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('payroll_actuals', sa.Column('annual_bonus_paid', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))

    # Migrate data: copy bonus_paid -> monthly_bonus_paid
    op.execute("""
        UPDATE payroll_actuals
        SET monthly_bonus_paid = bonus_paid
        WHERE bonus_paid IS NOT NULL AND bonus_paid > 0
    """)

    # Drop old column
    op.drop_column('payroll_actuals', 'bonus_paid')


def downgrade() -> None:
    # ### PayrollActual table: restore old structure ###
    # Add back old column
    op.add_column('payroll_actuals', sa.Column('bonus_paid', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))

    # Migrate data: sum all bonuses into bonus_paid
    op.execute("""
        UPDATE payroll_actuals
        SET bonus_paid = COALESCE(monthly_bonus_paid, 0) + COALESCE(quarterly_bonus_paid, 0) + COALESCE(annual_bonus_paid, 0)
    """)

    # Drop new columns
    op.drop_column('payroll_actuals', 'annual_bonus_paid')
    op.drop_column('payroll_actuals', 'quarterly_bonus_paid')
    op.drop_column('payroll_actuals', 'monthly_bonus_paid')

    # ### PayrollPlan table: restore old structure ###
    # Add back old column
    op.add_column('payroll_plans', sa.Column('bonus', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))

    # Migrate data: sum all bonuses into bonus
    op.execute("""
        UPDATE payroll_plans
        SET bonus = COALESCE(monthly_bonus, 0) + COALESCE(quarterly_bonus, 0) + COALESCE(annual_bonus, 0)
    """)

    # Drop new columns
    op.drop_column('payroll_plans', 'annual_bonus')
    op.drop_column('payroll_plans', 'quarterly_bonus')
    op.drop_column('payroll_plans', 'monthly_bonus')

    # ### Employee table: remove bonus base rates ###
    op.drop_column('employees', 'annual_bonus_base')
    op.drop_column('employees', 'quarterly_bonus_base')
    op.drop_column('employees', 'monthly_bonus_base')
