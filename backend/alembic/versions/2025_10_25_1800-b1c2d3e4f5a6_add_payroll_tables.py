"""add_payroll_tables

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2025-10-25 18:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create EmployeeStatusEnum
    op.execute("""
        CREATE TYPE employeestatusenum AS ENUM (
            'ACTIVE', 'ON_VACATION', 'ON_LEAVE', 'FIRED'
        )
    """)

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=False),
        sa.Column('employee_number', sa.String(length=50), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('fire_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM(
            'ACTIVE', 'ON_VACATION', 'ON_LEAVE', 'FIRED',
            name='employeestatusenum'
        ), nullable=False),
        sa.Column('base_salary', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    )

    # Create indexes for employees table
    op.create_index('ix_employees_id', 'employees', ['id'], unique=False)
    op.create_index('ix_employees_full_name', 'employees', ['full_name'], unique=False)
    op.create_index('ix_employees_employee_number', 'employees', ['employee_number'], unique=False)
    op.create_index('ix_employees_status', 'employees', ['status'], unique=False)
    op.create_index('ix_employees_department_id', 'employees', ['department_id'], unique=False)
    op.create_index('idx_employee_dept_status', 'employees', ['department_id', 'status'], unique=False)

    # Create salary_history table
    op.create_table(
        'salary_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('old_salary', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('new_salary', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    )

    # Create indexes for salary_history table
    op.create_index('ix_salary_history_id', 'salary_history', ['id'], unique=False)
    op.create_index('ix_salary_history_employee_id', 'salary_history', ['employee_id'], unique=False)
    op.create_index('idx_salary_history_employee_date', 'salary_history', ['employee_id', 'effective_date'], unique=False)

    # Create payroll_plans table
    op.create_table(
        'payroll_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('base_salary', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('bonus', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('other_payments', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_planned', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    )

    # Create indexes for payroll_plans table
    op.create_index('ix_payroll_plans_id', 'payroll_plans', ['id'], unique=False)
    op.create_index('ix_payroll_plans_year', 'payroll_plans', ['year'], unique=False)
    op.create_index('ix_payroll_plans_month', 'payroll_plans', ['month'], unique=False)
    op.create_index('ix_payroll_plans_employee_id', 'payroll_plans', ['employee_id'], unique=False)
    op.create_index('ix_payroll_plans_department_id', 'payroll_plans', ['department_id'], unique=False)
    op.create_index('idx_payroll_plan_dept_year_month', 'payroll_plans', ['department_id', 'year', 'month'], unique=False)
    op.create_index('idx_payroll_plan_employee_year_month', 'payroll_plans', ['employee_id', 'year', 'month'], unique=False)

    # Create payroll_actuals table
    op.create_table(
        'payroll_actuals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('base_salary_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('bonus_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('other_payments_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('expense_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ),
    )

    # Create indexes for payroll_actuals table
    op.create_index('ix_payroll_actuals_id', 'payroll_actuals', ['id'], unique=False)
    op.create_index('ix_payroll_actuals_year', 'payroll_actuals', ['year'], unique=False)
    op.create_index('ix_payroll_actuals_month', 'payroll_actuals', ['month'], unique=False)
    op.create_index('ix_payroll_actuals_employee_id', 'payroll_actuals', ['employee_id'], unique=False)
    op.create_index('ix_payroll_actuals_department_id', 'payroll_actuals', ['department_id'], unique=False)
    op.create_index('ix_payroll_actuals_expense_id', 'payroll_actuals', ['expense_id'], unique=False)
    op.create_index('idx_payroll_actual_dept_year_month', 'payroll_actuals', ['department_id', 'year', 'month'], unique=False)
    op.create_index('idx_payroll_actual_employee_year_month', 'payroll_actuals', ['employee_id', 'year', 'month'], unique=False)


def downgrade() -> None:
    # Drop payroll_actuals table and indexes
    op.drop_index('idx_payroll_actual_employee_year_month', table_name='payroll_actuals')
    op.drop_index('idx_payroll_actual_dept_year_month', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_expense_id', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_department_id', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_employee_id', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_month', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_year', table_name='payroll_actuals')
    op.drop_index('ix_payroll_actuals_id', table_name='payroll_actuals')
    op.drop_table('payroll_actuals')

    # Drop payroll_plans table and indexes
    op.drop_index('idx_payroll_plan_employee_year_month', table_name='payroll_plans')
    op.drop_index('idx_payroll_plan_dept_year_month', table_name='payroll_plans')
    op.drop_index('ix_payroll_plans_department_id', table_name='payroll_plans')
    op.drop_index('ix_payroll_plans_employee_id', table_name='payroll_plans')
    op.drop_index('ix_payroll_plans_month', table_name='payroll_plans')
    op.drop_index('ix_payroll_plans_year', table_name='payroll_plans')
    op.drop_index('ix_payroll_plans_id', table_name='payroll_plans')
    op.drop_table('payroll_plans')

    # Drop salary_history table and indexes
    op.drop_index('idx_salary_history_employee_date', table_name='salary_history')
    op.drop_index('ix_salary_history_employee_id', table_name='salary_history')
    op.drop_index('ix_salary_history_id', table_name='salary_history')
    op.drop_table('salary_history')

    # Drop employees table and indexes
    op.drop_index('idx_employee_dept_status', table_name='employees')
    op.drop_index('ix_employees_department_id', table_name='employees')
    op.drop_index('ix_employees_status', table_name='employees')
    op.drop_index('ix_employees_employee_number', table_name='employees')
    op.drop_index('ix_employees_full_name', table_name='employees')
    op.drop_index('ix_employees_id', table_name='employees')
    op.drop_table('employees')

    # Drop EmployeeStatusEnum
    op.execute("DROP TYPE employeestatusenum")
