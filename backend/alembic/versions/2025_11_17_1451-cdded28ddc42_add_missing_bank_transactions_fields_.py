"""add missing bank_transactions fields region exhibition document_type amounts and dates

Revision ID: cdded28ddc42
Revises: 181275141cb7
Create Date: 2025-11-17 14:51:38.859052+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cdded28ddc42'
down_revision: Union[str, None] = '181275141cb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    regionenum = postgresql.ENUM('MOSCOW', 'SPB', 'REGIONS', 'FOREIGN', name='regionenum', create_type=False)
    regionenum.create(op.get_bind(), checkfirst=True)

    documenttypeenum = postgresql.ENUM('PAYMENT_ORDER', 'CASH_ORDER', 'INVOICE', 'ACT', 'CONTRACT', 'OTHER', name='documenttypeenum', create_type=False)
    documenttypeenum.create(op.get_bind(), checkfirst=True)

    # Add region field
    op.add_column('bank_transactions', sa.Column('region', regionenum, nullable=True))
    op.create_index(op.f('ix_bank_transactions_region'), 'bank_transactions', ['region'], unique=False)

    # Add exhibition field
    op.add_column('bank_transactions', sa.Column('exhibition', sa.String(255), nullable=True))

    # Add document_type field
    op.add_column('bank_transactions', sa.Column('document_type', documenttypeenum, nullable=True))

    # Add amount fields by currency
    op.add_column('bank_transactions', sa.Column('amount_rub_credit', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('bank_transactions', sa.Column('amount_eur_credit', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('bank_transactions', sa.Column('amount_rub_debit', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('bank_transactions', sa.Column('amount_eur_debit', sa.Numeric(precision=15, scale=2), nullable=True))

    # Add time dimension fields
    op.add_column('bank_transactions', sa.Column('transaction_month', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_bank_transactions_transaction_month'), 'bank_transactions', ['transaction_month'], unique=False)

    op.add_column('bank_transactions', sa.Column('transaction_year', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_bank_transactions_transaction_year'), 'bank_transactions', ['transaction_year'], unique=False)

    op.add_column('bank_transactions', sa.Column('expense_acceptance_month', sa.Integer(), nullable=True))
    op.add_column('bank_transactions', sa.Column('expense_acceptance_year', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Drop added columns
    op.drop_column('bank_transactions', 'expense_acceptance_year')
    op.drop_column('bank_transactions', 'expense_acceptance_month')

    op.drop_index(op.f('ix_bank_transactions_transaction_year'), table_name='bank_transactions')
    op.drop_column('bank_transactions', 'transaction_year')

    op.drop_index(op.f('ix_bank_transactions_transaction_month'), table_name='bank_transactions')
    op.drop_column('bank_transactions', 'transaction_month')

    op.drop_column('bank_transactions', 'amount_eur_debit')
    op.drop_column('bank_transactions', 'amount_rub_debit')
    op.drop_column('bank_transactions', 'amount_eur_credit')
    op.drop_column('bank_transactions', 'amount_rub_credit')

    op.drop_column('bank_transactions', 'document_type')
    op.drop_column('bank_transactions', 'exhibition')

    op.drop_index(op.f('ix_bank_transactions_region'), table_name='bank_transactions')
    op.drop_column('bank_transactions', 'region')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS documenttypeenum')
    op.execute('DROP TYPE IF EXISTS regionenum')
