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
  Descriptions,
  Tabs,
  Alert,
  Select,
  Input,
  Form,
  Typography,
  DatePicker,
  Spin,
} from 'antd'
import {
  SyncOutlined,
  EyeOutlined,
  DeleteOutlined,
  DollarOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  CloudUploadOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'

import { invoiceProcessingApi } from '@/api/invoiceProcessing'
import { categoriesApi } from '@/api/categories'
import { useDepartment } from '@/contexts/DepartmentContext'
import QuickInvoiceUpload from './QuickInvoiceUpload'
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
  const [categoryForm] = Form.useForm()
  const [send1CForm] = Form.useForm()

  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<ProcessedInvoiceDetail | null>(null)
  const [createExpenseModalVisible, setCreateExpenseModalVisible] = useState(false)
  const [setCategoryModalVisible, setSetCategoryModalVisible] = useState(false)
  const [send1CModalVisible, setSend1CModalVisible] = useState(false)
  const [searchText, setSearchText] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<InvoiceProcessingStatus | undefined>()
  const [validationResult, setValidationResult] = useState<any>(null)

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

  // Категории ДДС из 1С - это общий справочник для всех пользователей
  // Не фильтруем по департаменту, загружаем все категории с external_id_1c
  const { data: cashFlowCategories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['cashFlowCategories', 'all'],
    queryFn: () => invoiceProcessingApi.getCashFlowCategories(undefined),
    enabled: visible,
  })

  // Process mutation (for re-processing existing invoices from table)
  const processMutation = useMutation({
    mutationFn: (invoiceId: number) =>
      invoiceProcessingApi.process({ invoice_id: invoiceId }),
    onSuccess: async (data, invoiceId) => {
      if (data.success) {
        message.success('Счет успешно обработан!')

        // Автоматически открыть модальное окно для выбора категории
        const details = await invoiceProcessingApi.getById(invoiceId)
        setSelectedInvoice(details)

        // Установить дату оплаты по умолчанию (дата счета + 3 дня)
        const invoiceDate = details.invoice_date ? dayjs(details.invoice_date) : dayjs()
        const defaultPaymentDate = invoiceDate.add(3, 'day')

        categoryForm.setFieldsValue({
          desired_payment_date: defaultPaymentDate,
        })

        setSetCategoryModalVisible(true)
      } else {
        message.warning('Обработка завершена с ошибками. Требуется ручная проверка.')
      }
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      if (selectedInvoice) {
        loadInvoiceDetails(selectedInvoice.id)
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка обработки: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  // Update category mutation
  const updateCategoryMutation = useMutation({
    mutationFn: (values: { category_id: number; desired_payment_date: string }) =>
      invoiceProcessingApi.updateCategory(selectedInvoice!.id, values),
    onSuccess: async () => {
      message.success('Категория и дата оплаты установлены!')
      setSetCategoryModalVisible(false)
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      if (selectedInvoice) {
        // Обновляем детали счета
        await loadInvoiceDetails(selectedInvoice.id)
        // Автоматически открываем модальное окно отправки в 1С
        setSend1CModalVisible(true)
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка обновления: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  // Validate for 1C mutation
  const validateFor1CMutation = useMutation({
    mutationFn: (invoiceId: number) =>
      invoiceProcessingApi.validateFor1C(invoiceId),
    onSuccess: (data) => {
      setValidationResult(data)
      if (data.is_valid) {
        message.success('Валидация успешна! Можно отправлять в 1С.')
      } else {
        message.error('Валидация не пройдена. Проверьте ошибки.')
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка валидации: ${error.response?.data?.detail || error.message}`
      )
    },
  })

  // Create in 1C mutation
  const createIn1CMutation = useMutation({
    mutationFn: ({ invoiceId, userComment }: { invoiceId: number; userComment?: string }) =>
      invoiceProcessingApi.createIn1C(invoiceId, true, userComment),
    onSuccess: (data) => {
      if (data.success) {
        message.success('Заявка на расход успешно создана в 1С!')
        setValidationResult(null)
        setSend1CModalVisible(false)
        send1CForm.resetFields()
        queryClient.invalidateQueries({ queryKey: ['invoices'] })
        if (selectedInvoice) {
          loadInvoiceDetails(selectedInvoice.id)
        }
      } else {
        message.error(data.message)
      }
    },
    onError: (error: any) => {
      message.error(
        `Ошибка создания в 1С: ${error.response?.data?.detail || error.message}`
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
      title: '1С',
      key: '1c_status',
      width: 80,
      render: (_: any, record: ProcessedInvoiceListItem) => (
        record.external_id_1c ? (
          <Tag color="blue" icon={<CheckCircleOutlined />}>
            Создан
          </Tag>
        ) : null
      ),
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
          {record.status === 'PROCESSED' && record.category_id && (
            <Button
              type="primary"
              size="small"
              icon={<CloudUploadOutlined />}
              onClick={async () => {
                try {
                  const details = await invoiceProcessingApi.getById(record.id)
                  setSelectedInvoice(details)
                  setSend1CModalVisible(true)
                } catch (error: any) {
                  message.error(
                    `Ошибка загрузки: ${error.response?.data?.detail || error.message}`
                  )
                }
              }}
              loading={createIn1CMutation.isPending}
            >
              → 1С
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
        title="🤖 AI Обработка счетов и отправка в 1С"
        width={1200}
        open={visible}
        onClose={onClose}
        destroyOnClose
      >
        <Tabs
          defaultActiveKey="quick"
          size="large"
          style={{ marginTop: -16 }}
          items={[
            {
              key: 'quick',
              label: (
                <span style={{ fontSize: 16, fontWeight: 500 }}>
                  🚀 Быстрая отправка в 1С
                </span>
              ),
              children: (
                <QuickInvoiceUpload
                  onSuccess={() => {
                    queryClient.invalidateQueries({ queryKey: ['invoices'] })
                    message.success('Счет успешно отправлен в 1С!')
                  }}
                />
              ),
            },
            {
              key: 'list',
              label: (
                <span style={{ fontSize: 16, fontWeight: 500 }}>
                  📋 Все счета
                </span>
              ),
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
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
              ),
            },
          ]}
        />
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
            // Кнопка для установки категории (если ещё не установлена)
            selectedInvoice.status === 'PROCESSED' &&
              !selectedInvoice.category_id && (
                <Button
                  key="set-category"
                  type="default"
                  onClick={() => {
                    const invoiceDate = selectedInvoice.invoice_date ? dayjs(selectedInvoice.invoice_date) : dayjs()
                    const defaultPaymentDate = invoiceDate.add(3, 'day')
                    categoryForm.setFieldsValue({
                      desired_payment_date: defaultPaymentDate,
                    })
                    setSetCategoryModalVisible(true)
                  }}
                >
                  Установить категорию
                </Button>
              ),
            // Кнопка валидации для 1С
            selectedInvoice.status === 'PROCESSED' &&
              selectedInvoice.category_id &&
              !selectedInvoice.external_id_1c && (
                <Button
                  key="validate-1c"
                  icon={<SafetyCertificateOutlined />}
                  onClick={() => validateFor1CMutation.mutate(selectedInvoice.id)}
                  loading={validateFor1CMutation.isPending}
                >
                  Проверить для 1С
                </Button>
              ),
            // Кнопка отправки в 1С (всегда показываем для тестирования)
            selectedInvoice.status === 'PROCESSED' && (
              <Button
                key="create-1c"
                type="primary"
                icon={<CloudUploadOutlined />}
                onClick={() => {
                  console.log('Кнопка нажата, selectedInvoice:', selectedInvoice)
                  console.log('Category ID:', selectedInvoice.category_id)
                  if (!selectedInvoice.category_id) {
                    message.warning('Сначала установите категорию ДДС!')
                    setSetCategoryModalVisible(true)
                  } else {
                    console.log('Открываем модальное окно отправки в 1С')
                    setSend1CModalVisible(true)
                  }
                }}
                loading={createIn1CMutation.isPending}
                disabled={validationResult && !validationResult.is_valid}
              >
                Отправить в 1С
              </Button>
            ),
            // Кнопка создания расхода (старый функционал)
            selectedInvoice.status === 'PROCESSED' &&
              !selectedInvoice.expense_id && (
                <Button
                  key="create-expense"
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
                        <Space>
                          {getStatusTag(selectedInvoice.status)}
                          {selectedInvoice.external_id_1c && (
                            <Tag color="blue" icon={<CheckCircleOutlined />}>
                              Создан в 1С
                            </Tag>
                          )}
                        </Space>
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

                    {selectedInvoice.category_id && selectedInvoice.desired_payment_date && (
                      <Alert
                        type="info"
                        message="Категория установлена"
                        description={
                          <>
                            <Text strong>Желаемая дата оплаты: </Text>
                            <Text>
                              {dayjs(selectedInvoice.desired_payment_date).format('DD.MM.YYYY')}
                            </Text>
                          </>
                        }
                        style={{ marginTop: 16 }}
                      />
                    )}

                    {validationResult && (
                      <Alert
                        type={validationResult.is_valid ? 'success' : 'error'}
                        message={validationResult.is_valid ? 'Валидация пройдена' : 'Ошибки валидации'}
                        description={
                          <>
                            {validationResult.errors?.length > 0 && (
                              <>
                                <Text strong>Ошибки:</Text>
                                <ul>
                                  {validationResult.errors.map((err: string, idx: number) => (
                                    <li key={idx}>{err}</li>
                                  ))}
                                </ul>
                              </>
                            )}
                            {validationResult.warnings?.length > 0 && (
                              <>
                                <Text strong>Предупреждения:</Text>
                                <ul>
                                  {validationResult.warnings.map((warn: string, idx: number) => (
                                    <li key={idx}>{warn}</li>
                                  ))}
                                </ul>
                              </>
                            )}
                            {validationResult.is_valid && validationResult.found_data && (
                              <>
                                {validationResult.found_data.counterparty && (
                                  <div>
                                    <Text strong>Контрагент: </Text>
                                    <Text>{validationResult.found_data.counterparty.name}</Text>
                                  </div>
                                )}
                                {validationResult.found_data.organization && (
                                  <div>
                                    <Text strong>Организация: </Text>
                                    <Text>{validationResult.found_data.organization.name}</Text>
                                  </div>
                                )}
                                {validationResult.found_data.cash_flow_category && (
                                  <div>
                                    <Text strong>Статья ДДС: </Text>
                                    <Text>{validationResult.found_data.cash_flow_category.name}</Text>
                                  </div>
                                )}
                              </>
                            )}
                          </>
                        }
                        style={{ marginTop: 16 }}
                      />
                    )}

                    {selectedInvoice.external_id_1c && (
                      <Alert
                        type="success"
                        message="Создан в 1С"
                        description={
                          <>
                            <Text strong>UUID документа: </Text>
                            <Text code copyable>{selectedInvoice.external_id_1c}</Text>
                            <br />
                            {selectedInvoice.created_in_1c_at && (
                              <>
                                <Text strong>Дата создания: </Text>
                                <Text>
                                  {dayjs(selectedInvoice.created_in_1c_at).format(
                                    'DD.MM.YYYY HH:mm:ss'
                                  )}
                                </Text>
                              </>
                            )}
                          </>
                        }
                        style={{ marginTop: 16 }}
                        icon={<CheckCircleOutlined />}
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

      {/* Set Category Modal */}
      {selectedInvoice && (
        <Modal
          title="Выбор категории и даты оплаты для отправки в 1С"
          open={setCategoryModalVisible}
          onCancel={() => setSetCategoryModalVisible(false)}
          onOk={() => categoryForm.submit()}
          confirmLoading={updateCategoryMutation.isPending}
          okText="Сохранить"
          cancelText="Отмена"
          width={600}
        >
          <Alert
            message="Важно!"
            description="Выберите статью движения денежных средств (ДДС) и укажите желаемую дату оплаты для создания заявки на расход в 1С."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form
            form={categoryForm}
            layout="vertical"
            onFinish={(values) => {
              const formattedValues = {
                category_id: values.category_id,
                desired_payment_date: values.desired_payment_date.format('YYYY-MM-DD'),
              }
              updateCategoryMutation.mutate(formattedValues)
            }}
          >
            <Form.Item
              name="category_id"
              label="Статья движения денежных средств (ДДС)"
              rules={[{ required: true, message: 'Выберите статью ДДС' }]}
            >
              <Select
                placeholder="Выберите категорию из 1С"
                showSearch
                optionFilterProp="children"
                loading={categoriesLoading}
                notFoundContent={categoriesLoading ? <Spin size="small" /> : 'Нет данных'}
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

            <Form.Item
              name="desired_payment_date"
              label="Желаемая дата оплаты"
              rules={[{ required: true, message: 'Выберите дату' }]}
            >
              <DatePicker
                format="DD.MM.YYYY"
                style={{ width: '100%' }}
                placeholder="Выберите дату"
              />
            </Form.Item>

            {selectedInvoice.invoice_number && (
              <Alert
                message={
                  <>
                    <Text strong>Счет: </Text>
                    <Text>{selectedInvoice.invoice_number}</Text>
                    <br />
                    <Text strong>Поставщик: </Text>
                    <Text>{selectedInvoice.supplier_name || 'Не указан'}</Text>
                    <br />
                    <Text strong>Сумма: </Text>
                    <Text>{selectedInvoice.total_amount?.toLocaleString('ru-RU')} ₽</Text>
                  </>
                }
                style={{ marginTop: 8 }}
              />
            )}
          </Form>
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

      {/* Send to 1C Modal with Comment */}
      {selectedInvoice && (
        <Modal
          title="Отправить заявку в 1С"
          open={send1CModalVisible}
          onCancel={() => {
            setSend1CModalVisible(false)
            send1CForm.resetFields()
          }}
          onOk={() => send1CForm.submit()}
          confirmLoading={createIn1CMutation.isPending}
          okText="Отправить"
          cancelText="Отмена"
          width={600}
        >
          <Alert
            message="Отправка заявки на расход в 1С"
            description="Вы можете добавить комментарий, который будет отображаться в назначении платежа в 1С."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form
            form={send1CForm}
            layout="vertical"
            onFinish={(values) => {
              createIn1CMutation.mutate({
                invoiceId: selectedInvoice.id,
                userComment: values.user_comment,
              })
            }}
          >
            <Form.Item
              name="user_comment"
              label="Комментарий (опционально)"
            >
              <TextArea
                rows={4}
                placeholder="Введите комментарий для заявки (будет добавлен в назначение платежа)"
                maxLength={500}
                showCount
              />
            </Form.Item>

            {selectedInvoice.invoice_number && (
              <Alert
                message={
                  <>
                    <Text strong>Счет: </Text>
                    <Text>{selectedInvoice.invoice_number}</Text>
                    <br />
                    <Text strong>Поставщик: </Text>
                    <Text>{selectedInvoice.supplier_name || 'Не указан'}</Text>
                    <br />
                    <Text strong>Сумма: </Text>
                    <Text>{selectedInvoice.total_amount?.toLocaleString('ru-RU')} ₽</Text>
                    <br />
                    <Text strong>Дата оплаты: </Text>
                    <Text>
                      {selectedInvoice.desired_payment_date
                        ? dayjs(selectedInvoice.desired_payment_date).format('DD.MM.YYYY')
                        : 'Не указана'}
                    </Text>
                  </>
                }
                style={{ marginTop: 8 }}
              />
            )}

            {selectedInvoice.external_id_1c && (
              <Alert
                message="Внимание!"
                description="Эта заявка уже была отправлена в 1С ранее. Повторная отправка создаст дубликат."
                type="warning"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </Form>
        </Modal>
      )}
    </>
  )
}

export default InvoiceProcessingDrawer
