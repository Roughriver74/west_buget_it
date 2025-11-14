import apiClient from './client'
import type {
  BankTransaction,
  BankTransactionCreate,
  BankTransactionUpdate,
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
} from '@/types/bankTransaction'

export const bankTransactionsApi = {
  // List transactions with filters
  getTransactions: async (params?: {
    skip?: number
    limit?: number
    status?: BankTransactionStatus
    transaction_type?: BankTransactionType
    category_id?: number
    organization_id?: number
    department_id?: number
    date_from?: string
    date_to?: string
    search?: string
    only_unprocessed?: boolean
    has_expense?: boolean
  }): Promise<BankTransactionList> => {
    const { data } = await apiClient.get('/bank-transactions', { params })
    return data
  },

  // Get statistics
  getStats: async (params?: {
    department_id?: number
    date_from?: string
    date_to?: string
  }): Promise<BankTransactionStats> => {
    const { data } = await apiClient.get('/bank-transactions/stats', { params })
    return data
  },

  // Get single transaction
  getTransaction: async (id: number): Promise<BankTransaction> => {
    const { data } = await apiClient.get(`/bank-transactions/${id}`)
    return data
  },

  // Update transaction
  updateTransaction: async (
    id: number,
    updates: BankTransactionUpdate
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

  // Import from Excel
  importFromExcel: async (
    file: File,
    departmentId?: number
  ): Promise<BankTransactionImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    if (departmentId) {
      formData.append('department_id', departmentId.toString())
    }

    const { data } = await apiClient.post('/bank-transactions/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },
}
