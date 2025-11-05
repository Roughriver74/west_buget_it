export enum InvoiceProcessingStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  PROCESSED = 'PROCESSED',
  ERROR = 'ERROR',
  MANUAL_REVIEW = 'MANUAL_REVIEW',
  EXPENSE_CREATED = 'EXPENSE_CREATED',
}

export interface SupplierData {
  name?: string | null
  inn?: string | null
  kpp?: string | null
  bank_name?: string | null
  bik?: string | null
  account?: string | null
  corr_account?: string | null
}

export interface InvoiceItem {
  description?: string | null
  quantity?: number | null
  unit?: string | null
  price?: number | null
  amount?: number | null
}

export interface ParsedInvoiceData {
  invoice_number?: string | null
  invoice_date?: string | null
  supplier?: SupplierData | null
  amount_without_vat?: number | null
  vat_amount?: number | null
  total_amount?: number | null
  payment_purpose?: string | null
  contract_number?: string | null
  contract_date?: string | null
  items?: InvoiceItem[]
}

export interface OCRResult {
  text: string
  confidence?: number | null
  processing_time_sec: number
}

export interface ProcessingError {
  field: string
  message: string
  severity: 'error' | 'warning'
}

export interface ProcessedInvoice {
  id: number
  department_id: number
  original_filename: string
  file_path: string
  file_size_kb?: number | null
  uploaded_by: number

  // OCR results
  ocr_text?: string | null
  ocr_processing_time_sec?: number | null

  // Parsed data
  invoice_number?: string | null
  invoice_date?: string | null
  supplier_name?: string | null
  supplier_inn?: string | null
  supplier_kpp?: string | null
  supplier_bank_name?: string | null
  supplier_bik?: string | null
  supplier_account?: string | null
  amount_without_vat?: number | null
  vat_amount?: number | null
  total_amount?: number | null
  payment_purpose?: string | null
  contract_number?: string | null
  contract_date?: string | null

  // Status and relations
  status: InvoiceProcessingStatus
  expense_id?: number | null
  contractor_id?: number | null

  // AI metadata
  parsed_data?: ParsedInvoiceData | null
  ai_processing_time_sec?: number | null
  ai_model_used?: string | null
  errors?: ProcessingError[] | null
  warnings?: ProcessingError[] | null

  // Timestamps
  created_at: string
  updated_at: string
  processed_at?: string | null
  expense_created_at?: string | null
}

export interface InvoiceUploadResponse {
  success: boolean
  invoice_id: number
  filename: string
  message: string
}

export interface InvoiceProcessRequest {
  invoice_id: number
}

export interface InvoiceProcessResponse {
  success: boolean
  invoice_id: number
  status: InvoiceProcessingStatus
  ocr_result?: OCRResult | null
  parsed_data?: ParsedInvoiceData | null
  errors: ProcessingError[]
  warnings: ProcessingError[]
  processing_time_sec: number
  message: string
}

export interface ProcessedInvoiceListItem {
  id: number
  department_id: number
  original_filename: string
  file_size_kb?: number | null
  status: InvoiceProcessingStatus
  invoice_number?: string | null
  invoice_date?: string | null
  supplier_name?: string | null
  total_amount?: number | null
  expense_id?: number | null
  created_at: string
  processed_at?: string | null
}

export interface ProcessedInvoiceList {
  total: number
  items: ProcessedInvoiceListItem[]
  page: number
  page_size: number
  pages: number
}

export interface ProcessedInvoiceDetail extends ProcessedInvoice {
  // Full details include all fields from ProcessedInvoice
}

export interface ProcessedInvoiceUpdate {
  invoice_number?: string | null
  invoice_date?: string | null
  supplier_name?: string | null
  supplier_inn?: string | null
  supplier_kpp?: string | null
  total_amount?: number | null
  payment_purpose?: string | null
  contract_number?: string | null
  contract_date?: string | null
}

export interface CreateExpenseFromInvoiceRequest {
  invoice_id: number
  category_id: number
  amount_override?: number | null
  description_override?: string | null
  contractor_id_override?: number | null
}

export interface CreateExpenseFromInvoiceResponse {
  success: boolean
  expense_id?: number | null
  contractor_id?: number | null
  contractor_created: boolean
  message: string
}

export interface InvoiceProcessingStats {
  total_invoices: number
  by_status: Record<InvoiceProcessingStatus, number>
  total_amount: number
  avg_processing_time_sec: number
}

export interface InvoiceListFilters {
  skip?: number
  limit?: number
  status?: InvoiceProcessingStatus
  department_id?: number
  date_from?: string
  date_to?: string
  search?: string
}
