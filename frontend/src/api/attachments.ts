import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Attachment {
  id: number
  expense_id: number
  filename: string
  file_path: string
  file_size: number
  mime_type: string | null
  file_type: string | null
  description: string | null
  uploaded_by: string | null
  created_at: string
  updated_at: string
}

export interface AttachmentList {
  total: number
  items: Attachment[]
}

export interface AttachmentUpdate {
  file_type?: string
  description?: string
}

export const attachmentsApi = {
  // Загрузить файл
  upload: async (
    expenseId: number,
    file: File,
    fileType?: string,
    description?: string,
    uploadedBy?: string
  ): Promise<Attachment> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('expense_id', expenseId.toString())
    if (fileType) formData.append('file_type', fileType)
    if (description) formData.append('description', description)
    if (uploadedBy) formData.append('uploaded_by', uploadedBy)

    const response = await axios.post<Attachment>(
      `${API_BASE_URL}/api/v1/attachments/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  // Получить список файлов для заявки
  getByExpenseId: async (expenseId: number): Promise<AttachmentList> => {
    const response = await axios.get<AttachmentList>(
      `${API_BASE_URL}/api/v1/attachments/expense/${expenseId}`
    )
    return response.data
  },

  // Получить информацию о файле
  getById: async (attachmentId: number): Promise<Attachment> => {
    const response = await axios.get<Attachment>(
      `${API_BASE_URL}/api/v1/attachments/${attachmentId}`
    )
    return response.data
  },

  // Скачать файл
  download: (attachmentId: number): string => {
    return `${API_BASE_URL}/api/v1/attachments/${attachmentId}/download`
  },

  // Обновить метаданные файла
  update: async (
    attachmentId: number,
    data: AttachmentUpdate
  ): Promise<Attachment> => {
    const response = await axios.patch<Attachment>(
      `${API_BASE_URL}/api/v1/attachments/${attachmentId}`,
      data
    )
    return response.data
  },

  // Удалить файл
  delete: async (attachmentId: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/v1/attachments/${attachmentId}`)
  },
}
