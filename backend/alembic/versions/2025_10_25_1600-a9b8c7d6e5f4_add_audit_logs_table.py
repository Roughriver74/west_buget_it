"""add_audit_logs_table

Revision ID: a9b8c7d6e5f4
Revises: f7g8h9i0j1k2
Create Date: 2025-10-25 16:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, None] = 'f7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create AuditActionEnum
    op.execute("""
        CREATE TYPE auditactionenum AS ENUM (
            'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT',
            'EXPORT', 'IMPORT', 'APPROVE', 'REJECT'
        )
    """)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', postgresql.ENUM(
            'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT',
            'EXPORT', 'IMPORT', 'APPROVE', 'REJECT',
            name='auditactionenum'
        ), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('changes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    )

    # Create indexes
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'], unique=False)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'], unique=False)
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'], unique=False)
    op.create_index('ix_audit_logs_department_id', 'audit_logs', ['department_id'], unique=False)
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'], unique=False)

    # Create composite indexes
    op.create_index('idx_audit_log_user_action', 'audit_logs', ['user_id', 'action'], unique=False)
    op.create_index('idx_audit_log_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_audit_log_entity', table_name='audit_logs')
    op.drop_index('idx_audit_log_user_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_department_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_id', table_name='audit_logs')

    # Drop table
    op.drop_table('audit_logs')

    # Drop enum
    op.execute("DROP TYPE auditactionenum")
