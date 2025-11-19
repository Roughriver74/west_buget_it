import React from 'react'
import { Card, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import dayjs from 'dayjs'
import { ExpenseStatus } from '@/types'
import { getApiBaseUrl } from '@/config/api'

const API_BASE = getApiBaseUrl()

interface RecentExpensesWidgetProps {
  title: string
  config: {
    limit?: number
  }
}

interface RecentExpenseRow {
  id: number
  number: string
  amount: number
  status: ExpenseStatus
  request_date: string
}

const RecentExpensesWidget: React.FC<RecentExpensesWidgetProps> = ({ title, config }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-recent', config],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/expenses`, {
        params: {
          limit: config.limit || 5,
          skip: 0,
        },
      })
      return response.data
    },
  })

  const columns: ColumnsType<RecentExpenseRow> = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 150,
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number) => `${amount.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Дата',
      dataIndex: 'request_date',
      key: 'request_date',
      width: 100,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ExpenseStatus) => (
        <Tag color={getExpenseStatusColor(status)}>{getExpenseStatusLabel(status)}</Tag>
      ),
    },
  ]

  return (
    <Card title={title} loading={isLoading}>
      <Table
        dataSource={(data?.items as RecentExpenseRow[]) || []}
        columns={columns}
        pagination={false}
        size="small"
        rowKey="id"
      />
    </Card>
  )
}

export default RecentExpensesWidget
