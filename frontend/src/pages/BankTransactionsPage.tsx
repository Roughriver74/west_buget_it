import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Tag,
  Select,
  DatePicker,
  Input,
  Space,
  Modal,
  Upload,
  Statistic,
  Row,
  Col,
  Drawer,
  Form,
  Tooltip,
  App,
} from 'antd'
import {
  UploadOutlined,
  ReloadOutlined,
  FilterOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DollarOutlined,
  FileTextOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { bankTransactionsApi, categoriesApi } from '@/api'
import type { BankTransaction, BankTransactionStatus } from '@/types/bankTransaction'
import type { BudgetCategory } from '@/types'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import ColumnMappingModal from '@/components/bank/ColumnMappingModal'

const { RangePicker } = DatePicker
const { Search } = Input

const BankTransactionsPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const { modal } = App.useApp()
  const { message } = App.useApp()

  // Filters
  const [status, setStatus] = useState<BankTransactionStatus | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [search, setSearch] = useState('')
  const [onlyUnprocessed, setOnlyUnprocessed] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  // Modals
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [mappingModalOpen, setMappingModalOpen] = useState(false)
  const [odataSyncModalOpen, setOdataSyncModalOpen] = useState(false)
  const [categorizeDrawerOpen, setCategorizeDrawerOpen] = useState(false)
  const [matchingDrawerOpen, setMatchingDrawerOpen] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null)

  // Import state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)

  // Selection state
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  // Editable state
  const [editingKey, setEditingKey] = useState<number | null>(null)
  const [editForm] = Form.useForm()

  // Forms
  const [categorizeForm] = Form.useForm()
  const [odataSyncForm] = Form.useForm()

  // Fetch transactions
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: [
      'bankTransactions',
      page,
      pageSize,
      status,
      dateRange,
      search,
      onlyUnprocessed,
      selectedDepartment?.id,
    ],
    queryFn: () =>
      bankTransactionsApi.getTransactions({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        status,
        date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
        search: search || undefined,
        only_unprocessed: onlyUnprocessed,
        department_id: selectedDepartment?.id,
      }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['bankTransactionsStats', selectedDepartment?.id],
    queryFn: () =>
      bankTransactionsApi.getStats({
        department_id: selectedDepartment?.id,
      }),
  })

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories', selectedDepartment?.id],
    queryFn: () => categoriesApi.getAll({ department_id: selectedDepartment?.id, is_active: true }),
  })

  // Fetch matching expenses
  const { data: matchingSuggestions, isLoading: matchingLoading } = useQuery({
    queryKey: ['matchingExpenses', selectedTransaction?.id],
    queryFn: () =>
      selectedTransaction
        ? bankTransactionsApi.getMatchingExpenses(selectedTransaction.id, 10)
        : Promise.resolve([]),
    enabled: !!selectedTransaction && matchingDrawerOpen,
  })

  // Fetch AI category suggestions
  const { data: categorySuggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ['categorySuggestions', selectedTransaction?.id],
    queryFn: () =>
      selectedTransaction
        ? bankTransactionsApi.getCategorySuggestions(selectedTransaction.id, 3)
        : Promise.resolve([]),
    enabled: !!selectedTransaction && categorizeDrawerOpen,
  })

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: (file: File) => bankTransactionsApi.previewImport(file),
    onSuccess: (result) => {
      setPreviewData(result)
      setImportModalOpen(false)
      setMappingModalOpen(true)
    },
    onError: (error: any) => {
      message.error(`Ошибка чтения файла: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Import mutation
  const importMutation = useMutation({
    mutationFn: ({ file, mapping }: { file: File; mapping: Record<string, string> }) =>
      bankTransactionsApi.importFromExcel(file, selectedDepartment?.id, mapping),
    onSuccess: (result) => {
      message.success(
        `Импортировано: ${result.imported}, пропущено: ${result.skipped} транзакций`
      )
      if (result.errors.length > 0) {
        message.warning(`Ошибок при импорте: ${result.errors.length}`)
      }
      setMappingModalOpen(false)
      setUploadFile(null)
      setPreviewData(null)
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка импорта: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Categorize mutation
  const categorizeMutation = useMutation({
    mutationFn: ({ id, categoryId, notes }: { id: number; categoryId: number; notes?: string }) =>
      bankTransactionsApi.categorize(id, { category_id: categoryId, notes }),
    onSuccess: () => {
      message.success('Категория установлена')
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
      setCategorizeDrawerOpen(false)
      setSelectedTransaction(null)
      categorizeForm.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Link mutation
  const linkMutation = useMutation({
    mutationFn: ({ id, expenseId }: { id: number; expenseId: number }) =>
      bankTransactionsApi.linkToExpense(id, { expense_id: expenseId }),
    onSuccess: () => {
      message.success('Транзакция связана с заявкой')
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
      setMatchingDrawerOpen(false)
      setSelectedTransaction(null)
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Bulk delete mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: (transactionIds: number[]) => bankTransactionsApi.bulkDelete(transactionIds),
    onSuccess: (result) => {
      message.success(`Удалено транзакций: ${result.deleted}`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Quick update mutation for inline editing
  const quickUpdateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: any }) =>
      bankTransactionsApi.updateTransaction(id, updates),
    onSuccess: () => {
      message.success('Транзакция обновлена')
      setEditingKey(null)
      editForm.resetFields()
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления: ${error.response?.data?.detail || error.message}`)
    },
  })

  // OData test connection mutation
  const odataTestMutation = useMutation({
    mutationFn: (params: { odata_url: string; username: string; password: string }) =>
      bankTransactionsApi.testODataConnection(params),
    onSuccess: (result) => {
      if (result.success) {
        message.success('Соединение с 1С успешно установлено')
      } else {
        message.error(`Ошибка соединения: ${result.message}`)
      }
    },
    onError: (error: any) => {
      message.error(`Ошибка тестирования: ${error.response?.data?.detail || error.message}`)
    },
  })

  // OData sync mutation
  const odataSyncMutation = useMutation({
    mutationFn: (params: {
      odata_url: string
      username: string
      password: string
      entity_name?: string
      department_id: number
      organization_id?: number
      date_from?: string
      date_to?: string
    }) => bankTransactionsApi.syncFromOData(params),
    onSuccess: (result) => {
      if (result.success) {
        message.success(
          `Синхронизация завершена: создано ${result.created}, обновлено ${result.updated}, пропущено ${result.skipped}`
        )
        setOdataSyncModalOpen(false)
        odataSyncForm.resetFields()
        queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
        queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
      } else {
        message.error(`Ошибка синхронизации: ${result.error || 'Неизвестная ошибка'}`)
      }
    },
    onError: (error: any) => {
      message.error(`Ошибка синхронизации: ${error.response?.data?.detail || error.message}`)
    },
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  const getStatusColor = (status: BankTransactionStatus) => {
    const colors: Record<BankTransactionStatus, string> = {
      NEW: 'default',
      CATEGORIZED: 'processing',
      MATCHED: 'success',
      APPROVED: 'success',
      NEEDS_REVIEW: 'warning',
      IGNORED: 'default',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: BankTransactionStatus) => {
    const texts: Record<BankTransactionStatus, string> = {
      NEW: 'Новая',
      CATEGORIZED: 'Категоризирована',
      MATCHED: 'Связана',
      APPROVED: 'Одобрена',
      NEEDS_REVIEW: 'Требует проверки',
      IGNORED: 'Игнорируется',
    }
    return texts[status] || status
  }

  const columns: ColumnsType<BankTransaction> = [
    {
      title: 'Дата',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 110,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
      sorter: (a, b) => dayjs(a.transaction_date).unix() - dayjs(b.transaction_date).unix(),
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 130,
      align: 'right',
      render: (amount: number, record) => (
        <span style={{ color: record.transaction_type === 'CREDIT' ? '#52c41a' : '#f5222d' }}>
          {record.transaction_type === 'CREDIT' ? '+' : '-'}
          {formatCurrency(amount)}
        </span>
      ),
      sorter: (a, b) => a.amount - b.amount,
    },
    {
      title: 'Контрагент',
      dataIndex: 'counterparty_name',
      key: 'counterparty_name',
      width: 280,
      ellipsis: true,
      render: (name: string, record) => (
        <Tooltip title={record.payment_purpose}>
          <div>
            <div>{name || 'Не указан'}</div>
            {record.counterparty_inn && (
              <div style={{ fontSize: 12, color: '#8c8c8c' }}>ИНН: {record.counterparty_inn}</div>
            )}
          </div>
        </Tooltip>
      ),
    },
    {
      title: 'Назначение',
      dataIndex: 'payment_purpose',
      key: 'payment_purpose',
      ellipsis: true,
      width: 250,
    },
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 250,
      render: (name: string, record) => {
        const editable = isEditing(record)
        if (editable) {
          return (
            <Form.Item
              name="category_id"
              style={{ margin: 0 }}
              rules={[{ required: false }]}
            >
              <Select
                style={{ width: '100%' }}
                placeholder="Выберите категорию"
                allowClear
                loading={!categories}
                options={(categories || []).map((cat: BudgetCategory) => ({
                  value: cat.id,
                  label: cat.name,
                }))}
                showSearch
                filterOption={(input, option) =>
                  String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
              />
            </Form.Item>
          )
        }

        if (name) {
          return (
            <Tag color="blue">
              {name}
              {record.category_confidence && (
                <span style={{ marginLeft: 4, fontSize: 11 }}>
                  ({Math.round(record.category_confidence * 100)}%)
                </span>
              )}
            </Tag>
          )
        }
        if (record.suggested_category_name) {
          return (
            <Tag color="orange" icon={<ExclamationCircleOutlined />}>
              {record.suggested_category_name}
            </Tag>
          )
        }
        return <span style={{ color: '#bfbfbf' }}>—</span>
      },
    },
    {
      title: 'Заявка',
      dataIndex: 'expense_number',
      key: 'expense_number',
      width: 120,
      render: (number: string, record) => {
        if (number) {
          return (
            <Tag color="green" icon={<LinkOutlined />}>
              {number}
            </Tag>
          )
        }
        if (record.suggested_expense_number) {
          return (
            <Tag color="orange" icon={<ExclamationCircleOutlined />}>
              {record.suggested_expense_number}
            </Tag>
          )
        }
        return <span style={{ color: '#bfbfbf' }}>—</span>
      },
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 180,
      render: (status: BankTransactionStatus, record) => {
        const editable = isEditing(record)
        if (editable) {
          return (
            <Form.Item
              name="status"
              style={{ margin: 0 }}
              rules={[{ required: false }]}
            >
              <Select
                style={{ width: '100%' }}
                placeholder="Выберите статус"
                options={[
                  { value: 'NEW', label: 'Новая' },
                  { value: 'CATEGORIZED', label: 'Категоризирована' },
                  { value: 'MATCHED', label: 'Связана' },
                  { value: 'APPROVED', label: 'Одобрена' },
                  { value: 'NEEDS_REVIEW', label: 'Требует проверки' },
                  { value: 'IGNORED', label: 'Игнорируется' },
                ]}
              />
            </Form.Item>
          )
        }
        return <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      },
      filters: [
        { text: 'Новая', value: 'NEW' },
        { text: 'Категоризирована', value: 'CATEGORIZED' },
        { text: 'Связана', value: 'MATCHED' },
        { text: 'Одобрена', value: 'APPROVED' },
        { text: 'Требует проверки', value: 'NEEDS_REVIEW' },
      ],
    },
    {
      title: 'Действия',
      key: 'actions',
      fixed: 'right',
      width: 240,
      render: (_, record) => {
        const editable = isEditing(record)
        return editable ? (
          <Space size="small">
            <Button
              size="small"
              type="primary"
              onClick={() => handleSave(record.id)}
              loading={quickUpdateMutation.isPending}
            >
              Сохранить
            </Button>
            <Button
              size="small"
              onClick={handleCancel}
            >
              Отмена
            </Button>
          </Space>
        ) : (
          <Space size="small">
            <Tooltip title={editingKey !== null ? 'Завершите редактирование другой строки' : 'Редактировать категорию и статус'}>
              <Button
                size="small"
                onClick={() => handleEdit(record)}
                disabled={editingKey !== null}
              >
                Редактировать
              </Button>
            </Tooltip>
            <Tooltip title="Связать с заявкой на расход">
              <Button
                size="small"
                icon={<LinkOutlined />}
                onClick={() => {
                  setSelectedTransaction(record)
                  setMatchingDrawerOpen(true)
                }}
                disabled={editingKey !== null}
              >
                Связать
              </Button>
            </Tooltip>
          </Space>
        )
      },
    },
  ]

  const handleImport = () => {
    if (!uploadFile) {
      message.warning('Выберите файл для импорта')
      return
    }

    // Для MANAGER и ADMIN требуется выбрать отдел
    if (user && ['MANAGER', 'ADMIN'].includes(user.role)) {
      if (!selectedDepartment) {
        message.error('Выберите отдел для импорта данных')
        return
      }
    }

    // Start with preview
    previewMutation.mutate(uploadFile)
  }

  const handleConfirmMapping = (mapping: Record<string, string>) => {
    if (!uploadFile) return
    importMutation.mutate({ file: uploadFile, mapping })
  }

  const handleCategorize = (values: any) => {
    if (!selectedTransaction) return
    categorizeMutation.mutate({
      id: selectedTransaction.id,
      categoryId: values.category_id,
      notes: values.notes,
    })
  }

  const handleLinkToExpense = (expenseId: number) => {
    if (!selectedTransaction) return
    linkMutation.mutate({
      id: selectedTransaction.id,
      expenseId,
    })
  }

  const handleBulkDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите транзакции для удаления')
      return
    }

    modal.confirm({
      title: 'Подтверждение удаления',
      content: `Вы уверены, что хотите удалить ${selectedRowKeys.length} транзакций? Это действие нельзя отменить.`,
      okText: 'Удалить',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => {
        bulkDeleteMutation.mutate(selectedRowKeys)
      },
    })
  }

  const handleDeleteAll = () => {
    const allIds = data?.items.map(item => item.id) || []
    if (allIds.length === 0) {
      message.warning('Нет транзакций для удаления')
      return
    }

    modal.confirm({
      title: 'Удалить все транзакции?',
      content: `Вы уверены, что хотите удалить ВСЕ ${allIds.length} транзакций на текущей странице? Это действие нельзя отменить.`,
      okText: 'Удалить всё',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => {
        bulkDeleteMutation.mutate(allIds)
      },
    })
  }

  const isEditing = (record: BankTransaction) => record.id === editingKey

  const handleEdit = (record: BankTransaction) => {
    editForm.setFieldsValue({
      category_id: record.category_id,
      status: record.status,
      notes: record.notes,
    })
    setEditingKey(record.id)
  }

  const handleCancel = () => {
    setEditingKey(null)
    editForm.resetFields()
  }

  const handleSave = async (id: number) => {
    try {
      const values = await editForm.validateFields()
      quickUpdateMutation.mutate({ id, updates: values })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleTestODataConnection = async () => {
    try {
      const values = await odataSyncForm.validateFields(['odata_url', 'username', 'password'])
      odataTestMutation.mutate({
        odata_url: values.odata_url,
        username: values.username,
        password: values.password,
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleODataSync = async () => {
    if (!selectedDepartment) {
      message.error('Выберите отдел для синхронизации')
      return
    }

    try {
      const values = await odataSyncForm.validateFields()
      odataSyncMutation.mutate({
        odata_url: values.odata_url,
        username: values.username,
        password: values.password,
        entity_name: values.entity_name || 'Document_BankStatement',
        department_id: selectedDepartment.id,
        organization_id: values.organization_id,
        date_from: values.date_range?.[0]?.format('YYYY-MM-DD'),
        date_to: values.date_range?.[1]?.format('YYYY-MM-DD'),
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  return (
    <div>
      {/* Stats */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Всего транзакций"
                value={stats.total_transactions}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Общая сумма"
                value={stats.total_amount}
                formatter={(value) => formatCurrency(Number(value))}
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Требует обработки"
                value={stats.new_count + stats.needs_review_count}
                valueStyle={{ color: '#faad14' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Обработано"
                value={stats.matched_count + stats.approved_count}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setImportModalOpen(true)}
          >
            Импорт из Excel
          </Button>
          {user && ['MANAGER', 'ADMIN'].includes(user.role) && (
            <Button
              type="primary"
              onClick={() => setOdataSyncModalOpen(true)}
              style={{ background: '#52c41a', borderColor: '#52c41a' }}
            >
              Синхронизация с 1С
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            Обновить
          </Button>
          {user && ['MANAGER', 'ADMIN'].includes(user.role) && data?.items && data.items.length > 0 && (
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={handleDeleteAll}
              loading={bulkDeleteMutation.isPending}
            >
              Удалить все ({data.items.length})
            </Button>
          )}
          <Select
            style={{ width: 180 }}
            placeholder="Статус"
            allowClear
            value={status}
            onChange={setStatus}
            options={[
              { value: 'NEW', label: 'Новая' },
              { value: 'CATEGORIZED', label: 'Категоризирована' },
              { value: 'MATCHED', label: 'Связана' },
              { value: 'APPROVED', label: 'Одобрена' },
              { value: 'NEEDS_REVIEW', label: 'Требует проверки' },
            ]}
          />
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            format="DD.MM.YYYY"
          />
          <Search
            placeholder="Поиск по контрагенту, ИНН, назначению..."
            style={{ width: 350 }}
            onSearch={setSearch}
            allowClear
          />
          <Button
            type={onlyUnprocessed ? 'primary' : 'default'}
            icon={<FilterOutlined />}
            onClick={() => setOnlyUnprocessed(!onlyUnprocessed)}
          >
            Только необработанные
          </Button>
        </Space>
      </Card>

      {/* Table */}
      <Card>
        {/* Bulk actions */}
        {selectedRowKeys.length > 0 && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Space>
              <span>Выбрано: {selectedRowKeys.length}</span>
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBulkDelete}
                loading={bulkDeleteMutation.isPending}
                disabled={!user || !['MANAGER', 'ADMIN'].includes(user.role)}
              >
                Удалить выбранные
              </Button>
              <Button size="small" onClick={() => setSelectedRowKeys([])}>
                Отменить выбор
              </Button>
            </Space>
          </div>
        )}

        <Form form={editForm} component={false}>
          <Table
            columns={columns}
            dataSource={data?.items || []}
            rowKey="id"
            scroll={{ x: 1900 }}
            rowSelection={{
              selectedRowKeys,
              onChange: (keys) => setSelectedRowKeys(keys as number[]),
              getCheckboxProps: () => ({
                disabled: !user || !['MANAGER', 'ADMIN'].includes(user.role),
              }),
            }}
            pagination={{
              current: page,
              pageSize,
              total: data?.total || 0,
              showSizeChanger: true,
              showTotal: (total) => `Всего ${total} транзакций`,
              onChange: (newPage, newPageSize) => {
                setPage(newPage)
                setPageSize(newPageSize)
              },
            }}
          />
        </Form>
      </Card>

      {/* Import Modal */}
      <Modal
        title="Импорт банковских операций"
        open={importModalOpen}
        onOk={handleImport}
        onCancel={() => {
          setImportModalOpen(false)
          setUploadFile(null)
        }}
        confirmLoading={previewMutation.isPending}
        okText="Далее"
      >
        {/* Department info for MANAGER/ADMIN */}
        {user && ['MANAGER', 'ADMIN'].includes(user.role) && (
          <div style={{
            marginBottom: 16,
            padding: 12,
            background: selectedDepartment ? '#f6ffed' : '#fff7e6',
            border: `1px solid ${selectedDepartment ? '#b7eb8f' : '#ffd591'}`,
            borderRadius: 4,
          }}>
            {selectedDepartment ? (
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <strong>Отдел:</strong> {selectedDepartment.name}
              </div>
            ) : (
              <div>
                <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
                <strong>Внимание:</strong> Выберите отдел в фильтрах для импорта данных
              </div>
            )}
          </div>
        )}

        <p>
          Загрузите файл Excel с банковской выпиской. Система автоматически определит колонки.
        </p>
        <Upload
          beforeUpload={(file) => {
            setUploadFile(file)
            return false
          }}
          maxCount={1}
          accept=".xlsx,.xls"
        >
          <Button icon={<UploadOutlined />}>Выбрать файл</Button>
        </Upload>
        {uploadFile && <div style={{ marginTop: 8 }}>Выбран файл: {uploadFile.name}</div>}
      </Modal>

      {/* Categorize Drawer */}
      <Drawer
        title="Установить категорию"
        open={categorizeDrawerOpen}
        onClose={() => {
          setCategorizeDrawerOpen(false)
          setSelectedTransaction(null)
          categorizeForm.resetFields()
        }}
        width={500}
      >
        {selectedTransaction && (
          <div>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <div><strong>Контрагент:</strong> {selectedTransaction.counterparty_name}</div>
              <div><strong>Сумма:</strong> {formatCurrency(selectedTransaction.amount)}</div>
              <div><strong>Дата:</strong> {dayjs(selectedTransaction.transaction_date).format('DD.MM.YYYY')}</div>
              {selectedTransaction.payment_purpose && (
                <div><strong>Назначение:</strong> {selectedTransaction.payment_purpose}</div>
              )}
            </div>

            {/* AI Suggestions */}
            {suggestionsLoading ? (
              <div style={{ textAlign: 'center', padding: 16 }}>
                <span>Поиск подходящих категорий...</span>
              </div>
            ) : categorySuggestions && categorySuggestions.length > 0 ? (
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>
                  🤖 AI рекомендует:
                </div>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {categorySuggestions.map((suggestion) => (
                    <Card
                      key={suggestion.category_id}
                      size="small"
                      hoverable
                      style={{
                        borderColor: suggestion.confidence >= 0.9 ? '#52c41a' : suggestion.confidence >= 0.7 ? '#1890ff' : '#faad14',
                        cursor: 'pointer',
                      }}
                      onClick={() => {
                        categorizeForm.setFieldsValue({ category_id: suggestion.category_id })
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 500 }}>{suggestion.category_name}</div>
                          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                            {suggestion.reasoning.join(', ')}
                          </div>
                        </div>
                        <Tag color={suggestion.confidence >= 0.9 ? 'green' : suggestion.confidence >= 0.7 ? 'blue' : 'orange'}>
                          {Math.round(suggestion.confidence * 100)}%
                        </Tag>
                      </div>
                    </Card>
                  ))}
                </Space>
              </div>
            ) : null}

            <Form form={categorizeForm} layout="vertical" onFinish={handleCategorize}>
              <Form.Item
                name="category_id"
                label="Категория"
                rules={[{ required: true, message: 'Выберите категорию' }]}
              >
                <Select
                  showSearch
                  placeholder="Выберите категорию"
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={categories?.map((cat: BudgetCategory) => ({
                    value: cat.id,
                    label: cat.name,
                  }))}
                />
              </Form.Item>

              <Form.Item name="notes" label="Примечания">
                <Input.TextArea rows={3} placeholder="Дополнительные комментарии..." />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={categorizeMutation.isPending}
                  block
                >
                  Сохранить
                </Button>
              </Form.Item>
            </Form>
          </div>
        )}
      </Drawer>

      {/* Matching Drawer */}
      <Drawer
        title="Связать с заявкой"
        open={matchingDrawerOpen}
        onClose={() => {
          setMatchingDrawerOpen(false)
          setSelectedTransaction(null)
        }}
        width={600}
      >
        {selectedTransaction && (
          <div>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <div><strong>Контрагент:</strong> {selectedTransaction.counterparty_name}</div>
              <div><strong>Сумма:</strong> {formatCurrency(selectedTransaction.amount)}</div>
              <div><strong>Дата:</strong> {dayjs(selectedTransaction.transaction_date).format('DD.MM.YYYY')}</div>
            </div>

            {matchingLoading ? (
              <LoadingState />
            ) : matchingSuggestions && matchingSuggestions.length > 0 ? (
              <div>
                <h4>Найденные заявки:</h4>
                {matchingSuggestions.map((suggestion) => (
                  <Card
                    key={suggestion.expense_id}
                    size="small"
                    style={{ marginBottom: 12 }}
                    actions={[
                      <Button
                        type="link"
                        onClick={() => handleLinkToExpense(suggestion.expense_id)}
                        loading={linkMutation.isPending}
                      >
                        Связать
                      </Button>,
                    ]}
                  >
                    <div>
                      <strong>Заявка #{suggestion.expense_number}</strong>
                      <Tag color="blue" style={{ marginLeft: 8 }}>
                        {Math.round(suggestion.matching_score)}%
                      </Tag>
                    </div>
                    <div>Сумма: {formatCurrency(suggestion.expense_amount)}</div>
                    <div>Дата: {dayjs(suggestion.expense_date).format('DD.MM.YYYY')}</div>
                    {suggestion.expense_contractor_name && (
                      <div>Контрагент: {suggestion.expense_contractor_name}</div>
                    )}
                    <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                      {suggestion.match_reasons.join(', ')}
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 24, color: '#8c8c8c' }}>
                Подходящие заявки не найдены
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* Column Mapping Modal */}
      <ColumnMappingModal
        open={mappingModalOpen}
        onCancel={() => {
          setMappingModalOpen(false)
          setPreviewData(null)
          setUploadFile(null)
        }}
        onConfirm={handleConfirmMapping}
        previewData={previewData}
        loading={importMutation.isPending}
      />

      {/* OData Sync Modal */}
      <Modal
        title="Синхронизация с 1С через OData"
        open={odataSyncModalOpen}
        onOk={handleODataSync}
        onCancel={() => {
          setOdataSyncModalOpen(false)
          odataSyncForm.resetFields()
        }}
        width={700}
        confirmLoading={odataSyncMutation.isPending}
        okText="Синхронизировать"
        cancelText="Отмена"
      >
        <div style={{ marginBottom: 16 }}>
          <p>
            Синхронизация банковских операций из 1С через протокол OData.
            Система автоматически создаст новые транзакции и обновит существующие.
          </p>
          {selectedDepartment && (
            <div style={{
              padding: 12,
              background: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: 4,
              marginBottom: 16,
            }}>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              <strong>Отдел:</strong> {selectedDepartment.name}
            </div>
          )}
        </div>

        <Form form={odataSyncForm} layout="vertical">
          <Form.Item
            name="odata_url"
            label="OData URL 1С"
            rules={[
              { required: true, message: 'Введите URL OData' },
              { type: 'url', message: 'Введите корректный URL' },
            ]}
            tooltip="Пример: http://server:port/base/odata/standard.odata"
          >
            <Input placeholder="http://server:port/base/odata/standard.odata" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="Имя пользователя 1С"
                rules={[{ required: true, message: 'Введите имя пользователя' }]}
              >
                <Input placeholder="admin" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="password"
                label="Пароль"
                rules={[{ required: true, message: 'Введите пароль' }]}
              >
                <Input.Password placeholder="password" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="entity_name"
            label="Имя сущности OData"
            tooltip="Имя документа в 1С (по умолчанию: Document_BankStatement)"
          >
            <Input placeholder="Document_BankStatement" />
          </Form.Item>

          <Form.Item
            name="date_range"
            label="Период синхронизации"
            rules={[{ required: true, message: 'Выберите период' }]}
          >
            <RangePicker
              style={{ width: '100%' }}
              format="DD.MM.YYYY"
              placeholder={['Дата начала', 'Дата окончания']}
            />
          </Form.Item>

          <Form.Item>
            <Button
              onClick={handleTestODataConnection}
              loading={odataTestMutation.isPending}
              block
            >
              Проверить соединение
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default BankTransactionsPage
