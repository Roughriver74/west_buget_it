/**
 * Business Operation Mapping Types
 * Типы для маппинга хозяйственных операций из 1С на категории бюджета
 */

export interface BusinessOperationMapping {
  id: number
  business_operation: string
  category_id: number
  category_name?: string
  category_type?: 'OPEX' | 'CAPEX'
  priority: number
  confidence: number
  notes?: string
  department_id: number
  department_name?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface BusinessOperationMappingList {
  items: BusinessOperationMapping[]
  total: number
  skip: number
  limit: number
}

export interface BusinessOperationMappingCreate {
  business_operation: string
  category_id: number
  priority?: number
  confidence?: number
  notes?: string
  department_id: number
}

export interface BusinessOperationMappingUpdate {
  category_id?: number
  priority?: number
  confidence?: number
  notes?: string
  is_active?: boolean
}

export interface BusinessOperationMappingFilters {
  department_id?: number
  is_active?: boolean
  business_operation?: string
  skip?: number
  limit?: number
}
