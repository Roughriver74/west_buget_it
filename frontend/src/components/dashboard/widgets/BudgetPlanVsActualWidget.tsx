/**
 * Budget Plan vs Actual Widget
 * Visual comparison of planned vs actual budget execution by month
 */
import React, { useMemo } from 'react'
import { Statistic, Typography, Tag } from 'antd'
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
import { Card } from '@/components/ui/Card'

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
  plan: { label: 'План', color: '#3b82f6' },
  actual: { label: 'Факт', color: '#f59e0b' },
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
      <div className="bg-white/95 dark:bg-gray-900/95 border border-gray-100 dark:border-gray-800 rounded-lg p-3 shadow-lg backdrop-blur-sm">
        <div className="font-semibold mb-2">{label}</div>
        {payload.map((entry) => {
          const key = entry.dataKey as CategoryKey
          const config = CATEGORY_CONFIG[key]
          return (
            <div key={entry.dataKey as string} className="flex items-center mb-1 gap-2">
              <span
                className="w-2.5 h-2.5 rounded-sm"
                style={{ backgroundColor: config?.color ?? '#1890ff' }}
              />
              <span className="flex-1 text-sm text-gray-600 dark:text-gray-300">{config?.label ?? entry.name}</span>
              <strong className="text-sm">{currencyFormatter.format(Number(entry.value))}</strong>
            </div>
          )
        })}
      </div>
    )
  }

  if (isLoading) {
    return (
      <Card title="Исполнение бюджета" variant="default">
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title="Исполнение бюджета" variant="default">
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
          onRetry={() => {}}
        />
      </Card>
    )
  }

  if (!data || !stats) {
    return (
      <Card title="Исполнение бюджета" variant="default">
        <Text type="secondary">Нет данных для отображения</Text>
      </Card>
    )
  }

  return (
    <Card
      title="Исполнение бюджета"
      variant="default"
      extra={
        <Tag color={stats.executionPercent > 100 ? 'red' : stats.executionPercent > 90 ? 'orange' : 'green'} className="mr-0 rounded-full px-3">
          {stats.executionPercent.toFixed(1)}% исполнено
        </Tag>
      }
    >
      {showStats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/50">
            <Statistic
              title={<span className="text-blue-600/80 dark:text-blue-400/80 text-sm font-medium">План на год</span>}
              value={stats.totalPlanned}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#3b82f6', fontWeight: 600 }}
            />
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-100 dark:border-green-800/50">
            <Statistic
              title={<span className="text-green-600/80 dark:text-green-400/80 text-sm font-medium">Факт</span>}
              value={stats.totalActual}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#10b981', fontWeight: 600 }}
            />
          </div>
          <div className={`p-4 rounded-lg border ${stats.totalRemaining >= 0 ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-100 dark:border-emerald-800/50' : 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50'}`}>
            <Statistic
              title={<span className={`${stats.totalRemaining >= 0 ? 'text-emerald-600/80 dark:text-emerald-400/80' : 'text-red-600/80 dark:text-red-400/80'} text-sm font-medium`}>Остаток</span>}
              value={stats.totalRemaining}
              precision={0}
              suffix="₽"
              prefix={stats.totalRemaining > 0 ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
              valueStyle={{
                color: stats.totalRemaining > 0 ? '#10b981' : '#ef4444',
                fontWeight: 600
              }}
            />
          </div>
        </div>
      )}

      {stats.currentMonthData && showStats && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="text-sm font-semibold mb-3">Текущий месяц ({stats.currentMonthData.month_name})</div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-gray-500 mb-1">План</div>
              <div className="font-medium">
                {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(
                  stats.currentMonthData.planned
                )}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Факт</div>
              <div className="font-medium">
                {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(
                  stats.currentMonthData.actual
                )}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Исполнение</div>
              <div
                className="font-bold"
                style={{
                  color:
                    stats.currentMonthData.execution_percent > 100
                      ? '#ef4444'
                      : stats.currentMonthData.execution_percent > 90
                        ? '#f59e0b'
                        : '#10b981',
                }}
              >
                {stats.currentMonthData.execution_percent.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 8, right: 24, left: 0, bottom: 8 }} barGap={8}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={{ stroke: '#e5e7eb' }} tick={{ fontSize: 12 }} />
          <YAxis
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(value: number) => formatAxisLabel(value).toString()}
            width={80}
            tick={{ fontSize: 12 }}
          />
          <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
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
