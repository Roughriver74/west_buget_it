/**
 * Budget Plan vs Actual Widget
 * Visual comparison of planned vs actual budget execution by month
 */
import React, { useMemo } from 'react'
import { Card, Statistic, Row, Col, Typography, Space, Tag } from 'antd'
import {
  ResponsiveContainer,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Legend,
  Bar,
  TooltipProps,
} from 'recharts'
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

const { Text } = Typography

interface BudgetPlanVsActualWidgetProps {
  year?: number
  departmentId?: number
  height?: number
  showStats?: boolean
}

interface MonthData {
  month: number
  month_name: string
  planned: number
  actual: number
  remaining: number
  execution_percent: number
}

type CategoryKey = 'plan' | 'actual'

interface ChartDatum {
  month: string
  monthNumber: number
  plan: number
  actual: number
}

const CATEGORY_CONFIG: Record<CategoryKey, { label: string; color: string }> = {
  plan: { label: 'План', color: '#1890ff' },
  actual: { label: 'Факт', color: '#fa8c16' },
}

const BudgetPlanVsActualWidget: React.FC<BudgetPlanVsActualWidgetProps> = ({
  year = new Date().getFullYear(),
  departmentId,
  height = 400,
  showStats = true,
}) => {
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['budget-execution', year, departmentId],
    queryFn: () => analyticsApi.getBudgetExecution({ year, department_id: departmentId }),
  })

  // Calculate totals and statistics
  const stats = useMemo(() => {
    if (!data?.months) return null

    const totalPlanned = data.months.reduce((sum: number, m: MonthData) => sum + m.planned, 0)
    const totalActual = data.months.reduce((sum: number, m: MonthData) => sum + m.actual, 0)
    const totalRemaining = totalPlanned - totalActual
    const executionPercent = totalPlanned > 0 ? (totalActual / totalPlanned) * 100 : 0

    // Current month data
    const currentMonth = new Date().getMonth() + 1
    const currentMonthData = data.months.find((m: MonthData) => m.month === currentMonth)

    return {
      totalPlanned,
      totalActual,
      totalRemaining,
      executionPercent,
      currentMonthData,
    }
  }, [data])

  // Prepare chart data
  const chartData = useMemo<ChartDatum[]>(() => {
    if (!data?.months) return []

    // Transform to format expected by stacked column chart
    const months = [...data.months].sort((a, b) => a.month - b.month)

    return months.map((m: MonthData) => ({
      month: m.month_name,
      monthNumber: m.month,
      plan: m.planned ?? 0,
      actual: m.actual ?? 0,
    }))
  }, [data])

  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }),
    []
  )

  const formatAxisLabel = (value: number) => {
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}K`
    }
    return value
  }

  const renderLegendText = (value: string) => {
    const key = value as CategoryKey
    return CATEGORY_CONFIG[key]?.label ?? value
  }

  const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({ active, label, payload }) => {
    if (!active || !payload || payload.length === 0) {
      return null
    }

    return (
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          padding: '12px 16px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 8 }}>{label}</div>
        {payload.map((entry) => {
          const key = entry.dataKey as CategoryKey
          const config = CATEGORY_CONFIG[key]
          return (
            <div key={entry.dataKey as string} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
              <span
                style={{
                  backgroundColor: config?.color ?? '#1890ff',
                  width: 10,
                  height: 10,
                  display: 'inline-block',
                  borderRadius: 2,
                  marginRight: 8,
                }}
              />
              <span style={{ flex: 1 }}>{config?.label ?? entry.name}</span>
              <strong>{currencyFormatter.format(Number(entry.value))}</strong>
            </div>
          )
        })}
      </div>
    )
  }

  if (isLoading) {
    return (
      <Card title="Исполнение бюджета">
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title="Исполнение бюджета">
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
          onRetry={() => {}}
        />
      </Card>
    )
  }

  if (!data || !stats) {
    return (
      <Card title="Исполнение бюджета">
        <Text type="secondary">Нет данных для отображения</Text>
      </Card>
    )
  }

  return (
    <Card
      title="Исполнение бюджета"
      extra={
        <Tag color={stats.executionPercent > 100 ? 'red' : stats.executionPercent > 90 ? 'orange' : 'green'}>
          {stats.executionPercent.toFixed(1)}% исполнено
        </Tag>
      }
    >
      {showStats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Statistic
              title="План на год"
              value={stats.totalPlanned}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="Факт"
              value={stats.totalActual}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="Остаток"
              value={stats.totalRemaining}
              precision={0}
              suffix="₽"
              prefix={stats.totalRemaining > 0 ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
              valueStyle={{
                color: stats.totalRemaining > 0 ? '#52c41a' : '#cf1322',
              }}
            />
          </Col>
        </Row>
      )}

      {stats.currentMonthData && showStats && (
        <Space direction="vertical" size="small" style={{ marginBottom: 16, width: '100%' }}>
          <Text strong>Текущий месяц ({stats.currentMonthData.month_name}):</Text>
          <Row gutter={8}>
            <Col span={8}>
              <Text type="secondary">План: </Text>
              <Text strong>
                {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(
                  stats.currentMonthData.planned
                )}
              </Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">Факт: </Text>
              <Text strong>
                {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(
                  stats.currentMonthData.actual
                )}
              </Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">Исполнение: </Text>
              <Text
                strong
                style={{
                  color:
                    stats.currentMonthData.execution_percent > 100
                      ? '#cf1322'
                      : stats.currentMonthData.execution_percent > 90
                        ? '#faad14'
                        : '#52c41a',
                }}
              >
                {stats.currentMonthData.execution_percent.toFixed(1)}%
              </Text>
            </Col>
          </Row>
        </Space>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 8, right: 24, left: 0, bottom: 8 }} barGap={12}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={{ stroke: '#d9d9d9' }} />
          <YAxis
            tickLine={false}
            axisLine={{ stroke: '#d9d9d9' }}
            tickFormatter={(value: number) => formatAxisLabel(value).toString()}
            width={80}
          />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend formatter={renderLegendText} />
          <Bar
            dataKey="plan"
            name="plan"
            fill={CATEGORY_CONFIG.plan.color}
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
          <Bar
            dataKey="actual"
            name="actual"
            fill={CATEGORY_CONFIG.actual.color}
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

export default BudgetPlanVsActualWidget
