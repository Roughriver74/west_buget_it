import { creditPortfolioApi, type FinBankAccount, type FinContract, type FinExpense, type FinExpenseDetail, type FinOrganization, type FinReceipt } from '@/api/creditPortfolio'
import type {
  Expense,
  ExpenseDetail,
  ExpenseDetailList,
  ExpenseDetailQueryParams,
  ExpenseList,
  ExpenseQueryParams,
  Receipt,
  ReceiptList,
  ReceiptQueryParams,
} from '@/legacy/types/api'

type ReferenceCacheEntry = {
  timestamp: number
  organizations: FinOrganization[]
  bankAccounts: FinBankAccount[]
  contracts: FinContract[]
  orgMap: Map<number, string>
  bankMap: Map<number, { account_number: string; bank_name?: string | null }>
  contractMap: Map<number, string>
}

const referenceCache = new Map<string, ReferenceCacheEntry>()
const CACHE_TTL = 5 * 60 * 1000

const getCacheKey = (departmentId?: number) => String(departmentId ?? 'all')

async function getReferenceData(departmentId?: number): Promise<ReferenceCacheEntry> {
  const cacheKey = getCacheKey(departmentId)
  const cached = referenceCache.get(cacheKey)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached
  }

  const [organizations, bankAccounts, contracts] = await Promise.all([
    creditPortfolioApi.getOrganizations({ department_id: departmentId, limit: 10000 }),
    creditPortfolioApi.getBankAccounts({ department_id: departmentId, limit: 10000 }),
    creditPortfolioApi.getContracts({ department_id: departmentId, limit: 10000 }),
  ])

  const entry: ReferenceCacheEntry = {
    timestamp: Date.now(),
    organizations,
    bankAccounts,
    contracts,
    orgMap: new Map(organizations.map((org: FinOrganization) => [org.id, org.name])),
    bankMap: new Map(bankAccounts.map((bank: FinBankAccount) => [bank.id, { account_number: bank.account_number, bank_name: bank.bank_name }])),
    contractMap: new Map(contracts.map((contract: FinContract) => [contract.id, contract.contract_number])),
  }

  referenceCache.set(cacheKey, entry)
  return entry
}

const mapReceipt = (receipt: FinReceipt, refs: ReferenceCacheEntry): Receipt => ({
  id: receipt.id,
  operation_id: receipt.operation_id,
  organization: refs.orgMap.get(receipt.organization_id) ?? 'Не указано',
  operation_type: receipt.operation_type,
  bank_account: receipt.bank_account_id ? refs.bankMap.get(receipt.bank_account_id)?.account_number ?? null : null,
  accounting_account: receipt.accounting_account,
  document_number: receipt.document_number,
  document_date: receipt.document_date ?? null,
  payer: receipt.payer,
  payer_account: receipt.payer_account,
  settlement_account: receipt.settlement_account,
  contract_number: receipt.contract_id
    ? refs.contractMap.get(receipt.contract_id) ?? null
    : null,
  contract_date: receipt.contract_date ?? null,
  currency: receipt.currency,
  amount: Number(receipt.amount || 0),
  commission: receipt.commission ?? null,
  payment_purpose: receipt.payment_purpose,
  responsible_person: receipt.responsible_person,
  comment: receipt.comment,
})

const mapExpense = (expense: FinExpense, refs: ReferenceCacheEntry): Expense => ({
  id: expense.id,
  operation_id: expense.operation_id,
  organization: refs.orgMap.get(expense.organization_id) ?? 'Не указано',
  operation_type: expense.operation_type,
  bank_account: expense.bank_account_id ? refs.bankMap.get(expense.bank_account_id)?.account_number ?? null : null,
  accounting_account: expense.accounting_account,
  document_number: expense.document_number,
  document_date: expense.document_date ?? null,
  recipient: expense.recipient,
  recipient_account: expense.recipient_account,
  debit_account: expense.debit_account,
  contract_number: expense.contract_id
    ? refs.contractMap.get(expense.contract_id) ?? null
    : null,
  contract_date: expense.contract_date ?? null,
  currency: expense.currency,
  amount: Number(expense.amount || 0),
  expense_article: expense.expense_article,
  payment_purpose: expense.payment_purpose,
  responsible_person: expense.responsible_person,
  comment: expense.comment,
  tax_period: expense.tax_period,
  unconfirmed_by_bank: expense.unconfirmed_by_bank,
})

const mapExpenseDetail = (detail: FinExpenseDetail): ExpenseDetail => ({
  id: detail.id,
  expense_operation_id: detail.expense_operation_id,
  contract_number: detail.contract_number,
  repayment_type: detail.repayment_type,
  settlement_account: detail.settlement_account,
  advance_account: detail.advance_account,
  payment_type: detail.payment_type,
  payment_amount: detail.payment_amount ? Number(detail.payment_amount) : null,
  settlement_rate: detail.settlement_rate ? Number(detail.settlement_rate) : null,
  settlement_amount: detail.settlement_amount ? Number(detail.settlement_amount) : null,
  vat_amount: detail.vat_amount ? Number(detail.vat_amount) : null,
  expense_amount: detail.expense_amount ? Number(detail.expense_amount) : null,
  vat_in_expense: detail.vat_in_expense ? Number(detail.vat_in_expense) : null,
  created_at: detail.created_at,
})

export const receiptsAPI = {
  getAll: async (params?: ReceiptQueryParams): Promise<ReceiptList> => {
    const references = await getReferenceData(params?.department_id)
    const receipts = await creditPortfolioApi.getReceipts({
      skip: params?.skip ?? 0,
      limit: Math.min(params?.limit ?? 10000, 10000),
      department_id: params?.department_id,
      date_from: params?.date_from,
      date_to: params?.date_to,
    })
    const items = receipts.map(receipt => mapReceipt(receipt, references))
    return {
      total: items.length,
      items,
    }
  },
}

export const expensesAPI = {
  getAll: async (params?: ExpenseQueryParams): Promise<ExpenseList> => {
    const references = await getReferenceData(params?.department_id)
    const expenses = await creditPortfolioApi.getExpenses({
      skip: params?.skip ?? 0,
      limit: Math.min(params?.limit ?? 10000, 10000),
      department_id: params?.department_id,
      date_from: params?.date_from,
      date_to: params?.date_to,
    })
    const items = expenses.map(expense => mapExpense(expense, references))
    return {
      total: items.length,
      items,
    }
  },
}

export const expenseDetailsAPI = {
  getAll: async (params?: ExpenseDetailQueryParams): Promise<ExpenseDetailList> => {
    const details = await creditPortfolioApi.getExpenseDetails({
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 150000,
      department_id: params?.department_id,
      date_from: params?.date_from,
      date_to: params?.date_to,
    })
    const items = details.map(mapExpenseDetail)
    return {
      total: items.length,
      items,
    }
  },
}

