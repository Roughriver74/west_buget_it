"""add bank_transactions table

Revision ID: add_bank_transactions_001
Revises: add_founder_role_001
Create Date: 2025-11-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_bank_transactions_001'
down_revision: Union[str, None] = 'add_founder_role_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types for bank transactions
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE banktransactiontypeenum AS ENUM ('DEBIT', 'CREDIT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE banktransactionstatusenum AS ENUM (
                'NEW', 'CATEGORIZED', 'MATCHED', 'APPROVED', 'NEEDS_REVIEW', 'IGNORED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create bank_transactions table
    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.Integer(), nullable=False),

        # Основная информация о транзакции
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('transaction_type',
                  postgresql.ENUM('DEBIT', 'CREDIT', name='banktransactiontypeenum', create_type=False),
                  nullable=False, server_default='DEBIT'),

        # Контрагент
        sa.Column('counterparty_name', sa.String(length=500), nullable=True),
        sa.Column('counterparty_inn', sa.String(length=12), nullable=True),
        sa.Column('counterparty_kpp', sa.String(length=9), nullable=True),
        sa.Column('counterparty_account', sa.String(length=20), nullable=True),
        sa.Column('counterparty_bank', sa.String(length=500), nullable=True),
        sa.Column('counterparty_bik', sa.String(length=9), nullable=True),

        # Назначение платежа
        sa.Column('payment_purpose', sa.Text(), nullable=True),

        # Наша организация
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('account_number', sa.String(length=20), nullable=True),

        # Банковские реквизиты документа
        sa.Column('document_number', sa.String(length=50), nullable=True),
        sa.Column('document_date', sa.Date(), nullable=True),

        # Классификация (AI и ручная)
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('category_confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('suggested_category_id', sa.Integer(), nullable=True),

        # Связь с заявками
        sa.Column('expense_id', sa.Integer(), nullable=True),
        sa.Column('matching_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('suggested_expense_id', sa.Integer(), nullable=True),

        # Статус обработки
        sa.Column('status',
                  postgresql.ENUM('NEW', 'CATEGORIZED', 'MATCHED', 'APPROVED', 'NEEDS_REVIEW', 'IGNORED',
                                 name='banktransactionstatusenum', create_type=False),
                  nullable=False, server_default='NEW'),

        # Дополнительные данные
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_regular_payment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('regular_payment_pattern_id', sa.Integer(), nullable=True),

        # Обработка и аудит
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),

        # Multi-tenancy
        sa.Column('department_id', sa.Integer(), nullable=False),

        # Импорт
        sa.Column('import_source', sa.String(length=50), nullable=True),
        sa.Column('import_file_name', sa.String(length=255), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),

        # External ID (для связи с 1С)
        sa.Column('external_id_1c', sa.String(length=100), nullable=True),

        # Системные поля
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),

        # Primary key and foreign keys
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['budget_categories.id'], ),
        sa.ForeignKeyConstraint(['suggested_category_id'], ['budget_categories.id'], ),
        sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ),
        sa.ForeignKeyConstraint(['suggested_expense_id'], ['expenses.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    )

    # Create indexes
    op.create_index('ix_bank_transactions_id', 'bank_transactions', ['id'])
    op.create_index('ix_bank_transactions_transaction_date', 'bank_transactions', ['transaction_date'])
    op.create_index('ix_bank_transactions_transaction_type', 'bank_transactions', ['transaction_type'])
    op.create_index('ix_bank_transactions_counterparty_name', 'bank_transactions', ['counterparty_name'])
    op.create_index('ix_bank_transactions_counterparty_inn', 'bank_transactions', ['counterparty_inn'])
    op.create_index('ix_bank_transactions_organization_id', 'bank_transactions', ['organization_id'])
    op.create_index('ix_bank_transactions_document_number', 'bank_transactions', ['document_number'])
    op.create_index('ix_bank_transactions_category_id', 'bank_transactions', ['category_id'])
    op.create_index('ix_bank_transactions_expense_id', 'bank_transactions', ['expense_id'])
    op.create_index('ix_bank_transactions_status', 'bank_transactions', ['status'])
    op.create_index('ix_bank_transactions_is_regular_payment', 'bank_transactions', ['is_regular_payment'])
    op.create_index('ix_bank_transactions_department_id', 'bank_transactions', ['department_id'])
    op.create_index('ix_bank_transactions_external_id_1c', 'bank_transactions', ['external_id_1c'], unique=True)
    op.create_index('ix_bank_transactions_is_active', 'bank_transactions', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_bank_transactions_is_active', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_external_id_1c', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_department_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_is_regular_payment', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_status', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_expense_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_category_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_document_number', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_organization_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_counterparty_inn', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_counterparty_name', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_transaction_type', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_transaction_date', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_id', table_name='bank_transactions')

    # Drop table
    op.drop_table('bank_transactions')

    # Drop enum types
    op.execute("DROP TYPE banktransactionstatusenum")
    op.execute("DROP TYPE banktransactiontypeenum")
