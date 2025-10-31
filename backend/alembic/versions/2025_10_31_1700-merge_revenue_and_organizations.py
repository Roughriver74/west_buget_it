"""merge revenue and organizations branches

Revision ID: merge_revenue_orgs
Revises: 9a1b2c3d4e5f, e9840a394414
Create Date: 2025-10-31 17:00:00.000000

"""
from typing import Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_revenue_orgs'
down_revision: Union[str, tuple] = ('9a1b2c3d4e5f', 'e9840a394414')
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Merge migration - no changes needed"""
    pass


def downgrade() -> None:
    """Merge migration - no changes needed"""
    pass
