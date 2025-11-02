/**
 * Revenue API Client
 *
 * API client for Revenue Budget module endpoints
 */

import apiClient from './client'
import type {
  RevenueStream,
  RevenueStreamTree,
  RevenueStreamCreate,
  RevenueStreamUpdate,
  RevenueStreamFilters,
  RevenueCategory,
  RevenueCategoryTree,
  RevenueCategoryCreate,
  RevenueCategoryUpdate,
  RevenueCategoryFilters,
  RevenueActual,
  RevenueActualCreate,
  RevenueActualUpdate,
  RevenueActualFilters,
  RevenuePlan,
  RevenuePlanCreate,
  RevenuePlanUpdate,
  RevenuePlanVersion,
  RevenuePlanVersionCreate,
  RevenuePlanVersionUpdate,
  RevenuePlanDetail,
  RevenuePlanDetailCreate,
  RevenuePlanDetailUpdate,
} from '@/types/revenue'

// ==================== Revenue Streams ====================

export const revenueStreamsApi = {
  /**
   * Get all revenue streams with filtering
   */
  getAll: async (params?: RevenueStreamFilters): Promise<RevenueStream[]> => {
    const { data } = await apiClient.get('/revenue/streams/', { params })
    return data
  },

  /**
   * Get revenue streams in tree structure (hierarchical)
   */
  getTree: async (params?: {
    stream_type?: string
    is_active?: boolean
    department_id?: number
  }): Promise<RevenueStreamTree[]> => {
    const { data } = await apiClient.get('/revenue/streams/tree', { params })
    return data
  },

  /**
   * Get a specific revenue stream by ID
   */
  getById: async (id: number): Promise<RevenueStream> => {
    const { data } = await apiClient.get(`/revenue/streams/${id}`)
    return data
  },

  /**
   * Create a new revenue stream
   */
  create: async (stream: RevenueStreamCreate): Promise<RevenueStream> => {
    const { data } = await apiClient.post('/revenue/streams/', stream)
    return data
  },

  /**
   * Update an existing revenue stream
   */
  update: async (id: number, stream: RevenueStreamUpdate): Promise<RevenueStream> => {
    const { data } = await apiClient.put(`/revenue/streams/${id}`, stream)
    return data
  },

  /**
   * Delete a revenue stream (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/revenue/streams/${id}`)
  },

  /**
   * Bulk update revenue streams
   */
  bulkUpdate: async (params: {
    ids: number[]
    is_active?: boolean
  }): Promise<RevenueStream[]> => {
    const { data } = await apiClient.post('/revenue/streams/bulk/update', params)
    return data
  },

  /**
   * Bulk delete revenue streams
   */
  bulkDelete: async (ids: number[]): Promise<void> => {
    await apiClient.delete('/revenue/streams/bulk/delete', { data: { ids } })
  },
}

// ==================== Revenue Categories ====================

export const revenueCategoriesApi = {
  /**
   * Get all revenue categories with filtering
   */
  getAll: async (params?: RevenueCategoryFilters): Promise<RevenueCategory[]> => {
    const { data } = await apiClient.get('/revenue/categories/', { params })
    return data
  },

  /**
   * Get revenue categories in tree structure (hierarchical)
   */
  getTree: async (params?: {
    category_type?: string
    is_active?: boolean
    department_id?: number
  }): Promise<RevenueCategoryTree[]> => {
    const { data } = await apiClient.get('/revenue/categories/tree', { params })
    return data
  },

  /**
   * Get a specific revenue category by ID
   */
  getById: async (id: number): Promise<RevenueCategory> => {
    const { data } = await apiClient.get(`/revenue/categories/${id}`)
    return data
  },

  /**
   * Create a new revenue category
   */
  create: async (category: RevenueCategoryCreate): Promise<RevenueCategory> => {
    const { data } = await apiClient.post('/revenue/categories/', category)
    return data
  },

  /**
   * Update an existing revenue category
   */
  update: async (id: number, category: RevenueCategoryUpdate): Promise<RevenueCategory> => {
    const { data } = await apiClient.put(`/revenue/categories/${id}`, category)
    return data
  },

  /**
   * Delete a revenue category (soft delete)
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/revenue/categories/${id}`)
  },

  /**
   * Bulk update revenue categories
   */
  bulkUpdate: async (params: {
    ids: number[]
    is_active?: boolean
  }): Promise<RevenueCategory[]> => {
    const { data } = await apiClient.post('/revenue/categories/bulk/update', params)
    return data
  },

  /**
   * Bulk delete revenue categories
   */
  bulkDelete: async (ids: number[]): Promise<void> => {
    await apiClient.delete('/revenue/categories/bulk/delete', { data: { ids } })
  },
}

