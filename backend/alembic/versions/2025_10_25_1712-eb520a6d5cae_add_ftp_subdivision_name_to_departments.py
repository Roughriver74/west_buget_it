"""add_ftp_subdivision_name_to_departments

Revision ID: eb520a6d5cae
Revises: b1c2d3e4f5a6
Create Date: 2025-10-25 17:12:05.135744+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb520a6d5cae'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ftp_subdivision_name column to departments table
    op.add_column('departments', sa.Column('ftp_subdivision_name', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_departments_ftp_subdivision_name'), 'departments', ['ftp_subdivision_name'], unique=False)


def downgrade() -> None:
    # Remove ftp_subdivision_name column from departments table
    op.drop_index(op.f('ix_departments_ftp_subdivision_name'), table_name='departments')
    op.drop_column('departments', 'ftp_subdivision_name')
