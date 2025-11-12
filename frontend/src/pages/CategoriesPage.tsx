import React, { useState } from 'react'
import { Typography, Card, Space, Button, Upload, message, Modal } from 'antd'
import { DownloadOutlined, UploadOutlined, DeleteOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import axios from 'axios'
import CategoryTable from '@/components/references/categories/CategoryTable'

const { Title, Paragraph } = Typography

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const CategoriesPage: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [bulkLoading, setBulkLoading] = useState(false)

  const handleExport = () => {
    const url = `${API_BASE}/categories/export`
    window.open(url, '_blank')
    message.success('Экспорт начат. Файл скоро будет загружен.')
  }

  const handleDownloadTemplate = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const url = `${API_URL}/api/v1/templates/download/categories`

      // Get token from localStorage
      const token = localStorage.getItem('token')

      // Fetch with authentication
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Не удалось скачать шаблон')
      }

      // Create blob and download
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = 'Шаблон_Категории.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      message.success('Шаблон успешно скачан')
    } catch (error) {
      console.error('Template download error:', error)
      message.error('Ошибка при скачивании шаблона')
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    action: `${API_BASE}/categories/import`,
    accept: '.xlsx,.xls',
    showUploadList: false,
    onChange(info) {
      if (info.file.status === 'done') {
        const response = info.file.response
        message.success(
          `Импорт завершен! Создано: ${response.created_count}, Обновлено: ${response.updated_count}`
        )
        if (response.errors && response.errors.length > 0) {
          Modal.warning({
            title: 'Предупреждения при импорте',
            content: (
              <div>
                {response.errors.map((error: string, index: number) => (
                  <div key={index}>{error}</div>
                ))}
              </div>
            ),
            width: 600,
          })
        }
        window.location.reload()
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} загрузка не удалась`)
      }
    },
  }

  const handleBulkActivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите категории для активации')
      return
    }

    setBulkLoading(true)
    try {
      await axios.post(`${API_BASE}/categories/bulk/update`, {
        ids: selectedRowKeys,
        is_active: true,
      })
      message.success(`Активировано ${selectedRowKeys.length} категорий`)
      setSelectedRowKeys([])
      window.location.reload()
    } catch (error) {
      message.error('Ошибка при активации категорий')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDeactivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите категории для деактивации')
      return
    }

    setBulkLoading(true)
    try {
      await axios.post(`${API_BASE}/categories/bulk/update`, {
        ids: selectedRowKeys,
        is_active: false,
      })
      message.success(`Деактивировано ${selectedRowKeys.length} категорий`)
      setSelectedRowKeys([])
      window.location.reload()
    } catch (error) {
      message.error('Ошибка при деактивации категорий')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите категории для удаления')
      return
    }

    Modal.confirm({
      title: 'Удалить выбранные категории?',
      content: `Будет удалено ${selectedRowKeys.length} категорий`,
      onOk: async () => {
        setBulkLoading(true)
        try {
          await axios.post(`${API_BASE}/categories/bulk/delete`, {
            ids: selectedRowKeys,
          })
          message.success(`Удалено ${selectedRowKeys.length} категорий`)
          setSelectedRowKeys([])
          window.location.reload()
        } catch (error) {
          message.error('Ошибка при удалении категорий')
        } finally {
          setBulkLoading(false)
        }
      },
    })
  }

  return (
    <div>
      <Title level={2}>Справочник статей расходов</Title>
      <Paragraph>
        Управление статьями расходов (категориями) для планирования и учёта бюджета.
        Статьи делятся на OPEX (операционные расходы) и CAPEX (капитальные расходы).
      </Paragraph>

      <Space style={{ marginBottom: 16 }} wrap>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          Экспорт в Excel
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate} type="dashed">
          Скачать шаблон
        </Button>
        <Upload {...uploadProps}>
          <Button icon={<UploadOutlined />}>Импорт из Excel</Button>
        </Upload>

        {selectedRowKeys.length > 0 && (
          <>
            <Button
              icon={<CheckOutlined />}
              onClick={handleBulkActivate}
              loading={bulkLoading}
            >
              Активировать ({selectedRowKeys.length})
            </Button>
            <Button
              icon={<CloseOutlined />}
              onClick={handleBulkDeactivate}
              loading={bulkLoading}
            >
              Деактивировать ({selectedRowKeys.length})
            </Button>
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={handleBulkDelete}
              loading={bulkLoading}
            >
              Удалить ({selectedRowKeys.length})
            </Button>
          </>
        )}
      </Space>

      <Card>
        <CategoryTable
          selectedRowKeys={selectedRowKeys}
          onSelectionChange={setSelectedRowKeys}
        />
      </Card>
    </div>
  )
}

export default CategoriesPage
