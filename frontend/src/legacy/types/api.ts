export type Decimal = number

export interface Organization {
  id: number
  name: string
  inn?: string | null
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface OrganizationList {
  items: Organization[]
}

export interface BankAccount {
  id: number
  account_number: string
  bank_name?: string | null
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface BankAccountList {
  items: BankAccount[]
}

export interface Contract {
  id: number
  contract_number: string
  contract_date?: string | null
  contract_type?: string | null
  counterparty?: string | null
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface ContractList {
  items: Contract[]
}

export interface Receipt {
  id: number
  operation_id: string
  organization: string
  operation_type?: string | null
  bank_account?: string | null
  accounting_account?: string | null
  document_number?: string | null
  document_date?: string | null
  payer?: string | null
  payer_account?: string | null
  settlement_account?: string | null
  contract_number?: string | null
  contract_date?: string | null
  currency?: string | null
  amount: Decimal
  commission?: Decimal | null
  payment_purpose?: string | null
  responsible_person?: string | null
  comment?: string | null
}

export interface ReceiptList {
  total: number
  items: Receipt[]
}

export interface Expense {
  id: number
  operation_id: string
  organization: string
  operation_type?: string | null
  bank_account?: string | null
  accounting_account?: string | null
  document_number?: string | null
  document_date?: string | null
  recipient?: string | null
  recipient_account?: string | null
  debit_account?: string | null
  contract_number?: string | null
  contract_date?: string | null
  currency?: string | null
  amount: Decimal
  expense_article?: string | null
  payment_purpose?: string | null
  responsible_person?: string | null
  comment?: string | null
  tax_period?: string | null
  unconfirmed_by_bank: boolean
}

export interface ExpenseList {
  total: number
  items: Expense[]
}

export interface ExpenseDetail {
  id: number
  expense_operation_id: string
  contract_number?: string | null
  repayment_type?: string | null
  settlement_account?: string | null
  advance_account?: string | null
  payment_type?: string | null
  payment_amount?: Decimal | null
  settlement_rate?: Decimal | null
  settlement_amount?: Decimal | null
  vat_amount?: Decimal | null
  expense_amount?: Decimal | null
  vat_in_expense?: Decimal | null
  created_at?: string
}

export interface ExpenseDetailList {
  total: number
  items: ExpenseDetail[]
}

export interface ReceiptQueryParams {
  skip?: number
  limit?: number
  department_id?: number
  organization?: string
  bank_account?: string
  date_from?: string
  date_to?: string
  contract_number?: string
  payer?: string
}

export interface ExpenseQueryParams {
  skip?: number
  limit?: number
  department_id?: number
  organization?: string
  bank_account?: string
  date_from?: string
  date_to?: string
  contract_number?: string
  recipient?: string
  expense_article?: string
}

export interface ExpenseDetailQueryParams {
  skip?: number
  limit?: number
  department_id?: number
  date_from?: string
  date_to?: string
  expense_operation_id?: string
  contract_number?: string
  payment_type?: string
}

