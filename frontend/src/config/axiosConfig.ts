/**
 * Global axios configuration
 * Adds Authorization header to all axios requests (not just apiClient)
 */
import axios from 'axios'
import { logger } from '../utils/logger'

// Add request interceptor to attach token to ALL axios requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      logger.debug(`[Axios Global] Token attached to request: ${config.url}`)
    } else {
      logger.warn(`[Axios Global] Request to ${config.url} WITHOUT token - localStorage is empty`)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for global 401 handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname
      const isAuthPage = currentPath === '/login' || currentPath === '/register'
      const isAuthMeRequest = error.config?.url?.includes('/auth/me')

      if (!isAuthPage && !isAuthMeRequest) {
        localStorage.removeItem('token')
        logger.warn('[Axios Global] 401 error: Token invalid, cleared from storage')
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
    }
    return Promise.reject(error)
  }
)

export default axios
