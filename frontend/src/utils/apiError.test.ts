import { describe, it, expect, vi, beforeEach } from 'vitest'
import { handleApiError, ApiErrorResponse } from './apiError'
import { AxiosError } from 'axios'
import { toast } from 'sonner'

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}))

describe('handleApiError', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should handle AxiosError with detail string', () => {
    const error = new AxiosError()
    error.response = {
      data: { detail: 'Error detail' },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    }

    const message = handleApiError(error)
    expect(message).toBe('Error detail')
    expect(toast.error).toHaveBeenCalledWith('Error detail')
  })

  it('should handle AxiosError with detail array', () => {
    const error = new AxiosError()
    error.response = {
      data: { detail: [{ msg: 'Error 1', loc: [] }, { msg: 'Error 2', loc: [] }] },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {} as any,
    }

    const message = handleApiError(error)
    expect(message).toBe('Error 1, Error 2')
    expect(toast.error).toHaveBeenCalledWith('Error 1, Error 2')
  })

  it('should handle standard Error', () => {
    const error = new Error('Standard error')
    const message = handleApiError(error)
    expect(message).toBe('Standard error')
    expect(toast.error).toHaveBeenCalledWith('Standard error')
  })

  it('should handle unknown error with default message', () => {
    const message = handleApiError({})
    expect(message).toBe('An unexpected error occurred')
    expect(toast.error).toHaveBeenCalledWith('An unexpected error occurred')
  })
})
