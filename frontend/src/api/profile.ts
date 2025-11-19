import apiClient from './client'
import type { User } from './users'

export interface UserProfileUpdatePayload {
  email?: string | null
  full_name?: string | null
  position?: string | null
  phone?: string | null
}

export interface ChangePasswordPayload {
  old_password: string
  new_password: string
}

export const profileApi = {
  getCurrent: async (): Promise<User> => {
    const { data } = await apiClient.get('auth/me')
    return data
  },

  updateProfile: async (payload: UserProfileUpdatePayload): Promise<User> => {
    const { data } = await apiClient.put('auth/me', payload)
    return data
  },

  changePassword: async (payload: ChangePasswordPayload): Promise<void> => {
    await apiClient.post('auth/me/change-password', payload)
  },
}
