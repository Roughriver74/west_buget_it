import React, { useState } from 'react'
import {
  Drawer,
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Upload,
  Descriptions,
  Tabs,
  Alert,
  Select,
  Input,
  Form,
  Typography,
} from 'antd'
import {
  UploadOutlined,
  SyncOutlined,
  EyeOutlined,
  DeleteOutlined,
  DollarOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { UploadFile } from 'antd'
import dayjs from 'dayjs'

import { invoiceProcessingApi } from '@/api/invoiceProcessing'
import { categoriesApi } from '@/api/categories'
import { useDepartment } from '@/contexts/DepartmentContext'
import type {
  ProcessedInvoiceListItem,
  InvoiceProcessingStatus,
  ProcessedInvoiceDetail,
  InvoiceListFilters,
} from '@/types/invoiceProcessing'

const { Text, Paragraph } = Typography
const { TextArea } = Input

interface InvoiceProcessingDrawerProps {
  visible: boolean
  onClose: () => void
}

const InvoiceProcessingDrawer: React.FC<InvoiceProcessingDrawerProps> = ({
  visible,
  onClose,
}) => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const [form] = Form.useForm()

  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<ProcessedInvoiceDetail | null>(null)
  const [createExpenseModalVisible, setCreateExpenseModalVisible] = useState(false)
  const [searchText, setSearchText] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<InvoiceProcessingStatus | undefined>()

  const filters: InvoiceListFilters = {
    department_id: selectedDepartment?.id,
    search: searchText || undefined,
    status: statusFilter,
  }

  // Fetch invoices
  const { data: invoicesData, isLoading } = useQuery({
    queryKey: ['invoices', selectedDepartment?.id, searchText, statusFilter],
    queryFn: () => invoiceProcessingApi.getAll(filters),
    enabled: !!selectedDepartment && visible,
  })

  // Fetch categories for expense creation
  const { data: categories } = useQuery({
    queryKey: ['categories', selectedDepartment?.id],
    queryFn: () => categoriesApi.getAll({ department_id: selectedDepartment?.id }),
    enabled: !!selectedDepartment && visible,
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      invoiceProcessingApi.upload(file, selectedDepartment?.id),
    onSuccess: (data) => {
      message.success(`Файл загружен успешно! Запуск обработки...`)
      setFileList([])
      queryClient.invalidateQueries({ queryKey: ['invoices'] })

      // Автоматически запускаем обработку загруженного файла
      if (data.invoice_id) {
        processMutation.mutate(data.invoice_id)
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка загрузки: ${error.response?.data?.detail || error.message}`
      )
      setUploading(false)
    },
  })

  // Process mutation
  const processMutation = useMutation({
    mutationFn: (invoiceId: number) =>
      invoiceProcessingApi.process({ invoice_id: invoiceId }),
    onSuccess: (data) => {
      setUploading(false)
      if (data.success) {
        message.success('Счет успешно обработан!')
      } else {
        message.warning('Обработка завершена с ошибками. Требуется ручная проверка.')
      }
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      if (selectedInvoice) {
        loadInvoiceDetails(selectedInvoice.id)
      }
    },
    onError: (error: any) => {
      setUploading(false)
      message.error(
        `Ошибка обработки: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  // Create expense mutation
  const createExpenseMutation = useMutation({
    mutationFn: (values: any) =>
      invoiceProcessingApi.createExpense({
        invoice_id: selectedInvoice!.id,
        category_id: values.category_id,
        amount_override: values.amount_override || null,
        description_override: values.description_override || null,
      }),
    onSuccess: (data) => {
      if (data.success) {
        message.success(
          data.contractor_created
            ? 'Расход создан! Контрагент добавлен автоматически.'
            : 'Расход успешно создан!'
        )
        setCreateExpenseModalVisible(false)
        queryClient.invalidateQueries({ queryKey: ['invoices'] })
        queryClient.invalidateQueries({ queryKey: ['expenses'] })
        if (selectedInvoice) {
          loadInvoiceDetails(selectedInvoice.id)
        }
      } else {
        message.error(data.message)
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка создания расхода: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (invoiceId: number) => invoiceProcessingApi.delete(invoiceId),
    onSuccess: () => {
      message.success('Счет удален')
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setDetailModalVisible(false)
    },
    onError: (error: any) => {
      message.error(
        `Ошибка удаления: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('Выберите файл для загрузки')
      return
    }

    setUploading(true)
    try {
      const file = fileList[0].originFileObj as File
      await uploadMutation.mutateAsync(file)
      setUploading(false)
    } catch (error) {
      setUploading(false)
    }
  }

  const handleProcess = (invoiceId: number) => {
    processMutation.mutate(invoiceId)
  }

  const loadInvoiceDetails = async (invoiceId: number) => {
    try {
      const details = await invoiceProcessingApi.getById(invoiceId)
      setSelectedInvoice(details)
      setDetailModalVisible(true)
    } catch (error: any) {
      message.error(
        `Ошибка загрузки деталей: ${error.response?.data?.detail || error.message}`
      )
    }
  }

  const handleDelete = (invoiceId: number) => {
    Modal.confirm({
      title: 'Удалить счет?',
      content: 'Это действие нельзя отменить.',
      okText: 'Удалить',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => deleteMutation.mutate(invoiceId),
    })
  }

  const getStatusTag = (status: InvoiceProcessingStatus) => {
    const statusConfig: Record<
      InvoiceProcessingStatus,
      { color: string; text: string; icon: React.ReactNode }
    > = {
      PENDING: {
        color: 'default',
        text: 'Ожидает',
        icon: <ClockCircleOutlined />,
      },
      PROCESSING: {
        color: 'processing',
        text: 'Обработка',
        icon: <SyncOutlined spin />,
      },
      PROCESSED: {
        color: 'success',
        text: 'Обработан',
        icon: <CheckCircleOutlined />,
      },
      ERROR: { color: 'error', text: 'Ошибка', icon: <CloseCircleOutlined /> },
      MANUAL_REVIEW: {
        color: 'warning',
        text: 'Требуется проверка',
        icon: <WarningOutlined />,
      },
      EXPENSE_CREATED: {
        color: 'cyan',
        text: 'Расход создан',
        icon: <CheckCircleOutlined />,
      },
    }
    const config = statusConfig[status]
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  const columns = [
    {
      title: 'Файл',
      dataIndex: 'original_filename',
      key: 'filename',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: InvoiceProcessingStatus) => getStatusTag(status),
    },
    {
      title: '№ Счета',
      dataIndex: 'invoice_number',
      key: 'invoice_number',
      width: 120,
    },
    {
      title: 'Поставщик',
      dataIndex: 'supplier_name',
      key: 'supplier_name',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Сумма',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (amount: number) =>
        amount ? `${amount.toLocaleString('ru-RU')} ₽` : '-',
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: ProcessedInvoiceListItem) => (
        <Space size="small">
          {record.status === 'PENDING' && (
            <Button
              type="primary"
              size="small"
              icon={<SyncOutlined />}
              onClick={() => handleProcess(record.id)}
              loading={processMutation.isPending}
            >
              Обработать
            </Button>
          )}
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => loadInvoiceDetails(record.id)}
          >
            Детали
          </Button>
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
            disabled={deleteMutation.isPending}
          />
        </Space>
      ),
    },
  ]

  return (
    <>
      <Drawer
        title="Обработка счетов AI"
        width={1200}
        open={visible}
        onClose={onClose}
        destroyOnClose
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="AI обработка счетов"
            description="Загружайте счета в формате PDF или изображения, и система автоматически распознает и извлечет данные с помощью OCR и AI."
            type="info"
            showIcon
          />

          {/* Upload Card */}
          <Card title="Загрузка счета" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                fileList={fileList}
                onChange={({ fileList }) => setFileList(fileList)}
                beforeUpload={(file) => {
                  const isValidType =
                    file.type === 'application/pdf' ||
                    file.type.startsWith('image/')
                  if (!isValidType) {
                    message.error('Поддерживаются только PDF и изображения!')
                    return false
                  }
                  const isLt10M = file.size / 1024 / 1024 < 10
                  if (!isLt10M) {
                    message.error('Файл должен быть меньше 10MB!')
                    return false
                  }
                  return false // Prevent auto upload
                }}
                maxCount={1}
                accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
              >
                <Button icon={<UploadOutlined />}>Выбрать файл</Button>
              </Upload>
              <Button
                type="primary"
                onClick={handleUpload}
                loading={uploading}
                disabled={fileList.length === 0}
              >
                Загрузить и начать обработку
              </Button>
            </Space>
          </Card>

          {/* Filters */}
          <Card size="small">
            <Space>
              <Input.Search
                placeholder="Поиск по номеру или поставщику"
                style={{ width: 250 }}
                onSearch={setSearchText}
                allowClear
                size="small"
              />
              <Select
                placeholder="Фильтр по статусу"
                style={{ width: 180 }}
                onChange={setStatusFilter}
                allowClear
                size="small"
              >
                <Select.Option value="PENDING">Ожидает</Select.Option>
                <Select.Option value="PROCESSING">Обработка</Select.Option>
                <Select.Option value="PROCESSED">Обработан</Select.Option>
                <Select.Option value="ERROR">Ошибка</Select.Option>
                <Select.Option value="MANUAL_REVIEW">
                  Требуется проверка
                </Select.Option>
                <Select.Option value="EXPENSE_CREATED">
                  Расход создан
                </Select.Option>
              </Select>
            </Space>
          </Card>

          {/* Invoices Table */}
          <Card
            title={`Загруженные счета (${invoicesData?.total || 0})`}
            size="small"
          >
            <Table
              columns={columns}
              dataSource={invoicesData?.items || []}
              loading={isLoading}
              rowKey="id"
              scroll={{ x: 1000 }}
              pagination={{
                total: invoicesData?.total || 0,
                pageSize: invoicesData?.page_size || 20,
                showSizeChanger: true,
                showTotal: (total) => `Всего: ${total}`,
                size: 'small',
              }}
              size="small"
            />
          </Card>
        </Space>
      </Drawer>

      {/* Invoice Detail Modal */}
      {selectedInvoice && (
        <Modal
          title={`Счет: ${selectedInvoice.original_filename}`}
          open={detailModalVisible}
          onCancel={() => setDetailModalVisible(false)}
          width={900}
          footer={[
            <Button key="close" onClick={() => setDetailModalVisible(false)}>
              Закрыть
            </Button>,
            selectedInvoice.status === 'PROCESSED' &&
              !selectedInvoice.expense_id && (
                <Button
                  key="create-expense"
                  type="primary"
                  icon={<DollarOutlined />}
                  onClick={() => {
                    setCreateExpenseModalVisible(true)
                    form.setFieldsValue({
                      amount_override: selectedInvoice.total_amount,
                      description_override: selectedInvoice.payment_purpose,
                    })
                  }}
                >
                  Создать расход
                </Button>
              ),
          ]}
        >
          <Tabs
            items={[
              {
                key: 'info',
                label: 'Информация',
                children: (
                  <div>
                    {selectedInvoice.errors &&
                      selectedInvoice.errors.length > 0 && (
                        <Alert
                          type="error"
                          message="Ошибки обработки"
                          description={
                            <ul>
                              {selectedInvoice.errors.map((err, idx) => (
                                <li key={idx}>
                                  {err.field}: {err.message}
                                </li>
                              ))}
                            </ul>
                          }
                          style={{ marginBottom: 16 }}
                        />
                      )}

                    {selectedInvoice.warnings &&
                      selectedInvoice.warnings.length > 0 && (
                        <Alert
                          type="warning"
                          message="Предупреждения"
                          description={
                            <ul>
                              {selectedInvoice.warnings.map((warn, idx) => (
                                <li key={idx}>
                                  {warn.field}: {warn.message}
                                </li>
                              ))}
                            </ul>
                          }
                          style={{ marginBottom: 16 }}
                        />
                      )}

                    <Descriptions bordered column={2} size="small">
                      <Descriptions.Item label="Статус" span={2}>
                        {getStatusTag(selectedInvoice.status)}
                      </Descriptions.Item>
                      <Descriptions.Item label="Номер счета">
                        {selectedInvoice.invoice_number || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Дата счета">
                        {selectedInvoice.invoice_date
                          ? dayjs(selectedInvoice.invoice_date).format(
                              'DD.MM.YYYY'
                            )
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Поставщик" span={2}>
                        {selectedInvoice.supplier_name || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="ИНН">
                        {selectedInvoice.supplier_inn || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="КПП">
                        {selectedInvoice.supplier_kpp || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Сумма без НДС">
                        {selectedInvoice.amount_without_vat
                          ? `${selectedInvoice.amount_without_vat.toLocaleString('ru-RU')} ₽`
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="НДС">
                        {selectedInvoice.vat_amount
                          ? `${selectedInvoice.vat_amount.toLocaleString('ru-RU')} ₽`
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Итого" span={2}>
                        <Text strong>
                          {selectedInvoice.total_amount
                            ? `${selectedInvoice.total_amount.toLocaleString('ru-RU')} ₽`
                            : '-'}
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Назначение платежа" span={2}>
                        {selectedInvoice.payment_purpose || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Договор">
                        {selectedInvoice.contract_number || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Дата договора">
                        {selectedInvoice.contract_date
                          ? dayjs(selectedInvoice.contract_date).format(
                              'DD.MM.YYYY'
                            )
                          : '-'}
                      </Descriptions.Item>
                    </Descriptions>

                    {selectedInvoice.expense_id && (
                      <Alert
                        type="info"
                        message={`Расход создан (ID: ${selectedInvoice.expense_id})`}
                        style={{ marginTop: 16 }}
                      />
                    )}
                  </div>
                ),
              },
              {
                key: 'ocr',
                label: 'OCR Текст',
                children: (
                  <div>
                    <Paragraph>
                      <Text type="secondary">
                        Время обработки:{' '}
                        {selectedInvoice.ocr_processing_time_sec || 0} сек
                      </Text>
                    </Paragraph>
                    <TextArea
                      value={selectedInvoice.ocr_text || 'Текст не распознан'}
                      rows={15}
                      readOnly
                    />
                  </div>
                ),
              },
              {
                key: 'json',
                label: 'JSON',
                children: (
                  <div>
                    <Paragraph>
                      <Text type="secondary">
                        Модель: {selectedInvoice.ai_model_used || 'N/A'}
                        <br />
                        Время: {selectedInvoice.ai_processing_time_sec || 0} сек
                      </Text>
                    </Paragraph>
                    <TextArea
                      value={JSON.stringify(
                        selectedInvoice.parsed_data,
                        null,
                        2
                      )}
                      rows={15}
                      readOnly
                    />
                  </div>
                ),
              },
            ]}
          />
        </Modal>
      )}

      {/* Create Expense Modal */}
      <Modal
        title="Создать расход из счета"
        open={createExpenseModalVisible}
        onCancel={() => setCreateExpenseModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={createExpenseMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => createExpenseMutation.mutate(values)}
        >
          <Form.Item
            name="category_id"
            label="Категория"
            rules={[{ required: true, message: 'Выберите категорию' }]}
          >
            <Select placeholder="Выберите категорию бюджета">
              {categories?.map((cat) => (
                <Select.Option key={cat.id} value={cat.id}>
                  {cat.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="amount_override" label="Сумма (переопределить)">
            <Input type="number" prefix="₽" />
          </Form.Item>
          <Form.Item
            name="description_override"
            label="Описание (переопределить)"
          >
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default InvoiceProcessingDrawer
