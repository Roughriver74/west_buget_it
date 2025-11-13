import apiClient from './client'

export interface DepartmentSummary {
  department_id: number
  department_name: string
  budget_planned: number
  budget_actual: number
  budget_remaining: number
  budget_execution_percent: number
  expenses_count: number
  expenses_pending: number
  expenses_paid_amount: number
  employees_count: number
  payroll_planned: number
  payroll_actual: number
  avg_kpi_achievement: number | null
}

export interface CompanySummary {
  total_budget_planned: number
  total_budget_actual: number
  total_budget_remaining: number
  total_budget_execution_percent: number
  total_expenses_count: number
  total_expenses_pending: number
  total_expenses_paid: number
  total_employees: number
  total_payroll_planned: number
  total_payroll_actual: number
  departments_count: number
}

export interface TopCategoryByDepartment {
  department_id: number
  department_name: string
  category_id: number | null
  category_name: string
  category_type: string | null
  amount: number
  execution_percent: number
}

export interface ExpenseTrend {
  month: number
  month_name: string
  planned: number
  actual: number
  execution_percent: number
}

export interface DepartmentKPI {
  department_id: number
  department_name: string
  avg_achievement: number
  employees_with_kpi: number
  total_employees: number
  coverage_percent: number
}

export interface BudgetAlert {
  alert_type: string
  department_id: number
  department_name: string
  category_id: number | null
  category_name: string | null
  planned: number
  actual: number
  execution_percent: number
  message: string
}

export interface FounderDashboardData {
  year: number
  month: number | null
  company_summary: CompanySummary
  departments: DepartmentSummary[]
  top_categories_by_department: TopCategoryByDepartment[]
  expense_trends: ExpenseTrend[]
  department_kpis: DepartmentKPI[]
  alerts: BudgetAlert[]
}

export interface FounderDepartmentDetails {
  department_id: number
  department_name: string
  year: number
  month: number | null
  budget_by_category: any[]
  expenses_by_month: any[]
  employee_kpis: any[]
  recent_expenses: any[]
}

export const founderDashboardApi = {
  getDashboard: async (params?: { year?: number; month?: number }): Promise<FounderDashboardData> => {
    const { data } = await apiClient.get('founder/dashboard', { params })
    return data
  },

  getDepartmentDetails: async (
    departmentId: number,
    params?: { year?: number; month?: number }
  ): Promise<FounderDepartmentDetails> => {
    const { data } = await apiClient.get(`founder/department/${departmentId}`, { params })
    return data
  },
}
