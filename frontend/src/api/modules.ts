/**
 * API client for Module Management
 */

import apiClient from './client'
import type {
  Module,
  ModuleCreate,
  ModuleUpdate,
  EnabledModulesResponse,
  ModuleEnableRequest,
  ModuleDisableRequest,
  OrganizationModule,
  ModuleEvent,
  ModuleStatistics,
  OrganizationModuleStatus,
  ModuleEventType,
} from '@/types/module'

// ==================== Module CRUD ====================

/**
 * Get list of all modules
 */
export const getModules = (params?: { active_only?: boolean }): Promise<Module[]> => {
  return apiClient.get('/modules', { params })
}

/**
 * Get module by ID
 */
export const getModule = (moduleId: number): Promise<Module> => {
  return apiClient.get(`/modules/${moduleId}`)
}

/**
 * Create a new module (ADMIN only)
 */
export const createModule = (data: ModuleCreate): Promise<Module> => {
  return apiClient.post('/modules', data)
}

/**
 * Update a module (ADMIN only)
 */
export const updateModule = (moduleId: number, data: ModuleUpdate): Promise<Module> => {
  return apiClient.put(`/modules/${moduleId}`, data)
}

/**
 * Delete a module (ADMIN only, soft delete)
 */
export const deleteModule = (moduleId: number): Promise<void> => {
  return apiClient.delete(`/modules/${moduleId}`)
}

// ==================== Enabled Modules ====================

/**
 * Get enabled modules for current user's organization
 */
export const getMyEnabledModules = (params?: {
  include_expired?: boolean
}): Promise<EnabledModulesResponse> => {
  return apiClient.get('/modules/enabled/my', { params })
}

/**
 * Get enabled modules for a specific organization (ADMIN only)
 */
export const getOrganizationEnabledModules = (
  organizationId: number,
  params?: { include_expired?: boolean }
): Promise<EnabledModulesResponse> => {
  return apiClient.get(`/modules/enabled/${organizationId}`, { params })
}

// ==================== Enable/Disable Modules ====================

/**
 * Enable a module for an organization (ADMIN only)
 */
export const enableModule = (data: ModuleEnableRequest): Promise<OrganizationModule> => {
  return apiClient.post('/modules/enable', data)
}

/**
 * Disable a module for an organization (ADMIN only)
 */
export const disableModule = (data: ModuleDisableRequest): Promise<void> => {
  return apiClient.post('/modules/disable', data)
}

// ==================== Module Events (Audit Log) ====================

/**
 * Get module events for auditing (ADMIN only)
 */
export const getModuleEvents = (params?: {
  organization_id?: number
  module_code?: string
  event_type?: ModuleEventType
  skip?: number
  limit?: number
}): Promise<ModuleEvent[]> => {
  return apiClient.get('/modules/events/', { params })
}

// ==================== Statistics & Analytics ====================

/**
 * Get statistics for all modules (ADMIN only)
 */
export const getModuleStatistics = (): Promise<ModuleStatistics[]> => {
  return apiClient.get('/modules/statistics/')
}

/**
 * Get module status summary for an organization (ADMIN only)
 */
export const getOrganizationModuleStatus = (
  organizationId: number
): Promise<OrganizationModuleStatus> => {
  return apiClient.get(`/modules/status/${organizationId}`)
}

// ==================== Helper Functions ====================

/**
 * Check if a module is enabled (client-side check)
 */
export const checkModuleEnabled = async (moduleCode: string): Promise<boolean> => {
  try {
    const response = await getMyEnabledModules({ include_expired: false })
    return response.modules.some((m) => m.code === moduleCode && !m.is_expired)
  } catch (error) {
    console.error('Failed to check module access:', error)
    return false
  }
}

/**
 * Get a specific enabled module info
 */
export const getEnabledModuleInfo = async (moduleCode: string) => {
  try {
    const response = await getMyEnabledModules({ include_expired: false })
    return response.modules.find((m) => m.code === moduleCode && !m.is_expired)
  } catch (error) {
    console.error('Failed to get module info:', error)
    return undefined
  }
}
