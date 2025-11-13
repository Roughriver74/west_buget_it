import { useState, useMemo } from 'react'
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
  message,
  Statistic,
  Row,
  Col,
  Drawer,
  Form,
  Tooltip,
  Popconfirm,
} from 'antd'
import {
  UploadOutlined,
  ReloadOutlined,
  SearchOutlined,
  FilterOutlined,
  LinkOutlined,
  TagsOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DollarOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { bankTransactionsApi, categoriesApi, expensesApi } from '@/api'
import type {
  BankTransaction,
  BankTransactionStatus,
  BankTransactionType,
  MatchingSuggestion,
} from '@/types/bankTransaction'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { RangePicker } = DatePicker
const { Search } = Input

const BankTransactionsPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()

  // Filters
  const [status, setStatus] = useState<BankTransactionStatus | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [search, setSearch] = useState('')
  const [onlyUnprocessed, setOnlyUnprocessed] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  // Modals
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [categorizeDrawerOpen, setCategorizeDrawerOpen] = useState(false)
  const [matchingDrawerOpen, setMatchingDrawerOpen] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null)

  // Forms
  const [categorizeForm] = Form.useForm()
  const [uploadFile, setUploadFile] = useState<File | null>(null)

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
    queryFn: () => categoriesApi.getCategories({ department_id: selectedDepartment?.id }),
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

  // Import mutation
  const importMutation = useMutation({
    mutationFn: (file: File) =>
      bankTransactionsApi.importFromExcel(file, selectedDepartment?.id),
    onSuccess: (result) => {
      message.success(
        `Импортировано: ${result.imported}, пропущено: ${result.skipped} транзакций`
      )
      if (result.errors.length > 0) {
        message.warning(`Ошибок при импорте: ${result.errors.length}`)
      }
      setImportModalOpen(false)
      setUploadFile(null)
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
      width: 180,
      render: (name: string, record) => {
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
      width: 140,
      render: (status: BankTransactionStatus) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
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
      width: 160,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<TagsOutlined />}
            onClick={() => {
              setSelectedTransaction(record)
              setCategorizeDrawerOpen(true)
              if (record.category_id) {
                categorizeForm.setFieldsValue({
                  category_id: record.category_id,
                  notes: record.notes,
                })
              }
            }}
          >
            Категория
          </Button>
          <Button
            size="small"
            icon={<LinkOutlined />}
            onClick={() => {
              setSelectedTransaction(record)
              setMatchingDrawerOpen(true)
            }}
          >
            Связать
          </Button>
        </Space>
      ),
    },
  ]

  const handleImport = () => {
    if (!uploadFile) {
      message.warning('Выберите файл для импорта')
      return
    }
    importMutation.mutate(uploadFile)
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
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            Обновить
          </Button>
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
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          scroll={{ x: 1400 }}
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
        confirmLoading={importMutation.isPending}
      >
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
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={categories?.map((cat) => ({
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
    </div>
  )
}

export default BankTransactionsPage
