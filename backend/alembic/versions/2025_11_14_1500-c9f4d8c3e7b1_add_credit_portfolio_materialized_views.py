"""add credit portfolio materialized views

Revision ID: c9f4d8c3e7b1
Revises: 22fbd61c50d0
Create Date: 2025-11-14 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c9f4d8c3e7b1'
down_revision: Union[str, None] = '22fbd61c50d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DROP TRIGGER IF EXISTS trg_receipts_refresh_mv ON fin_receipts;
    DROP TRIGGER IF EXISTS trg_expenses_refresh_mv ON fin_expenses;
    DROP TRIGGER IF EXISTS trg_expense_details_refresh_mv ON fin_expense_details;
    DROP FUNCTION IF EXISTS trigger_refresh_materialized_views() CASCADE;
    DROP FUNCTION IF EXISTS refresh_all_materialized_views() CASCADE;

    DROP MATERIALIZED VIEW IF EXISTS mv_monthly_efficiency CASCADE;
    CREATE MATERIALIZED VIEW mv_monthly_efficiency AS
    SELECT
        DATE_TRUNC('month', fe.document_date) AS month,
        SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) AS principal,
        SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END) AS interest,
        SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) +
        SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END) AS total,
        CASE
            WHEN (
                SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) +
                SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END)
            ) > 0
            THEN (
                SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) /
                (
                    SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) +
                    SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END)
                )
            ) * 100
            ELSE 0
        END AS efficiency
    FROM fin_expenses fe
    JOIN fin_expense_details fed ON fe.operation_id = fed.expense_operation_id
    WHERE fe.document_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', fe.document_date)
    ORDER BY month;

    CREATE UNIQUE INDEX idx_mv_monthly_efficiency_month ON mv_monthly_efficiency(month);
    COMMENT ON MATERIALIZED VIEW mv_monthly_efficiency IS 'Эффективность погашения по месяцам (principal vs interest)';

    DROP MATERIALIZED VIEW IF EXISTS mv_org_efficiency CASCADE;
    CREATE MATERIALIZED VIEW mv_org_efficiency AS
    WITH receipts_by_org AS (
        SELECT organization_id, SUM(amount) AS received
        FROM fin_receipts
        GROUP BY organization_id
    )
    SELECT
        COALESCE(o.name, 'Не указано') AS organization,
        SUM(fe.amount) AS total_paid,
        SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) AS principal,
        SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END) AS interest,
        COALESCE(r.received, 0) AS received,
        CASE
            WHEN SUM(fe.amount) > 0
            THEN (SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END) / SUM(fe.amount)) * 100
            ELSE 0
        END AS efficiency,
        CASE
            WHEN COALESCE(r.received, 0) > 0
            THEN ((COALESCE(r.received, 0) - SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END)) / COALESCE(r.received, 0)) * 100
            ELSE 0
        END AS debt_ratio
    FROM fin_expenses fe
    JOIN fin_expense_details fed ON fe.operation_id = fed.expense_operation_id
    LEFT JOIN fin_organizations o ON fe.organization_id = o.id
    LEFT JOIN receipts_by_org r ON fe.organization_id = r.organization_id
    GROUP BY o.name, r.received
    ORDER BY total_paid DESC;

    CREATE UNIQUE INDEX idx_mv_org_efficiency_org ON mv_org_efficiency(organization);
    COMMENT ON MATERIALIZED VIEW mv_org_efficiency IS 'Эффективность и долговая нагрузка по организациям';

    DROP MATERIALIZED VIEW IF EXISTS mv_contracts_summary CASCADE;
    CREATE MATERIALIZED VIEW mv_contracts_summary AS
    SELECT
        fc.contract_number,
        COALESCE(o.name, 'Не указано') AS organization,
        COUNT(fe.id) AS operations_count,
        SUM(fe.amount) AS total_paid,
        MAX(fe.document_date) AS last_payment,
        COALESCE(SUM(CASE WHEN fed.payment_type = 'Погашение долга' THEN fed.payment_amount ELSE 0 END), 0) AS principal,
        COALESCE(SUM(CASE WHEN fed.payment_type = 'Уплата процентов' THEN fed.payment_amount ELSE 0 END), 0) AS interest
    FROM fin_expenses fe
    LEFT JOIN fin_expense_details fed ON fe.operation_id = fed.expense_operation_id
    LEFT JOIN fin_contracts fc ON fe.contract_id = fc.id
    LEFT JOIN fin_organizations o ON fe.organization_id = o.id
    WHERE fe.contract_id IS NOT NULL
    GROUP BY fc.contract_number, o.name
    ORDER BY total_paid DESC;

    CREATE UNIQUE INDEX idx_mv_contracts_contract_org ON mv_contracts_summary(contract_number, organization);
    CREATE INDEX idx_mv_contracts_total_paid ON mv_contracts_summary(total_paid DESC);
    CREATE INDEX idx_mv_contracts_last_payment ON mv_contracts_summary(last_payment DESC);
    COMMENT ON MATERIALIZED VIEW mv_contracts_summary IS 'Сводка по договорам с агрегированными данными';

    DROP MATERIALIZED VIEW IF EXISTS mv_cashflow_monthly CASCADE;
    CREATE MATERIALIZED VIEW mv_cashflow_monthly AS
    WITH receipts_monthly AS (
        SELECT
            DATE_TRUNC('month', document_date) AS month,
            SUM(amount) AS inflow
        FROM fin_receipts
        WHERE document_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', document_date)
    ),
    expenses_monthly AS (
        SELECT
            DATE_TRUNC('month', document_date) AS month,
            SUM(amount) AS outflow
        FROM fin_expenses
        WHERE document_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', document_date)
    )
    SELECT
        COALESCE(r.month, e.month) AS month,
        COALESCE(r.inflow, 0) AS inflow,
        COALESCE(e.outflow, 0) AS outflow,
        COALESCE(r.inflow, 0) - COALESCE(e.outflow, 0) AS net
    FROM receipts_monthly r
    FULL OUTER JOIN expenses_monthly e ON r.month = e.month
    ORDER BY COALESCE(r.month, e.month);

    CREATE UNIQUE INDEX idx_mv_cashflow_month ON mv_cashflow_monthly(month);
    COMMENT ON MATERIALIZED VIEW mv_cashflow_monthly IS 'Месячный cash flow (приток, отток, баланс)';

    DROP MATERIALIZED VIEW IF EXISTS mv_yearly_comparison CASCADE;
    CREATE MATERIALIZED VIEW mv_yearly_comparison AS
    WITH receipts_yearly AS (
        SELECT
            EXTRACT(YEAR FROM document_date)::INTEGER AS year,
            SUM(amount) AS received
        FROM fin_receipts
        WHERE document_date IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM document_date)
    ),
    expenses_yearly AS (
        SELECT
            EXTRACT(YEAR FROM document_date)::INTEGER AS year,
            SUM(amount) AS paid
        FROM fin_expenses
        WHERE document_date IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM document_date)
    )
    SELECT
        COALESCE(r.year, e.year) AS year,
        COALESCE(r.received, 0) AS received,
        COALESCE(e.paid, 0) AS paid,
        COALESCE(r.received, 0) - COALESCE(e.paid, 0) AS net
    FROM receipts_yearly r
    FULL OUTER JOIN expenses_yearly e ON r.year = e.year
    ORDER BY COALESCE(r.year, e.year);

    CREATE UNIQUE INDEX idx_mv_yearly_year ON mv_yearly_comparison(year);
    COMMENT ON MATERIALIZED VIEW mv_yearly_comparison IS 'Годовое сравнение поступлений и платежей';

    CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
    RETURNS void AS $$
    BEGIN
        REFRESH MATERIALIZED VIEW mv_monthly_efficiency;
        REFRESH MATERIALIZED VIEW mv_org_efficiency;
        REFRESH MATERIALIZED VIEW mv_contracts_summary;
        REFRESH MATERIALIZED VIEW mv_cashflow_monthly;
        REFRESH MATERIALIZED VIEW mv_yearly_comparison;
        RAISE NOTICE 'All materialized views refreshed successfully at %', NOW();
    END;
    $$ LANGUAGE plpgsql;

    COMMENT ON FUNCTION refresh_all_materialIZED_views IS 'Обновляет все materialized views одним вызовом';

    CREATE OR REPLACE FUNCTION trigger_refresh_materialIZED_views()
    RETURNS trigger AS $$
    BEGIN
        RAISE NOTICE 'Data changed in %. Materialized views need refresh.', TG_TABLE_NAME;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_receipts_refresh_mv ON fin_receipts;
    CREATE TRIGGER trg_receipts_refresh_mv
        AFTER INSERT OR UPDATE OR DELETE ON fin_receipts
        FOR EACH STATEMENT
        EXECUTE FUNCTION trigger_refresh_materialIZED_views();

    DROP TRIGGER IF EXISTS trg_expenses_refresh_mv ON fin_expenses;
    CREATE TRIGGER trg_expenses_refresh_mv
        AFTER INSERT OR UPDATE OR DELETE ON fin_expenses
        FOR EACH STATEMENT
        EXECUTE FUNCTION trigger_refresh_materialIZED_views();

    DROP TRIGGER IF EXISTS trg_expense_details_refresh_mv ON fin_expense_details;
    CREATE TRIGGER trg_expense_details_refresh_mv
        AFTER INSERT OR UPDATE OR DELETE ON fin_expense_details
        FOR EACH STATEMENT
        EXECUTE FUNCTION trigger_refresh_materialIZED_views();

    SELECT refresh_all_materialIZED_views();
    """)


def downgrade() -> None:
    op.execute("""
    DROP TRIGGER IF EXISTS trg_receipts_refresh_mv ON receipts;
    DROP TRIGGER IF EXISTS trg_expenses_refresh_mv ON expenses;
    DROP TRIGGER IF EXISTS trg_expense_details_refresh_mv ON expense_details;

    DROP FUNCTION IF EXISTS trigger_refresh_materialized_views() CASCADE;
    DROP FUNCTION IF EXISTS refresh_all_materialized_views() CASCADE;

    DROP MATERIALIZED VIEW IF EXISTS mv_monthly_efficiency CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS mv_org_efficiency CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS mv_contracts_summary CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS mv_cashflow_monthly CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS mv_yearly_comparison CASCADE;
    """)

