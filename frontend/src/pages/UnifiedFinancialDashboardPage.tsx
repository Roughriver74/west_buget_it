/**
 * Unified Financial Dashboard (Совмещенный финансовый дашборд)
 *
 * Comprehensive dashboard combining Revenue + Expenses + Profit
 * Interactive visualization of financial performance
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Typography, Card, Row, Col, Select, Statistic, Progress, Space, Tag } from 'antd'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts'
import { analyticsApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs from 'dayjs'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

const UnifiedFinancialDashboardPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const { selectedDepartment } = useDepartment()

  // Fetch БДР data (contains all needed info: revenue, expenses, profit)
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['unified-dashboard', year, selectedDepartment?.id],
    queryFn: () =>
      analyticsApi.getBudgetIncomeStatement({
        year,
        department_id: selectedDepartment?.id,
      }),
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  // Calculate additional metrics
  const metrics = useMemo(() => {
    if (!data) return null

    // Top revenue categories
    const topRevenue = data.revenue_by_category
      ?.sort((a: any, b: any) => b.actual - a.actual)
      .slice(0, 5) || []

    // Top expense categories
    const topExpenses = data.expenses_by_category
      ?.sort((a: any, b: any) => b.actual - a.actual)
      .slice(0, 5) || []

    // Monthly profit trend
    const profitTrend = data.by_month.map((m: any) => ({
      month: m.month_name,
      profit: m.profit_actual,
      margin: m.profit_margin_actual,
    }))

    // Cash flow (cumulative)
    let cumulative = 0
    const cashFlow = data.by_month.map((m: any) => {
      cumulative += m.profit_actual
      return {
        month: m.month_name,
        cashFlow: cumulative,
      }
    })

    return {
      topRevenue,
      topExpenses,
      profitTrend,
      cashFlow,
    }
  }, [data])

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return (
      <ErrorState
        description={String(error)}
        onRetry={refetch}
        retryLabel="Повторить попытку"
      />
    )
  }

  if (!data || !metrics) {
    return (
      <ErrorState
        status="info"
        title="Нет данных для отображения"
        description="Попробуйте изменить параметры фильтрации или период."
        fullHeight
      />
    )
  }

  // Prepare chart data
  const monthlyData = data.by_month.map((item: any) => ({
    month: item.month_name,
    'Доходы': item.revenue_actual,
    'Расходы': item.expenses_actual,
    'Прибыль': item.profit_actual,
  }))

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Финансовый дашборд</Title>
        <Paragraph>
          Комплексный обзор финансовых показателей: доходы, расходы, прибыль и рентабельность.
        </Paragraph>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Год</div>
            <Select value={year} onChange={setYear} style={{ width: '100%' }} size="large">
              {Array.from({ length: 5 }, (_, i) => currentYear - 2 + i).map((y) => (
                <Option key={y} value={y}>{y} год</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={16} md={18}>
            {data.department_name && (
              <Space>
                <Text type="secondary">Отдел:</Text>
                <Text strong>{data.department_name}</Text>
              </Space>
            )}
          </Col>
        </Row>
      </Card>

      {/* Key Metrics - Large Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card style={{ height: '100%' }}>
            <Statistic
              title="Доходы (факт)"
              value={data.revenue_actual}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a', fontSize: 32 }}
            />
            <div style={{ marginTop: 16 }}>
              <Progress
                percent={data.revenue_execution_percent}
                strokeColor="#52c41a"
                format={(percent) => `${percent?.toFixed(1)}%`}
              />
              <Space style={{ marginTop: 8 }}>
                <Text type="secondary">План:</Text>
                <Text strong>{formatCurrency(data.revenue_planned)}</Text>
              </Space>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card style={{ height: '100%' }}>
            <Statistic
              title="Расходы (факт)"
              value={data.expenses_actual}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f', fontSize: 32 }}
            />
            <div style={{ marginTop: 16 }}>
              <Progress
                percent={data.expenses_execution_percent}
                strokeColor="#ff4d4f"
                format={(percent) => `${percent?.toFixed(1)}%`}
              />
              <Space style={{ marginTop: 8 }}>
                <Text type="secondary">План:</Text>
                <Text strong>{formatCurrency(data.expenses_planned)}</Text>
              </Space>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card style={{ height: '100%' }}>
            <Statistic
              title="Прибыль (факт)"
              value={data.profit_actual}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={
                data.profit_actual >= 0 ? (
                  <RiseOutlined style={{ color: '#1890ff' }} />
                ) : (
                  <WarningOutlined style={{ color: '#ff4d4f' }} />
                )
              }
              valueStyle={{
                color: data.profit_actual >= 0 ? '#1890ff' : '#ff4d4f',
                fontSize: 32,
              }}
            />
            <div style={{ marginTop: 16 }}>
              <Row gutter={8}>
                <Col span={12}>
                  <Text type="secondary">Рентабельность:</Text>
                  <div>
                    <Text strong style={{ fontSize: 18 }}>
                      {formatPercent(data.profit_margin_actual)}
                    </Text>
                  </div>
                </Col>
                <Col span={12}>
                  <Text type="secondary">ROI:</Text>
                  <div>
                    <Text strong style={{ fontSize: 18 }}>
                      {formatPercent(data.roi_actual)}
                    </Text>
                  </div>
                </Col>
              </Row>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Main Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Динамика финансовых показателей">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Доходы"
                  stroke="#52c41a"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="Расходы"
                  stroke="#ff4d4f"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="Прибыль"
                  stroke="#1890ff"
                  strokeWidth={3}
                  dot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Накопительный денежный поток">
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={metrics.cashFlow}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Area
                  type="monotone"
                  dataKey="cashFlow"
                  stroke="#1890ff"
                  fill="#1890ff"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Profit Trend */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="Динамика прибыли и рентабельности">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={metrics.profitTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="profit" fill="#1890ff" name="Прибыль" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="margin"
                  stroke="#722ed1"
                  strokeWidth={3}
                  name="Рентабельность (%)"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Top Categories */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={<><TrophyOutlined /> Топ-5 источников доходов</>}>
            {metrics.topRevenue.map((item: any, index: number) => (
              <div
                key={item.category_id}
                style={{
                  padding: '12px 0',
                  borderBottom: index < metrics.topRevenue.length - 1 ? '1px solid #f0f0f0' : 'none',
                }}
              >
                <Row align="middle" justify="space-between">
                  <Col span={12}>
                    <Tag color="green">#{index + 1}</Tag>
                    <Text strong>{item.category_name}</Text>
                  </Col>
                  <Col span={12} style={{ textAlign: 'right' }}>
                    <Text strong style={{ fontSize: 16 }}>
                      {formatCurrency(item.actual)}
                    </Text>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatPercent(item.execution_percent)} исполнения
                      </Text>
                    </div>
                  </Col>
                </Row>
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={<><WarningOutlined /> Топ-5 статей расходов</>}>
            {metrics.topExpenses.map((item: any, index: number) => (
              <div
                key={item.category_id}
                style={{
                  padding: '12px 0',
                  borderBottom: index < metrics.topExpenses.length - 1 ? '1px solid #f0f0f0' : 'none',
                }}
              >
                <Row align="middle" justify="space-between">
                  <Col span={12}>
                    <Tag color="red">#{index + 1}</Tag>
                    <Text strong>{item.category_name}</Text>
                  </Col>
                  <Col span={12} style={{ textAlign: 'right' }}>
                    <Text strong style={{ fontSize: 16 }}>
                      {formatCurrency(item.actual)}
                    </Text>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatPercent(item.execution_percent)} исполнения
                      </Text>
                    </div>
                  </Col>
                </Row>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default UnifiedFinancialDashboardPage
