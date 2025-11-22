"""remove_kpi_tasks_and_task_complexity_bonus

Revision ID: 477726141e8b
Revises: d3f25188bf40
Create Date: 2025-11-20 05:14:39.643482+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '477726141e8b'
down_revision: Union[str, None] = 'd3f25188bf40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop task_complexity bonus columns from employee_kpis
    op.drop_column('employee_kpis', 'annual_bonus_complexity')
    op.drop_column('employee_kpis', 'quarterly_bonus_complexity')
    op.drop_column('employee_kpis', 'monthly_bonus_complexity')
    op.drop_column('employee_kpis', 'task_complexity_weight')
    op.drop_column('employee_kpis', 'task_complexity_multiplier')
    op.drop_column('employee_kpis', 'task_complexity_avg')

    # Drop kpi_tasks table completely
    op.drop_table('kpi_tasks')


def downgrade() -> None:
    # Recreate kpi_tasks table
    op.create_table(
        'kpi_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_kpi_goal_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('TODO', 'IN_PROGRESS', 'DONE', 'CANCELLED', name='kpitaskstatusenum'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='kpitaskpriorityenum'), nullable=False),
        sa.Column('complexity', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('completion_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['employee_kpi_goal_id'], ['employee_kpi_goals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_kpi_task_due_date', 'kpi_tasks', ['due_date'], unique=False)
    op.create_index('idx_kpi_task_employee', 'kpi_tasks', ['employee_id'], unique=False)
    op.create_index('idx_kpi_task_goal', 'kpi_tasks', ['employee_kpi_goal_id'], unique=False)
    op.create_index('idx_kpi_task_priority', 'kpi_tasks', ['priority'], unique=False)
    op.create_index('idx_kpi_task_status', 'kpi_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_kpi_tasks_id'), 'kpi_tasks', ['id'], unique=False)

    # Recreate task_complexity columns in employee_kpis
    op.add_column('employee_kpis', sa.Column('task_complexity_avg', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('employee_kpis', sa.Column('task_complexity_multiplier', sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column('employee_kpis', sa.Column('task_complexity_weight', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('employee_kpis', sa.Column('monthly_bonus_complexity', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('employee_kpis', sa.Column('quarterly_bonus_complexity', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('employee_kpis', sa.Column('annual_bonus_complexity', sa.Numeric(precision=15, scale=2), nullable=True))
