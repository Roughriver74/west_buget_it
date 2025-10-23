import apiClient from './client'
import type { BudgetCategory } from '@/types'

export const categoriesApi = {
  getAll: async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<BudgetCategory[]> => {
    const { data } = await apiClient.get('/categories', { params })
    return data
  },

  getById: async (id: number): Promise<BudgetCategory> => {
    const { data } = await apiClient.get(`/categories/${id}`)
    return data
  },

  create: async (category: Partial<BudgetCategory>): Promise<BudgetCategory> => {
    const { data } = await apiClient.post('/categories', category)
    return data
  },

  update: async (id: number, category: Partial<BudgetCategory>): Promise<BudgetCategory> => {
    const { data } = await apiClient.put(`/categories/${id}`, category)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  },
}
