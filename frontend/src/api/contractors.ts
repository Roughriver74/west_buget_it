import apiClient from './client'
import type { Contractor } from '@/types'

export const contractorsApi = {
  getAll: async (params?: { skip?: number; limit?: number; is_active?: boolean; search?: string; department_id?: number }): Promise<Contractor[]> => {
    const { data} = await apiClient.get('contractors/', { params })
    return data
  },

  getById: async (id: number): Promise<Contractor> => {
    const { data } = await apiClient.get(`contractors/${id}`)
    return data
  },

  getOne: async (id: number): Promise<Contractor> => {
    const { data } = await apiClient.get(`contractors/${id}`)
    return data
  },

  create: async (contractor: Partial<Contractor>): Promise<Contractor> => {
    const { data } = await apiClient.post('contractors/', contractor)
    return data
  },

  update: async (id: number, contractor: Partial<Contractor>): Promise<Contractor> => {
    const { data } = await apiClient.put(`contractors/${id}`, contractor)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`contractors/${id}`)
  },
}
