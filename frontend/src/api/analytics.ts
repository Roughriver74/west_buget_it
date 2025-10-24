import apiClient from './client'
import type {
  DashboardData,
  BudgetExecution,
  PaymentCalendar,
  PaymentsByDay,
  PaymentForecast,
  ForecastSummary,
  ForecastMethod,
} from '@/types'

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

  // Payment Calendar methods
  getPaymentCalendar: async (params: {
    year?: number
    month?: number
    category_id?: number
    organization_id?: number
  }): Promise<PaymentCalendar> => {
    const { data } = await apiClient.get('/analytics/payment-calendar', { params })
    return data
  },

  getPaymentsByDay: async (params: {
    date: string
    category_id?: number
    organization_id?: number
  }): Promise<PaymentsByDay> => {
    const { date, ...otherParams } = params
    const { data } = await apiClient.get(`/analytics/payment-calendar/${date}`, {
      params: otherParams,
    })
    return data
  },

  // Payment Forecast methods
  getPaymentForecast: async (params: {
    start_date: string
    end_date: string
    method?: ForecastMethod
    lookback_days?: number
    category_id?: number
    organization_id?: number
  }): Promise<PaymentForecast> => {
    const { data } = await apiClient.get('/analytics/payment-forecast', { params })
    return data
  },

  getForecastSummary: async (params: {
    start_date: string
    end_date: string
    category_id?: number
    organization_id?: number
  }): Promise<ForecastSummary> => {
    const { data } = await apiClient.get('/analytics/payment-forecast/summary', { params })
    return data
  },
}
