"""Add insurance rates and payroll scenarios tables

Revision ID: a5f8c9d3e1b2
Revises: 4c1dbd50b74c
Create Date: 2025-11-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a5f8c9d3e1b2'
down_revision: Union[str, None] = '4c1dbd50b74c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PayrollScenarioTypeEnum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE payrollscenariotypeenum AS ENUM ('BASE', 'OPTIMISTIC', 'PESSIMISTIC', 'CUSTOM');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create insurance_rates table
    op.create_table(
        'insurance_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('rate_type', postgresql.ENUM('INCOME_TAX', 'PENSION_FUND', 'MEDICAL_INSURANCE', 'SOCIAL_INSURANCE', 'INJURY_INSURANCE', name='taxtypeenum', create_type=False), nullable=False),
        sa.Column('rate_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('threshold_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('rate_above_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('legal_basis', sa.String(length=255), nullable=True),
        sa.Column('total_employer_burden', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_insurance_rate_year_type', 'insurance_rates', ['year', 'rate_type'], unique=False)
    op.create_index('ix_insurance_rate_dept_year', 'insurance_rates', ['department_id', 'year'], unique=False)
    op.create_index(op.f('ix_insurance_rates_id'), 'insurance_rates', ['id'], unique=False)
    op.create_index(op.f('ix_insurance_rates_is_active'), 'insurance_rates', ['is_active'], unique=False)
    op.create_index(op.f('ix_insurance_rates_year'), 'insurance_rates', ['year'], unique=False)
    op.create_index(op.f('ix_insurance_rates_rate_type'), 'insurance_rates', ['rate_type'], unique=False)
    op.create_index(op.f('ix_insurance_rates_department_id'), 'insurance_rates', ['department_id'], unique=False)

    # Create payroll_scenarios table
    op.create_table(
        'payroll_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_type', postgresql.ENUM('BASE', 'OPTIMISTIC', 'PESSIMISTIC', 'CUSTOM', name='payrollscenariotypeenum', create_type=False), nullable=False),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('base_year', sa.Integer(), nullable=False),
        sa.Column('headcount_change_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
        sa.Column('salary_change_percent', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
        sa.Column('total_headcount', sa.Integer(), nullable=True),
        sa.Column('total_base_salary', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_insurance_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_payroll_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('base_year_total_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('cost_difference', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('cost_difference_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payroll_scenario_dept_year', 'payroll_scenarios', ['department_id', 'target_year'], unique=False)
    op.create_index(op.f('ix_payroll_scenarios_id'), 'payroll_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_payroll_scenarios_is_active'), 'payroll_scenarios', ['is_active'], unique=False)
    op.create_index(op.f('ix_payroll_scenarios_target_year'), 'payroll_scenarios', ['target_year'], unique=False)
    op.create_index(op.f('ix_payroll_scenarios_department_id'), 'payroll_scenarios', ['department_id'], unique=False)

    # Create payroll_scenario_details table
    op.create_table(
        'payroll_scenario_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('employee_name', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('is_new_hire', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_terminated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('termination_month', sa.Integer(), nullable=True),
        sa.Column('base_salary', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('monthly_bonus', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('pension_contribution', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('medical_contribution', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('social_contribution', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('injury_contribution', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_insurance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('income_tax', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_employee_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('base_year_salary', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('base_year_insurance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('cost_increase', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['scenario_id'], ['payroll_scenarios.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payroll_scenario_detail_scenario', 'payroll_scenario_details', ['scenario_id'], unique=False)
    op.create_index('ix_payroll_scenario_detail_employee', 'payroll_scenario_details', ['employee_id'], unique=False)
    op.create_index(op.f('ix_payroll_scenario_details_id'), 'payroll_scenario_details', ['id'], unique=False)
    op.create_index(op.f('ix_payroll_scenario_details_department_id'), 'payroll_scenario_details', ['department_id'], unique=False)

    # Create payroll_yearly_comparisons table
    op.create_table(
        'payroll_yearly_comparisons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('base_year', sa.Integer(), nullable=False),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('base_year_headcount', sa.Integer(), nullable=True),
        sa.Column('base_year_total_salary', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('base_year_total_insurance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('base_year_total_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('target_year_headcount', sa.Integer(), nullable=True),
        sa.Column('target_year_total_salary', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('target_year_total_insurance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('target_year_total_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('insurance_rate_change', sa.JSON(), nullable=True),
        sa.Column('total_cost_increase', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_cost_increase_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('pension_increase', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('medical_increase', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('social_increase', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payroll_comparison_dept_years', 'payroll_yearly_comparisons', ['department_id', 'base_year', 'target_year'], unique=False)
    op.create_index(op.f('ix_payroll_yearly_comparisons_id'), 'payroll_yearly_comparisons', ['id'], unique=False)
    op.create_index(op.f('ix_payroll_yearly_comparisons_base_year'), 'payroll_yearly_comparisons', ['base_year'], unique=False)
    op.create_index(op.f('ix_payroll_yearly_comparisons_target_year'), 'payroll_yearly_comparisons', ['target_year'], unique=False)
    op.create_index(op.f('ix_payroll_yearly_comparisons_department_id'), 'payroll_yearly_comparisons', ['department_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('payroll_yearly_comparisons')
    op.drop_table('payroll_scenario_details')
    op.drop_table('payroll_scenarios')
    op.drop_table('insurance_rates')

    # Drop enum
    op.execute('DROP TYPE IF EXISTS payrollscenariotypeenum')
