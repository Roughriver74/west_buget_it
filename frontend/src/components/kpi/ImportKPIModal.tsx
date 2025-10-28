import { useState } from 'react'
import { Modal, Form, Upload, DatePicker, message, Alert, Typography, List, Statistic, Row, Col, Divider, Button } from 'antd'
import { UploadOutlined, InboxOutlined, DownloadOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import type { KPIImportResult } from '@/api/kpi'
import dayjs from 'dayjs'

const { Dragger } = Upload
const { Title, Text, Paragraph } = Typography

interface ImportKPIModalProps {
  visible: boolean
  onCancel: () => void
}

const ImportKPIModal: React.FC<ImportKPIModalProps> = ({ visible, onCancel }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [importResult, setImportResult] = useState<KPIImportResult | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async (values: { file: File; year: number; month: number }) => {
      return await kpiApi.importKPI(values.file, values.year, values.month)
    },
    onSuccess: (data) => {
      setImportResult(data)

      if (data.success) {
        message.success(data.message || 'KPI данные успешно импортированы')

        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['employees'] })
        queryClient.invalidateQueries({ queryKey: ['employee-kpis'] })
        queryClient.invalidateQueries({ queryKey: ['kpi-analytics'] })
      } else {
        message.warning('Импорт завершен с ошибками')
      }
    },
    onError: (error: any) => {
      message.error(`Ошибка импорта: ${error.response?.data?.detail || error.message}`)
      setImportResult(null)
    },
    onSettled: () => {
      setIsUploading(false)
    },
  })

  const handleDownloadTemplate = () => {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${API_URL}/api/v1/templates/download/kpi`

    // Create temporary link and trigger download
    const link = document.createElement('a')
    link.href = url
    link.download = 'Шаблон_КПИ.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    message.success('Скачивание шаблона начато')
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (fileList.length === 0) {
        message.error('Пожалуйста, выберите файл для импорта')
        return
      }

      const file = fileList[0].originFileObj as File
      const date = dayjs(values.period)

      setIsUploading(true)
      setImportResult(null)

      importMutation.mutate({
        file,
        year: date.year(),
        month: date.month() + 1, // dayjs months are 0-indexed
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    setFileList([])
    setImportResult(null)
    onCancel()
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.xlsx,.xls',
    fileList,
    beforeUpload: (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                      file.type === 'application/vnd.ms-excel' ||
                      file.name.endsWith('.xlsx') ||
                      file.name.endsWith('.xls')

      if (!isExcel) {
        message.error('Вы можете загружать только Excel файлы (.xlsx, .xls)')
        return Upload.LIST_IGNORE
      }

      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('Файл должен быть меньше 10MB')
        return Upload.LIST_IGNORE
      }

      setFileList([file as any])
      return false // Prevent auto upload
    },
    onRemove: () => {
      setFileList([])
    },
  }

  return (
    <Modal
      title={<Title level={4}>Импорт данных КПИ из Excel</Title>}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isUploading}
      okText={importResult ? 'Закрыть' : 'Импортировать'}
      cancelText="Отмена"
      width={700}
      okButtonProps={importResult ? { onClick: handleCancel } : undefined}
    >
      {!importResult ? (
        <>
          <Alert
            message="Формат файла"
            description={
              <>
                <Paragraph>
                  Ожидаемая структура файла Excel (KPI_Manager_2025.xlsx):
                </Paragraph>
                <ul style={{ marginBottom: 0 }}>
                  <li>Лист "УПРАВЛЕНИЕ КПИ" с таблицей, начинающейся со строки 6</li>
                  <li><strong>Столбец A:</strong> Сотрудник (ФИО)</li>
                  <li><strong>Столбец B:</strong> Оклад</li>
                  <li><strong>Столбец C:</strong> Должность</li>
                  <li><strong>Столбец E:</strong> Базовая премия</li>
                  <li><strong>Столбец F:</strong> Вариант премии (Результативный/Фиксированный/Смешанный)</li>
                  <li><strong>Столбец G:</strong> КПИ Общий %</li>
                </ul>
              </>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownloadTemplate}
            style={{ marginBottom: 16 }}
            type="default"
          >
            Скачать шаблон Excel
          </Button>

          <Form form={form} layout="vertical">
            <Form.Item
              name="period"
              label="Период (месяц и год)"
              rules={[{ required: true, message: 'Выберите период' }]}
              initialValue={dayjs()}
            >
              <DatePicker
                picker="month"
                format="MMMM YYYY"
                placeholder="Выберите месяц"
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="Файл Excel" required>
              <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">Нажмите или перетащите файл в эту область</p>
                <p className="ant-upload-hint">
                  Поддерживаются файлы .xlsx и .xls (макс. 10MB)
                </p>
              </Dragger>
            </Form.Item>
          </Form>
        </>
      ) : (
        <>
          <Alert
            message={importResult.success ? 'Импорт завершен успешно' : 'Импорт завершен с предупреждениями'}
            description={importResult.message}
            type={importResult.success && (!importResult.errors || importResult.errors.length === 0) ? 'success' : 'warning'}
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Title level={5}>Статистика импорта</Title>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="Сотрудников создано"
                value={importResult.statistics.employees_created}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Сотрудников обновлено"
                value={importResult.statistics.employees_updated}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Всего обработано"
                value={importResult.statistics.total_processed}
              />
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="КПИ записей создано"
                value={importResult.statistics.kpi_records_created}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="КПИ записей обновлено"
                value={importResult.statistics.kpi_records_updated}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Ошибок"
                value={importResult.statistics.errors}
                valueStyle={{ color: importResult.statistics.errors > 0 ? '#cf1322' : '#000' }}
              />
            </Col>
          </Row>

          {importResult.errors && importResult.errors.length > 0 && (
            <>
              <Divider />
              <Title level={5}>Ошибки импорта</Title>
              <List
                size="small"
                bordered
                dataSource={importResult.errors}
                renderItem={(error) => (
                  <List.Item>
                    <Text type="danger">{error}</Text>
                  </List.Item>
                )}
                style={{ maxHeight: 200, overflow: 'auto' }}
              />
            </>
          )}
        </>
      )}
    </Modal>
  )
}

export default ImportKPIModal
