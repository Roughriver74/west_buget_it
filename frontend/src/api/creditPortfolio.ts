import apiClient from './client'

// Types will be defined later in types/creditPortfolio.ts
export interface FinOrganization {
  id: number
  name: string
  inn?: string
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface FinBankAccount {
  id: number
  account_number: string
  bank_name?: string
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface FinContract {
  id: number
  contract_number: string
  contract_date?: string
  contract_type?: string
  principal?: number
  interest?: number
  total_paid?: number | null
  counterparty?: string
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface FinReceipt {
  id: number
  operation_id: string
  organization_id: number
  bank_account_id?: number
  contract_id?: number
  operation_type?: string
  accounting_account?: string
  document_number?: string
  document_date?: string
  payer?: string
  payer_account?: string
  settlement_account?: string
  contract_date?: string
  currency: string
  amount: number
  commission?: number
  payment_purpose?: string
  responsible_person?: string
  comment?: string
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface FinExpense {
  id: number
  operation_id: string
  organization_id: number
  bank_account_id?: number
  contract_id?: number
  operation_type?: string
  accounting_account?: string
  document_number?: string
  document_date?: string
  recipient?: string
  recipient_account?: string
  debit_account?: string
  contract_date?: string
  currency: string
  amount: number
  expense_article?: string
  payment_purpose?: string
  responsible_person?: string
  comment?: string
  tax_period?: string
  unconfirmed_by_bank: boolean
  is_active: boolean
  department_id: number
  created_at: string
  updated_at?: string
}

export interface FinExpenseDetail {
  id: number
  expense_operation_id: string
  contract_number?: string
  repayment_type?: string
  settlement_account?: string
  advance_account?: string
  payment_type?: string
  payment_amount?: number
  settlement_rate?: number
  settlement_amount?: number
  vat_amount?: number
  expense_amount?: number
  vat_in_expense?: number
  department_id: number
  created_at: string
}

export interface CreditPortfolioSummary {
  total_receipts: number
  total_expenses: number
  net_balance: number
  active_contracts_count: number
  total_interest: number
  total_principal: number
}

export interface MonthlyStats {
  month: string
  receipts: number
  expenses: number
  net: number
}

export const creditPortfolioApi = {
  // ==================== Organizations ====================
  getOrganizations: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    is_active?: boolean
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/organizations', { params })
    return data
  },

  getOrganization: async (id: number) => {
    const { data } = await apiClient.get(`/credit-portfolio/organizations/${id}`)
    return data
  },

  // ==================== Bank Accounts ====================
  getBankAccounts: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    is_active?: boolean
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/bank-accounts', { params })
    return data
  },

  getBankAccount: async (id: number) => {
    const { data } = await apiClient.get(`/credit-portfolio/bank-accounts/${id}`)
    return data
  },

  // ==================== Contracts ====================
  getContracts: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    is_active?: boolean
    contract_type?: string
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/contracts', { params })
    return data
  },

  getContract: async (id: number) => {
    const { data } = await apiClient.get(`/credit-portfolio/contracts/${id}`)
    return data
  },

  // ==================== Receipts ====================
  getReceipts: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    organization_id?: number
    bank_account_id?: number
    contract_id?: number
    date_from?: string
    date_to?: string
  }): Promise<FinReceipt[]> => {
    const { data } = await apiClient.get('/credit-portfolio/receipts', { params })
    return data
  },

  getReceipt: async (id: number): Promise<FinReceipt> => {
    const { data } = await apiClient.get(`/credit-portfolio/receipts/${id}`)
    return data
  },

  // ==================== Expenses ====================
  getExpenses: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    organization_id?: number
    bank_account_id?: number
    contract_id?: number
    date_from?: string
    date_to?: string
  }): Promise<FinExpense[]> => {
    const { data } = await apiClient.get('/credit-portfolio/expenses', { params })
    return data
  },

  getExpense: async (id: number): Promise<FinExpense> => {
    const { data } = await apiClient.get(`/credit-portfolio/expenses/${id}`)
    return data
  },

  // ==================== Expense Details ====================
  getExpenseDetails: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<FinExpenseDetail[]> => {
    const { data } = await apiClient.get('/credit-portfolio/expense-details', { params })
    return data
  },

  // ==================== Analytics ====================
  getSummary: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<CreditPortfolioSummary> => {
    const { data } = await apiClient.get('/credit-portfolio/summary', { params })
    return data
  },

  getMonthlyStats: async (params?: {
    department_id?: number
    year?: number
  }): Promise<MonthlyStats[]> => {
    const { data } = await apiClient.get('/credit-portfolio/monthly-stats', { params })
    return data
  },

  getContractStats: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/contract-stats', { params })
    return data
  },

  getOrganizationStats: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/organization-stats', { params })
    return data
  },

  // ==================== Advanced Analytics ====================
  getMonthlyEfficiency: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
    organization_id?: number
    bank_account_id?: number
  }) => {
    const response = await apiClient.get('/credit-portfolio/analytics/monthly-efficiency', { params })
    return response.data.data || []
  },

  getOrgEfficiency: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
    organization_id?: number
  }) => {
    const response = await apiClient.get('/credit-portfolio/analytics/org-efficiency', { params })
    return response.data.data || []
  },

  getCashflowMonthly: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
    organization_id?: number
  }) => {
    const response = await apiClient.get('/credit-portfolio/analytics/cashflow-monthly', { params })
    return response.data.data || []
  },

  getYearlyComparison: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
    exclude_contracts?: string
  }) => {
    const response = await apiClient.get('/credit-portfolio/analytics/yearly-comparison', { params })
    return response.data.data || []
  },

  // ==================== Import ====================
  triggerImport: async () => {
    const { data } = await apiClient.post('/credit-portfolio/import/trigger')
    return data
  },

  getImportLogs: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
  }) => {
    const { data } = await apiClient.get('/credit-portfolio/import/logs', { params })
    return data
  },

  // ==================== Test Data ====================
  loadTestData: async (force: boolean = false) => {
    const { data } = await apiClient.post('/credit-portfolio/load-test-data', null, {
      params: { force }
    })
    return data
  },
}
