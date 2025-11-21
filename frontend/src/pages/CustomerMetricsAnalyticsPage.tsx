/**
 * Customer Metrics Analytics (Аналитика клиентских метрик)
 *
 * Comprehensive analytics showing:
 * - ОКБ (Общая клиентская база) - Total Customer Base
 * - АКБ (Активная клиентская база) - Active Customer Base
 * - Покрытие (АКБ/ОКБ) - Coverage Rate
 * - Средний чек по сегментам - Average Order Value by segments
 * - Динамика по месяцам - Monthly trends
 * - Разбивка по потокам доходов - Breakdown by revenue streams
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Typography, Card, Row, Col, Select, Statistic, Table, Tabs, Space, Tag } from 'antd'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  AreaChart,
} from 'recharts'
import { analyticsApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import dayjs from 'dayjs'
import {
  TeamOutlined,
  UserAddOutlined,
  PercentageOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import ExportButton from '@/components/common/ExportButton'
import { generateExportFilename } from '@/utils/downloadUtils'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

// Type definitions (matching backend schemas)
interface CustomerMetricsMonthly {
  month: number
  month_name: string
  total_customer_base: number
  active_customer_base: number
  coverage_rate: number
  avg_order_value: number
  avg_order_value_regular: number
  avg_order_value_network: number
  avg_order_value_new: number
}

interface CustomerMetricsByStream {
  revenue_stream_id: number
  revenue_stream_name: string
  total_customer_base: number
  active_customer_base: number
  coverage_rate: number
  avg_order_value: number
  regular_clinics: number
  network_clinics: number
  new_clinics: number
}

interface CustomerMetricsAnalytics {
  year: number
  department_id?: number
  department_name?: string
  total_customer_base: number
  active_customer_base: number
  coverage_rate: number
  regular_clinics: number
  network_clinics: number
  new_clinics: number
  avg_order_value: number
  avg_order_value_regular: number
  avg_order_value_network: number
  avg_order_value_new: number
  customer_base_growth?: number
  active_base_growth?: number
  avg_check_growth?: number
  by_month: CustomerMetricsMonthly[]
  by_stream?: CustomerMetricsByStream[]
}

const CustomerMetricsAnalyticsPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const { selectedDepartment } = useDepartment()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  // Fetch customer metrics analytics
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<CustomerMetricsAnalytics>({
    queryKey: ['customer-metrics-analytics', year, selectedDepartment?.id],
    queryFn: () =>
      analyticsApi.getCustomerMetricsAnalytics({
        year,
        department_id: selectedDepartment?.id,
      }),
  })

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('ru-RU').format(value)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`
  }

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

  if (!data) {
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
  const monthlyChartData = data.by_month.map((item) => ({
    month: item.month_name,
    'ОКБ': item.total_customer_base,
    'АКБ': item.active_customer_base,
    'Покрытие %': item.coverage_rate,
    'Средний чек': item.avg_order_value,
  }))

  // Monthly table columns
  const monthlyColumns = [
    {
      title: 'Месяц',
      dataIndex: 'month_name',
      key: 'month_name',
      width: 120,
      fixed: 'left' as const,
    },
    {
      title: 'ОКБ',
      dataIndex: 'total_customer_base',
      key: 'total_customer_base',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'АКБ',
      dataIndex: 'active_customer_base',
      key: 'active_customer_base',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Покрытие',
      dataIndex: 'coverage_rate',
      key: 'coverage_rate',
      align: 'right' as const,
      render: (value: number) => formatPercent(value),
    },
    {
      title: 'Средний чек',
      dataIndex: 'avg_order_value',
      key: 'avg_order_value',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Чек (Обычные)',
      dataIndex: 'avg_order_value_regular',
      key: 'avg_order_value_regular',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Чек (Сети)',
      dataIndex: 'avg_order_value_network',
      key: 'avg_order_value_network',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Чек (Новые)',
      dataIndex: 'avg_order_value_new',
      key: 'avg_order_value_new',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
  ]

  // Stream columns
  const streamColumns = [
    {
      title: 'Поток доходов',
      dataIndex: 'revenue_stream_name',
      key: 'revenue_stream_name',
      width: 200,
    },
    {
      title: 'ОКБ',
      dataIndex: 'total_customer_base',
      key: 'total_customer_base',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'АКБ',
      dataIndex: 'active_customer_base',
      key: 'active_customer_base',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Покрытие',
      dataIndex: 'coverage_rate',
      key: 'coverage_rate',
      align: 'right' as const,
      render: (value: number) => formatPercent(value),
    },
    {
      title: 'Средний чек',
      dataIndex: 'avg_order_value',
      key: 'avg_order_value',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Обычные',
      dataIndex: 'regular_clinics',
      key: 'regular_clinics',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Сети',
      dataIndex: 'network_clinics',
      key: 'network_clinics',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Новые',
      dataIndex: 'new_clinics',
      key: 'new_clinics',
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Аналитика клиентских метрик</Title>
        <Paragraph>
          Комплексная аналитика клиентской базы: ОКБ, АКБ, покрытие, средний чек по сегментам.
        </Paragraph>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>Год</div>
            <Select
              value={year}
              onChange={setYear}
              style={{ width: '100%' }}
              size="large"
            >
              {Array.from({ length: 5 }, (_, i) => currentYear - 2 + i).map((y) => (
                <Option key={y} value={y}>
                  {y} год
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={16} md={18}>
            <Row justify="space-between" align="middle">
              <Col>
                {data.department_name && (
                  <Space>
                    <Text type="secondary">Отдел:</Text>
                    <Text strong>{data.department_name}</Text>
                  </Space>
                )}
              </Col>
              <Col>
                <ExportButton
                  exportFn={() => analyticsApi.exportCustomerMetricsAnalytics({
                    year,
                    department_id: selectedDepartment?.id
                  })}
                  filename={generateExportFilename('Customer_Metrics', year)}
                  buttonText="Экспорт в Excel"
                />
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ОКБ (Общая клиентская база)"
              value={data.total_customer_base}
              prefix={<TeamOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
            {data.customer_base_growth !== null && data.customer_base_growth !== undefined && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Рост г-к-г: </Text>
                <Text style={{ color: data.customer_base_growth >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {data.customer_base_growth >= 0 ? <RiseOutlined /> : <FallOutlined />}{' '}
                  {formatPercent(Math.abs(data.customer_base_growth))}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="АКБ (Активная клиентская база)"
              value={data.active_customer_base}
              prefix={<UserAddOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            {data.active_base_growth !== null && data.active_base_growth !== undefined && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Рост г-к-г: </Text>
                <Text style={{ color: data.active_base_growth >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {data.active_base_growth >= 0 ? <RiseOutlined /> : <FallOutlined />}{' '}
                  {formatPercent(Math.abs(data.active_base_growth))}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Покрытие (АКБ/ОКБ)"
              value={data.coverage_rate}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Space size="small" direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Tag color="blue">Обычные: {formatNumber(data.regular_clinics)}</Tag>
                </div>
                <div>
                  <Tag color="green">Сети: {formatNumber(data.network_clinics)}</Tag>
                </div>
                <div>
                  <Tag color="orange">Новые: {formatNumber(data.new_clinics)}</Tag>
                </div>
              </Space>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Средний чек"
              value={data.avg_order_value}
              precision={0}
              prefix={<DollarOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
              formatter={(value) => formatCurrency(Number(value))}
            />
            {data.avg_check_growth !== null && data.avg_check_growth !== undefined && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Рост г-к-г: </Text>
                <Text style={{ color: data.avg_check_growth >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {data.avg_check_growth >= 0 ? <RiseOutlined /> : <FallOutlined />}{' '}
                  {formatPercent(Math.abs(data.avg_check_growth))}
                </Text>
              </div>
            )}
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              <div>Обычные: {formatCurrency(data.avg_order_value_regular)}</div>
              <div>Сети: {formatCurrency(data.avg_order_value_network)}</div>
              <div>Новые: {formatCurrency(data.avg_order_value_new)}</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts and Tables */}
      <Tabs
        defaultActiveKey="overview"
        size="large"
        items={[
          {
            key: 'overview',
            label: 'Обзор',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Динамика клиентской базы">
                    <ResponsiveContainer width="100%" height={350}>
                      <LineChart data={monthlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value: number) => formatNumber(value)} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="ОКБ"
                          stroke="#1890ff"
                          strokeWidth={3}
                          dot={{ r: 4 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="АКБ"
                          stroke="#52c41a"
                          strokeWidth={3}
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24} lg={12}>
                  <Card title="Покрытие и средний чек">
                    <ResponsiveContainer width="100%" height={350}>
                      <ComposedChart data={monthlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis yAxisId="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <Tooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="Покрытие %" fill="#722ed1" />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="Средний чек"
                          stroke="#faad14"
                          strokeWidth={3}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24}>
                  <Card title="Рост клиентской базы">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={monthlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value: number) => formatNumber(value)} />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="ОКБ"
                          stackId="1"
                          stroke="#1890ff"
                          fill="#1890ff"
                          fillOpacity={0.6}
                        />
                        <Area
                          type="monotone"
                          dataKey="АКБ"
                          stackId="2"
                          stroke="#52c41a"
                          fill="#52c41a"
                          fillOpacity={0.6}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'monthly',
            label: 'Помесячная детализация',
            children: (
              <Card>
                <ResponsiveTable
                  dataSource={data.by_month}
                  columns={monthlyColumns}
                  rowKey="month"
                  pagination={false}
                  scroll={{ x: 1200 }}
                />
              </Card>
            ),
          },
          {
            key: 'streams',
            label: 'По потокам доходов',
            children: data.by_stream && data.by_stream.length > 0 ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Клиентская база по потокам">
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={data.by_stream}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="revenue_stream_name" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip formatter={(value: number) => formatNumber(value)} />
                        <Legend />
                        <Bar dataKey="total_customer_base" name="ОКБ" fill="#1890ff" />
                        <Bar dataKey="active_customer_base" name="АКБ" fill="#52c41a" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Детализация по потокам">
                    <ResponsiveTable
                      dataSource={data.by_stream}
                      columns={streamColumns}
                      rowKey="revenue_stream_id"
                      pagination={false}
                      scroll={{ x: 1000 }}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card>
                <Text type="secondary">Нет данных по потокам доходов</Text>
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}

export default CustomerMetricsAnalyticsPage
