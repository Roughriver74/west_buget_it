"""add category_id to processed_invoices

Revision ID: add_category_002
Revises: add_1c_fields_001
Create Date: 2025-11-05 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_category_002'
down_revision: Union[str, None] = 'add_1c_fields_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category_id field for budget category selection
    op.add_column('processed_invoices',
        sa.Column('category_id', sa.Integer(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_processed_invoices_category_id',
        'processed_invoices', 'budget_categories',
        ['category_id'], ['id']
    )

    # Create index for better query performance
    op.create_index('ix_processed_invoices_category_id',
        'processed_invoices', ['category_id'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_processed_invoices_category_id',
        table_name='processed_invoices')

    # Remove foreign key constraint
    op.drop_constraint('fk_processed_invoices_category_id',
        'processed_invoices', type_='foreignkey')

    # Remove column
    op.drop_column('processed_invoices', 'category_id')
