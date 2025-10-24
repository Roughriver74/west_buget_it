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

export interface DashboardData {
  year: number
  month?: number
  totals: {
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }
  capex_vs_opex: {
    capex: number
    opex: number
    capex_percent: number
    opex_percent: number
  }
  status_distribution: Array<{
    status: string
    count: number
    amount: number
  }>
  top_categories: Array<{
    category_id: number
    category_name: string
    category_type: string
    amount: number
  }>
  recent_expenses: Array<{
    id: number
    number: string
    amount: number
    status: string
    request_date: string
    category_id: number
  }>
}

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

export interface PaymentCalendarDay {
  date: string
  total_amount: number
  payment_count: number
}

export interface PaymentCalendar {
  year: number
  month: number
  days: PaymentCalendarDay[]
}

export interface PaymentDetail {
  id: number
  number: string
  amount: number
  payment_date: string | null
  category_id: number
  category_name: string | null
  contractor_id: number | null
  contractor_name: string | null
  organization_id: number
  organization_name: string | null
  status: string
  comment: string | null
}

export interface PaymentsByDay {
  date: string
  total_count: number
  total_amount: number
  payments: PaymentDetail[]
}

export type ForecastMethod = 'simple_average' | 'moving_average' | 'seasonal'

export type ForecastConfidence = 'low' | 'medium' | 'high'

export interface ForecastDataPoint {
  date: string
  predicted_amount: number
  confidence: ForecastConfidence
  method: string
}

export interface PaymentForecast {
  period: {
    start_date: string
    end_date: string
    days: number
  }
  method: ForecastMethod
  lookback_days: number
  summary: {
    total_predicted: number
    average_daily: number
  }
  forecast: ForecastDataPoint[]
}

export interface ForecastSummary {
  period: {
    start_date: string
    end_date: string
  }
  forecasts: {
    simple_average: {
      total: number
      daily_avg: number
    }
    moving_average: {
      total: number
      daily_avg: number
    }
    seasonal: {
      total: number
      daily_avg: number
    }
  }
}
