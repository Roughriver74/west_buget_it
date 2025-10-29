import type { components } from './api.generated'

export enum ExpenseType {
  OPEX = 'OPEX',
  CAPEX = 'CAPEX',
}

export enum ExpenseStatus {
  DRAFT = 'DRAFT',
  PENDING = 'PENDING',
  PAID = 'PAID',
  REJECTED = 'REJECTED',
  CLOSED = 'CLOSED',
}

export interface BudgetCategory {
  id: number
  name: string
  type: ExpenseType
  description?: string
  is_active: boolean
  parent_id?: number | null
  created_at: string
  updated_at: string
  children?: BudgetCategory[]
}

export interface Contractor {
  id: number
  name: string
  short_name?: string
  inn?: string
  kpp?: string
  email?: string
  phone?: string
  address?: string
  contact_info?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Organization {
  id: number
  name: string
  legal_name?: string
  inn?: string
  kpp?: string
  address?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Attachment {
  id: number
  expense_id: number
  filename: string
  file_path: string
  file_size: number
  mime_type?: string
  file_type?: string
  uploaded_by?: string
  created_at: string
  updated_at: string
}

export interface Expense {
  id: number
  number: string
  category_id: number
  contractor_id?: number
  organization_id: number
  amount: number
  request_date: string
  payment_date?: string
  status: ExpenseStatus
  is_paid: boolean
  is_closed: boolean
  comment?: string
  requester?: string
  imported_from_ftp: boolean
  needs_review: boolean
  created_at: string
  updated_at: string
  category?: BudgetCategory
  contractor?: Contractor
  organization?: Organization
  attachments?: Attachment[]
}

export interface ExpenseList {
  total: number
  items: Expense[]
  page: number
  page_size: number
  pages: number
}

export interface BudgetPlan {
  id: number
  year: number
  month: number
  category_id: number
  planned_amount: number
  capex_planned: number
  opex_planned: number
  created_at: string
  updated_at: string
}

export interface ForecastExpense {
  id: number
  department_id: number
  category_id: number
  contractor_id?: number
  organization_id: number
  forecast_date: string
  amount: number
  comment?: string
  is_regular: boolean
  based_on_expense_id?: number
  created_at: string
  updated_at: string
  category?: BudgetCategory
  contractor?: Contractor
  organization?: Organization
}

export type DashboardData = components['schemas']['DashboardData']

export interface BudgetSummary {
  year: number
  month?: number
  categories: Array<{
    category_id: number
    category_name: string
    category_type: string
    planned: number
    actual: number
    remaining: number
    execution_percent: number
    capex_plan: number
    opex_plan: number
  }>
  totals: {
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }
}

export interface BudgetExecution {
  year: number
  months: Array<{
    month: number
    month_name: string
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }>
}

export type PaymentCalendarDay = components['schemas']['PaymentCalendarDay']
export type PaymentCalendar = components['schemas']['PaymentCalendar']
export type PaymentDetail = components['schemas']['PaymentDetail']
export type PaymentsByDay = components['schemas']['PaymentsByDay']

export type ForecastMethod = components['schemas']['ForecastMethodEnum']

export type ForecastConfidence = 'low' | 'medium' | 'high'
export type ForecastDataPoint = components['schemas']['PaymentForecastPoint']

export type WidgetType =
  | 'total_amount'
  | 'category_chart'
  | 'status_chart'
  | 'monthly_trend'
  | 'recent_expenses'
  | 'budget_execution'
  | 'top_contractors'
  | 'capex_opex_ratio'
  | 'budget_plan_vs_actual'

export interface WidgetLayout {
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
}

export interface Widget {
  id: string
  type: WidgetType
  title: string
  config: Record<string, any>
  layout: WidgetLayout
}

export interface DashboardConfig {
  id: number
  name: string
  description?: string
  user_id?: string
  is_default: boolean
  is_public: boolean
  config: {
    widgets: Widget[]
  }
  created_at: string
  updated_at: string
}

export type PaymentForecast = components['schemas']['PaymentForecast']

export type ForecastSummary = components['schemas']['ForecastSummary']
