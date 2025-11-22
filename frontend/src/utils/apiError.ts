import { AxiosError } from 'axios'
import { toast } from 'sonner'

export interface ApiErrorResponse {
  detail?: string | Array<{ msg: string; loc: string[] }>
  message?: string
}

export const handleApiError = (error: unknown, defaultMessage = 'An unexpected error occurred') => {
  console.error('API Error:', error)

  let message = defaultMessage

  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse
    
    if (data) {
      if (typeof data.detail === 'string') {
        message = data.detail
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map(err => err.msg).join(', ')
      } else if (data.message) {
        message = data.message
      }
    } else if (error.message) {
      message = error.message
    }
  } else if (error instanceof Error) {
    message = error.message
  }

  toast.error(message)
  return message
}
