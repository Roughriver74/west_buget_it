"""merge budget and payroll branches

Revision ID: 5c5af3ac5381
Revises: 8c0d9570cd45, c4d5e6f7g8h9
Create Date: 2025-10-28 21:07:14.780369+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c5af3ac5381'
down_revision: Union[str, None] = ('8c0d9570cd45', 'c4d5e6f7g8h9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
