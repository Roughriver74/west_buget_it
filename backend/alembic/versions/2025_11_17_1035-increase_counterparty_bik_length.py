"""increase counterparty_bik length to 20

Revision ID: increase_bik_20251117
Revises: abc123def456
Create Date: 2025-11-17 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'increase_bik_20251117'
down_revision = 'abc123def456'
branch_labels = None
depends_on = None


def upgrade():
    # Increase counterparty_bik field length from VARCHAR(9) to VARCHAR(20)
    # to support international SWIFT/BIC codes (8-11 characters)
    op.alter_column('bank_transactions', 'counterparty_bik',
                    existing_type=sa.String(length=9),
                    type_=sa.String(length=20),
                    existing_nullable=True)


def downgrade():
    # Revert back to VARCHAR(9)
    op.alter_column('bank_transactions', 'counterparty_bik',
                    existing_type=sa.String(length=20),
                    type_=sa.String(length=9),
                    existing_nullable=True)
