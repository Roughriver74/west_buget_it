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
      localStorage.removeItem('token')
      // Redirect to login page if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
