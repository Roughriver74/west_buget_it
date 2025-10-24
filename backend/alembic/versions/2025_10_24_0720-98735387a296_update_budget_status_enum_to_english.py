"""update_budget_status_enum_to_english

Revision ID: 98735387a296
Revises: add_parent_status
Create Date: 2025-10-24 07:20:54.766135+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98735387a296'
down_revision: Union[str, None] = 'add_parent_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop the default value
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status DROP DEFAULT")

    # Step 2: Convert the column to VARCHAR to allow updates
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status TYPE VARCHAR(50)")

    # Step 3: Update existing data to English values
    op.execute("UPDATE budget_plans SET status = 'DRAFT' WHERE status = 'Черновик'")
    op.execute("UPDATE budget_plans SET status = 'APPROVED' WHERE status = 'Утвержден'")

    # Step 4: Drop the old enum type
    op.execute("DROP TYPE budgetstatusenum")

    # Step 5: Create the new enum type with English values
    op.execute("CREATE TYPE budgetstatusenum AS ENUM ('DRAFT', 'APPROVED')")

    # Step 6: Convert the column back to the new enum type
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status TYPE budgetstatusenum USING status::budgetstatusenum")

    # Step 7: Set the new default value
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status SET DEFAULT 'DRAFT'::budgetstatusenum")


def downgrade() -> None:
    # Step 1: Update data back to Russian values
    op.execute("UPDATE budget_plans SET status = 'Черновик' WHERE status = 'DRAFT'")
    op.execute("UPDATE budget_plans SET status = 'Утвержден' WHERE status = 'APPROVED'")

    # Step 2: Drop the column constraint
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status TYPE VARCHAR(50)")

    # Step 3: Drop the new enum type
    op.execute("DROP TYPE budgetstatusenum")

    # Step 4: Recreate the old enum type with Russian values
    op.execute("CREATE TYPE budgetstatusenum AS ENUM ('Черновик', 'Утвержден')")

    # Step 5: Convert the column back to the old enum type
    op.execute("ALTER TABLE budget_plans ALTER COLUMN status TYPE budgetstatusenum USING status::budgetstatusenum")
