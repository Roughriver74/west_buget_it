import React, { useState } from 'react'
import {
  Card,
  Upload,
  Form,
  Select,
  DatePicker,
  Button,
  Steps,
  Alert,
  Typography,
  Space,
  message,
  Spin,
  Progress,
  Result,
  Input,
} from 'antd'
import {
  InboxOutlined,
  CalendarOutlined,
  FolderOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CommentOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { UploadFile, UploadProps } from 'antd'
import dayjs, { Dayjs } from 'dayjs'

import { invoiceProcessingApi } from '@/api/invoiceProcessing'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Dragger } = Upload
const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface QuickInvoiceUploadProps {
  onSuccess?: () => void
}

type ProcessStep = 'upload' | 'ocr' | 'category' | 'validate' | 'create' | 'done'

const QuickInvoiceUpload: React.FC<QuickInvoiceUploadProps> = ({ onSuccess }) => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const [form] = Form.useForm()

  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [currentStep, setCurrentStep] = useState<ProcessStep>('upload')
  const [progress, setProgress] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string; external_id?: string } | null>(null)

  // Категории ДДС из 1С - это общий справочник для всех пользователей
  // Не фильтруем по департаменту, загружаем все категории с external_id_1c
  const { data: cashFlowCategories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['cashFlowCategories', 'all'],
    queryFn: () => invoiceProcessingApi.getCashFlowCategories(undefined),
    enabled: true,
  })

  // Steps configuration
  const steps = [
    { key: 'upload', title: 'Загрузка', icon: <InboxOutlined /> },
    { key: 'ocr', title: 'Распознавание', icon: <LoadingOutlined /> },
    { key: 'category', title: 'Категория', icon: <FolderOutlined /> },
    { key: 'validate', title: 'Проверка', icon: <LoadingOutlined /> },
    { key: 'create', title: 'Отправка в 1С', icon: <CloudUploadOutlined /> },
    { key: 'done', title: 'Готово', icon: <CheckCircleOutlined /> },
  ]

  const getCurrentStepIndex = () => {
    return steps.findIndex((s) => s.key === currentStep)
  }

  // Upload configuration
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.pdf,.png,.jpg,.jpeg',
    fileList,
    beforeUpload: (file) => {
      const isPDF = file.type === 'application/pdf'
      const isImage = file.type.startsWith('image/')
      if (!isPDF && !isImage) {
        message.error('Можно загружать только PDF или изображения!')
        return false
      }
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('Файл должен быть меньше 10MB!')
        return false
      }

      setFileList([file])
      return false // Prevent auto upload
    },
    onRemove: () => {
      setFileList([])
    },
  }

  // Main processing function
  const handleSubmit = async (values: {
    category_id: number
    desired_payment_date: Dayjs
    user_comment?: string
  }) => {
    if (fileList.length === 0) {
      message.error('Выберите файл для загрузки')
      return
    }

    setProcessing(true)
    setProgress(0)
    setResult(null)

    try {
      // Step 1: Upload
      setCurrentStep('upload')
      setProgress(10)
      const uploadResponse = await invoiceProcessingApi.upload(
        fileList[0] as any,
        selectedDepartment?.id
      )
      const newInvoiceId = uploadResponse.invoice_id
      setProgress(20)

      // Step 2: OCR + AI Processing
      setCurrentStep('ocr')
      setProgress(30)
      await invoiceProcessingApi.process({ invoice_id: newInvoiceId })
      setProgress(50)

      // Step 3: Set Category
      setCurrentStep('category')
      setProgress(60)
      await invoiceProcessingApi.updateCategory(newInvoiceId, {
        category_id: values.category_id,
        desired_payment_date: values.desired_payment_date.format('YYYY-MM-DD'),
      })
      setProgress(70)

      // Step 4: Validate
      setCurrentStep('validate')
      setProgress(80)
      const validationResult = await invoiceProcessingApi.validateFor1C(newInvoiceId)
      if (!validationResult.is_valid) {
        throw new Error(`Ошибка валидации: ${validationResult.errors.join(', ')}`)
      }
      setProgress(85)

      // Step 5: Create in 1C
      setCurrentStep('create')
      setProgress(90)
      const createResult = await invoiceProcessingApi.createIn1C(
        newInvoiceId,
        true,
        values.user_comment
      )
      if (!createResult.success) {
        throw new Error(createResult.message)
      }
      setProgress(100)

      // Step 6: Done
      setCurrentStep('done')
      setResult({
        success: true,
        message: 'Заявка на расход успешно создана в 1С!',
        external_id: createResult.external_id_1c || undefined,
      })

      // Reset form
      setTimeout(() => {
        form.resetFields()
        setFileList([])
        queryClient.invalidateQueries({ queryKey: ['invoices'] })
        if (onSuccess) onSuccess()
      }, 3000)
    } catch (error: any) {
      setCurrentStep('upload')
      setProgress(0)

      // Обработка ошибок валидации Pydantic (массив объектов)
      let errorMessage = 'Произошла ошибка'
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          errorMessage = detail.map((err: any) => err.msg || JSON.stringify(err)).join('; ')
        } else if (typeof detail === 'string') {
          errorMessage = detail
        } else {
          errorMessage = JSON.stringify(detail)
        }
      } else if (error.message) {
        errorMessage = error.message
      }

      setResult({
        success: false,
        message: errorMessage,
      })
      message.error(errorMessage)
    } finally {
      setProcessing(false)
    }
  }

  // Set default payment date (today + 3 days)
  const defaultPaymentDate = dayjs().add(3, 'day')

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 0' }}>
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '16px 16px 0 0',
          padding: '32px',
          textAlign: 'center',
          color: 'white',
        }}
      >
        <CloudUploadOutlined style={{ fontSize: 48, marginBottom: 16 }} />
        <Title level={2} style={{ color: 'white', margin: 0 }}>
          Быстрая отправка счета в 1С
        </Title>
        <Paragraph style={{ color: 'rgba(255,255,255,0.9)', marginTop: 8, marginBottom: 0 }}>
          Загрузите счет, выберите категорию и дату — система сама распознает и отправит в 1С
        </Paragraph>
      </div>

      {/* Main Card */}
      <Card
        style={{
          borderRadius: '0 0 16px 16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        }}
      >
        {/* Progress Steps */}
        {processing && (
          <div style={{ marginBottom: 24 }}>
            <Steps current={getCurrentStepIndex()} size="small">
              {steps.map((step) => (
                <Step key={step.key} title={step.title} icon={step.icon} />
              ))}
            </Steps>
            <Progress percent={progress} status="active" style={{ marginTop: 16 }} />
          </div>
        )}

        {/* Result */}
        {result && (
          <Result
            status={result.success ? 'success' : 'error'}
            title={result.success ? 'Успешно!' : 'Ошибка'}
            subTitle={result.message}
            extra={
              result.success && result.external_id ? (
                <Alert
                  type="info"
                  message={
                    <>
                      <Text strong>UUID документа в 1С: </Text>
                      <Text code copyable>
                        {result.external_id}
                      </Text>
                    </>
                  }
                />
              ) : null
            }
            style={{ marginBottom: 24 }}
          />
        )}

        {/* Form */}
        {!processing && !result && (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              desired_payment_date: defaultPaymentDate,
            }}
          >
            {/* File Upload */}
            <Form.Item
              label={
                <Space>
                  <InboxOutlined />
                  <Text strong>Файл счета</Text>
                </Space>
              }
              required
            >
              <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ color: '#667eea' }} />
                </p>
                <p className="ant-upload-text">
                  Нажмите или перетащите файл для загрузки
                </p>
                <p className="ant-upload-hint">
                  Поддерживаются форматы: PDF, PNG, JPG (макс. 10MB)
                </p>
              </Dragger>
            </Form.Item>

            {/* Category */}
            <Form.Item
              name="category_id"
              label={
                <Space>
                  <FolderOutlined />
                  <Text strong>Статья движения денежных средств (ДДС)</Text>
                </Space>
              }
              rules={[{ required: true, message: 'Выберите статью ДДС' }]}
            >
              <Select
                size="large"
                placeholder="Выберите категорию из 1С"
                showSearch
                optionFilterProp="children"
                loading={categoriesLoading}
                notFoundContent={categoriesLoading ? <Spin size="small" /> : 'Нет данных'}
                suffixIcon={<FolderOutlined />}
              >
                {cashFlowCategories
                  ?.filter((cat) => !cat.is_folder)
                  .map((cat) => (
                    <Select.Option key={cat.id} value={cat.id}>
                      {cat.code ? `[${cat.code}] ${cat.name}` : cat.name}
                    </Select.Option>
                  ))}
              </Select>
            </Form.Item>

            {/* Payment Date */}
            <Form.Item
              name="desired_payment_date"
              label={
                <Space>
                  <CalendarOutlined />
                  <Text strong>Желаемая дата оплаты</Text>
                </Space>
              }
              rules={[{ required: true, message: 'Выберите дату оплаты' }]}
            >
              <DatePicker
                size="large"
                format="DD.MM.YYYY"
                style={{ width: '100%' }}
                placeholder="Выберите дату"
                suffixIcon={<CalendarOutlined />}
              />
            </Form.Item>

            {/* User Comment */}
            <Form.Item
              name="user_comment"
              label={
                <Space>
                  <CommentOutlined />
                  <Text strong>Комментарий</Text>
                </Space>
              }
            >
              <Input.TextArea
                size="large"
                rows={3}
                placeholder="Введите комментарий для заявки (опционально)"
                maxLength={500}
                showCount
              />
            </Form.Item>

            {/* Submit Button */}
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                icon={<CloudUploadOutlined />}
                disabled={fileList.length === 0}
                style={{
                  height: 56,
                  fontSize: 16,
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                }}
              >
                Отправить в 1С
              </Button>
            </Form.Item>

            {/* Info Alert */}
            <Alert
              type="info"
              showIcon
              message="Как это работает?"
              description={
                <ol style={{ paddingLeft: 20, margin: '8px 0 0 0' }}>
                  <li>Система автоматически распознает текст счета (OCR)</li>
                  <li>AI извлекает данные: номер, дату, сумму, контрагента</li>
                  <li>Проверяет данные в справочниках 1С</li>
                  <li>Создает заявку на расход в 1С с прикрепленным файлом</li>
                </ol>
              }
            />
          </Form>
        )}

        {/* Reset button after result */}
        {result && (
          <Button
            type="default"
            size="large"
            block
            onClick={() => {
              setResult(null)
              setCurrentStep('upload')
              setProgress(0)
              form.resetFields()
              setFileList([])
            }}
            style={{ marginTop: 16 }}
          >
            Загрузить еще один счет
          </Button>
        )}
      </Card>
    </div>
  )
}

export default QuickInvoiceUpload
