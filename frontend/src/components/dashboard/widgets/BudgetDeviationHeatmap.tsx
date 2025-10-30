/**
 * Budget Deviation Heatmap
 * Heat map showing budget deviations by category and month
 */
import React, { useMemo } from 'react'
import { Card, Typography, Tag, Space, Tooltip } from 'antd'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const { Text } = Typography

interface BudgetDeviationHeatmapProps {
  year: number
  departmentId?: number
  height?: number
}

interface MonthlyData {
  month: number
  month_name: string
  planned: number
  actual: number
  difference: number
  execution_percent: number
}

interface CategoryData {
  category_id: number
  category_name: string
  planned: number
  actual: number
  difference: number
  execution_percent: number
  monthly: MonthlyData[]
}

const MONTHS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

const BudgetDeviationHeatmap: React.FC<BudgetDeviationHeatmapProps> = ({
  year,
  departmentId,
  height = 600,
}) => {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['plan-vs-actual', year, departmentId],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/analytics/plan-vs-actual`, {
        params: { year, department_id: departmentId },
      })
      return response.data
    },
  })

  // Calculate color based on execution percentage
  const getHeatmapColor = (executionPercent: number, hasData: boolean) => {
    if (!hasData) return '#f5f5f5' // No data

    // Color scale from green (under budget) to red (over budget)
    if (executionPercent <= 50) return '#d9f7be'      // Far under budget
    if (executionPercent <= 75) return '#b7eb8f'      // Under budget
    if (executionPercent <= 90) return '#95de64'      // On track
    if (executionPercent <= 100) return '#ffd666'     // Near limit
    if (executionPercent <= 110) return '#ff9c6e'     // Slightly over
    return '#ff4d4f'                                   // Significantly over
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const heatmapData = useMemo(() => {
    if (!data?.by_category) return []

    return data.by_category.map((category: CategoryData) => ({
      category_id: category.category_id,
      category_name: category.category_name,
      monthly: category.monthly,
    }))
  }, [data])

  if (isLoading) {
    return (
      <Card title={`Тепловая карта отклонений ${year}`}>
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title={`Тепловая карта отклонений ${year}`}>
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
        />
      </Card>
    )
  }

  if (!data || !heatmapData.length) {
    return (
      <Card title={`Тепловая карта отклонений ${year}`}>
        <Text type="secondary">
          Нет базовой версии бюджета для {year} года. Установите утвержденную версию как baseline.
        </Text>
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <span>{`Тепловая карта отклонений ${year}`}</span>
          {data.baseline_version_name && (
            <Tag color="blue">Baseline: {data.baseline_version_name}</Tag>
          )}
        </Space>
      }
    >
      {/* Legend */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>Легенда:</Text>
        <Space size={4}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#d9f7be',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>≤50%</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#b7eb8f',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>≤75%</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#95de64',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>≤90%</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#ffd666',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>≤100%</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#ff9c6e',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>≤110%</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 16,
                height: 16,
                backgroundColor: '#ff4d4f',
                border: '1px solid #ddd',
              }}
            />
            <Text style={{ fontSize: 11 }}>&gt;110%</Text>
          </div>
        </Space>
      </div>

      {/* Heatmap Table */}
      <div style={{ overflowX: 'auto', maxHeight: height - 150, overflowY: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: 12,
          }}
        >
          <thead>
            <tr style={{ backgroundColor: '#fafafa' }}>
              <th
                style={{
                  padding: '8px',
                  textAlign: 'left',
                  borderBottom: '2px solid #f0f0f0',
                  position: 'sticky',
                  top: 0,
                  backgroundColor: '#fafafa',
                  zIndex: 1,
                  minWidth: 200,
                }}
              >
                Категория
              </th>
              {MONTHS.map((month, idx) => (
                <th
                  key={idx}
                  style={{
                    padding: '8px',
                    textAlign: 'center',
                    borderBottom: '2px solid #f0f0f0',
                    position: 'sticky',
                    top: 0,
                    backgroundColor: '#fafafa',
                    zIndex: 1,
                    minWidth: 70,
                  }}
                >
                  {month}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {heatmapData.map((category: any) => (
              <tr key={category.category_id}>
                <td
                  style={{
                    padding: '8px',
                    borderBottom: '1px solid #f0f0f0',
                    fontWeight: 500,
                  }}
                >
                  {category.category_name}
                </td>
                {category.monthly.map((monthData: MonthlyData, idx: number) => {
                  const hasData = monthData.planned > 0 || monthData.actual > 0
                  const color = getHeatmapColor(monthData.execution_percent, hasData)

                  return (
                    <Tooltip
                      key={idx}
                      title={
                        hasData ? (
                          <div>
                            <div>План: {formatCurrency(monthData.planned)}</div>
                            <div>Факт: {formatCurrency(monthData.actual)}</div>
                            <div>
                              Отклонение: {formatCurrency(monthData.difference)} (
                              {monthData.execution_percent.toFixed(1)}%)
                            </div>
                          </div>
                        ) : (
                          'Нет данных'
                        )
                      }
                    >
                      <td
                        style={{
                          padding: '8px',
                          textAlign: 'center',
                          borderBottom: '1px solid #f0f0f0',
                          backgroundColor: color,
                          cursor: hasData ? 'pointer' : 'default',
                          transition: 'all 0.2s',
                        }}
                      >
                        {hasData ? `${monthData.execution_percent.toFixed(0)}%` : '-'}
                      </td>
                    </Tooltip>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

export default BudgetDeviationHeatmap
