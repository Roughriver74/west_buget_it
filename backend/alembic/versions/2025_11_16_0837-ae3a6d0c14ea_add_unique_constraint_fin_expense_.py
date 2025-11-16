"""add_unique_constraint_fin_expense_details

Revision ID: ae3a6d0c14ea
Revises: add_org_to_fin_contracts_001
Create Date: 2025-11-16 08:37:44.011723+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae3a6d0c14ea'
down_revision: Union[str, None] = 'add_org_to_fin_contracts_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Remove duplicates before creating unique index
    # Keep only the first record (MIN(id)) for each unique combination
    op.execute("""
        DELETE FROM fin_expense_details
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fin_expense_details
            GROUP BY expense_operation_id, payment_type, payment_amount, department_id
        );
    """)

    # Step 2: Create unique index to prevent duplicate expense details
    # This prevents the same operation from being imported multiple times
    op.create_index(
        'ix_fin_expense_details_unique_detail',
        'fin_expense_details',
        ['expense_operation_id', 'payment_type', 'payment_amount', 'department_id'],
        unique=True
    )


def downgrade() -> None:
    # Drop unique index
    op.drop_index(
        'ix_fin_expense_details_unique_detail',
        table_name='fin_expense_details'
    )
