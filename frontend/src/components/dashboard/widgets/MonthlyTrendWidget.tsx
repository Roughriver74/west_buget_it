import React from 'react'
import { Card } from 'antd'
import { Line } from '@ant-design/plots'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface MonthlyTrendWidgetProps {
  title: string
  config: {
    year?: number
  }
}

const MonthlyTrendWidget: React.FC<MonthlyTrendWidgetProps> = ({ title, config }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-trend', config],
    queryFn: async () => {
      const year = config.year || new Date().getFullYear()
      const response = await axios.get(`${API_BASE}/analytics/execution/${year}`)
      return response.data
    },
  })

  const chartData = (data?.months || []).map((item: any) => ({
    month: item.month_name,
    value: parseFloat(item.actual),
    category: 'Факт',
  })).concat(
    (data?.months || []).map((item: any) => ({
      month: item.month_name,
      value: parseFloat(item.planned),
      category: 'План',
    }))
  )

  const chartConfig = {
    data: chartData,
    xField: 'month',
    yField: 'value',
    seriesField: 'category',
    smooth: true,
  }

  return (
    <Card title={title} loading={isLoading}>
      {chartData.length > 0 ? <Line {...chartConfig} /> : <div>Нет данных</div>}
    </Card>
  )
}

export default MonthlyTrendWidget
