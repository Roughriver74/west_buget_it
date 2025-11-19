import React, { useState } from 'react'
import { Upload, Button, List, message, Popconfirm, Tag, Space } from 'antd'
import { UploadOutlined, DeleteOutlined, DownloadOutlined, FileOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import { Attachment } from '../../types'
import axios from 'axios'
import { getApiBaseUrl } from '@/config/api'

const API_BASE = getApiBaseUrl()

interface AttachmentManagerProps {
  expenseId?: number
  attachments?: Attachment[]
  onAttachmentsChange?: (attachments: Attachment[]) => void
  readOnly?: boolean
}

const AttachmentManager: React.FC<AttachmentManagerProps> = ({
  expenseId,
  attachments = [],
  onAttachmentsChange,
  readOnly = false,
}) => {
  const [uploading, setUploading] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const handleUpload = async (file: File) => {
    if (!expenseId) {
      message.error('Сначала сохраните заявку, чтобы прикрепить файлы')
      return false
    }

    setUploading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(
        `${API_BASE}/expenses/${expenseId}/attachments`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      message.success(`Файл ${file.name} успешно загружен`)

      // Update attachments list
      if (onAttachmentsChange) {
        onAttachmentsChange([...attachments, response.data])
      }

      setFileList([])
    } catch (error) {
      console.error('Error uploading file:', error)
      message.error(`Ошибка загрузки файла ${file.name}`)
    } finally {
      setUploading(false)
    }

    return false // Prevent default upload behavior
  }

  const handleDelete = async (attachmentId: number) => {
    try {
      await axios.delete(`${API_BASE}/expenses/attachments/${attachmentId}`)
      message.success('Файл удален')

      // Update attachments list
      if (onAttachmentsChange) {
        onAttachmentsChange(attachments.filter((a) => a.id !== attachmentId))
      }
    } catch (error) {
      console.error('Error deleting file:', error)
      message.error('Ошибка удаления файла')
    }
  }

  const handleDownload = async (attachment: Attachment) => {
    try {
      const response = await axios.get(
        `${API_BASE}/expenses/attachments/${attachment.id}/download`,
        {
          responseType: 'blob',
        }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', attachment.filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading file:', error)
      message.error('Ошибка загрузки файла')
    }
  }

  const uploadProps: UploadProps = {
    fileList,
    beforeUpload: handleUpload,
    onChange: (info) => {
      setFileList(info.fileList)
    },
    multiple: true,
    showUploadList: false,
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const getFileTypeTag = (mimeType?: string): React.ReactNode => {
    if (!mimeType) return <Tag>Файл</Tag>

    if (mimeType.includes('pdf')) return <Tag color="red">PDF</Tag>
    if (mimeType.includes('word') || mimeType.includes('document'))
      return <Tag color="blue">DOC</Tag>
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet'))
      return <Tag color="green">EXCEL</Tag>
    if (mimeType.includes('image')) return <Tag color="orange">Изображение</Tag>
    if (mimeType.includes('zip') || mimeType.includes('rar'))
      return <Tag color="purple">Архив</Tag>

    return <Tag>Файл</Tag>
  }

  return (
    <div>
      {!readOnly && expenseId && (
        <Upload {...uploadProps}>
          <Button icon={<UploadOutlined />} loading={uploading} style={{ marginBottom: 16 }}>
            Прикрепить файл
          </Button>
        </Upload>
      )}

      {!expenseId && !readOnly && (
        <div style={{ marginBottom: 16, color: '#999' }}>
          Сначала сохраните заявку, чтобы прикрепить файлы
        </div>
      )}

      {attachments.length > 0 && (
        <List
          size="small"
          dataSource={attachments}
          renderItem={(attachment) => (
            <List.Item
              actions={[
                <Button
                  key="download"
                  type="link"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(attachment)}
                >
                  Скачать
                </Button>,
                !readOnly && (
                  <Popconfirm
                    key="delete"
                    title="Удалить файл?"
                    onConfirm={() => handleDelete(attachment.id)}
                    okText="Да"
                    cancelText="Нет"
                  >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                      Удалить
                    </Button>
                  </Popconfirm>
                ),
              ].filter(Boolean)}
            >
              <List.Item.Meta
                avatar={<FileOutlined style={{ fontSize: 24 }} />}
                title={
                  <Space>
                    {attachment.filename}
                    {getFileTypeTag(attachment.mime_type)}
                  </Space>
                }
                description={
                  <Space size="large">
                    <span>{formatFileSize(attachment.file_size)}</span>
                    {attachment.uploaded_by && <span>Загрузил: {attachment.uploaded_by}</span>}
                    <span>{new Date(attachment.created_at).toLocaleString('ru-RU')}</span>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}

      {attachments.length === 0 && (
        <div style={{ textAlign: 'center', color: '#999', padding: '16px 0' }}>
          Нет прикрепленных файлов
        </div>
      )}
    </div>
  )
}

export default AttachmentManager
