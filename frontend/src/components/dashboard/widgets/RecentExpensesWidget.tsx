import React from 'react'
import { Card, Table, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import dayjs from 'dayjs'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface RecentExpensesWidgetProps {
  title: string
  config: {
    limit?: number
  }
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

  const columns = [
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
      render: (status: string) => (
        <Tag color={getExpenseStatusColor(status)}>{getExpenseStatusLabel(status)}</Tag>
      ),
    },
  ]

  return (
    <Card title={title} loading={isLoading}>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        pagination={false}
        size="small"
        rowKey="id"
      />
    </Card>
  )
}

export default RecentExpensesWidget
