import apiClient from './client'
import type { Expense, ExpenseList, ExpenseStatus } from '@/types'

export interface ExpenseFilters {
  skip?: number
  limit?: number
  status?: ExpenseStatus
  category_id?: number
  contractor_id?: number
  organization_id?: number
  department_id?: number
  date_from?: string
  date_to?: string
  search?: string
}

export const expensesApi = {
  getAll: async (filters?: ExpenseFilters): Promise<ExpenseList> => {
    const { data } = await apiClient.get('expenses/', { params: filters })
    return data
  },

  getById: async (id: number): Promise<Expense> => {
    const { data } = await apiClient.get(`expenses/${id}`)
    return data
  },

  create: async (expense: Partial<Expense>): Promise<Expense> => {
    const { data } = await apiClient.post('expenses/', expense)
    return data
  },

  update: async (id: number, expense: Partial<Expense>): Promise<Expense> => {
    const { data } = await apiClient.put(`expenses/${id}`, expense)
    return data
  },

  updateStatus: async (id: number, status: ExpenseStatus): Promise<Expense> => {
    const { data } = await apiClient.patch(`expenses/${id}/status`, { status })
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`expenses/${id}`)
  },

  bulkDelete: async (ids: number[]): Promise<{ deleted_count: number }> => {
    const { data } = await apiClient.post('expenses/bulk-delete', ids)
    return data
  },

  bulkTransferDepartment: async (
    expenseIds: number[],
    targetDepartmentId: number
  ): Promise<{ success: boolean; message: string; transferred_count: number; target_department: { id: number; name: string } }> => {
    const { data } = await apiClient.post('expenses/bulk/transfer-department', {
      expense_ids: expenseIds,
      target_department_id: targetDepartmentId,
    })
    return data
  },

  getTotals: async (filters?: { year?: number; month?: number; category_id?: number }) => {
    const { data } = await apiClient.get('expenses/stats/totals', { params: filters })
    return data
  },

  importFromFTP: async (params: {
    remote_path: string
    delete_from_year?: number
    delete_from_month?: number
    skip_duplicates?: boolean
  }) => {
    const { data } = await apiClient.post('expenses/import/ftp', params)
    return data
  },

  markReviewed: async (id: number): Promise<Expense> => {
    const { data } = await apiClient.patch(`expenses/${id}/mark-reviewed`)
    return data
  },
}
