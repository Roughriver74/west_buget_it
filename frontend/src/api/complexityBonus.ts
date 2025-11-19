/**
 * Task Complexity Bonus API Client
 *
 * API functions for calculating and retrieving complexity-based bonus components.
 */

import apiClient from './client'

/**
 * Calculate complexity bonus for a single EmployeeKPI
 */
export const calculateComplexityBonus = async (kpiId: number) => {
  const response = await apiClient.post(`/api/v1/kpi/employee-kpis/${kpiId}/calculate-complexity`)
  return response.data
}

/**
 * Bulk calculate complexity bonuses for a period
 */
export const bulkCalculateComplexityBonuses = async (params: {
  year: number
  month: number
  department_id?: number
}) => {
  const response = await apiClient.post('/api/v1/kpi/employee-kpis/bulk/calculate-complexity', null, {
    params,
  })
  return response.data
}

/**
 * Get detailed breakdown of complexity bonus calculation
 */
export const getComplexityBreakdown = async (kpiId: number) => {
  const response = await apiClient.get(`/api/v1/kpi/employee-kpis/${kpiId}/complexity-breakdown`)
  return response.data
}

/**
 * Types for complexity bonus
 */
export interface ComplexityBonusBreakdown {
  employee_kpi_id: number
  employee_id: number
  employee_name: string
  period: string
  completed_tasks: Array<{
    id: number
    title: string
    complexity: number
    completed_at: string
  }>
  completed_tasks_count: number
  avg_complexity: number | null
  complexity_tier: 'simple' | 'medium' | 'complex' | 'unknown'
  complexity_multiplier: number | null
  complexity_weight: number
  bonuses: {
    monthly?: {
      base: number
      complexity_component: number
      formula: string
    }
    quarterly?: {
      base: number
      complexity_component: number
      formula: string
    }
    annual?: {
      base: number
      complexity_component: number
      formula: string
    }
  }
}

export interface BulkCalculateResponse {
  year: number
  month: number
  department_id: number
  updated_count: number
  skipped_count: number
  total_count: number
  message: string
}
