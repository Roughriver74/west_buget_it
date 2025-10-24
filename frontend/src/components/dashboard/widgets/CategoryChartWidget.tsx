import React from 'react'
import { Card } from 'antd'
import { Pie } from '@ant-design/plots'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

interface CategoryChartWidgetProps {
  title: string
  config: {
    year?: number
    month?: number
    limit?: number
  }
}

const CategoryChartWidget: React.FC<CategoryChartWidgetProps> = ({ title, config }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-categories', config],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (config.year) params.append('year', config.year.toString())
      if (config.month) params.append('month', config.month.toString())

      const response = await axios.get(`${API_BASE}/analytics/dashboard?${params}`)
      return response.data
    },
  })

  const chartData = (data?.top_categories || []).slice(0, config.limit || 5).map((item: any) => ({
    type: item.category_name,
    value: parseFloat(item.amount),
  }))

  const chartConfig = {
    data: chartData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [{ type: 'element-active' }],
  }

  return (
    <Card title={title} loading={isLoading}>
      {chartData.length > 0 ? <Pie {...chartConfig} /> : <div>Нет данных</div>}
    </Card>
  )
}

export default CategoryChartWidget
