"""add KPI system tables

Revision ID: dc3a59754bb0
Revises: 69c1c52fa5c5
Create Date: 2025-10-27 14:00:00.000000

Description:
    Adds KPI (Key Performance Indicators) system for tracking employee performance
    and calculating performance-based bonuses.

    Tables:
    - kpi_goals: Goals and metrics for performance evaluation
    - employee_kpis: Employee KPI tracking by period with bonus calculations
    - employee_kpi_goals: Many-to-many relationship between employees and goals

    Enums:
    - BonusTypeEnum: PERFORMANCE_BASED, FIXED, MIXED
    - KPIGoalStatusEnum: DRAFT, ACTIVE, ACHIEVED, NOT_ACHIEVED, CANCELLED

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc3a59754bb0'
down_revision = '69c1c52fa5c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create Enums with IF NOT EXISTS ###
    # Using raw SQL to safely create enum types if they don't already exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE bonustypeenum AS ENUM ('PERFORMANCE_BASED', 'FIXED', 'MIXED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kpigoalstatusenum AS ENUM ('DRAFT', 'ACTIVE', 'ACHIEVED', 'NOT_ACHIEVED', 'CANCELLED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create enum objects with create_type=False to use existing types
    bonus_type_enum = postgresql.ENUM('PERFORMANCE_BASED', 'FIXED', 'MIXED', name='bonustypeenum', create_type=False)
    kpi_goal_status_enum = postgresql.ENUM('DRAFT', 'ACTIVE', 'ACHIEVED', 'NOT_ACHIEVED', 'CANCELLED', name='kpigoalstatusenum', create_type=False)

    # ### Create kpi_goals table ###
    op.create_table(
        'kpi_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('metric_name', sa.String(length=255), nullable=True),
        sa.Column('metric_unit', sa.String(length=50), nullable=True),
        sa.Column('target_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=False, server_default='100'),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('is_annual', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', kpi_goal_status_enum, nullable=False, server_default='DRAFT'),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_kpi_goal_dept_status', 'kpi_goals', ['department_id', 'status'])
    op.create_index(op.f('ix_kpi_goals_category'), 'kpi_goals', ['category'])
    op.create_index(op.f('ix_kpi_goals_department_id'), 'kpi_goals', ['department_id'])
    op.create_index(op.f('ix_kpi_goals_id'), 'kpi_goals', ['id'])
    op.create_index(op.f('ix_kpi_goals_name'), 'kpi_goals', ['name'])
    op.create_index(op.f('ix_kpi_goals_status'), 'kpi_goals', ['status'])
    op.create_index(op.f('ix_kpi_goals_year'), 'kpi_goals', ['year'])

    # ### Create employee_kpis table ###
    op.create_table(
        'employee_kpis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('kpi_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('monthly_bonus_type', bonus_type_enum, nullable=False, server_default='PERFORMANCE_BASED'),
        sa.Column('quarterly_bonus_type', bonus_type_enum, nullable=False, server_default='PERFORMANCE_BASED'),
        sa.Column('annual_bonus_type', bonus_type_enum, nullable=False, server_default='PERFORMANCE_BASED'),
        sa.Column('monthly_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('quarterly_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('annual_bonus_base', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('monthly_bonus_calculated', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('quarterly_bonus_calculated', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('annual_bonus_calculated', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('monthly_bonus_fixed_part', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('quarterly_bonus_fixed_part', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('annual_bonus_fixed_part', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_employee_kpi_dept', 'employee_kpis', ['department_id', 'year', 'month'])
    op.create_index('idx_employee_kpi_period', 'employee_kpis', ['employee_id', 'year', 'month'])
    op.create_index(op.f('ix_employee_kpis_department_id'), 'employee_kpis', ['department_id'])
    op.create_index(op.f('ix_employee_kpis_employee_id'), 'employee_kpis', ['employee_id'])
    op.create_index(op.f('ix_employee_kpis_id'), 'employee_kpis', ['id'])
    op.create_index(op.f('ix_employee_kpis_month'), 'employee_kpis', ['month'])
    op.create_index(op.f('ix_employee_kpis_year'), 'employee_kpis', ['year'])

    # ### Create employee_kpi_goals table ###
    op.create_table(
        'employee_kpi_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('employee_kpi_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('target_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('actual_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('achievement_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', kpi_goal_status_enum, nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['employee_kpi_id'], ['employee_kpis.id'], ),
        sa.ForeignKeyConstraint(['goal_id'], ['kpi_goals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_emp_kpi_goal_period', 'employee_kpi_goals', ['employee_id', 'goal_id', 'year', 'month'])
    op.create_index(op.f('ix_employee_kpi_goals_employee_id'), 'employee_kpi_goals', ['employee_id'])
    op.create_index(op.f('ix_employee_kpi_goals_employee_kpi_id'), 'employee_kpi_goals', ['employee_kpi_id'])
    op.create_index(op.f('ix_employee_kpi_goals_goal_id'), 'employee_kpi_goals', ['goal_id'])
    op.create_index(op.f('ix_employee_kpi_goals_id'), 'employee_kpi_goals', ['id'])
    op.create_index(op.f('ix_employee_kpi_goals_month'), 'employee_kpi_goals', ['month'])
    op.create_index(op.f('ix_employee_kpi_goals_year'), 'employee_kpi_goals', ['year'])


def downgrade() -> None:
    # ### Drop tables ###
    op.drop_index(op.f('ix_employee_kpi_goals_year'), table_name='employee_kpi_goals')
    op.drop_index(op.f('ix_employee_kpi_goals_month'), table_name='employee_kpi_goals')
    op.drop_index(op.f('ix_employee_kpi_goals_id'), table_name='employee_kpi_goals')
    op.drop_index(op.f('ix_employee_kpi_goals_goal_id'), table_name='employee_kpi_goals')
    op.drop_index(op.f('ix_employee_kpi_goals_employee_kpi_id'), table_name='employee_kpi_goals')
    op.drop_index(op.f('ix_employee_kpi_goals_employee_id'), table_name='employee_kpi_goals')
    op.drop_index('idx_emp_kpi_goal_period', table_name='employee_kpi_goals')
    op.drop_table('employee_kpi_goals')

    op.drop_index(op.f('ix_employee_kpis_year'), table_name='employee_kpis')
    op.drop_index(op.f('ix_employee_kpis_month'), table_name='employee_kpis')
    op.drop_index(op.f('ix_employee_kpis_id'), table_name='employee_kpis')
    op.drop_index(op.f('ix_employee_kpis_employee_id'), table_name='employee_kpis')
    op.drop_index(op.f('ix_employee_kpis_department_id'), table_name='employee_kpis')
    op.drop_index('idx_employee_kpi_period', table_name='employee_kpis')
    op.drop_index('idx_employee_kpi_dept', table_name='employee_kpis')
    op.drop_table('employee_kpis')

    op.drop_index(op.f('ix_kpi_goals_year'), table_name='kpi_goals')
    op.drop_index(op.f('ix_kpi_goals_status'), table_name='kpi_goals')
    op.drop_index(op.f('ix_kpi_goals_name'), table_name='kpi_goals')
    op.drop_index(op.f('ix_kpi_goals_id'), table_name='kpi_goals')
    op.drop_index(op.f('ix_kpi_goals_department_id'), table_name='kpi_goals')
    op.drop_index(op.f('ix_kpi_goals_category'), table_name='kpi_goals')
    op.drop_index('idx_kpi_goal_dept_status', table_name='kpi_goals')
    op.drop_table('kpi_goals')

    # ### Drop Enums ###
    # Using raw SQL to safely drop enum types if they exist
    op.execute("DROP TYPE IF EXISTS kpigoalstatusenum")
    op.execute("DROP TYPE IF EXISTS bonustypeenum")
