"""add 1C integration fields to processed_invoices

Revision ID: add_1c_fields_001
Revises: feb0bf4080a5
Create Date: 2025-11-05 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_1c_fields_001'
down_revision: Union[str, None] = 'feb0bf4080a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 1C integration tracking fields
    op.add_column('processed_invoices',
        sa.Column('external_id_1c', sa.String(length=100), nullable=True))
    op.add_column('processed_invoices',
        sa.Column('created_in_1c_at', sa.DateTime(), nullable=True))

    # Create indexes for better query performance
    op.create_index('ix_processed_invoices_external_id_1c',
        'processed_invoices', ['external_id_1c'], unique=False)
    op.create_index('ix_processed_invoices_created_in_1c_at',
        'processed_invoices', ['created_in_1c_at'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_processed_invoices_created_in_1c_at',
        table_name='processed_invoices')
    op.drop_index('ix_processed_invoices_external_id_1c',
        table_name='processed_invoices')

    # Remove columns
    op.drop_column('processed_invoices', 'created_in_1c_at')
    op.drop_column('processed_invoices', 'external_id_1c')
