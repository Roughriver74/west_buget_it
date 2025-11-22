import apiClient from './client'
import type {
  WorkTimesheet,
  WorkTimesheetWithEmployee,
  WorkTimesheetCreate,
  WorkTimesheetUpdate,
  WorkTimesheetApprove,
  DailyWorkRecord,
  DailyWorkRecordCreate,
  DailyWorkRecordUpdate,
  DailyWorkRecordBulkCreate,
  TimesheetGrid,
  TimesheetSummary,
  EmployeeTimesheetStats,
  DepartmentTimesheetStats,
  TimesheetMonthlyComparison,
  TimesheetStatus,
} from '@/types/timesheet'

// ==================== Filter Interfaces ====================

export interface WorkTimesheetFilters {
  skip?: number
  limit?: number
  department_id?: number
  employee_id?: number
  year?: number
  month?: number
  status?: TimesheetStatus
}

export interface DailyWorkRecordFilters {
  skip?: number
  limit?: number
  timesheet_id?: string
  work_date_from?: string
  work_date_to?: string
}

export interface TimesheetGridParams {
  year: number
  month: number
  department_id?: number
}

export interface TimesheetAnalyticsParams {
  year?: number
  month?: number
  department_id?: number
  employee_id?: number
}

// ==================== API Client ====================

export const timesheetsApi = {
  // ============ WorkTimesheet CRUD ============

  getTimesheets: async (filters?: WorkTimesheetFilters): Promise<WorkTimesheetWithEmployee[]> => {
    const { data } = await apiClient.get('timesheets/', { params: filters })
    return data
  },

  getTimesheetById: async (id: string): Promise<WorkTimesheet> => {
    const { data } = await apiClient.get(`timesheets/${id}`)
    return data
  },

  createTimesheet: async (timesheet: WorkTimesheetCreate): Promise<WorkTimesheet> => {
    const { data } = await apiClient.post('timesheets/', timesheet)
    return data
  },

  updateTimesheet: async (id: string, timesheet: WorkTimesheetUpdate): Promise<WorkTimesheet> => {
    const { data } = await apiClient.put(`timesheets/${id}`, timesheet)
    return data
  },

  approveTimesheet: async (id: string, approval: WorkTimesheetApprove): Promise<WorkTimesheet> => {
    const { data } = await apiClient.post(`timesheets/${id}/approve`, approval)
    return data
  },

  deleteTimesheet: async (id: string): Promise<void> => {
    await apiClient.delete(`timesheets/${id}`)
  },

  // ============ DailyWorkRecord CRUD ============

  getDailyRecords: async (filters?: DailyWorkRecordFilters): Promise<DailyWorkRecord[]> => {
    const { data } = await apiClient.get('timesheets/daily-records/', { params: filters })
    return data
  },

  getDailyRecordById: async (id: string): Promise<DailyWorkRecord> => {
    const { data } = await apiClient.get(`timesheets/daily-records/${id}`)
    return data
  },

  createDailyRecord: async (record: DailyWorkRecordCreate): Promise<DailyWorkRecord> => {
    const { data } = await apiClient.post(`timesheets/${record.timesheet_id}/records`, record)
    return data
  },

  updateDailyRecord: async (id: string, record: DailyWorkRecordUpdate): Promise<DailyWorkRecord> => {
    const { data } = await apiClient.put(`timesheets/records/${id}`, record)
    return data
  },

  deleteDailyRecord: async (id: string): Promise<void> => {
    await apiClient.delete(`timesheets/records/${id}`)
  },

  bulkCreateDailyRecords: async (bulkData: DailyWorkRecordBulkCreate): Promise<DailyWorkRecord[]> => {
    const { data } = await apiClient.post('timesheets/daily-records/bulk', bulkData)
    return data
  },

  // ============ Grid View ============

  getTimesheetGrid: async (params: TimesheetGridParams): Promise<TimesheetGrid> => {
    const { year, month, department_id } = params
    const queryParams = department_id ? { department_id } : {}
    const { data } = await apiClient.get(`timesheets/grid/${year}/${month}`, { params: queryParams })
    return data
  },

  // ============ Analytics ============

  getTimesheetSummary: async (params: TimesheetAnalyticsParams): Promise<TimesheetSummary> => {
    const { data } = await apiClient.get('timesheets/analytics/summary', { params })
    return data
  },

  getEmployeeStats: async (params: TimesheetAnalyticsParams): Promise<EmployeeTimesheetStats[]> => {
    const { data } = await apiClient.get('timesheets/analytics/employee-stats', { params })
    return data
  },

  getDepartmentStats: async (params: TimesheetAnalyticsParams): Promise<DepartmentTimesheetStats[]> => {
    const { data } = await apiClient.get('timesheets/analytics/department-stats', { params })
    return data
  },

  getMonthlyComparison: async (params: { year: number; month: number; department_id?: number }): Promise<TimesheetMonthlyComparison> => {
    const { data } = await apiClient.get('timesheets/analytics/monthly-comparison', { params })
    return data
  },

  // ============ Excel Import/Export ============

  exportTimesheetsToExcel: async (params: {
    year: number
    month: number
    department_id?: number
  }): Promise<Blob> => {
    const { data } = await apiClient.get('timesheets/export/excel', {
      params,
      responseType: 'blob',
    })
    return data
  },

  importTimesheetsFromExcel: async (params: {
    file: File
    year: number
    month: number
    department_id: number
    auto_create_employees?: boolean
  }): Promise<{
    success: boolean
    imported_count: number
    created_count: number
    updated_count: number
    errors: string[]
    warnings: string[]
  }> => {
    const formData = new FormData()
    formData.append('file', params.file)
    formData.append('year', params.year.toString())
    formData.append('month', params.month.toString())
    formData.append('department_id', params.department_id.toString())
    if (params.auto_create_employees !== undefined) {
      formData.append('auto_create_employees', params.auto_create_employees.toString())
    }

    const { data } = await apiClient.post('timesheets/import/excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },

  downloadTemplate: async (language: 'ru' | 'en' = 'ru'): Promise<Blob> => {
    const { data } = await apiClient.get('timesheets/export/template', {
      params: { language },
      responseType: 'blob',
    })
    return data
  },
}
