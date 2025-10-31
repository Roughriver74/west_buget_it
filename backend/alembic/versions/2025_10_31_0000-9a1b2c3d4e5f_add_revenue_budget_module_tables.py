"""add revenue budget module tables

Revision ID: 9a1b2c3d4e5f
Revises: 4f5a6b7c8d9e
Create Date: 2025-10-31 00:00:00.000000+00:00

Description:
    Adds Revenue Budget Module for managing income planning and tracking.

    Tables:
    - revenue_streams: Classification of revenue sources (regional, channel, product)
    - revenue_categories: Product and service categories
    - revenue_plans: Annual revenue plans with versioning support
    - revenue_plan_versions: Version control for revenue plans
    - revenue_plan_details: Monthly revenue plan details by category
    - revenue_actuals: Actual revenue data with plan vs actual comparison
    - customer_metrics: Customer base metrics (total, active, coverage, avg order value)
    - seasonality_coefficients: Historical seasonality coefficients for forecasting
    - revenue_forecasts: ML-based revenue forecasts

    Enums:
    - RevenueStreamTypeEnum: REGIONAL, CHANNEL, PRODUCT
    - RevenueCategoryTypeEnum: PRODUCT, SERVICE, EQUIPMENT, TENDER
    - RevenuePlanStatusEnum: DRAFT, PENDING_APPROVAL, APPROVED, ACTIVE, ARCHIVED
    - RevenueVersionStatusEnum: DRAFT, IN_REVIEW, REVISION_REQUESTED, APPROVED, REJECTED, ARCHIVED

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, None] = '4f5a6b7c8d9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create Enums with IF NOT EXISTS ###
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE revenuestreamtypeenum AS ENUM ('REGIONAL', 'CHANNEL', 'PRODUCT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE revenuecategorytypeenum AS ENUM ('PRODUCT', 'SERVICE', 'EQUIPMENT', 'TENDER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE revenueplanstatusenum AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'ARCHIVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE revenueversionstatusenum AS ENUM ('DRAFT', 'IN_REVIEW', 'REVISION_REQUESTED', 'APPROVED', 'REJECTED', 'ARCHIVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ### Create Tables ###

    # 1. revenue_streams
    op.create_table(
        'revenue_streams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('stream_type', sa.Enum('REGIONAL', 'CHANNEL', 'PRODUCT', name='revenuestreamtypeenum'), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_stream_dept_active', 'revenue_streams', ['department_id', 'is_active'])
    op.create_index('idx_revenue_stream_type', 'revenue_streams', ['stream_type'])
    op.create_index(op.f('ix_revenue_streams_code'), 'revenue_streams', ['code'])
    op.create_index(op.f('ix_revenue_streams_id'), 'revenue_streams', ['id'])

    # 2. revenue_categories
    op.create_table(
        'revenue_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('category_type', sa.Enum('PRODUCT', 'SERVICE', 'EQUIPMENT', 'TENDER', name='revenuecategorytypeenum'), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('default_margin', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['revenue_categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_revenue_category_dept_active', 'revenue_categories', ['department_id', 'is_active'])
    op.create_index('idx_revenue_category_type', 'revenue_categories', ['category_type'])
    op.create_index(op.f('ix_revenue_categories_code'), 'revenue_categories', ['code'])
    op.create_index(op.f('ix_revenue_categories_id'), 'revenue_categories', ['id'])

    # 3. revenue_plans
    op.create_table(
        'revenue_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=True),
        sa.Column('revenue_category_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'ARCHIVED', name='revenueplanstatusenum'), nullable=False, server_default='DRAFT'),
        sa.Column('total_planned_revenue', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_category_id'], ['revenue_categories.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_plan_status', 'revenue_plans', ['status'])
    op.create_index('idx_revenue_plan_year_dept', 'revenue_plans', ['year', 'department_id'])
    op.create_index(op.f('ix_revenue_plans_id'), 'revenue_plans', ['id'])
    op.create_index(op.f('ix_revenue_plans_year'), 'revenue_plans', ['year'])

    # 4. revenue_plan_versions
    op.create_table(
        'revenue_plan_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'IN_REVIEW', 'REVISION_REQUESTED', 'APPROVED', 'REJECTED', 'ARCHIVED', name='revenueversionstatusenum'), nullable=False, server_default='DRAFT'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['revenue_plans.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_version_plan', 'revenue_plan_versions', ['plan_id'])
    op.create_index('idx_revenue_version_status', 'revenue_plan_versions', ['status'])
    op.create_index(op.f('ix_revenue_plan_versions_id'), 'revenue_plan_versions', ['id'])

    # 5. revenue_plan_details
    op.create_table(
        'revenue_plan_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=True),
        sa.Column('revenue_category_id', sa.Integer(), nullable=True),
        sa.Column('month_01', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_02', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_03', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_04', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_05', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_06', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_07', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_08', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_09', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_10', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_11', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('month_12', sa.Numeric(precision=15, scale=2), nullable=True, server_default='0'),
        sa.Column('total', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_category_id'], ['revenue_categories.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.ForeignKeyConstraint(['version_id'], ['revenue_plan_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_detail_category', 'revenue_plan_details', ['revenue_category_id'])
    op.create_index('idx_revenue_detail_dept', 'revenue_plan_details', ['department_id'])
    op.create_index('idx_revenue_detail_stream', 'revenue_plan_details', ['revenue_stream_id'])
    op.create_index('idx_revenue_detail_version', 'revenue_plan_details', ['version_id'])
    op.create_index(op.f('ix_revenue_plan_details_id'), 'revenue_plan_details', ['id'])

    # 6. revenue_actuals
    op.create_table(
        'revenue_actuals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=True),
        sa.Column('revenue_category_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('planned_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('actual_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('variance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('variance_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_category_id'], ['revenue_categories.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_actual_category', 'revenue_actuals', ['revenue_category_id'])
    op.create_index('idx_revenue_actual_dept', 'revenue_actuals', ['department_id'])
    op.create_index('idx_revenue_actual_stream', 'revenue_actuals', ['revenue_stream_id'])
    op.create_index('idx_revenue_actual_year_month', 'revenue_actuals', ['year', 'month'])
    op.create_index(op.f('ix_revenue_actuals_id'), 'revenue_actuals', ['id'])
    op.create_index(op.f('ix_revenue_actuals_month'), 'revenue_actuals', ['month'])
    op.create_index(op.f('ix_revenue_actuals_year'), 'revenue_actuals', ['year'])

    # 7. customer_metrics
    op.create_table(
        'customer_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_customer_base', sa.Integer(), nullable=True),
        sa.Column('active_customer_base', sa.Integer(), nullable=True),
        sa.Column('coverage_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('regular_clinics', sa.Integer(), nullable=True),
        sa.Column('network_clinics', sa.Integer(), nullable=True),
        sa.Column('new_clinics', sa.Integer(), nullable=True),
        sa.Column('avg_order_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('avg_order_value_regular', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('avg_order_value_network', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('avg_order_value_new', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_metrics_dept', 'customer_metrics', ['department_id'])
    op.create_index('idx_customer_metrics_stream', 'customer_metrics', ['revenue_stream_id'])
    op.create_index('idx_customer_metrics_year_month', 'customer_metrics', ['year', 'month'])
    op.create_index(op.f('ix_customer_metrics_id'), 'customer_metrics', ['id'])
    op.create_index(op.f('ix_customer_metrics_month'), 'customer_metrics', ['month'])
    op.create_index(op.f('ix_customer_metrics_year'), 'customer_metrics', ['year'])

    # 8. seasonality_coefficients
    op.create_table(
        'seasonality_coefficients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('coef_01', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_02', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_03', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_04', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_05', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_06', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_07', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_08', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_09', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_10', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_11', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('coef_12', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_seasonality_dept', 'seasonality_coefficients', ['department_id'])
    op.create_index('idx_seasonality_stream', 'seasonality_coefficients', ['revenue_stream_id'])
    op.create_index('idx_seasonality_year', 'seasonality_coefficients', ['year'])
    op.create_index(op.f('ix_seasonality_coefficients_id'), 'seasonality_coefficients', ['id'])
    op.create_index(op.f('ix_seasonality_coefficients_year'), 'seasonality_coefficients', ['year'])

    # 9. revenue_forecasts
    op.create_table(
        'revenue_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('revenue_stream_id', sa.Integer(), nullable=True),
        sa.Column('revenue_category_id', sa.Integer(), nullable=True),
        sa.Column('forecast_year', sa.Integer(), nullable=False),
        sa.Column('forecast_month', sa.Integer(), nullable=False),
        sa.Column('forecast_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('confidence_level', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('model_type', sa.String(length=50), nullable=True),
        sa.Column('model_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['revenue_category_id'], ['revenue_categories.id']),
        sa.ForeignKeyConstraint(['revenue_stream_id'], ['revenue_streams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_revenue_forecast_category', 'revenue_forecasts', ['revenue_category_id'])
    op.create_index('idx_revenue_forecast_dept', 'revenue_forecasts', ['department_id'])
    op.create_index('idx_revenue_forecast_stream', 'revenue_forecasts', ['revenue_stream_id'])
    op.create_index('idx_revenue_forecast_year_month', 'revenue_forecasts', ['forecast_year', 'forecast_month'])
    op.create_index(op.f('ix_revenue_forecasts_forecast_month'), 'revenue_forecasts', ['forecast_month'])
    op.create_index(op.f('ix_revenue_forecasts_forecast_year'), 'revenue_forecasts', ['forecast_year'])
    op.create_index(op.f('ix_revenue_forecasts_id'), 'revenue_forecasts', ['id'])


def downgrade() -> None:
    # ### Drop Tables ###
    op.drop_table('revenue_forecasts')
    op.drop_table('seasonality_coefficients')
    op.drop_table('customer_metrics')
    op.drop_table('revenue_actuals')
    op.drop_table('revenue_plan_details')
    op.drop_table('revenue_plan_versions')
    op.drop_table('revenue_plans')
    op.drop_table('revenue_categories')
    op.drop_table('revenue_streams')

    # ### Drop Enums ###
    op.execute('DROP TYPE IF EXISTS revenueversionstatusenum')
    op.execute('DROP TYPE IF EXISTS revenueplanstatusenum')
    op.execute('DROP TYPE IF EXISTS revenuecategorytypeenum')
    op.execute('DROP TYPE IF EXISTS revenuestreamtypeenum')
