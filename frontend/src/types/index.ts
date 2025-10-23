export enum ExpenseType {
  OPEX = 'OPEX',
  CAPEX = 'CAPEX',
}

export enum ExpenseStatus {
  DRAFT = 'Черновик',
  PENDING = 'К оплате',
  PAID = 'Оплачена',
  REJECTED = 'Отклонена',
  CLOSED = 'Закрыта',
}

export interface BudgetCategory {
  id: number
  name: string
  type: ExpenseType
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
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
  is_active: boolean
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
  created_at: string
  updated_at: string
  category?: BudgetCategory
  contractor?: Contractor
  organization?: Organization
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
