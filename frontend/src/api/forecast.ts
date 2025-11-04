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

export interface ForecastScenario {
  name: string
  label: string
  probability: number
  total: number
  range_min: number
  range_max: number
  description: string
}

export interface ForecastItem {
  description: string
  amount: number
  range_min: number
  range_max: number
  reasoning: string
  source: 'plan' | 'history' | 'other'
  confidence: number
  category_hint?: number | null
}

export interface ForecastCorrelation {
  driver: string
  impact: string
  confidence: number
  lag_months?: number | null
}

export interface ForecastRecommendation {
  title: string
  description: string
  potential_saving?: number | null
}

export interface ForecastBaselineMetrics {
  simple_average?: number | null
  moving_average?: number | null
  seasonal_reference?: number | null
  last_12_months_total?: number | null
}

export interface ForecastAnomalySummaryItem {
  year: number
  month: number
  total: number
  deviation_percent: number
}

export interface ForecastAnomalySummary {
  items: ForecastAnomalySummaryItem[]
  mean?: number | null
  std?: number | null
  threshold?: number | null
}

export interface ForecastPlanContextItem {
  category_name?: string | null
  planned_amount?: number | null
  justification?: string | null
  calculation_method?: string | null
}

export interface AIForecastResponse {
  success: boolean
  forecast_total: number
  confidence: number
  items: ForecastItem[]
  scenarios: ForecastScenario[]
  correlations: ForecastCorrelation[]
  recommendations: ForecastRecommendation[]
  summary: string
  quality_notes?: string
  baseline_metrics?: ForecastBaselineMetrics
  anomaly_summary?: ForecastAnomalySummary
  plan_context?: ForecastPlanContextItem[]
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
