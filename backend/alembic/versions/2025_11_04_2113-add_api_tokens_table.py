"""add api tokens table

Revision ID: add_api_tokens_001
Revises: 2025_10_31_1700
Create Date: 2025-11-04 21:13:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_api_tokens_001'
down_revision = 'merge_revenue_orgs'
branch_labels = None
depends_on = None


def upgrade():
    """Create api_tokens table"""
    op.create_table(
        'api_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('token_key', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'REVOKED', 'EXPIRED', name='apitokenstatusenum'), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by', sa.Integer(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_api_token_key', 'api_tokens', ['token_key'], unique=True)
    op.create_index('idx_api_token_dept', 'api_tokens', ['department_id'], unique=False)
    op.create_index('idx_api_token_status', 'api_tokens', ['status'], unique=False)

    # Create unique constraint on token_key
    op.create_unique_constraint('uq_api_tokens_token_key', 'api_tokens', ['token_key'])


def downgrade():
    """Drop api_tokens table"""
    op.drop_constraint('uq_api_tokens_token_key', 'api_tokens', type_='unique')
    op.drop_index('idx_api_token_status', table_name='api_tokens')
    op.drop_index('idx_api_token_dept', table_name='api_tokens')
    op.drop_index('idx_api_token_key', table_name='api_tokens')
    op.drop_table('api_tokens')
    op.execute('DROP TYPE apitokenstatusenum')
