import apiClient from './client'

export interface BudgetPlanYear {
  year: number
  categories: Array<{
    category_id: number
    category_name: string
    category_type: string
    parent_id: number | null
    months: {
      [month: string]: {
        id: number | null
        planned_amount: number
        actual_amount: number
        remaining: number
        capex_planned: number
        opex_planned: number
      }
    }
  }>
}

export interface CellUpdateRequest {
  year: number
  month: number
  category_id: number
  planned_amount: number
}

export interface CopyPlanRequest {
  coefficient: number
}

export interface BudgetOverviewCategory {
  category_id: number
  category_name: string
  category_type: string
  parent_id: number | null
  planned: number
  actual: number
  remaining: number
  execution_percent: number
  is_overspent: boolean
}

export interface BudgetOverview {
  year: number
  month: number
  categories: BudgetOverviewCategory[]
  totals: {
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }
  opex_totals: {
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }
  capex_totals: {
    planned: number
    actual: number
    remaining: number
    execution_percent: number
  }
}

export const budgetApi = {
  // Получить план на год в pivot формате
  getPlanForYear: async (year: number): Promise<BudgetPlanYear> => {
    const { data } = await apiClient.get(`/budget/plans/year/${year}`)
    return data
  },

  // Инициализировать план на год (создать пустые записи)
  initializePlan: async (year: number): Promise<{ message: string; created_entries: number }> => {
    const { data } = await apiClient.post(`/budget/plans/year/${year}/init`)
    return data
  },

  // Скопировать план из другого года
  copyPlan: async (
    targetYear: number,
    sourceYear: number,
    coefficient: number = 1.0
  ): Promise<{ message: string; created_entries: number; updated_entries: number }> => {
    const { data } = await apiClient.post(`/budget/plans/year/${targetYear}/copy-from/${sourceYear}`, {
      coefficient,
    })
    return data
  },

  // Обновить одну ячейку (upsert)
  updateCell: async (request: CellUpdateRequest): Promise<any> => {
    const { data } = await apiClient.patch('/budget/plans/cell', request)
    return data
  },

  // Получить сводку план vs факт
  getSummary: async (year: number, month?: number): Promise<any> => {
    const params: any = { year }
    if (month) params.month = month
    const { data } = await apiClient.get('/budget/summary', { params })
    return data
  },

  // Получить обзор бюджета за месяц (План-Факт-Остаток)
  getOverview: async (year: number, month: number): Promise<BudgetOverview> => {
    const { data } = await apiClient.get(`/budget/overview/${year}/${month}`)
    return data
  },
}
