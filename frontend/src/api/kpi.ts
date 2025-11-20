import apiClient from './client'
import type { components } from '@/types/api.generated'

export type KPIGoal = components['schemas']['KPIGoalInDB']
export type KPIGoalCreate = components['schemas']['KPIGoalCreate']
export type KPIGoalUpdate = components['schemas']['KPIGoalUpdate']
export type KPIGoalStatus = components['schemas']['KPIGoalStatusEnum']

// Task Complexity Bonus Extension (Task 3.2)
export type EmployeeKPI = components['schemas']['EmployeeKPIWithGoals'] & {
  task_complexity_avg?: number | null
  task_complexity_multiplier?: number | null
  task_complexity_weight?: number | null
  monthly_bonus_complexity?: number | null
  quarterly_bonus_complexity?: number | null
  annual_bonus_complexity?: number | null
}

export type EmployeeKPICreate = components['schemas']['EmployeeKPICreate']
export type EmployeeKPIUpdate = components['schemas']['EmployeeKPIUpdate']

export type EmployeeKPIGoal = components['schemas']['EmployeeKPIGoalWithDetails']
export type EmployeeKPIGoalCreate = components['schemas']['EmployeeKPIGoalCreate']
export type EmployeeKPIGoalUpdate = components['schemas']['EmployeeKPIGoalUpdate']

export type KPIEmployeeSummary = components['schemas']['KPIEmployeeSummary']
export type BonusType = components['schemas']['BonusTypeEnum']

// Manual type definitions for analytics (not auto-generated)
export interface KPIDepartmentSummary {
  department_id: number
  department_name: string
  year: number
  month: number | null
  avg_kpi_percentage: string | number
  total_employees: number
  total_bonus_calculated: string | number
  goals_count: number
  goals_achieved: number
}

export interface KPIGoalProgress {
  goal_id: number
  goal_name: string
  category: string | null
  target_value: string | number | null
  metric_unit: string | null
  employees_assigned: number
  employees_achieved: number
  avg_achievement_percentage: string | number
  total_weight: string | number
}

export interface KPIImportResult {
  success: boolean
  message: string
  statistics: {
    employees_created: number
    employees_updated: number
    kpi_records_created: number
    kpi_records_updated: number
    total_processed: number
    errors: number
  }
  errors: string[] | null
}

export interface KPITrendData {
  month: number
  avg_kpi: number
  min_kpi: number
  max_kpi: number
  employee_count: number
  total_bonus: number
}

export interface BonusDistributionData {
  department_id: number
  department_name: string
  monthly_total: number
  quarterly_total: number
  annual_total: number
  total_bonus: number
  employee_count: number
}

// ============ KPI Goal Template Types ============
// TEMPORARILY DISABLED: KPI Task types missing due to kpi_tasks endpoint being disabled

// export type KPIGoalTemplate = components['schemas']['KPIGoalTemplateWithGoals']
// export type KPIGoalTemplateCreate = components['schemas']['KPIGoalTemplateCreate']
// export type KPIGoalTemplateUpdate = components['schemas']['KPIGoalTemplateUpdate']
// export type KPIGoalTemplateItem = components['schemas']['KPIGoalTemplateItemWithGoal']

// Temporary placeholder types until KPITask model is implemented
export interface KPIGoalTemplate {
  id: number
  name: string
  description?: string
  department_id: number
  is_active: boolean
  template_items?: KPIGoalTemplateItem[]
  template_goals?: any[] // For backward compatibility
}

export interface KPIGoalTemplateCreate {
  name: string
  description?: string
  department_id?: number
  is_active?: boolean
}

export interface KPIGoalTemplateUpdate {
  name?: string
  description?: string
  is_active?: boolean
}

export interface KPIGoalTemplateItem {
  id: number
  template_id: number
  kpi_goal?: any
}

export interface ApplyTemplateRequest {
  employee_ids: number[]
  year: number
  month: number
}

