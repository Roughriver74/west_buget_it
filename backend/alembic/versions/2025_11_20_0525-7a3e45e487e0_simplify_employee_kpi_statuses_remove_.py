"""simplify_employee_kpi_statuses_remove_in_progress

Revision ID: 7a3e45e487e0
Revises: 477726141e8b
Create Date: 2025-11-20 05:25:17.708547+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3e45e487e0'
down_revision: Union[str, None] = '477726141e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
