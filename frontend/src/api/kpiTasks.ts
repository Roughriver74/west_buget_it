/**
 * KPI Tasks API Client
 *
 * API functions for managing KPI tasks.
 */

import apiClient from './client'
import type {
  KPITaskResponse,
  KPITaskCreate,
  KPITaskUpdate,
  KPITaskStatusUpdate,
  KPITaskComplexityUpdate,
  KPITaskBulkStatusUpdate,
  KPITaskStatistics,
  KPITaskFilters,
} from '@/types/kpiTask'

const BASE_URL = '/api/v1/kpi/tasks'

/**
 * Get list of KPI tasks with filtering
 */
export const getKPITasks = async (filters?: KPITaskFilters): Promise<KPITaskResponse[]> => {
  const response = await apiClient.get<KPITaskResponse[]>(BASE_URL, {
    params: filters,
  })
  return response.data
}

/**
 * Get single KPI task by ID
 */
export const getKPITask = async (taskId: number): Promise<KPITaskResponse> => {
  const response = await apiClient.get<KPITaskResponse>(`${BASE_URL}/${taskId}`)
  return response.data
}

/**
 * Create new KPI task
 */
export const createKPITask = async (task: KPITaskCreate): Promise<KPITaskResponse> => {
  const response = await apiClient.post<KPITaskResponse>(BASE_URL, task)
  return response.data
}

/**
 * Update KPI task
 */
export const updateKPITask = async (
  taskId: number,
  task: KPITaskUpdate
): Promise<KPITaskResponse> => {
  const response = await apiClient.put<KPITaskResponse>(`${BASE_URL}/${taskId}`, task)
  return response.data
}

/**
 * Delete KPI task
 */
export const deleteKPITask = async (taskId: number): Promise<void> => {
  await apiClient.delete(`${BASE_URL}/${taskId}`)
}

/**
 * Update task status
 */
export const updateKPITaskStatus = async (
  taskId: number,
  statusUpdate: KPITaskStatusUpdate
): Promise<KPITaskResponse> => {
  const response = await apiClient.post<KPITaskResponse>(
    `${BASE_URL}/${taskId}/status`,
    statusUpdate
  )
  return response.data
}

/**
 * Bulk update task status
 */
export const bulkUpdateKPITaskStatus = async (
  bulkUpdate: KPITaskBulkStatusUpdate
): Promise<{ success: boolean; message: string; updated_count: number; task_ids: number[] }> => {
  const response = await apiClient.post<{
    success: boolean
    message: string
    updated_count: number
    task_ids: number[]
  }>(`${BASE_URL}/bulk/status`, bulkUpdate)
  return response.data
}

/**
 * Update task complexity
 */
export const updateKPITaskComplexity = async (
  taskId: number,
  complexityUpdate: KPITaskComplexityUpdate
): Promise<KPITaskResponse> => {
  const response = await apiClient.post<KPITaskResponse>(
    `${BASE_URL}/${taskId}/complexity`,
    complexityUpdate
  )
  return response.data
}

/**
 * Get task statistics
 */
export const getKPITaskStatistics = async (
  employeeId?: number,
  departmentId?: number
): Promise<KPITaskStatistics> => {
  const response = await apiClient.get<KPITaskStatistics>(`${BASE_URL}/analytics/statistics`, {
    params: { employee_id: employeeId, department_id: departmentId },
  })
  return response.data
}

// Re-export types for convenience
export type {
  KPITaskResponse,
  KPITaskCreate,
  KPITaskUpdate,
  KPITaskStatusUpdate,
  KPITaskComplexityUpdate,
  KPITaskBulkStatusUpdate,
  KPITaskStatistics,
  KPITaskFilters,
}
