import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Space, Tag, Input, Select, DatePicker, message, Tooltip, Badge } from 'antd'
import { PlusOutlined, SearchOutlined, DownloadOutlined, EditOutlined, CloudUploadOutlined, WarningOutlined, CloudDownloadOutlined } from '@ant-design/icons'
import { expensesApi, categoriesApi } from '@/api'
import { ExpenseStatus, type Expense } from '@/types'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import ExpenseFormModal from '@/components/expenses/ExpenseFormModal'
import FTPImportModal from '@/components/expenses/FTPImportModal'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const ExpensesPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ExpenseStatus | undefined>()
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null)
  const [importModalVisible, setImportModalVisible] = useState(false)

  const queryClient = useQueryClient()

  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses', page, pageSize, search, status, categoryId, dateRange],
    queryFn: () =>
      expensesApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        status,
        category_id: categoryId,
        date_from: dateRange?.[0]?.toISOString(),
        date_to: dateRange?.[1]?.toISOString(),
      }),
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })


  const handleExport = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const params = new URLSearchParams()

    if (status) params.append('status', status)
    if (categoryId) params.append('category_id', categoryId.toString())
    if (search) params.append('search', search)
    if (dateRange?.[0]) params.append('date_from', dateRange[0].toISOString())
    if (dateRange?.[1]) params.append('date_to', dateRange[1].toISOString())

    const url = `${apiUrl}/api/v1/expenses/export?${params.toString()}`
    window.open(url, '_blank')
    message.success('Экспорт начат. Файл скоро будет загружен.')
  }

  const handleCreate = () => {
    setModalMode('create')
    setSelectedExpense(null)
    setModalVisible(true)
  }

  const handleEdit = (expense: Expense) => {
    setModalMode('edit')
    setSelectedExpense(expense)
    setModalVisible(true)
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setSelectedExpense(null)
  }

  const columns = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 180,
      render: (number: string, record: Expense) => (
        <Space>
          {record.imported_from_ftp && (
            <Tooltip title="Загружена из FTP">
              <CloudDownloadOutlined style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
          {record.needs_review && (
            <Tooltip title="Требует проверки категории">
              <Badge status="warning" />
            </Tooltip>
          )}
          <span>{number}</span>
        </Space>
      ),
    },
    {
      title: 'Дата заявки',
      dataIndex: 'request_date',
      key: 'request_date',
      width: 120,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Категория',
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 150,
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right' as const,
      render: (amount: number) =>
        new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB',
          minimumFractionDigits: 0,
        }).format(amount),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: ExpenseStatus) => (
        <Tag color={getExpenseStatusColor(status)}>
          {getExpenseStatusLabel(status)}
        </Tag>
      ),
    },
    {
      title: 'Контрагент',
      dataIndex: ['contractor', 'name'],
      key: 'contractor',
      width: 200,
      ellipsis: true,
      render: (_: string, record: Expense) =>
        record.contractor ? (
          <Link
            to={`/contractors/${record.contractor.id}`}
            style={{ color: '#1890ff' }}
          >
            {record.contractor.name}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      title: 'Организация',
      dataIndex: ['organization', 'name'],
      key: 'organization',
      width: 150,
      render: (_: string, record: Expense) =>
        record.organization ? (
          <Link
            to={`/organizations/${record.organization.id}`}
            style={{ color: '#1890ff' }}
          >
            {record.organization.name}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      title: 'Заявитель',
      dataIndex: 'requester',
      key: 'requester',
      width: 150,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Expense) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Изменить
          </Button>
          {record.needs_review && (
            <Tooltip title="Отметить категорию как проверенную">
              <Button
                type="link"
                size="small"
                onClick={async () => {
                  try {
                    await expensesApi.markReviewed(record.id)
                    message.success('Заявка отмечена как проверенная')
                    queryClient.invalidateQueries({ queryKey: ['expenses'] })
                  } catch (error) {
                    message.error('Ошибка при обновлении')
                  }
                }}
                style={{ color: '#52c41a' }}
              >
                ✓ Проверено
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Input
          placeholder="Поиск по номеру, комментарию, заявителю"
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
        <Select
          placeholder="Статус"
          style={{ width: 150 }}
          value={status}
          onChange={setStatus}
          allowClear
          options={[
            { value: ExpenseStatus.DRAFT, label: getExpenseStatusLabel(ExpenseStatus.DRAFT) },
            { value: ExpenseStatus.PENDING, label: getExpenseStatusLabel(ExpenseStatus.PENDING) },
            { value: ExpenseStatus.PAID, label: getExpenseStatusLabel(ExpenseStatus.PAID) },
            { value: ExpenseStatus.REJECTED, label: getExpenseStatusLabel(ExpenseStatus.REJECTED) },
            { value: ExpenseStatus.CLOSED, label: getExpenseStatusLabel(ExpenseStatus.CLOSED) },
          ]}
        />
        <Select
          placeholder="Категория"
          style={{ width: 200 }}
          value={categoryId}
          onChange={setCategoryId}
          allowClear
          options={categories?.map((cat) => ({ value: cat.id, label: cat.name }))}
        />
        <RangePicker
          format="DD.MM.YYYY"
          value={dateRange}
          onChange={setDateRange as any}
        />
        <Button icon={<CloudUploadOutlined />} onClick={() => setImportModalVisible(true)}>
          Импорт из FTP
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          Экспорт в Excel
        </Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Создать заявку
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={expenses?.items}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: expenses?.total,
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total}`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage)
            setPageSize(newPageSize)
          },
        }}
      />

      <ExpenseFormModal
        visible={modalVisible}
        onCancel={handleModalCancel}
        expense={selectedExpense}
        mode={modalMode}
      />

      <FTPImportModal
        visible={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
      />
    </div>
  )
}

export default ExpensesPage
