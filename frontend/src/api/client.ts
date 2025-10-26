import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import { logger } from '../utils/logger'

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token from localStorage
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      logger.api(config.method?.toUpperCase() || 'GET', config.url || '', config.data)
      logger.debug(`[API] Token attached to request: ${config.url}`)
    } else {
      logger.warn(`[API] Request to ${config.url} WITHOUT token - localStorage is empty`)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle errors globally
    logger.error('API Error:', error.response?.data || error.message)

    // If we get a 401 Unauthorized, the token is invalid - clear it
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname

      // Only clear token and redirect if we're not already on login/register pages
      // AND if it's not the initial /auth/me request (which happens on page load)
      const isAuthMeRequest = error.config?.url?.includes('/auth/me')
      const isAuthPage = currentPath === '/login' || currentPath === '/register'

      if (!isAuthPage && !isAuthMeRequest) {
        // Clear token and dispatch logout event
        localStorage.removeItem('token')
        logger.warn('[API] 401 error: Token invalid, cleared from storage')

        // Dispatch custom event to trigger logout
        // This allows AuthContext to handle the logout gracefully
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
