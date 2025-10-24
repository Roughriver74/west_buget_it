"""add_employees_and_payroll_tables

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2025-10-24 17:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create employees table
    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=500), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=False),
        sa.Column('position_level', sa.Enum('JUNIOR', 'MIDDLE', 'SENIOR', 'LEAD', 'MANAGER', name='positionlevelenum'), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'VACATION', 'SICK_LEAVE', 'DISMISSED', name='employeestatusenum'), nullable=False),
        sa.Column('base_salary', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_full_name'), 'employees', ['full_name'], unique=False)
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_status'), 'employees', ['status'], unique=False)

    # Create payrolls table
    op.create_table('payrolls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('base_salary', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('bonus', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('other_payments', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('gross_salary', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('taxes', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('net_salary', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('employer_taxes', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('worked_days', sa.Integer(), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payrolls_employee_id'), 'payrolls', ['employee_id'], unique=False)
    op.create_index(op.f('ix_payrolls_id'), 'payrolls', ['id'], unique=False)
    op.create_index(op.f('ix_payrolls_month'), 'payrolls', ['month'], unique=False)
    op.create_index(op.f('ix_payrolls_year'), 'payrolls', ['year'], unique=False)


def downgrade() -> None:
    # Drop payrolls table
    op.drop_index(op.f('ix_payrolls_year'), table_name='payrolls')
    op.drop_index(op.f('ix_payrolls_month'), table_name='payrolls')
    op.drop_index(op.f('ix_payrolls_id'), table_name='payrolls')
    op.drop_index(op.f('ix_payrolls_employee_id'), table_name='payrolls')
    op.drop_table('payrolls')

    # Drop employees table
    op.drop_index(op.f('ix_employees_status'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_index(op.f('ix_employees_full_name'), table_name='employees')
    op.drop_table('employees')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS employeestatusenum')
    op.execute('DROP TYPE IF EXISTS positionlevelenum')
