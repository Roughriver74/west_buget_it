import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Typography, Card, Row, Col, Select, Tabs, Statistic } from 'antd'
import { LineChart, Line, BarChart, Bar, AreaChart, Area, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { analyticsApi } from '@/api'
import dayjs from 'dayjs'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Paragraph } = Typography
const { Option } = Select

type ComparisonMode = 'none' | 'previous-period' | 'previous-year'
type MonthlyChartItem = {
  month: string
  'План': number
  'Факт': number
  'Остаток': number
}

type CategoryChartItem = {
  category: string
  fullName: string
  'План': number
  'Факт': number
  'Остаток': number
}

const AnalyticsPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState<number | undefined>(undefined)
  const [comparisonMode, setComparisonMode] = useState<ComparisonMode>('none')

  // Основные данные дашборда
  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboard', year, month],
    queryFn: () => analyticsApi.getDashboard({ year, month }),
  })

  // Данные для сравнения
  const {
    data: comparisonData,
    isLoading: comparisonLoading,
    error: comparisonError,
    refetch: refetchComparison,
  } = useQuery({
    queryKey: ['dashboard-comparison', year, month, comparisonMode],
    queryFn: () => {
      if (comparisonMode === 'none') return null

      if (comparisonMode === 'previous-year') {
        return analyticsApi.getDashboard({ year: year - 1, month })
      }

      if (comparisonMode === 'previous-period' && month) {
        const prevMonth = month === 1 ? 12 : month - 1
        const prevYear = month === 1 ? year - 1 : year
        return analyticsApi.getDashboard({ year: prevYear, month: prevMonth })
      }

      return null
    },
    enabled: comparisonMode !== 'none',
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('ru-RU').format(value)
  }

  const isLoading = dashboardLoading || (comparisonMode !== 'none' && comparisonLoading)
  const queryError = dashboardError || comparisonError

  const handleRetry = () => {
    refetchDashboard()
    if (comparisonMode !== 'none') {
      refetchComparison()
    }
  }

  if (isLoading) {
    return <LoadingState />
  }

  if (queryError) {
    return (
      <ErrorState
        description={String(queryError)}
        onRetry={handleRetry}
        retryLabel="Повторить попытку"
      />
    )
  }

  if (!dashboardData) {
    return (
      <ErrorState
        status="info"
        title="Нет данных для отображения"
        description="Попробуйте изменить параметры фильтрации или период."
        fullHeight
      />
    )
  }

  // Подготовка данных для графиков
  const monthlyData: MonthlyChartItem[] = (dashboardData.by_month ?? []).map((item) => ({
    month: `${item.month} мес`,
    'План': item.planned,
    'Факт': item.actual,
    'Остаток': item.remaining,
  }))

  const categoryData: CategoryChartItem[] = (dashboardData.by_category ?? []).map((item) => {
    const truncatedName =
      item.category_name.length > 20
        ? `${item.category_name.substring(0, 20)}...`
        : item.category_name

    return {
      category: truncatedName,
      fullName: item.category_name,
      'План': item.planned,
      'Факт': item.actual,
      'Остаток': item.remaining,
    }
  })

  // Данные сравнения периодов
  const calculateChange = (current: number, previous: number) => {
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  const comparisonStats = comparisonData ? {
    plannedChange: calculateChange(dashboardData.totals.planned, comparisonData.totals.planned),
    actualChange: calculateChange(dashboardData.totals.actual, comparisonData.totals.actual),
    executionChange: dashboardData.totals.execution_percent - comparisonData.totals.execution_percent,
  } : null

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Расширенная аналитика</Title>
        <Paragraph>
          Детальный анализ исполнения бюджета с возможностью сравнения периодов и углубленной визуализацией.
        </Paragraph>
      </div>

      {/* Фильтры */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Год</div>
            <Select
              value={year}
              onChange={setYear}
              style={{ width: '100%' }}
              size="large"
            >
              {Array.from({ length: 5 }, (_, i) => currentYear - 2 + i).map(y => (
                <Option key={y} value={y}>{y} год</Option>
              ))}
            </Select>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Месяц</div>
            <Select
              value={month}
              onChange={setMonth}
              allowClear
              placeholder="Все месяцы"
              style={{ width: '100%' }}
              size="large"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                <Option key={m} value={m}>
                  {dayjs().month(m - 1).format('MMMM')}
                </Option>
              ))}
            </Select>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Режим сравнения</div>
            <Select
              value={comparisonMode}
              onChange={setComparisonMode}
              style={{ width: '100%' }}
              size="large"
            >
              <Option value="none">Без сравнения</Option>
              <Option value="previous-period">С предыдущим периодом</Option>
              <Option value="previous-year">С прошлым годом</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Сравнение периодов */}
      {comparisonStats && comparisonData && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title={`Изменение плана (${comparisonMode === 'previous-year' ? 'г-к-г' : 'м-к-м'})`}
                value={Math.abs(comparisonStats.plannedChange)}
                precision={2}
                valueStyle={{ color: comparisonStats.plannedChange >= 0 ? '#3f8600' : '#cf1322' }}
                prefix={comparisonStats.plannedChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="%"
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Предыдущий период: {formatCurrency(comparisonData.totals.planned)}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title={`Изменение факта (${comparisonMode === 'previous-year' ? 'г-к-г' : 'м-к-м'})`}
                value={Math.abs(comparisonStats.actualChange)}
                precision={2}
                valueStyle={{ color: comparisonStats.actualChange >= 0 ? '#cf1322' : '#3f8600' }}
                prefix={comparisonStats.actualChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="%"
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Предыдущий период: {formatCurrency(comparisonData.totals.actual)}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="Изменение исполнения"
                value={Math.abs(comparisonStats.executionChange)}
                precision={2}
                valueStyle={{ color: comparisonStats.executionChange >= 0 ? '#1890ff' : '#666' }}
                prefix={comparisonStats.executionChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                suffix="п.п."
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Предыдущий период: {comparisonData.totals.execution_percent.toFixed(2)}%
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Графики */}
      <Tabs
        defaultActiveKey="monthly"
        size="large"
        items={[
          {
            key: 'monthly',
            label: 'Помесячная динамика',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="План vs Факт по месяцам">
                    <ResponsiveContainer width="100%" height={350}>
                      <ComposedChart data={monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Bar dataKey="План" fill="#91d5ff" />
                        <Bar dataKey="Факт" fill="#1890ff" />
                        <Line type="monotone" dataKey="Остаток" stroke="#ff7875" strokeWidth={2} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24} lg={12}>
                  <Card title="Накопительное исполнение">
                    <ResponsiveContainer width="100%" height={350}>
                      <AreaChart data={monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Area type="monotone" dataKey="План" stackId="1" stroke="#91d5ff" fill="#91d5ff" />
                        <Area type="monotone" dataKey="Факт" stackId="2" stroke="#1890ff" fill="#1890ff" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'category',
            label: 'По статьям расходов',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24}>
                  <Card title="Исполнение по статьям расходов">
                    <ResponsiveContainer width="100%" height={500}>
                      <BarChart
                        data={categoryData}
                        layout="vertical"
                        margin={{ left: 150 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" tickFormatter={(value) => formatNumber(value)} />
                        <YAxis type="category" dataKey="category" width={140} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelFormatter={(label) => {
                            const item = categoryData.find(d => d.category === label)
                            return item?.fullName || label
                          }}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Bar dataKey="План" fill="#91d5ff" />
                        <Bar dataKey="Факт" fill="#1890ff" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'trend',
            label: 'Тренды',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24}>
                  <Card title="Тренд исполнения бюджета">
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="План"
                          stroke="#91d5ff"
                          strokeWidth={3}
                          dot={{ r: 5 }}
                          activeDot={{ r: 7 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="Факт"
                          stroke="#1890ff"
                          strokeWidth={3}
                          dot={{ r: 5 }}
                          activeDot={{ r: 7 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24}>
                  <Card title="Динамика остатка">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={monthlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="Остаток"
                          stroke="#52c41a"
                          fill="#95de64"
                          fillOpacity={0.6}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            ),
          },
        ]}
      />
    </div>
  )
}

export default AnalyticsPage
