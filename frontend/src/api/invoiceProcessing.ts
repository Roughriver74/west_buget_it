import apiClient from './client'
import type {
  InvoiceUploadResponse,
  InvoiceProcessRequest,
  InvoiceProcessResponse,
  ProcessedInvoiceList,
  ProcessedInvoiceDetail,
  ProcessedInvoiceUpdate,
  CreateExpenseFromInvoiceRequest,
  CreateExpenseFromInvoiceResponse,
  InvoiceProcessingStats,
  InvoiceListFilters,
  InvoiceUpdateCategoryRequest,
  Invoice1CValidationResponse,
  Create1CExpenseRequestResponse,
  CashFlowCategoryListItem,
} from '@/types/invoiceProcessing'

export const invoiceProcessingApi = {
  /**
   * Upload invoice file (PDF or image)
   */
  upload: async (file: File, departmentId?: number): Promise<InvoiceUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    // department_id передается как query параметр, а не form data
    const params = departmentId ? { department_id: departmentId } : undefined

    const { data } = await apiClient.post(
      'invoices/invoice-processing/upload',
      formData,
      {
        params,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return data
  },

  /**
   * Process invoice with OCR + AI parsing
   */
  process: async (request: InvoiceProcessRequest): Promise<InvoiceProcessResponse> => {
    const { data } = await apiClient.post(
      'invoices/invoice-processing/process',
      request
    )
    return data
  },

  /**
   * Get list of processed invoices with filters
   */
  getAll: async (filters?: InvoiceListFilters): Promise<ProcessedInvoiceList> => {
    const { data } = await apiClient.get('invoices/invoice-processing/', {
      params: filters,
    })

    // Backend возвращает просто массив, преобразуем в ожидаемый формат
    if (Array.isArray(data)) {
      return {
        total: data.length,
        items: data,
        page: 1,
        page_size: data.length,
        pages: 1,
      }
    }

    return data
  },

  /**
   * Get invoice details by ID
   */
  getById: async (invoiceId: number): Promise<ProcessedInvoiceDetail> => {
    const { data } = await apiClient.get(
      `invoices/invoice-processing/${invoiceId}`
    )
    return data
  },

  /**
   * Update invoice parsed data
   */
  update: async (
    invoiceId: number,
    update: ProcessedInvoiceUpdate
  ): Promise<ProcessedInvoiceDetail> => {
    const { data } = await apiClient.put(
      `invoices/invoice-processing/${invoiceId}`,
      update
    )
    return data
  },

  /**
   * Delete invoice (soft delete)
   */
  delete: async (invoiceId: number): Promise<{ message: string }> => {
    const { data } = await apiClient.delete(
      `invoices/invoice-processing/${invoiceId}`
    )
    return data
  },

  /**
   * Create expense from processed invoice
   */
  createExpense: async (
    request: CreateExpenseFromInvoiceRequest
  ): Promise<CreateExpenseFromInvoiceResponse> => {
    const { data } = await apiClient.post(
      'invoices/invoice-processing/create-expense',
      request
    )
    return data
  },

  /**
   * Get processing statistics
   */
  getStats: async (departmentId?: number): Promise<InvoiceProcessingStats> => {
    const { data } = await apiClient.get(
      'invoices/invoice-processing/stats/summary',
      {
        params: departmentId ? { department_id: departmentId } : undefined,
      }
    )
    return data
  },

  /**
   * Update invoice category and desired payment date
   */
  updateCategory: async (
    invoiceId: number,
    request: InvoiceUpdateCategoryRequest
  ): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.put(
      `invoices/invoice-processing/${invoiceId}/category`,
      request
    )
    return data
  },

  /**
   * Validate invoice for 1C integration
   */
  validateFor1C: async (invoiceId: number): Promise<Invoice1CValidationResponse> => {
    const { data } = await apiClient.post(
      `invoices/invoice-processing/${invoiceId}/validate-for-1c`
    )
    return data
  },

  /**
   * Create expense request in 1C
   */
  createIn1C: async (
    invoiceId: number,
    uploadAttachment: boolean = true
  ): Promise<Create1CExpenseRequestResponse> => {
    const { data } = await apiClient.post(
      `invoices/invoice-processing/${invoiceId}/create-1c-expense-request`,
      { upload_attachment: uploadAttachment }
    )
    return data
  },

  /**
   * Get cash flow categories (for category selection)
   */
  getCashFlowCategories: async (
    departmentId?: number
  ): Promise<CashFlowCategoryListItem[]> => {
    const { data } = await apiClient.get(
      'invoices/invoice-processing/cash-flow-categories',
      {
        params: departmentId ? { department_id: departmentId } : undefined,
      }
    )
    return data
  },
}
