import apiClient from './client'
import type { ForecastExpense } from '@/types'

export interface GenerateForecastRequest {
  target_month: number
  target_year: number
  department_id: number
  include_regular?: boolean
  include_average?: boolean
}

export interface GenerateAIForecastRequest {
  target_month: number
  target_year: number
  department_id: number
  category_id?: number
}

export interface AIForecastResponse {
  success: boolean
  forecast_total: number
  confidence: number
  items: Array<{
    description: string
    amount: number
    reasoning: string
  }>
  summary: string
  created_forecast_records: number
  target_month: number
  target_year: number
  ai_model?: string
  generated_at?: string
  historical_months?: number
  error?: string
}

export const forecastApi = {
  getAll: async (year: number, month: number, department_id: number): Promise<ForecastExpense[]> => {
    const { data } = await apiClient.get('forecast/', { params: { year, month, department_id } })
    return data
  },

  generate: async (request: GenerateForecastRequest) => {
    const { data } = await apiClient.post('forecast/generate', request)
    return data
  },

  generateAI: async (request: GenerateAIForecastRequest): Promise<AIForecastResponse> => {
    const { data } = await apiClient.post('forecast/ai-generate', request)
    return data
  },

  create: async (forecast: Partial<ForecastExpense>): Promise<ForecastExpense> => {
    const { data} = await apiClient.post('forecast/', forecast)
    return data
  },

  update: async (id: number, forecast: Partial<ForecastExpense>): Promise<ForecastExpense> => {
    const { data } = await apiClient.put(`forecast/${id}`, forecast)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`forecast/${id}`)
  },

  clear: async (year: number, month: number, department_id: number): Promise<void> => {
    await apiClient.delete(`forecast/clear/${year}/${month}`, { params: { department_id } })
  },

  exportToExcel: async (year: number, month: number, department_id: number): Promise<Blob> => {
    const response = await apiClient.get(`forecast/export/${year}/${month}`, {
      params: { department_id },
      responseType: 'blob'
    })
    return response.data
  },
}
