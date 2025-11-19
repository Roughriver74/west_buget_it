"""add default_category_id to departments

Revision ID: 2025_11_19_2124
Revises: 7265be4a81c3
Create Date: 2025-11-19 21:24:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_11_19_2124'
down_revision = '7265be4a81c3'
branch_labels = None
depends_on = None


def upgrade():
    # Add default_category_id column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='departments' AND column_name='default_category_id'
            ) THEN
                ALTER TABLE departments ADD COLUMN default_category_id INTEGER;
                ALTER TABLE departments ADD CONSTRAINT fk_departments_default_category
                    FOREIGN KEY (default_category_id) REFERENCES budget_categories(id);
            END IF;
        END $$;
    """)


def downgrade():
    op.execute('ALTER TABLE departments DROP CONSTRAINT IF EXISTS fk_departments_default_category')
    op.execute('ALTER TABLE departments DROP COLUMN IF EXISTS default_category_id')
