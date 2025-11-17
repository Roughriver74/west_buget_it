/**
 * Business Operation Mappings API Client
 * API для управления маппингами хозяйственных операций
 */
import { apiClient } from './client'
import type {
  BusinessOperationMapping,
  BusinessOperationMappingList,
  BusinessOperationMappingCreate,
  BusinessOperationMappingUpdate,
  BusinessOperationMappingFilters,
} from '@/types/businessOperationMapping'

/**
 * Get list of business operation mappings
 */
export const getMappings = async (
  filters?: BusinessOperationMappingFilters
): Promise<BusinessOperationMappingList> => {
  const response = await apiClient.get('/business-operation-mappings', {
    params: filters,
  })
  return response.data
}

/**
 * Get single mapping by ID
 */
export const getMapping = async (id: number): Promise<BusinessOperationMapping> => {
  const response = await apiClient.get(`/business-operation-mappings/${id}`)
  return response.data
}

/**
 * Create new mapping
 */
export const createMapping = async (
  data: BusinessOperationMappingCreate
): Promise<BusinessOperationMapping> => {
  const response = await apiClient.post('/business-operation-mappings', data)
  return response.data
}

/**
 * Update existing mapping
 */
export const updateMapping = async (
  id: number,
  data: BusinessOperationMappingUpdate
): Promise<BusinessOperationMapping> => {
  const response = await apiClient.put(`/business-operation-mappings/${id}`, data)
  return response.data
}

/**
 * Delete mapping
 */
export const deleteMapping = async (id: number): Promise<void> => {
  await apiClient.delete(`/business-operation-mappings/${id}`)
}

/**
 * Bulk deactivate mappings
 */
export const bulkDeactivate = async (ids: number[]): Promise<{ updated: number }> => {
  const response = await apiClient.post('/business-operation-mappings/bulk-deactivate', ids)
  return response.data
}

/**
 * Bulk activate mappings
 */
export const bulkActivate = async (ids: number[]): Promise<{ updated: number }> => {
  const response = await apiClient.post('/business-operation-mappings/bulk-activate', ids)
  return response.data
}

/**
 * Bulk delete mappings
 */
export const bulkDelete = async (ids: number[]): Promise<{ deleted: number }> => {
  const response = await apiClient.post('/business-operation-mappings/bulk-delete', ids)
  return response.data
}
