/**
 * TypeScript types for Module system
 * Mirrors backend Pydantic schemas
 */

// ==================== Module Types ====================

export interface Module {
  id: number
  code: string
  name: string
  description?: string
  version?: string
  dependencies?: string[]
  icon?: string
  sort_order?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ModuleCreate {
  code: string
  name: string
  description?: string
  version?: string
  dependencies?: string[]
  icon?: string
  sort_order?: number
  is_active?: boolean
}

export interface ModuleUpdate {
  name?: string
  description?: string
  version?: string
  dependencies?: string[]
  is_active?: boolean
  icon?: string
  sort_order?: number
}

// ==================== Organization Module Types ====================

export interface OrganizationModule {
  id: number
  organization_id: number
  module_id: number
  enabled_at: string
  expires_at?: string
  limits?: Record<string, any>
  is_active: boolean
  enabled_by_id?: number
  updated_by_id?: number
  created_at: string
  updated_at: string
}

export interface OrganizationModuleCreate {
  organization_id: number
  module_id: number
  expires_at?: string
  limits?: Record<string, any>
  is_active?: boolean
}

export interface OrganizationModuleUpdate {
  expires_at?: string
  limits?: Record<string, any>
  is_active?: boolean
}

// ==================== Module Enable/Disable Requests ====================

export interface ModuleEnableRequest {
  module_code: string
  organization_id: number
  expires_at?: string
  limits?: Record<string, any>
}

export interface ModuleDisableRequest {
  module_code: string
  organization_id: number
}

// ==================== Enabled Modules Response ====================

export interface EnabledModuleInfo {
  code: string
  name: string
  description?: string
  version?: string
  icon?: string
  enabled_at: string
  expires_at?: string
  is_expired: boolean
  limits: Record<string, any>
}

export interface EnabledModulesResponse {
  modules: EnabledModuleInfo[]
  organization_id: number
  organization_name: string
}

// ==================== Feature Limit Types ====================

export interface FeatureLimit {
  id: number
  organization_module_id: number
  limit_type: string
  limit_value: number
  current_usage: number
  warning_threshold?: number
  last_checked_at?: string
  warning_sent: boolean
  created_at: string
  updated_at: string
  usage_percent: number
  is_exceeded: boolean
  is_warning_threshold_reached: boolean
}

export interface FeatureLimitCreate {
  organization_module_id: number
  limit_type: string
  limit_value: number
  warning_threshold?: number
  current_usage?: number
}

export interface FeatureLimitUpdate {
  limit_value?: number
  warning_threshold?: number
  current_usage?: number
}

// ==================== Module Event Types ====================

export type ModuleEventType =
  | 'MODULE_ENABLED'
  | 'MODULE_DISABLED'
  | 'MODULE_EXPIRED'
  | 'LIMIT_EXCEEDED'
  | 'LIMIT_WARNING'
  | 'ACCESS_DENIED'
  | 'MODULE_UPDATED'

export interface ModuleEvent {
  id: number
  organization_id: number
  module_id: number
  event_type: ModuleEventType
  event_metadata?: Record<string, any>
  created_by_id?: number
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface ModuleEventCreate {
  organization_id: number
  module_id: number
  event_type: ModuleEventType
  event_metadata?: Record<string, any>
  created_by_id?: number
  ip_address?: string
  user_agent?: string
}

// ==================== Statistics & Analytics ====================

export interface ModuleStatistics {
  module_code: string
  module_name: string
  total_organizations: number
  active_organizations: number
  expired_organizations: number
  total_events: number
}

export interface OrganizationModuleStatus {
  organization_id: number
  organization_name: string
  total_modules: number
  enabled_modules: number
  expired_modules: number
  modules: EnabledModuleInfo[]
}

// ==================== Module Codes (Enum) ====================

export enum ModuleCode {
  BUDGET_CORE = 'BUDGET_CORE',
  AI_FORECAST = 'AI_FORECAST',
  CREDIT_PORTFOLIO = 'CREDIT_PORTFOLIO',
  REVENUE_BUDGET = 'REVENUE_BUDGET',
  PAYROLL_KPI = 'PAYROLL_KPI',
  INTEGRATIONS_1C = 'INTEGRATIONS_1C',
  FOUNDER_DASHBOARD = 'FOUNDER_DASHBOARD',
  ADVANCED_ANALYTICS = 'ADVANCED_ANALYTICS',
  MULTI_DEPARTMENT = 'MULTI_DEPARTMENT',
}

// ==================== Helper Types ====================

/**
 * Module access check result
 */
export interface ModuleAccessResult {
  hasAccess: boolean
  module?: EnabledModuleInfo
  reason?: string
}

/**
 * Module loading state
 */
export interface ModuleLoadingState {
  isLoading: boolean
  isError: boolean
  error?: Error
}
