import apiClient from './client'
import type { Organization } from '@/types'

export const organizationsApi = {
  getAll: async (params?: { skip?: number; limit?: number; search?: string; is_active?: boolean }): Promise<Organization[]> => {
    const { data } = await apiClient.get('organizations/', { params })
    return data
  },

  getById: async (id: number): Promise<Organization> => {
    const { data } = await apiClient.get(`organizations/${id}`)
    return data
  },

  getOne: async (id: number): Promise<Organization> => {
    const { data } = await apiClient.get(`organizations/${id}`)
    return data
  },

  create: async (organization: Partial<Organization>): Promise<Organization> => {
    const { data } = await apiClient.post('organizations/', organization)
    return data
  },

  update: async (id: number, organization: Partial<Organization>): Promise<Organization> => {
    const { data } = await apiClient.put(`organizations/${id}`, organization)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`organizations/${id}`)
  },
}
