/**
 * Budget Plan vs Actual Widget
 * Visual comparison of planned vs actual budget execution by month
 */
import React, { useMemo } from 'react'
import { Card, Statistic, Row, Col, Typography, Space, Tag } from 'antd'
import { Column } from '@ant-design/plots'
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
  const chartData = useMemo(() => {
    if (!data?.months) return []

    // Transform to format expected by stacked column chart
    return data.months.flatMap((m: MonthData) => [
      {
        month: m.month_name,
        category: 'План',
        amount: m.planned,
        monthNumber: m.month,
      },
      {
        month: m.month_name,
        category: 'Факт',
        amount: m.actual,
        monthNumber: m.month,
      },
    ])
  }, [data])

  const chartConfig = {
    data: chartData,
    xField: 'month',
    yField: 'amount',
    seriesField: 'category',
    isGroup: true,
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
    color: ['#1890ff', '#52c41a'],
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      formatter: (datum: any) => {
        return {
          name: datum.category,
          value: new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(datum.amount),
        }
      },
    },
    xAxis: {
      label: {
        autoRotate: false,
      },
    },
    yAxis: {
      label: {
        formatter: (v: string) => {
          const num = parseFloat(v)
          if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`
          }
          if (num >= 1000) {
            return `${(num / 1000).toFixed(0)}K`
          }
          return v
        },
      },
    },
    height,
  }

  if (isLoading) {
    return (
      <Card title={`Исполнение бюджета ${year}`}>
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title={`Исполнение бюджета ${year}`}>
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
          onRetry={() => {}}
        />
      </Card>
    )
  }

  if (!data || !stats) {
    return (
      <Card title={`Исполнение бюджета ${year}`}>
        <Text type="secondary">Нет данных для отображения</Text>
      </Card>
    )
  }

  return (
    <Card
      title={`Исполнение бюджета ${year}`}
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

      <Column {...chartConfig} />
    </Card>
  )
}

export default BudgetPlanVsActualWidget