export interface ApplyTemplateResponse {
  success: boolean
  message: string
  employees_updated: number
  goals_created: number
  errors: string[]
}

export const kpiApi = {
  listGoals: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    year?: number
    status?: KPIGoalStatus
    category?: string
  }): Promise<KPIGoal[]> => {
    const { data } = await apiClient.get<KPIGoal[]>('kpi/goals', { params })
    return data
  },

  createGoal: async (payload: KPIGoalCreate): Promise<KPIGoal> => {
    const { data } = await apiClient.post<KPIGoal>('kpi/goals', payload)
    return data
  },

  updateGoal: async (id: number, payload: KPIGoalUpdate): Promise<KPIGoal> => {
    const { data } = await apiClient.put<KPIGoal>(`kpi/goals/${id}`, payload)
    return data
  },

  deleteGoal: async (id: number): Promise<void> => {
    await apiClient.delete(`kpi/goals/${id}`)
  },

  listEmployeeKpis: async (params?: {
    skip?: number
    limit?: number
    department_id?: number
    employee_id?: number
    year?: number
    month?: number
  }): Promise<EmployeeKPI[]> => {
    const { data } = await apiClient.get<EmployeeKPI[]>('kpi/employee-kpis', { params })
    return data
  },

  createEmployeeKpi: async (payload: EmployeeKPICreate): Promise<components['schemas']['EmployeeKPIInDB']> => {
    const { data } = await apiClient.post<components['schemas']['EmployeeKPIInDB']>('kpi/employee-kpis', payload)
    return data
  },

  updateEmployeeKpi: async (id: number, payload: EmployeeKPIUpdate): Promise<components['schemas']['EmployeeKPIInDB']> => {
    const { data } = await apiClient.put<components['schemas']['EmployeeKPIInDB']>(`kpi/employee-kpis/${id}`, payload)
    return data
  },

  deleteEmployeeKpi: async (id: number): Promise<void> => {
    await apiClient.delete(`kpi/employee-kpis/${id}`)
  },

  listAssignments: async (params?: {
    skip?: number
    limit?: number
    employee_id?: number
    goal_id?: number
    year?: number
    month?: number
    status?: KPIGoalStatus
  }): Promise<EmployeeKPIGoal[]> => {
    const { data } = await apiClient.get<EmployeeKPIGoal[]>('kpi/employee-kpi-goals', { params })
    return data
  },

  createAssignment: async (payload: EmployeeKPIGoalCreate): Promise<components['schemas']['EmployeeKPIGoalInDB']> => {
    const { data } = await apiClient.post<components['schemas']['EmployeeKPIGoalInDB']>('kpi/employee-kpi-goals', payload)
    return data
  },

  updateAssignment: async (id: number, payload: EmployeeKPIGoalUpdate): Promise<components['schemas']['EmployeeKPIGoalInDB']> => {
    const { data } = await apiClient.put<components['schemas']['EmployeeKPIGoalInDB']>(`kpi/employee-kpi-goals/${id}`, payload)
    return data
  },

  deleteAssignment: async (id: number): Promise<void> => {
    await apiClient.delete(`kpi/employee-kpi-goals/${id}`)
  },

  importEmployeeKpis: async (file: File): Promise<KPIImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post<KPIImportResult>('kpi/employee-kpis/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  getEmployeeSummary: async (params: { year: number; month?: number; department_id?: number }): Promise<KPIEmployeeSummary[]> => {
    const { data } = await apiClient.get<KPIEmployeeSummary[]>('kpi/analytics/employee-summary', { params })
    return data
  },

  getDepartmentSummary: async (params: { year: number; month?: number; department_id?: number }): Promise<KPIDepartmentSummary[]> => {
    const { data } = await apiClient.get<KPIDepartmentSummary[]>('kpi/analytics/department-summary', { params })
    return data
  },

  getGoalProgress: async (params: { year: number; month?: number; department_id?: number }): Promise<KPIGoalProgress[]> => {
    const { data } = await apiClient.get<KPIGoalProgress[]>('kpi/analytics/goal-progress', { params })
    return data
  },

  getKpiTrends: async (params: { year: number; employee_id?: number; department_id?: number }): Promise<KPITrendData[]> => {
    const { data } = await apiClient.get<KPITrendData[]>('kpi/analytics/kpi-trends', { params })
    return data
  },

  getBonusDistribution: async (params: { year: number; month?: number }): Promise<BonusDistributionData[]> => {
    const { data } = await apiClient.get<BonusDistributionData[]>('kpi/analytics/bonus-distribution', { params })
    return data
  },

  importKPI: async (file: File, year: number, month: number): Promise<KPIImportResult> => {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await apiClient.post<KPIImportResult>(
      `kpi/import?year=${year}&month=${month}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return data
  },

  // ==================== KPI Auto-Calculation ====================

  /**
   * Автоматический пересчет KPI% для конкретной записи EmployeeKPI
   */
  recalculateEmployeeKPI: async (employeeKpiId: number): Promise<{
    success: boolean
    message: string
    data: {
      employee_kpi_id: number
      kpi_percentage: number | null
      total_weight: number
      goals_count: number
      goals: Array<{
        goal_id: number
        goal_name: string
        achievement_percentage: number
        weight: number
        weighted_achievement: number
      }>
    }
  }> => {
    const { data } = await apiClient.post(`kpi/employees/kpi/${employeeKpiId}/recalculate`)
    return data
  },

  /**
   * Пересчет KPI% для сотрудника за конкретный период
   */
  recalculateKPIForPeriod: async (params: {
    employee_id: number
    year: number
    month: number
  }): Promise<{
    success: boolean
    message: string
    data: any
  }> => {
    const { data } = await apiClient.post('kpi/recalculate-period', null, { params })
    return data
  },

  /**
   * Массовый пересчет KPI% для всех сотрудников отдела за период
   */
  recalculateKPIForDepartment: async (params: {
    department_id: number
    year?: number
    month?: number
  }): Promise<{
    success: boolean
    message: string
    statistics: {
      total: number
      success: number
      errors: number
      error_details: Array<{
        employee_kpi_id: number
        employee_id: number
        period: string
        error: string
      }>
    }
  }> => {
    const { data } = await apiClient.post('kpi/recalculate-department', null, { params })
    return data
  },

  // ============ KPI Goal Templates ============

  listTemplates: async (params?: {
    department_id?: number
    is_active?: boolean
  }): Promise<KPIGoalTemplate[]> => {
    const { data } = await apiClient.get<KPIGoalTemplate[]>('kpi/templates', { params })
    return data
  },

  getTemplate: async (templateId: number): Promise<KPIGoalTemplate> => {
    const { data } = await apiClient.get<KPIGoalTemplate>(`kpi/templates/${templateId}`)
    return data
  },

  createTemplate: async (templateData: KPIGoalTemplateCreate): Promise<KPIGoalTemplate> => {
    const { data } = await apiClient.post<KPIGoalTemplate>('kpi/templates', templateData)
    return data
  },

  updateTemplate: async (
    templateId: number,
    templateData: KPIGoalTemplateUpdate
  ): Promise<KPIGoalTemplate> => {
    const { data } = await apiClient.put<KPIGoalTemplate>(`kpi/templates/${templateId}`, templateData)
    return data
  },

  deleteTemplate: async (templateId: number): Promise<void> => {
    await apiClient.delete(`kpi/templates/${templateId}`)
  },

  applyTemplate: async (
    templateId: number,
    request: ApplyTemplateRequest
  ): Promise<ApplyTemplateResponse> => {
    const { data } = await apiClient.post<ApplyTemplateResponse>(
      `kpi/templates/${templateId}/apply`,
      request
    )
    return data
  },
}