// ==================== Revenue Actuals ====================

export const revenueActualsApi = {
  /**
   * Get all revenue actuals with filtering
   */
  getAll: async (params?: RevenueActualFilters): Promise<RevenueActual[]> => {
    const { data } = await apiClient.get('/revenue/actuals/', { params })
    return data
  },

  /**
   * Get a specific revenue actual by ID
   */
  getById: async (id: number): Promise<RevenueActual> => {
    const { data } = await apiClient.get(`/revenue/actuals/${id}`)
    return data
  },

  /**
   * Create a new revenue actual
   */
  create: async (actual: RevenueActualCreate): Promise<RevenueActual> => {
    const { data } = await apiClient.post('/revenue/actuals/', actual)
    return data
  },

  /**
   * Update an existing revenue actual
   */
  update: async (id: number, actual: RevenueActualUpdate): Promise<RevenueActual> => {
    const { data } = await apiClient.put(`/revenue/actuals/${id}`, actual)
    return data
  },

  /**
   * Delete a revenue actual
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/revenue/actuals/${id}`)
  },

  /**
   * Get plan vs actual comparison
   */
  getPlanVsActual: async (params: {
    year: number
    revenue_stream_id?: number
    revenue_category_id?: number
    department_id?: number
  }): Promise<any> => {
    const { data } = await apiClient.get('/revenue/actuals/plan-vs-actual', { params })
    return data
  },

  /**
   * Bulk update revenue actuals
   */
  bulkUpdate: async (params: {
    ids: number[]
    updates: Partial<RevenueActual>
  }): Promise<RevenueActual[]> => {
    const { data } = await apiClient.post('/revenue/actuals/bulk/update', params)
    return data
  },

  /**
   * Bulk delete revenue actuals
   */
  bulkDelete: async (ids: number[]): Promise<void> => {
    await apiClient.delete('/revenue/actuals/bulk/delete', { data: { ids } })
  },
}

// ==================== Revenue Plans ====================

