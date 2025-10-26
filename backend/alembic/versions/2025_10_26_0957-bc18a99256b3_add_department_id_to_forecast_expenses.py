"""add_department_id_to_forecast_expenses

Revision ID: bc18a99256b3
Revises: 39fcb0613cd9
Create Date: 2025-10-26 09:57:28.044562+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc18a99256b3'
down_revision: Union[str, None] = '39fcb0613cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add department_id column as nullable
    op.add_column('forecast_expenses',
        sa.Column('department_id', sa.Integer(), nullable=True)
    )

    # Step 2: Set default department_id for existing records (department_id=2 is IT Отдел WEST)
    op.execute('UPDATE forecast_expenses SET department_id = 2 WHERE department_id IS NULL')

    # Step 3: Make the column NOT NULL
    op.alter_column('forecast_expenses', 'department_id', nullable=False)

    # Step 4: Add foreign key constraint
    op.create_foreign_key(
        'fk_forecast_expenses_department_id',
        'forecast_expenses', 'departments',
        ['department_id'], ['id']
    )

    # Step 5: Add index for performance
    op.create_index(
        op.f('ix_forecast_expenses_department_id'),
        'forecast_expenses',
        ['department_id'],
        unique=False
    )


def downgrade() -> None:
    # Remove index
    op.drop_index(op.f('ix_forecast_expenses_department_id'), table_name='forecast_expenses')

    # Remove foreign key
    op.drop_constraint('fk_forecast_expenses_department_id', 'forecast_expenses', type_='foreignkey')

    # Remove column
    op.drop_column('forecast_expenses', 'department_id')
