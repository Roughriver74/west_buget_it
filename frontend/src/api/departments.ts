import apiClient from './client'
import type { Department } from '@/contexts/DepartmentContext'

export interface DepartmentCreate {
  name: string
  code: string
  description?: string
  ftp_subdivision_name?: string
  manager_name?: string
  contact_email?: string
  contact_phone?: string
  is_active?: boolean
}

export interface DepartmentUpdate {
  name?: string
  code?: string
  description?: string
  ftp_subdivision_name?: string
  manager_name?: string
  contact_email?: string
  contact_phone?: string
  is_active?: boolean
}

export interface DepartmentWithStats extends Department {
  users_count: number
  expenses_count: number
  total_budget: number
}

export const departmentsApi = {
  getAll: async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<Department[]> => {
    const { data } = await apiClient.get('departments/', { params })
    return data
  },

  list: async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<Department[]> => {
    const { data } = await apiClient.get('departments/', { params })
    return data
  },

  getById: async (id: number): Promise<Department> => {
    const { data } = await apiClient.get(`departments/${id}`)
    return data
  },

  getStats: async (id: number): Promise<DepartmentWithStats> => {
    const { data } = await apiClient.get(`departments/${id}/stats`)
    return data
  },

  create: async (department: DepartmentCreate): Promise<Department> => {
    const { data } = await apiClient.post('departments/', department)
    return data
  },

  update: async (id: number, department: DepartmentUpdate): Promise<Department> => {
    const { data } = await apiClient.put(`departments/${id}`, department)
    return data
  },

  deactivate: async (id: number): Promise<void> => {
    await apiClient.delete(`departments/${id}`)
  },

  activate: async (id: number): Promise<Department> => {
    const { data } = await apiClient.post(`departments/${id}/activate`)
    return data
  },
}

// Alias for consistency
export const departmentsAPI = departmentsApi
