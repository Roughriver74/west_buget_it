-- Add extended fields to bank_transactions table
-- Migration: add_extended_bank_fields

-- Create enums
CREATE TYPE regionenum AS ENUM ('MOSCOW', 'SPB', 'REGIONS', 'FOREIGN');
CREATE TYPE documenttypeenum AS ENUM ('PAYMENT_ORDER', 'CASH_ORDER', 'INVOICE', 'ACT', 'CONTRACT', 'OTHER');

-- Add new columns
ALTER TABLE bank_transactions
  ADD COLUMN IF NOT EXISTS region regionenum,
  ADD COLUMN IF NOT EXISTS exhibition VARCHAR(255),
  ADD COLUMN IF NOT EXISTS document_type documenttypeenum,
  ADD COLUMN IF NOT EXISTS amount_rub_credit NUMERIC(15, 2),
  ADD COLUMN IF NOT EXISTS amount_eur_credit NUMERIC(15, 2),
  ADD COLUMN IF NOT EXISTS amount_rub_debit NUMERIC(15, 2),
  ADD COLUMN IF NOT EXISTS amount_eur_debit NUMERIC(15, 2),
  ADD COLUMN IF NOT EXISTS transaction_month INTEGER,
  ADD COLUMN IF NOT EXISTS transaction_year INTEGER,
  ADD COLUMN IF NOT EXISTS expense_acceptance_month INTEGER,
  ADD COLUMN IF NOT EXISTS expense_acceptance_year INTEGER;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_bank_transactions_region ON bank_transactions(region);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_transaction_month ON bank_transactions(transaction_month);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_transaction_year ON bank_transactions(transaction_year);

-- Comments
COMMENT ON COLUMN bank_transactions.region IS 'Регион операции';
COMMENT ON COLUMN bank_transactions.exhibition IS 'Выставка/мероприятие';
COMMENT ON COLUMN bank_transactions.document_type IS 'Тип документа';
COMMENT ON COLUMN bank_transactions.amount_rub_credit IS 'Приход в рублях';
COMMENT ON COLUMN bank_transactions.amount_eur_credit IS 'Приход в евро';
COMMENT ON COLUMN bank_transactions.amount_rub_debit IS 'Расход в рублях';
COMMENT ON COLUMN bank_transactions.amount_eur_debit IS 'Расход в евро';
COMMENT ON COLUMN bank_transactions.transaction_month IS 'Месяц операции (1-12)';
COMMENT ON COLUMN bank_transactions.transaction_year IS 'Год операции';
COMMENT ON COLUMN bank_transactions.expense_acceptance_month IS 'Месяц принятия к расходу (1-12)';
COMMENT ON COLUMN bank_transactions.expense_acceptance_year IS 'Год принятия к расходу';
