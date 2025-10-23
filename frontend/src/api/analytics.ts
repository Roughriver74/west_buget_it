import apiClient from './client'
import type { DashboardData, BudgetExecution } from '@/types'

export const analyticsApi = {
  getDashboard: async (params?: { year?: number; month?: number }): Promise<DashboardData> => {
    const { data } = await apiClient.get('/analytics/dashboard', { params })
    return data
  },

  getBudgetExecution: async (year: number): Promise<BudgetExecution> => {
    const { data } = await apiClient.get('/analytics/budget-execution', { params: { year } })
    return data
  },

  getByCategory: async (params: { year: number; month?: number }) => {
    const { data } = await apiClient.get('/analytics/by-category', { params })
    return data
  },

  getTrends: async (params: { year: number; category_id?: number }) => {
    const { data } = await apiClient.get('/analytics/trends', { params })
    return data
  },
}
