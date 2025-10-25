import axios from 'axios'
import { API_BASE_URL } from '../config/api'

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
      console.log(`[API] Request to ${config.url} with token:`, token.substring(0, 20) + '...')
    } else {
      console.log(`[API] Request to ${config.url} WITHOUT token`)
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
    console.error('API Error:', error.response?.data || error.message)

    // If we get a 401 Unauthorized, the token is invalid - clear it
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname

      // Only clear token and redirect if we're not already on login/register pages
      // AND if it's not the initial /auth/me request (which happens on page load)
      const isAuthMeRequest = error.config?.url?.includes('/auth/me')
      const isAuthPage = currentPath === '/login' || currentPath === '/register'

      if (!isAuthPage) {
        // Clear token only if it's not the initial auth check
        if (!isAuthMeRequest) {
          localStorage.removeItem('token')
          console.warn('[API] 401 error: Token invalid, cleared from storage')
        }

        // Dispatch custom event instead of hard redirect
        // This allows AuthContext to handle the logout gracefully
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
