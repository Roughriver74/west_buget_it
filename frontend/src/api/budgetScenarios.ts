import { apiClient } from './client'

export type BudgetCategoryType = 'OPEX' | 'CAPEX'
export type BudgetPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface BudgetScenarioItem {
  id: number
  scenario_id: number
  category_type: BudgetCategoryType
  category_name: string
  percentage: number
  amount: number
  priority: BudgetPriority
  change_from_previous?: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface BudgetScenarioItemCreate {
  category_type: BudgetCategoryType
  category_name: string
  percentage: number
  priority?: BudgetPriority
  change_from_previous?: number
  notes?: string
}

export interface BudgetScenarioItemUpdate {
  category_type?: BudgetCategoryType
  category_name?: string
  percentage?: number
  priority?: BudgetPriority
  change_from_previous?: number
  notes?: string
}

export interface BudgetScenario {
  id: number
  name: string
  description?: string
  year: number
  total_budget: number
  budget_change_percent?: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface BudgetScenarioCreate {
  name: string
  description?: string
  year: number
  total_budget: number
  budget_change_percent?: number
  is_active?: boolean
  notes?: string
  items?: BudgetScenarioItemCreate[]
}

export interface BudgetScenarioUpdate {
  name?: string
  description?: string
  year?: number
  total_budget?: number
  budget_change_percent?: number
  is_active?: boolean
  notes?: string
}

export interface BudgetScenarioWithItems extends BudgetScenario {
  items: BudgetScenarioItem[]
}

export interface BudgetScenarioSummary {
  scenario_id: number
  scenario_name: string
  year: number
  total_budget: number
  opex_total: number
  opex_percentage: number
  capex_total: number
  capex_percentage: number
  items_count: number
}

export interface BudgetScenarioComparison {
  year: number
  scenarios: BudgetScenarioWithItems[]
}

export interface BudgetCategoryComparison {
  category_name: string
  category_type: BudgetCategoryType
  scenarios_data: {
    [scenarioName: string]: {
      amount: number
      percentage: number
      priority: string
      change_from_previous?: number
    }
  }
}

export const budgetScenariosApi = {
  async getAll(params?: {
    year?: number
    is_active?: boolean
    skip?: number
    limit?: number
  }): Promise<BudgetScenario[]> {
    const response = await apiClient.get('/budget-scenarios', { params })
    return response.data
  },

  async getSummary(params?: {
    year?: number
  }): Promise<BudgetScenarioSummary[]> {
    const response = await apiClient.get('/budget-scenarios/summary', { params })
    return response.data
  },

  async compareByYear(year: number): Promise<BudgetScenarioComparison> {
    const response = await apiClient.get(`/budget-scenarios/compare/${year}`)
    return response.data
  },

  async compareCategory(year: number, categoryName: string): Promise<BudgetCategoryComparison> {
    const response = await apiClient.get(`/budget-scenarios/compare-category/${year}/${encodeURIComponent(categoryName)}`)
    return response.data
  },

  async getById(id: number): Promise<BudgetScenarioWithItems> {
    const response = await apiClient.get(`/budget-scenarios/${id}`)
    return response.data
  },

  async create(data: BudgetScenarioCreate): Promise<BudgetScenarioWithItems> {
    const response = await apiClient.post('/budget-scenarios', data)
    return response.data
  },

  async update(id: number, data: BudgetScenarioUpdate): Promise<BudgetScenarioWithItems> {
    const response = await apiClient.put(`/budget-scenarios/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/budget-scenarios/${id}`)
  },

  // Scenario Items
  async getItems(scenarioId: number, params?: {
    category_type?: BudgetCategoryType
  }): Promise<BudgetScenarioItem[]> {
    const response = await apiClient.get(`/budget-scenarios/${scenarioId}/items`, { params })
    return response.data
  },

  async createItem(scenarioId: number, data: BudgetScenarioItemCreate): Promise<BudgetScenarioItem> {
    const response = await apiClient.post(`/budget-scenarios/${scenarioId}/items`, data)
    return response.data
  },

  async updateItem(itemId: number, data: BudgetScenarioItemUpdate): Promise<BudgetScenarioItem> {
    const response = await apiClient.put(`/budget-scenarios/items/${itemId}`, data)
    return response.data
  },

  async deleteItem(itemId: number): Promise<void> {
    await apiClient.delete(`/budget-scenarios/items/${itemId}`)
  },
}
