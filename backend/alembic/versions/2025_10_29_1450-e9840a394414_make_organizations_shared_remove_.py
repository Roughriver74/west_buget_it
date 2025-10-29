"""make organizations shared - remove department_id

Revision ID: e9840a394414
Revises: 4f5a6b7c8d9e
Create Date: 2025-10-29 14:50:36.637793+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9840a394414'
down_revision: Union[str, None] = '4f5a6b7c8d9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Make organizations shared across all departments:
    1. Drop foreign key constraint to departments
    2. Drop index on department_id
    3. Drop department_id column
    4. Add unique constraint on name (was removed for multi-tenancy)
    """
    # Drop foreign key constraint (actual name in DB)
    op.drop_constraint('fk_organizations_department_id', 'organizations', type_='foreignkey')

    # Drop index
    op.drop_index('idx_organization_dept_active', table_name='organizations')

    # Drop department_id column
    op.drop_column('organizations', 'department_id')

    # Add unique constraint on name (organizations are now shared)
    op.create_unique_constraint('uq_organizations_name', 'organizations', ['name'])


def downgrade() -> None:
    """
    Revert organizations to multi-tenant model:
    1. Drop unique constraint on name
    2. Add department_id column
    3. Re-create index
    4. Re-create foreign key constraint

    WARNING: This downgrade requires manual data migration!
    Each organization must be assigned to a department.
    """
    # Drop unique constraint
    op.drop_constraint('uq_organizations_name', 'organizations', type_='unique')

    # Add department_id column (nullable for migration)
    op.add_column('organizations', sa.Column('department_id', sa.Integer(), nullable=True))

    # MANUAL STEP REQUIRED: Assign organizations to departments
    # op.execute("UPDATE organizations SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id NOT NULL (after manual assignment)
    # op.alter_column('organizations', 'department_id', nullable=False)

    # Re-create index
    op.create_index('idx_organization_dept_active', 'organizations', ['department_id', 'is_active'])

    # Re-create foreign key constraint
    op.create_foreign_key('fk_organizations_department_id', 'organizations', 'departments', ['department_id'], ['id'])
