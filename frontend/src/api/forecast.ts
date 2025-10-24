import apiClient from './client'
import type { ForecastExpense } from '@/types'

export interface GenerateForecastRequest {
  target_month: number
  target_year: number
  include_regular?: boolean
  include_average?: boolean
}

export const forecastApi = {
  getAll: async (year: number, month: number): Promise<ForecastExpense[]> => {
    const { data } = await apiClient.get('/forecast', { params: { year, month } })
    return data
  },

  generate: async (request: GenerateForecastRequest) => {
    const { data } = await apiClient.post('/forecast/generate', request)
    return data
  },

  create: async (forecast: Partial<ForecastExpense>): Promise<ForecastExpense> => {
    const { data } = await apiClient.post('/forecast', forecast)
    return data
  },

  update: async (id: number, forecast: Partial<ForecastExpense>): Promise<ForecastExpense> => {
    const { data } = await apiClient.put(`/forecast/${id}`, forecast)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/forecast/${id}`)
  },

  clear: async (year: number, month: number): Promise<void> => {
    await apiClient.delete(`/forecast/clear/${year}/${month}`)
  },
}
