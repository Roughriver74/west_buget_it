import { useState } from 'react'
import {
  Upload,
  Button,
  List,
  message,
  Popconfirm,
  Typography,
  Space,
  Tag,
  Select,
  Input,
} from 'antd'
import {
  UploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FileImageOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { attachmentsApi, type Attachment } from '@/api/attachments'

const { Text } = Typography

interface AttachmentManagerProps {
  expenseId: number
}

const AttachmentManager: React.FC<AttachmentManagerProps> = ({ expenseId }) => {
  const queryClient = useQueryClient()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [fileType, setFileType] = useState<string>('other')
  const [description, setDescription] = useState<string>('')

  // Fetch attachments
  const { data: attachments, isLoading } = useQuery({
    queryKey: ['attachments', expenseId],
    queryFn: () => attachmentsApi.getByExpenseId(expenseId),
    enabled: !!expenseId,
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      attachmentsApi.upload(expenseId, file, fileType, description),
    onSuccess: () => {
      message.success('Файл успешно загружен')
      queryClient.invalidateQueries({ queryKey: ['attachments', expenseId] })
      setFileList([])
      setDescription('')
    },
    onError: (error: any) => {
      message.error(`Ошибка при загрузке файла: ${error.message}`)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (attachmentId: number) => attachmentsApi.delete(attachmentId),
    onSuccess: () => {
      message.success('Файл успешно удален')
      queryClient.invalidateQueries({ queryKey: ['attachments', expenseId] })
    },
    onError: (error: any) => {
      message.error(`Ошибка при удалении файла: ${error.message}`)
    },
  })

  const uploadProps: UploadProps = {
    beforeUpload: (file) => {
      // Check file size (50MB)
      const isLt50M = file.size / 1024 / 1024 < 50
      if (!isLt50M) {
        message.error('Файл должен быть меньше 50MB!')
        return Upload.LIST_IGNORE
      }
      setFileList([file])
      return false // Prevent auto upload
    },
    fileList,
    onRemove: () => {
      setFileList([])
    },
  }

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('Выберите файл для загрузки')
      return
    }

    const file = fileList[0] as any
    uploadMutation.mutate(file)
  }

  const handleDownload = (attachment: Attachment) => {
    const url = attachmentsApi.download(attachment.id)
    window.open(url, '_blank')
  }

  const handleDelete = (attachmentId: number) => {
    deleteMutation.mutate(attachmentId)
  }

  const getFileIcon = (mimeType: string | null) => {
    if (!mimeType) return <FileOutlined />

    if (mimeType.includes('pdf')) return <FilePdfOutlined style={{ color: '#f40' }} />
    if (mimeType.includes('word') || mimeType.includes('document'))
      return <FileWordOutlined style={{ color: '#1890ff' }} />
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet'))
      return <FileExcelOutlined style={{ color: '#52c41a' }} />
    if (mimeType.includes('image')) return <FileImageOutlined style={{ color: '#722ed1' }} />
    if (mimeType.includes('text')) return <FileTextOutlined />

    return <FileOutlined />
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getFileTypeLabel = (type: string | null): string => {
    const types: Record<string, string> = {
      invoice: 'Счет',
      contract: 'Договор',
      receipt: 'Квитанция',
      other: 'Другое',
    }
    return types[type || 'other'] || 'Другое'
  }

  return (
    <div style={{ marginTop: 16 }}>
      <Typography.Title level={5}>Вложения</Typography.Title>

      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* Upload section */}
        <Space direction="vertical" style={{ width: '100%' }}>
          <Select
            style={{ width: 200 }}
            value={fileType}
            onChange={setFileType}
            placeholder="Тип файла"
          >
            <Select.Option value="invoice">Счет</Select.Option>
            <Select.Option value="contract">Договор</Select.Option>
            <Select.Option value="receipt">Квитанция</Select.Option>
            <Select.Option value="other">Другое</Select.Option>
          </Select>

          <Input.TextArea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Описание файла (опционально)"
            rows={2}
          />

          <Space>
            <Upload {...uploadProps} maxCount={1}>
              <Button icon={<UploadOutlined />}>Выбрать файл</Button>
            </Upload>
            <Button
              type="primary"
              onClick={handleUpload}
              disabled={fileList.length === 0}
              loading={uploadMutation.isPending}
            >
              Загрузить
            </Button>
          </Space>
        </Space>

        {/* Attachments list */}
        <List
          loading={isLoading}
          dataSource={attachments?.items || []}
          locale={{ emptyText: 'Нет вложений' }}
          renderItem={(attachment) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(attachment)}
                >
                  Скачать
                </Button>,
                <Popconfirm
                  title="Удалить файл?"
                  description="Это действие нельзя отменить"
                  onConfirm={() => handleDelete(attachment.id)}
                  okText="Да"
                  cancelText="Нет"
                >
                  <Button
                    type="link"
                    danger
                    icon={<DeleteOutlined />}
                    loading={deleteMutation.isPending}
                  >
                    Удалить
                  </Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={getFileIcon(attachment.mime_type)}
                title={
                  <Space>
                    <Text strong>{attachment.filename}</Text>
                    <Tag color="blue">{getFileTypeLabel(attachment.file_type)}</Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size={0}>
                    {attachment.description && (
                      <Text type="secondary">{attachment.description}</Text>
                    )}
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {formatFileSize(attachment.file_size)} •{' '}
                      {new Date(attachment.created_at).toLocaleString('ru-RU')}
                      {attachment.uploaded_by && ` • ${attachment.uploaded_by}`}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Space>
    </div>
  )
}

export default AttachmentManager
