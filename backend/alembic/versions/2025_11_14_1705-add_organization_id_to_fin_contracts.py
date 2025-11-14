"""add organization foreign key to fin_contracts

Revision ID: add_org_to_fin_contracts_001
Revises: c9f4d8c3e7b1
Create Date: 2025-11-14 17:05:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_org_to_fin_contracts_001'
down_revision: Union[str, None] = 'c9f4d8c3e7b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fin_contracts', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_fin_contracts_organization_id'), 'fin_contracts', ['organization_id'], unique=False)
    op.create_foreign_key(
        'fk_fin_contracts_organization_id_fin_organizations',
        'fin_contracts',
        'fin_organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_fin_contracts_organization_id_fin_organizations', 'fin_contracts', type_='foreignkey')
    op.drop_index(op.f('ix_fin_contracts_organization_id'), table_name='fin_contracts')
    op.drop_column('fin_contracts', 'organization_id')

