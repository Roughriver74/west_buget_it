import { Button, message } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { downloadBlob, generateExportFilename } from '@/utils/downloadUtils'

interface ExportButtonProps {
  exportFn: () => Promise<Blob>
  filename: string
  buttonText?: string
  type?: 'primary' | 'default' | 'dashed' | 'link' | 'text'
  size?: 'large' | 'middle' | 'small'
  icon?: React.ReactNode
}

const ExportButton: React.FC<ExportButtonProps> = ({
  exportFn,
  filename,
  buttonText = 'Экспорт в Excel',
  type = 'default',
  size = 'middle',
  icon = <DownloadOutlined />,
}) => {
  const [loading, setLoading] = useState(false)

  const handleExport = async () => {
    try {
      setLoading(true)
      const blob = await exportFn()
      downloadBlob(blob, filename)
      message.success('Файл успешно экспортирован')
    } catch (error: any) {
      console.error('Export error:', error)
      message.error(error.response?.data?.detail || 'Ошибка при экспорте данных')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      type={type}
      size={size}
      icon={icon}
      loading={loading}
      onClick={handleExport}
    >
      {buttonText}
    </Button>
  )
}

export default ExportButton
