import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table, Button, Space, Tag, Input, Select, DatePicker } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { expensesApi, categoriesApi } from '@/api'
import type { Expense, ExpenseStatus } from '@/types'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const ExpensesPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ExpenseStatus | undefined>()
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

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

  const statusColors: Record<string, string> = {
    'Черновик': 'default',
    'К оплате': 'processing',
    'Оплачена': 'success',
    'Отклонена': 'error',
    'Закрыта': 'default',
  }

  const columns = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 150,
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
      render: (status: string) => <Tag color={statusColors[status]}>{status}</Tag>,
    },
    {
      title: 'Контрагент',
      dataIndex: ['contractor', 'name'],
      key: 'contractor',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Организация',
      dataIndex: ['organization', 'name'],
      key: 'organization',
      width: 150,
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
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Expense) => (
        <Space size="small">
          <Button type="link" size="small">
            Изменить
          </Button>
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
            { value: 'Черновик', label: 'Черновик' },
            { value: 'К оплате', label: 'К оплате' },
            { value: 'Оплачена', label: 'Оплачена' },
            { value: 'Отклонена', label: 'Отклонена' },
            { value: 'Закрыта', label: 'Закрыта' },
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
        <Button type="primary" icon={<PlusOutlined />}>
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
    </div>
  )
}

export default ExpensesPage
