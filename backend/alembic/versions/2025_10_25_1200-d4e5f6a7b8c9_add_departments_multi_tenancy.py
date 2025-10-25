"""add_departments_multi_tenancy

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-10-25 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create departments table ###
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('manager_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=True)
    op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)

    # Create default department
    op.execute("""
        INSERT INTO departments (id, name, code, description, is_active, created_at, updated_at)
        VALUES (1, 'IT Department', 'IT', 'Information Technology Department', true, NOW(), NOW())
    """)

    # ### Update UserRoleEnum ###
    # Drop old enum values and create new ones
    op.execute("ALTER TYPE userroleenum RENAME TO userroleenum_old")
    op.execute("CREATE TYPE userroleenum AS ENUM ('ADMIN', 'MANAGER', 'USER')")

    # Update users table - change role column to use new enum
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userroleenum
        USING CASE
            WHEN role::text = 'ADMIN' THEN 'ADMIN'::userroleenum
            WHEN role::text = 'ACCOUNTANT' THEN 'MANAGER'::userroleenum
            WHEN role::text = 'REQUESTER' THEN 'USER'::userroleenum
            ELSE 'USER'::userroleenum
        END
    """)

    # Drop old enum
    op.execute("DROP TYPE userroleenum_old")

    # ### Update users table ###
    # Add department_id
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_department_id'), 'users', ['department_id'], unique=False)
    op.create_foreign_key('fk_users_department_id', 'users', 'departments', ['department_id'], ['id'])

    # Set default department for existing users
    op.execute("UPDATE users SET department_id = 1 WHERE department_id IS NULL")

    # Drop old department column (string)
    op.drop_column('users', 'department')

    # Update default role
    op.alter_column('users', 'role',
                    existing_type=sa.Enum('ADMIN', 'MANAGER', 'USER', name='userroleenum'),
                    server_default='USER')

    # ### Update budget_categories table ###
    # Remove unique constraint from name
    op.drop_index('ix_budget_categories_name', table_name='budget_categories')
    op.create_index(op.f('ix_budget_categories_name'), 'budget_categories', ['name'], unique=False)

    # Add department_id
    op.add_column('budget_categories', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_budget_categories_department_id'), 'budget_categories', ['department_id'], unique=False)
    op.create_foreign_key('fk_budget_categories_department_id', 'budget_categories', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE budget_categories SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('budget_categories', 'department_id', nullable=False)

    # ### Update contractors table ###
    # Remove unique constraint from inn
    op.drop_index('contractors_inn_key', table_name='contractors')
    op.create_index(op.f('ix_contractors_inn'), 'contractors', ['inn'], unique=False)

    # Add department_id
    op.add_column('contractors', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_contractors_department_id'), 'contractors', ['department_id'], unique=False)
    op.create_foreign_key('fk_contractors_department_id', 'contractors', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE contractors SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('contractors', 'department_id', nullable=False)

    # ### Update organizations table ###
    # Remove unique constraint from name
    op.drop_index('organizations_name_key', table_name='organizations')
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)

    # Add department_id
    op.add_column('organizations', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_organizations_department_id'), 'organizations', ['department_id'], unique=False)
    op.create_foreign_key('fk_organizations_department_id', 'organizations', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE organizations SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('organizations', 'department_id', nullable=False)

    # ### Update expenses table ###
    # Remove unique constraint from number
    op.drop_index('expenses_number_key', table_name='expenses')
    op.create_index(op.f('ix_expenses_number'), 'expenses', ['number'], unique=False)

    # Add department_id
    op.add_column('expenses', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_expenses_department_id'), 'expenses', ['department_id'], unique=False)
    op.create_foreign_key('fk_expenses_department_id', 'expenses', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE expenses SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('expenses', 'department_id', nullable=False)

    # ### Update forecast_expenses table ###
    op.add_column('forecast_expenses', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_forecast_expenses_department_id'), 'forecast_expenses', ['department_id'], unique=False)
    op.create_foreign_key('fk_forecast_expenses_department_id', 'forecast_expenses', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE forecast_expenses SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('forecast_expenses', 'department_id', nullable=False)

    # ### Update budget_plans table ###
    op.add_column('budget_plans', sa.Column('department_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_budget_plans_department_id'), 'budget_plans', ['department_id'], unique=False)
    op.create_foreign_key('fk_budget_plans_department_id', 'budget_plans', 'departments', ['department_id'], ['id'])

    # Set default department for existing records
    op.execute("UPDATE budget_plans SET department_id = 1 WHERE department_id IS NULL")

    # Make department_id required
    op.alter_column('budget_plans', 'department_id', nullable=False)


def downgrade() -> None:
    # ### Revert budget_plans ###
    op.drop_constraint('fk_budget_plans_department_id', 'budget_plans', type_='foreignkey')
    op.drop_index(op.f('ix_budget_plans_department_id'), table_name='budget_plans')
    op.drop_column('budget_plans', 'department_id')

    # ### Revert forecast_expenses ###
    op.drop_constraint('fk_forecast_expenses_department_id', 'forecast_expenses', type_='foreignkey')
    op.drop_index(op.f('ix_forecast_expenses_department_id'), table_name='forecast_expenses')
    op.drop_column('forecast_expenses', 'department_id')

    # ### Revert expenses ###
    op.drop_constraint('fk_expenses_department_id', 'expenses', type_='foreignkey')
    op.drop_index(op.f('ix_expenses_department_id'), table_name='expenses')
    op.drop_column('expenses', 'department_id')

    # Restore unique constraint for number
    op.drop_index(op.f('ix_expenses_number'), table_name='expenses')
    op.create_index('expenses_number_key', 'expenses', ['number'], unique=True)

    # ### Revert organizations ###
    op.drop_constraint('fk_organizations_department_id', 'organizations', type_='foreignkey')
    op.drop_index(op.f('ix_organizations_department_id'), table_name='organizations')
    op.drop_column('organizations', 'department_id')

    # Restore unique constraint for name
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.create_index('organizations_name_key', 'organizations', ['name'], unique=True)

    # ### Revert contractors ###
    op.drop_constraint('fk_contractors_department_id', 'contractors', type_='foreignkey')
    op.drop_index(op.f('ix_contractors_department_id'), table_name='contractors')
    op.drop_column('contractors', 'department_id')

    # Restore unique constraint for inn
    op.drop_index(op.f('ix_contractors_inn'), table_name='contractors')
    op.create_index('contractors_inn_key', 'contractors', ['inn'], unique=True)

    # ### Revert budget_categories ###
    op.drop_constraint('fk_budget_categories_department_id', 'budget_categories', type_='foreignkey')
    op.drop_index(op.f('ix_budget_categories_department_id'), table_name='budget_categories')
    op.drop_column('budget_categories', 'department_id')

    # Restore unique constraint for name
    op.drop_index(op.f('ix_budget_categories_name'), table_name='budget_categories')
    op.create_index('ix_budget_categories_name', 'budget_categories', ['name'], unique=True)

    # ### Revert users ###
    # Add back department string column
    op.add_column('users', sa.Column('department', sa.String(length=255), nullable=True))

    # Drop department_id
    op.drop_constraint('fk_users_department_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_department_id'), table_name='users')
    op.drop_column('users', 'department_id')

    # Revert UserRoleEnum
    op.execute("ALTER TYPE userroleenum RENAME TO userroleenum_old")
    op.execute("CREATE TYPE userroleenum AS ENUM ('ADMIN', 'ACCOUNTANT', 'REQUESTER')")

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userroleenum
        USING CASE
            WHEN role::text = 'ADMIN' THEN 'ADMIN'::userroleenum
            WHEN role::text = 'MANAGER' THEN 'ACCOUNTANT'::userroleenum
            WHEN role::text = 'USER' THEN 'REQUESTER'::userroleenum
            ELSE 'REQUESTER'::userroleenum
        END
    """)

    op.execute("DROP TYPE userroleenum_old")

    # Restore default role
    op.alter_column('users', 'role',
                    existing_type=sa.Enum('ADMIN', 'ACCOUNTANT', 'REQUESTER', name='userroleenum'),
                    server_default='REQUESTER')

    # ### Drop departments table ###
    op.drop_index(op.f('ix_departments_code'), table_name='departments')
    op.drop_index(op.f('ix_departments_name'), table_name='departments')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_table('departments')
