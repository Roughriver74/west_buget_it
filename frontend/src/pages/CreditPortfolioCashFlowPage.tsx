import { useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Spin, Button } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  WalletOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  AreaChart,
  Area,
  Bar,
  BarChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import CreditPortfolioFilters, {
  type CreditPortfolioFilterValues,
} from '@/components/bank/CreditPortfolioFilters'

interface MonthlyCashFlow {
  month: string
  inflow: number
  outflow: number
  net: number
  cumulative: number
}

interface QuarterlyData {
  quarter: string
  inflow: number
  outflow: number
  net: number
}

interface Metrics {
  totalInflow: number
  totalOutflow: number
  netCashFlow: number
  avgMonthlyInflow: number
  avgMonthlyOutflow: number
}

export default function CreditPortfolioCashFlowPage() {
  const { selectedDepartment } = useDepartment()
  const [filters, setFilters] = useState<CreditPortfolioFilterValues>({})

  const { data: cashflowData, isLoading, isError, refetch } = useQuery({
    queryKey: ['credit-portfolio-cashflow', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getCashflowMonthly({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        organization_id: filters.organizationIds?.[0], // API accepts single org ID
      }),
    enabled: !!selectedDepartment,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  const monthlyData = (cashflowData ?? []) as MonthlyCashFlow[]

  // Calculate quarterly cash flow
  const quarterlyData = useMemo(() => {
    const quarterly: Record<string, QuarterlyData> = {}

    monthlyData.forEach((m) => {
      const [year, month] = m.month.split('-')
      const monthNum = parseInt(month)
      const quarter = `Q${Math.floor((monthNum - 1) / 3) + 1} ${year}`

      if (!quarterly[quarter]) {
        quarterly[quarter] = { quarter, inflow: 0, outflow: 0, net: 0 }
      }
      quarterly[quarter].inflow += m.inflow || 0
      quarterly[quarter].outflow += m.outflow || 0
    })

    return Object.values(quarterly)
      .map((q) => ({ ...q, net: q.inflow - q.outflow }))
      .sort((a, b) => a.quarter.localeCompare(b.quarter))
  }, [monthlyData])

  // Calculate cash flow metrics
  const metrics = useMemo<Metrics>(() => {
    const totalInflow = monthlyData.reduce((sum, m) => sum + (m.inflow || 0), 0)
    const totalOutflow = monthlyData.reduce((sum, m) => sum + (m.outflow || 0), 0)
    const netCashFlow = totalInflow - totalOutflow

    const avgMonthlyInflow =
      monthlyData.length > 0 ? totalInflow / monthlyData.length : 0
    const avgMonthlyOutflow =
      monthlyData.length > 0 ? totalOutflow / monthlyData.length : 0

    return {
      totalInflow,
      totalOutflow,
      netCashFlow,
      avgMonthlyInflow,
      avgMonthlyOutflow,
    }
  }, [monthlyData])

  // Loading state
  if (isLoading && !cashflowData) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: 24,
        }}
      >
        <Spin size="large" />
        <p style={{ marginTop: 16, color: '#8c8c8c' }}>Загрузка данных...</p>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: 24,
          gap: 16,
        }}
      >
        <p style={{ color: '#8c8c8c', textAlign: 'center' }}>
          Не удалось загрузить данные cash flow. Попробуйте еще раз.
        </p>
        <Button type="primary" icon={<ReloadOutlined />} onClick={() => refetch()}>
          Обновить
        </Button>
      </div>
    )
  }

  const dateTickFormatter = (value: string) => {
    if (!value) return ''
    const [year, month] = value.split('-')
    const months = [
      'Янв',
      'Фев',
      'Мар',
      'Апр',
      'Май',
      'Июн',
      'Июл',
      'Авг',
      'Сен',
      'Окт',
      'Ноя',
      'Дек',
    ]
    return `${months[parseInt(month) - 1]} '${year.slice(-2)}`
  }

  const formatAmount = (value: number) => {
    return `${value.toLocaleString('ru-RU')} ₽`
  }

  const formatAxisAmount = (value: number) => {
    if (Math.abs(value) >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    }
    if (Math.abs(value) >= 1000) {
      return `${(value / 1000).toFixed(0)}K`
    }
    return value.toString()
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Анализ денежных потоков</h1>
        <p style={{ margin: '8px 0 0 0', color: '#8c8c8c' }}>
          Cash Flow Analysis - движение средств
        </p>
      </div>

      {/* Filters */}
      <CreditPortfolioFilters
        onFilterChange={setFilters}
        initialValues={filters}
      />

      {/* Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="Общий приток"
              value={metrics.totalInflow}
              precision={0}
              suffix="₽"
              prefix={<ArrowUpOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 8 }}>
              Ср. {formatAmount(metrics.avgMonthlyInflow)}/мес
            </div>
            <div style={{ fontSize: 11, color: '#bfbfbf', marginTop: 4, fontStyle: 'italic' }}>
              Сумма всех поступлений (receipts) за период
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="Общий отток"
              value={metrics.totalOutflow}
              precision={0}
              suffix="₽"
              prefix={<ArrowDownOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 8 }}>
              Ср. {formatAmount(metrics.avgMonthlyOutflow)}/мес
            </div>
            <div style={{ fontSize: 11, color: '#bfbfbf', marginTop: 4, fontStyle: 'italic' }}>
              Сумма всех платежей (expenses) за период
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="Чистый поток"
              value={metrics.netCashFlow}
              precision={0}
              suffix="₽"
              prefix={<WalletOutlined style={{ color: metrics.netCashFlow >= 0 ? '#1890ff' : '#fa8c16' }} />}
              valueStyle={{ color: metrics.netCashFlow >= 0 ? '#1890ff' : '#fa8c16' }}
            />
            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 8 }}>
              {metrics.netCashFlow >= 0 ? 'Положительный' : 'Отрицательный'}
            </div>
            <div style={{ fontSize: 11, color: '#bfbfbf', marginTop: 4, fontStyle: 'italic' }}>
              Приток - Отток = {formatAmount(metrics.totalInflow)} - {formatAmount(metrics.totalOutflow)}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        {/* Monthly Cash Flow with Cumulative */}
        <Col xs={24}>
          <Card
            title="Ежемесячные денежные потоки"
            extra={
              <span style={{ fontSize: 13, color: '#8c8c8c', fontWeight: 'normal' }}>
                Приток, отток и накопительный баланс
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="month"
                  tickFormatter={dateTickFormatter}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  yAxisId="left"
                  tickFormatter={formatAxisAmount}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={formatAxisAmount}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                />
                <Tooltip
                  formatter={(value: any) => formatAmount(Number(value))}
                  labelFormatter={dateTickFormatter}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="inflow" name="Приток" fill="#52c41a" />
                <Bar yAxisId="left" dataKey="outflow" name="Отток" fill="#ff4d4f" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cumulative"
                  name="Накопительный"
                  stroke="#1890ff"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Net Cash Flow Area */}
        <Col xs={24}>
          <Card
            title="Чистый денежный поток"
            extra={
              <span style={{ fontSize: 13, color: '#8c8c8c', fontWeight: 'normal' }}>
                Разница между притоком и оттоком
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1890ff" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#1890ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="month"
                  tickFormatter={dateTickFormatter}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  tickFormatter={formatAxisAmount}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                />
                <Tooltip
                  formatter={(value: any) => formatAmount(Number(value))}
                  labelFormatter={dateTickFormatter}
                />
                <Area
                  type="monotone"
                  dataKey="net"
                  stroke="#1890ff"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorNet)"
                  name="Чистый поток"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Quarterly Analysis */}
        <Col xs={24}>
          <Card
            title="Квартальный анализ"
            extra={
              <span style={{ fontSize: 13, color: '#8c8c8c', fontWeight: 'normal' }}>
                Денежные потоки по кварталам
              </span>
            }
          >
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={quarterlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="quarter" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis
                  tickFormatter={formatAxisAmount}
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                />
                <Tooltip formatter={(value: any) => formatAmount(Number(value))} />
                <Legend />
                <Bar dataKey="inflow" name="Приток" fill="#52c41a" />
                <Bar dataKey="outflow" name="Отток" fill="#ff4d4f" />
                <Bar dataKey="net" name="Чистый" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
