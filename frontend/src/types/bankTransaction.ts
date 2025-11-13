/**
 * Types for Bank Transactions
 */

export enum BankTransactionType {
  DEBIT = 'DEBIT',
  CREDIT = 'CREDIT',
}

export enum BankTransactionStatus {
  NEW = 'NEW',
  CATEGORIZED = 'CATEGORIZED',
  MATCHED = 'MATCHED',
  APPROVED = 'APPROVED',
  NEEDS_REVIEW = 'NEEDS_REVIEW',
  IGNORED = 'IGNORED',
}

export interface BankTransaction {
  id: number
  transaction_date: string
  amount: number
  transaction_type: BankTransactionType
  counterparty_name?: string
  counterparty_inn?: string
  counterparty_kpp?: string
  counterparty_account?: string
  counterparty_bank?: string
  counterparty_bik?: string
  payment_purpose?: string
  organization_id?: number
  account_number?: string
  document_number?: string
  document_date?: string
  category_id?: number
  category_confidence?: number
  suggested_category_id?: number
  expense_id?: number
  matching_score?: number
  suggested_expense_id?: number
  status: BankTransactionStatus
  notes?: string
  is_regular_payment: boolean
  regular_payment_pattern_id?: number
  reviewed_by?: number
  reviewed_at?: string
  department_id: number
  import_source?: string
  import_file_name?: string
  imported_at?: string
  external_id_1c?: string
  is_active: boolean
  created_at: string
  updated_at?: string
  // Relations
  category_name?: string
  suggested_category_name?: string
  expense_number?: string
  suggested_expense_number?: string
  organization_name?: string
  reviewed_by_name?: string
  department_name?: string
}

export interface BankTransactionCreate {
  transaction_date: string
  amount: number
  transaction_type: BankTransactionType
  counterparty_name?: string
  counterparty_inn?: string
  counterparty_kpp?: string
  counterparty_account?: string
  counterparty_bank?: string
  counterparty_bik?: string
  payment_purpose?: string
  organization_id?: number
  account_number?: string
  document_number?: string
  document_date?: string
  notes?: string
  department_id: number
}

export interface BankTransactionUpdate {
  category_id?: number
  expense_id?: number
  status?: BankTransactionStatus
  notes?: string
  is_regular_payment?: boolean
}

export interface BankTransactionCategorize {
  category_id: number
  notes?: string
}

export interface BankTransactionLink {
  expense_id: number
  notes?: string
}

export interface BankTransactionList {
  total: number
  items: BankTransaction[]
  page: number
  page_size: number
  pages: number
}

export interface BankTransactionStats {
  total_transactions: number
  total_amount: number
  new_count: number
  categorized_count: number
  matched_count: number
  approved_count: number
  needs_review_count: number
  avg_category_confidence?: number
  avg_matching_score?: number
}

export interface BankTransactionImportResult {
  total_rows: number
  imported: number
  skipped: number
  errors: Array<{ row: number; error: string }>
  warnings: Array<{ row: number; warning: string }>
}

export interface MatchingSuggestion {
  expense_id: number
  expense_number: string
  expense_amount: number
  expense_date: string
  expense_category_id?: number
  expense_contractor_name?: string
  matching_score: number
  match_reasons: string[]
}

export interface CategorySuggestion {
  category_id: number
  category_name: string
  confidence: number
  reasoning: string[]
}

export interface RegularPaymentPattern {
  id: number
  counterparty_inn?: string
  counterparty_name?: string
  category_id: number
  category_name: string
  avg_amount: number
  frequency_days: number
  last_payment_date: string
  transaction_count: number
}

export interface BulkCategorizeRequest {
  transaction_ids: number[]
  category_id: number
  notes?: string
}

export interface BulkLinkRequest {
  links: Array<{ transaction_id: number; expense_id: number }>
}

export interface BulkStatusUpdateRequest {
  transaction_ids: number[]
  status: BankTransactionStatus
}
