/**
 * KPI Task Types
 *
 * TypeScript type definitions for KPI task management.
 */

// Enums matching backend
export type KPITaskStatus = 'TODO' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED'

export type KPITaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

// Core task interface
export interface KPITask {
  id: number
  employee_kpi_goal_id: number
  employee_id: number
  assigned_by_id: number | null
  department_id: number

  // Task details
  title: string
  description: string | null
  status: KPITaskStatus
  priority: KPITaskPriority

  // Complexity and estimation
  complexity: number | null // 1-10 scale
  estimated_hours: number | null
  actual_hours: number | null

  // Progress
  completion_percentage: number | null // 0-100%

  // Dates
  due_date: string | null
  start_date: string | null
  completed_at: string | null

  // Additional
  notes: string | null

  // Timestamps
  created_at: string
  updated_at: string
}

// Extended response with related data
export interface KPITaskResponse extends KPITask {
  employee_name?: string | null
  goal_name?: string | null
  assigned_by_name?: string | null
}

// Create task request
export interface KPITaskCreate {
  employee_kpi_goal_id: number
  employee_id: number
  title: string
  description?: string | null
  status?: KPITaskStatus
  priority?: KPITaskPriority
  complexity?: number | null
  estimated_hours?: number | null
  due_date?: string | null
  start_date?: string | null
  notes?: string | null
}

// Update task request
export interface KPITaskUpdate {
  title?: string
  description?: string | null
  status?: KPITaskStatus
  priority?: KPITaskPriority
  complexity?: number | null
  estimated_hours?: number | null
  actual_hours?: number | null
  completion_percentage?: number | null
  due_date?: string | null
  start_date?: string | null
  notes?: string | null
}

// Status update request
export interface KPITaskStatusUpdate {
  status: KPITaskStatus
  completion_percentage?: number | null
  notes?: string | null
}

// Complexity update request
export interface KPITaskComplexityUpdate {
  complexity: number // 1-10
  estimated_hours?: number | null
  notes?: string | null
}

// Bulk status update
export interface KPITaskBulkStatusUpdate {
  task_ids: number[]
  status: KPITaskStatus
  notes?: string | null
}

// Statistics
export interface KPITaskStatistics {
  total_tasks: number
  by_status: Record<KPITaskStatus, number>
  by_priority: Record<KPITaskPriority, number>
  avg_complexity: number | null
  total_estimated_hours: number | null
  total_actual_hours: number | null
  completion_rate: number // percentage
  overdue_tasks: number
}

// Filter options for API requests
export interface KPITaskFilters {
  employee_id?: number
  employee_kpi_goal_id?: number
  status?: KPITaskStatus
  priority?: KPITaskPriority
  overdue_only?: boolean
  department_id?: number
  skip?: number
  limit?: number
}

// UI-specific types
export interface KPITaskFormValues {
  title: string
  description: string
  status: KPITaskStatus
  priority: KPITaskPriority
  complexity: number | null
  estimated_hours: number | null
  due_date: string | null
  notes: string
}

// Task priority display config
export const TASK_PRIORITY_CONFIG: Record<
  KPITaskPriority,
  { label: string; color: string; badge: string }
> = {
  LOW: { label: 'Низкий', color: 'default', badge: 'L' },
  MEDIUM: { label: 'Средний', color: 'blue', badge: 'M' },
  HIGH: { label: 'Высокий', color: 'orange', badge: 'H' },
  CRITICAL: { label: 'Критический', color: 'red', badge: '!' },
}

// Task status display config
export const TASK_STATUS_CONFIG: Record<
  KPITaskStatus,
  { label: string; color: string; icon: string }
> = {
  TODO: { label: 'К выполнению', color: 'default', icon: 'ClockCircleOutlined' },
  IN_PROGRESS: { label: 'В работе', color: 'processing', icon: 'SyncOutlined' },
  DONE: { label: 'Выполнено', color: 'success', icon: 'CheckCircleOutlined' },
  CANCELLED: { label: 'Отменено', color: 'error', icon: 'CloseCircleOutlined' },
}

// Complexity scale labels
export const COMPLEXITY_LABELS: Record<number, string> = {
  1: 'Очень простая',
  2: 'Простая',
  3: 'Несложная',
  4: 'Средняя',
  5: 'Умеренная',
  6: 'Умеренно сложная',
  7: 'Сложная',
  8: 'Очень сложная',
  9: 'Крайне сложная',
  10: 'Максимальная сложность',
}
