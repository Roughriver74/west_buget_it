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

// Export all as a combined object for convenience
export const revenueApi = {
  streams: revenueStreamsApi,
  categories: revenueCategoriesApi,
  actuals: revenueActualsApi,
}

export default revenueApi
