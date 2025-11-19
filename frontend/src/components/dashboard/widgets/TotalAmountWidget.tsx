import React from 'react'
import { Card, Statistic } from 'antd'
import { DollarOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { getApiBaseUrl } from '@/config/api'

const API_BASE = getApiBaseUrl()

interface TotalAmountWidgetProps {
  title: string
  config: {
    year?: number
    month?: number
    status?: string
  }
}

const TotalAmountWidget: React.FC<TotalAmountWidgetProps> = ({ title, config }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-total', config],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (config.year) params.append('year', config.year.toString())
      if (config.month) params.append('month', config.month.toString())

      const response = await axios.get(`${API_BASE}/analytics/dashboard?${params}`)
      return response.data
    },
  })

  const total = data?.totals?.actual || 0

  return (
    <Card>
      <Statistic
        title={title}
        value={total}
        precision={2}
        prefix={<DollarOutlined />}
        suffix="₽"
        loading={isLoading}
      />
    </Card>
  )
}

export default TotalAmountWidget
