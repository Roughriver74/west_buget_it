// Timesheet status enums matching backend
export type TimesheetStatus = 'DRAFT' | 'APPROVED' | 'PAID'

// Day type enums matching backend
export type DayType = 'WORK' | 'UNPAID_LEAVE' | 'SICK_LEAVE' | 'VACATION' | 'WEEKEND' | 'HOLIDAY'

// ==================== WorkTimesheet Types ====================

export interface WorkTimesheet {
  id: string  // UUID
  employee_id: number
  year: number
  month: number
  total_days_worked: number
  total_hours_worked: number
  status: TimesheetStatus
  approved_by_id?: number
  approved_at?: string  // Date string
  notes?: string
  daily_summary?: Record<string, any>  // JSON
  department_id: number
  created_at: string
  updated_at?: string
  // Computed properties
  can_edit: boolean
  period_display: string
}

export interface WorkTimesheetWithEmployee extends WorkTimesheet {
  employee_full_name: string
  employee_position: string
  employee_number?: string
}

export interface WorkTimesheetCreate {
  year: number
  month: number
  employee_id: number
  notes?: string
}

export interface WorkTimesheetUpdate {
  notes?: string
}

export interface WorkTimesheetApprove {
  notes?: string
}

// ==================== DailyWorkRecord Types ====================

export interface DailyWorkRecord {
  id: string  // UUID
  timesheet_id: string  // UUID
  work_date: string  // Date string
  is_working_day: boolean
  hours_worked: number
  day_type: DayType
  break_hours?: number
  overtime_hours?: number
  notes?: string
  department_id: number
  created_at: string
  updated_at?: string
  // Computed property
  net_hours_worked: number
}

export interface DailyWorkRecordCreate {
  timesheet_id: string
  work_date: string
  is_working_day: boolean
  hours_worked: number
  day_type?: DayType
  break_hours?: number
  overtime_hours?: number
  notes?: string
}

export interface DailyWorkRecordUpdate {
  is_working_day?: boolean
  hours_worked?: number
  day_type?: DayType
  break_hours?: number
  overtime_hours?: number
  notes?: string
}

export interface DailyWorkRecordBulkCreate {
  timesheet_id: string
  records: Array<{
    work_date: string
    is_working_day: boolean
    hours_worked: number
    break_hours?: number
    overtime_hours?: number
    notes?: string
  }>
}

// ==================== Grid/Calendar View Types ====================

export interface TimesheetGridDay {
  date: string  // Date string
  day_of_week: number  // 1=Mon, 7=Sun
  is_working_day: boolean
  hours_worked: number
  day_type?: DayType  // Day type (WORK, UNPAID_LEAVE, etc.)
  break_hours?: number
  overtime_hours?: number
  net_hours_worked: number
  notes?: string
  record_id?: string  // UUID if record exists
}

export interface TimesheetGridEmployee {
  employee_id: number
  employee_full_name: string
  employee_position: string
  employee_number?: string
  timesheet_id?: string
  timesheet_status?: TimesheetStatus
  total_days_worked: number
  total_hours_worked: number
  can_edit: boolean
  days: TimesheetGridDay[]
}

export interface TimesheetGrid {
  year: number
  month: number
  department_id: number
  department_name: string
  employees: TimesheetGridEmployee[]
  working_days_in_month: number
  calendar_days_in_month: number
}

// ==================== Analytics Types ====================

export interface TimesheetSummary {
  year: number
  month: number
  department_id: number
  total_employees: number
  employees_with_timesheets: number
  total_days_worked: number
  total_hours_worked: number
  average_hours_per_employee: number
  draft_count: number
  approved_count: number
  paid_count: number
}

export interface EmployeeTimesheetStats {
  employee_id: number
  employee_full_name: string
  employee_position: string
  department_id: number
  months_count: number
  total_days_worked: number
  total_hours_worked: number
  average_hours_per_month: number
  last_timesheet_date?: string
}

