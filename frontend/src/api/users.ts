import apiClient from './client'

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: 'ADMIN' | 'ACCOUNTANT' | 'REQUESTER' | 'MANAGER' | 'USER'
  is_active: boolean
  is_verified: boolean
  department_id: number | null
  position: string | null
  phone: string | null
  last_login: string | null
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string
  role?: 'ADMIN' | 'ACCOUNTANT' | 'REQUESTER' | 'MANAGER' | 'USER'
  department_id?: number
  position?: string
  phone?: string
}

export interface UserUpdate {
  email?: string
  full_name?: string
  role?: 'ADMIN' | 'ACCOUNTANT' | 'REQUESTER' | 'MANAGER' | 'USER'
  department_id?: number
  position?: string
  phone?: string
  is_active?: boolean
}

export interface UserListItem {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  department_id: number | null
}

export const usersApi = {
  getAll: async (params?: { skip?: number; limit?: number }): Promise<UserListItem[]> => {
    const { data } = await apiClient.get('auth/users', { params })
    return data
  },

  getById: async (id: number): Promise<User> => {
    const { data } = await apiClient.get(`auth/users/${id}`)
    return data
  },

  create: async (user: UserCreate): Promise<User> => {
    const { data } = await apiClient.post('auth/register', user)
    return data
  },

  update: async (id: number, user: UserUpdate): Promise<User> => {
    const { data } = await apiClient.put(`auth/users/${id}`, user)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`auth/users/${id}`)
  },
}