export const revenuePlansApi = {
  /**
   * Get all revenue plans with filtering
   */
  getAll: async (params?: {
    year?: number
    status?: string
    department_id?: number
    skip?: number
    limit?: number
  }): Promise<RevenuePlan[]> => {
    const { data } = await apiClient.get('/revenue/plans/', { params })
    return data
  },

  /**
   * Get a specific revenue plan by ID
   */
  getById: async (id: number): Promise<RevenuePlan> => {
    const { data } = await apiClient.get(`/revenue/plans/${id}`)
    return data
  },

  /**
   * Create a new revenue plan
   */
  create: async (plan: RevenuePlanCreate): Promise<RevenuePlan> => {
    const { data } = await apiClient.post('/revenue/plans/', plan)
    return data
  },

  /**
   * Update an existing revenue plan
   */
  update: async (id: number, plan: RevenuePlanUpdate): Promise<RevenuePlan> => {
    const { data } = await apiClient.put(`/revenue/plans/${id}`, plan)
    return data
  },

  /**
   * Delete a revenue plan
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/revenue/plans/${id}`)
  },

  /**
   * Approve a revenue plan
   */
  approve: async (id: number): Promise<RevenuePlan> => {
    const { data } = await apiClient.post(`/revenue/plans/${id}/approve`)
    return data
  },

  /**
   * Get all versions for a revenue plan
   */
  getVersions: async (planId: number, params?: { status?: string }): Promise<RevenuePlanVersion[]> => {
    const { data } = await apiClient.get(`/revenue/plans/${planId}/versions`, { params })
    return data
  },

  /**
   * Create a new version for a revenue plan
   */
  createVersion: async (planId: number, version: RevenuePlanVersionCreate): Promise<RevenuePlanVersion> => {
    const { data } = await apiClient.post(`/revenue/plans/${planId}/versions`, version)
    return data
  },

  /**
   * Update a revenue plan version
   */
  updateVersion: async (
    planId: number,
    versionId: number,
    version: RevenuePlanVersionUpdate
  ): Promise<RevenuePlanVersion> => {
    const { data } = await apiClient.put(`/revenue/plans/${planId}/versions/${versionId}`, version)
    return data
  },

  /**
   * Delete a revenue plan version
   */
  deleteVersion: async (planId: number, versionId: number): Promise<void> => {
    await apiClient.delete(`/revenue/plans/${planId}/versions/${versionId}`)
  },

  /**
   * Copy revenue plan from source year to target year
   */
  copyPlan: async (
    targetYear: number,
    sourceYear: number,
    coefficient: number = 1.0,
    departmentId?: number
  ): Promise<{
    message: string
    department_id: number
    created_plans: number
    created_versions: number
    created_details: number
    skipped_plans: number
  }> => {
    const { data } = await apiClient.post(
      `/revenue/plans/year/${targetYear}/copy-from/${sourceYear}`,
      { coefficient },
      { params: departmentId ? { department_id: departmentId } : undefined }
    )
    return data
  },
}

// ==================== Revenue Plan Details ====================

export const revenuePlanDetailsApi = {
  /**
   * Get all revenue plan details for a version
   */
  getAll: async (params: {
    version_id: number
    revenue_stream_id?: number
    revenue_category_id?: number
    skip?: number
    limit?: number
  }): Promise<RevenuePlanDetail[]> => {
    const { data } = await apiClient.get('/revenue/plan-details/', { params })
    return data
  },

  /**
   * Get a specific revenue plan detail by ID
   */
  getById: async (id: number): Promise<RevenuePlanDetail> => {
    const { data } = await apiClient.get(`/revenue/plan-details/${id}`)
    return data
  },

  /**
   * Create a new revenue plan detail
   */
  create: async (detail: RevenuePlanDetailCreate): Promise<RevenuePlanDetail> => {
    const { data } = await apiClient.post('/revenue/plan-details/', detail)
    return data
  },

  /**
   * Bulk create revenue plan details
   */
  bulkCreate: async (details: RevenuePlanDetailCreate[]): Promise<RevenuePlanDetail[]> => {
    const { data } = await apiClient.post('/revenue/plan-details/bulk', { details })
    return data
  },

  /**
   * Update an existing revenue plan detail
   */
  update: async (id: number, detail: RevenuePlanDetailUpdate): Promise<RevenuePlanDetail> => {
    const { data } = await apiClient.put(`/revenue/plan-details/${id}`, detail)
    return data
  },

  /**
   * Bulk update revenue plan details
   */
  bulkUpdate: async (updates: Array<{ id: number; updates: Record<string, number> }>): Promise<RevenuePlanDetail[]> => {
    const { data } = await apiClient.put('/revenue/plan-details/bulk/update', { updates })
    return data
  },

  /**
   * Delete a revenue plan detail
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/revenue/plan-details/${id}`)
  },

  /**
   * Get summary statistics for a revenue plan version
   */
  getSummary: async (versionId: number): Promise<{
    version_id: number
    total_revenue: number
    monthly_totals: Record<string, number>
    by_stream: Array<{ stream_id: number; total: number }>
    by_category: Array<{ category_id: number; total: number }>
  }> => {
    const { data } = await apiClient.get(`/revenue/plan-details/version/${versionId}/summary`)
    return data
  },
}

// Export all as a combined object for convenience
export const revenueApi = {
  streams: revenueStreamsApi,
  categories: revenueCategoriesApi,
  actuals: revenueActualsApi,
  plans: revenuePlansApi,
  planDetails: revenuePlanDetailsApi,
}

export default revenueApi
