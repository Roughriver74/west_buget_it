import apiClient from './client'
import type { components } from '@/types/api.generated'

export type KPIGoal = components['schemas']['KPIGoalInDB']
export type KPIGoalCreate = components['schemas']['KPIGoalCreate']
export type KPIGoalUpdate = components['schemas']['KPIGoalUpdate']
export type KPIGoalStatus = components['schemas']['KPIGoalStatusEnum']

export type EmployeeKPI = components['schemas']['EmployeeKPIWithGoals']
export type EmployeeKPICreate = components['schemas']['EmployeeKPICreate']
export type EmployeeKPIUpdate = components['schemas']['EmployeeKPIUpdate']

export type EmployeeKPIGoal = components['schemas']['EmployeeKPIGoalWithDetails']
export type EmployeeKPIGoalCreate = components['schemas']['EmployeeKPIGoalCreate']
export type EmployeeKPIGoalUpdate = components['schemas']['EmployeeKPIGoalUpdate']

export type KPIEmployeeSummary = components['schemas']['KPIEmployeeSummary']
export type BonusType = components['schemas']['BonusTypeEnum']

export interface KPIImportResult {
  created: number
  updated: number
  missing_employees: string[]
  missing_sheets: string[]
  no_access: string[]
  year: number
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
}
