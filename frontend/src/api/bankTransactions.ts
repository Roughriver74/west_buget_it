import apiClient from './client'
import type {
  BankTransaction,
  BankTransactionCategorize,
  BankTransactionLink,
  BankTransactionList,
  BankTransactionStats,
  BankTransactionImportResult,
  MatchingSuggestion,
  CategorySuggestion,
  RegularPaymentPattern,
  BulkCategorizeRequest,
  BulkStatusUpdateRequest,
  BankTransactionStatus,
  BankTransactionType,
  BankTransactionAnalytics,
  BankTransactionAnalyticsParams,
} from '@/types/bankTransaction'

export const bankTransactionsApi = {
  // List transactions with filters
  getTransactions: async (params?: {
    skip?: number
    limit?: number
    status?: BankTransactionStatus
    transaction_type?: BankTransactionType
    payment_source?: 'BANK' | 'CASH'
    category_id?: number
    organization_id?: number
    department_id?: number
    date_from?: string
    date_to?: string
    search?: string
    only_unprocessed?: boolean
    has_expense?: boolean
    account_number?: string
    account_is_null?: boolean
  }): Promise<BankTransactionList> => {
    const { data } = await apiClient.get('/bank-transactions', { params })
    return data
  },

  // Get statistics (with all filters for accurate totals)
  getStats: async (params?: {
    department_id?: number
    status?: BankTransactionStatus
    transaction_type?: BankTransactionType
    payment_source?: 'BANK' | 'CASH'
    date_from?: string
    date_to?: string
    search?: string
    account_number?: string
    account_is_null?: boolean
    category_id?: number
    organization_id?: number
    has_expense?: boolean
    only_unprocessed?: boolean
  }): Promise<BankTransactionStats> => {
    const { data } = await apiClient.get('/bank-transactions/stats', { params })
    return data
  },

  // Get single transaction
  getTransaction: async (id: number): Promise<BankTransaction> => {
    const { data } = await apiClient.get(`/bank-transactions/${id}`)
    return data
  },

  // Update transaction (category, status, notes)
  updateTransaction: async (
    id: number,
    updates: Partial<{ category_id?: number; status?: string; notes?: string }>
  ): Promise<BankTransaction> => {
    const { data } = await apiClient.put(`/bank-transactions/${id}`, updates)
    return data
  },

  // Categorize transaction
  categorize: async (
    id: number,
    request: BankTransactionCategorize
  ): Promise<BankTransaction> => {
    const { data } = await apiClient.put(`/bank-transactions/${id}/categorize`, request)
    return data
  },

  // Link transaction to expense
  linkToExpense: async (id: number, request: BankTransactionLink): Promise<BankTransaction> => {
    const { data } = await apiClient.put(`/bank-transactions/${id}/link`, request)
    return data
  },

  // Bulk categorize
  bulkCategorize: async (request: BulkCategorizeRequest): Promise<{ message: string; updated: number }> => {
    const { data } = await apiClient.post('/bank-transactions/bulk-categorize', request)
    return data
  },

  // Bulk status update
  bulkStatusUpdate: async (
    request: BulkStatusUpdateRequest
  ): Promise<{ message: string; updated: number }> => {
    const { data } = await apiClient.post('/bank-transactions/bulk-status-update', request)
    return data
  },

  // Get matching expenses
  getMatchingExpenses: async (id: number, limit?: number): Promise<MatchingSuggestion[]> => {
    const { data } = await apiClient.get(`/bank-transactions/${id}/matching-expenses`, {
      params: { limit },
    })
    return data
  },

  // Get AI category suggestions
  getCategorySuggestions: async (id: number, topN?: number): Promise<CategorySuggestion[]> => {
    const { data } = await apiClient.get(`/bank-transactions/${id}/category-suggestions`, {
      params: { top_n: topN },
    })
    return data
  },

  // Get regular payment patterns
  getRegularPatterns: async (departmentId?: number): Promise<RegularPaymentPattern[]> => {
    const { data } = await apiClient.get('/bank-transactions/regular-patterns', {
      params: { department_id: departmentId },
    })
    return data
  },

  // Delete transaction
  deleteTransaction: async (id: number): Promise<{ message: string }> => {
    const { data } = await apiClient.delete(`/bank-transactions/${id}`)
    return data
  },

  // Bulk delete transactions
  bulkDelete: async (transactionIds: number[]): Promise<{ message: string; deleted: number }> => {
    const { data } = await apiClient.post('/bank-transactions/bulk-delete', transactionIds)
    return data
  },

  // Preview import from Excel
  previewImport: async (file: File): Promise<{
    success: boolean
    columns: string[]
    detected_mapping: Record<string, string>
    sample_data: Record<string, any>[]
    total_rows: number
    required_fields: Record<string, string>
    error?: string
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await apiClient.post('/bank-transactions/import/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },

  // Import from Excel
  importFromExcel: async (
    file: File,
    departmentId?: number,
    columnMapping?: Record<string, string>
  ): Promise<BankTransactionImportResult> => {
    const formData = new FormData()
    formData.append('file', file)

    // department_id и column_mapping должны быть query параметрами
    const params = new URLSearchParams()
    if (departmentId) {
      params.append('department_id', departmentId.toString())
    }
    if (columnMapping) {
      params.append('column_mapping', JSON.stringify(columnMapping))
    }

    const url = `/bank-transactions/import${params.toString() ? `?${params.toString()}` : ''}`
    const { data } = await apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },

  // Test OData connection
  testODataConnection: async (params: {
    odata_url: string
    username: string
    password: string
    timeout?: number
  }): Promise<{
    success: boolean
    message: string
    status_code?: number
    url?: string
    error?: string
  }> => {
    const { data } = await apiClient.post('/bank-transactions/odata/test-connection', params)
    return data
  },

  // Sync from 1C OData (Background Task)
  syncFromOData: async (params: {
    odata_url: string
    username: string
    password: string
    entity_name?: string
    department_id: number
    organization_id?: number
    date_from?: string
    date_to?: string
    timeout?: number
  }): Promise<{
    task_id: string
    message: string
    status: string
    department: {
      id: number
      name: string
    }
  }> => {
    const { data } = await apiClient.post('/bank-transactions/odata/sync', params)
    return data
  },

  // Get OData sync task status
  getSyncStatus: async (taskId: string): Promise<{
    task_id: string
    status: 'STARTED' | 'COMPLETED' | 'FAILED'
    started_at: string
    completed_at?: string
    result?: {
      total_fetched: number
      created: number
      updated: number
      skipped: number
      auto_categorized: number
    }
    error?: string
  }> => {
    const { data } = await apiClient.get(`/bank-transactions/odata/sync/status/${taskId}`)
    return data
  },

  // Get comprehensive analytics
  getAnalytics: async (params?: BankTransactionAnalyticsParams): Promise<BankTransactionAnalytics> => {
    const { data } = await apiClient.get('/bank-transactions/analytics', { params })
    return data
  },
}