export interface DepartmentTimesheetStats {
  department_id: number
  department_name: string
  year: number
  month: number
  total_employees: number
  employees_with_approved: number
  total_hours_worked: number
  average_hours_per_employee: number
  completion_rate: number  // Percentage
}

export interface TimesheetMonthlyComparison {
  year: number
  month: number
  current_hours: number
  previous_hours: number
  variance: number
  variance_percent: number
  employee_count: number
}

// ==================== Excel Import/Export Types ====================

export interface TimesheetExcelImport {
  year: number
  month: number
  department_id: number
  auto_create_employees: boolean
}

export interface TimesheetExcelImportResult {
  success: boolean
  imported_count: number
  created_count: number
  updated_count: number
  errors: string[]
  warnings: string[]
}

// ==================== Filter/Query Types ====================

export interface TimesheetFilters {
  department_id?: number
  employee_id?: number
  year?: number
  month?: number
  status?: TimesheetStatus
  skip?: number
  limit?: number
}

// ==================== UI Helper Types ====================

export interface TimesheetMonthOption {
  value: number
  label: string
}

export interface TimesheetYearOption {
  value: number
  label: string
}

export const MONTHS_RU: TimesheetMonthOption[] = [
  { value: 1, label: 'Январь' },
  { value: 2, label: 'Февраль' },
  { value: 3, label: 'Март' },
  { value: 4, label: 'Апрель' },
  { value: 5, label: 'Май' },
  { value: 6, label: 'Июнь' },
  { value: 7, label: 'Июль' },
  { value: 8, label: 'Август' },
  { value: 9, label: 'Сентябрь' },
  { value: 10, label: 'Октябрь' },
  { value: 11, label: 'Ноябрь' },
  { value: 12, label: 'Декабрь' },
]

export const TIMESHEET_STATUS_LABELS: Record<TimesheetStatus, string> = {
  DRAFT: 'Черновик',
  APPROVED: 'Утвержден',
  PAID: 'Оплачен',
}

export const TIMESHEET_STATUS_COLORS: Record<TimesheetStatus, string> = {
  DRAFT: 'default',
  APPROVED: 'processing',
  PAID: 'success',
}

// Day type labels (Russian)
export const DAY_TYPE_LABELS: Record<DayType, string> = {
  WORK: 'Рабочий день',
  UNPAID_LEAVE: 'День за свой счет',
  SICK_LEAVE: 'Больничный',
  VACATION: 'Отпуск',
  WEEKEND: 'Выходной',
  HOLIDAY: 'Праздник',
}

// Day type colors for background
export const DAY_TYPE_COLORS: Record<DayType, { bg: string; bgDark: string; label: string }> = {
  WORK: {
    bg: '#f6ffed',        // Light green
    bgDark: 'rgba(82, 196, 26, 0.2)',
    label: 'Оплачиваемый день',
  },
  UNPAID_LEAVE: {
    bg: '#fff1f0',        // Light red/orange
    bgDark: 'rgba(255, 77, 79, 0.2)',
    label: 'День за свой счет',
  },
  SICK_LEAVE: {
    bg: '#f0f5ff',        // Light blue
    bgDark: 'rgba(24, 144, 255, 0.2)',
    label: 'Больничный',
  },
  VACATION: {
    bg: '#fffbe6',        // Light yellow
    bgDark: 'rgba(250, 173, 20, 0.2)',
    label: 'Отпуск',
  },
  WEEKEND: {
    bg: '#fafafa',        // Light gray
    bgDark: 'rgba(255, 255, 255, 0.08)',
    label: 'Выходной',
  },
  HOLIDAY: {
    bg: '#fff1f0',        // Light red
    bgDark: 'rgba(255, 77, 79, 0.15)',
    label: 'Праздник',
  },
}

// ==================== Form Types ====================

export interface TimesheetFormData {
  employee_id?: number
  year: number
  month: number
  notes?: string
}

export interface DailyRecordFormData {
  work_date: string
  is_working_day: boolean
  hours_worked: number
  break_hours?: number
  overtime_hours?: number
  notes?: string
}
