import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Select, Spin, Tabs, Table, Tag, Progress } from 'antd'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { useDepartment } from '@/contexts/DepartmentContext'
import { revenueApi } from '@/api/revenue'

const { Option } = Select

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c']

const RevenueAnalyticsPage = () => {
  const { selectedDepartment } = useDepartment()
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())

  // Fetch regional breakdown
  const { data: regionalData, isLoading: isLoadingRegional } = useQuery({
    queryKey: ['revenue-analytics-regional', selectedYear, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.analytics.getRegionalBreakdown({
        year: selectedYear,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch product mix
  const { data: productMixData, isLoading: isLoadingProductMix } = useQuery({
    queryKey: ['revenue-analytics-product-mix', selectedYear, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.analytics.getProductMix({
        year: selectedYear,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch monthly trends
  const { data: trendsData, isLoading: isLoadingTrends } = useQuery({
    queryKey: ['revenue-analytics-trends', selectedYear, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.analytics.getMonthlyTrends({
        year: selectedYear,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch top performers
  const { data: topPerformersData, isLoading: isLoadingTopPerformers } = useQuery({
    queryKey: ['revenue-analytics-top-performers', selectedYear, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.analytics.getTopPerformers({
        year: selectedYear,
        limit: 5,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Calculate summary metrics
  const summary = useMemo(() => {
    if (!regionalData) return null

    const totalPlanned = regionalData.total_planned
    const totalActual = regionalData.total_actual
    const variance = totalActual - totalPlanned
    const variancePercent = totalPlanned > 0 ? (variance / totalPlanned) * 100 : 0

    return {
      totalPlanned,
      totalActual,
      variance,
      variancePercent,
    }
  }, [regionalData])

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Regional breakdown table columns
  const regionalColumns = [
    {
      title: 'Регион/Поток',
      dataIndex: 'stream_name',
      key: 'stream_name',
      fixed: 'left' as const,
      width: 200,
    },
    {
      title: 'Тип',
      dataIndex: 'stream_type',
      key: 'stream_type',
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'План',
      dataIndex: 'planned_revenue',
      key: 'planned_revenue',
      width: 150,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Факт',
      dataIndex: 'actual_revenue',
      key: 'actual_revenue',
      width: 150,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Отклонение',
      dataIndex: 'variance',
      key: 'variance',
      width: 150,
      align: 'right' as const,
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {value >= 0 ? '+' : ''}
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      title: 'Отклонение, %',
      dataIndex: 'variance_percent',
      key: 'variance_percent',
      width: 150,
      align: 'center' as const,
      render: (value: number) => (
        <Tag color={value >= 0 ? 'green' : 'red'}>
          {value >= 0 ? '+' : ''}
          {value.toFixed(1)}%
        </Tag>
      ),
    },
  ]

  // Product mix table columns
  const productMixColumns = [
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      fixed: 'left' as const,
      width: 200,
    },
    {
      title: 'Тип',
      dataIndex: 'category_type',
      key: 'category_type',
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'План',
      dataIndex: 'planned_revenue',
      key: 'planned_revenue',
      width: 150,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Доля плана, %',
      dataIndex: 'planned_share',
      key: 'planned_share',
      width: 150,
      align: 'center' as const,
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          format={(percent) => `${percent?.toFixed(1)}%`}
        />
      ),
    },
    {
      title: 'Факт',
      dataIndex: 'actual_revenue',
      key: 'actual_revenue',
      width: 150,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Доля факта, %',
      dataIndex: 'actual_share',
      key: 'actual_share',
      width: 150,
      align: 'center' as const,
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          format={(percent) => `${percent?.toFixed(1)}%`}
        />
      ),
    },
  ]

  if (!selectedDepartment) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin tip="Загрузка данных отдела..." />
      </div>
    )
  }

  const isLoading =
    isLoadingRegional || isLoadingProductMix || isLoadingTrends || isLoadingTopPerformers

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0, marginBottom: 8 }}>Аналитика доходов</h1>
            <p style={{ margin: 0, color: '#8c8c8c' }}>
              Расширенная аналитика: региональная разбивка, продуктовый микс, тренды
            </p>
          </Col>
          <Col>
            <span style={{ marginRight: 8 }}>Год:</span>
            <Select value={selectedYear} onChange={setSelectedYear} style={{ width: 120 }}>
              {[2023, 2024, 2025, 2026, 2027].map((year) => (
                <Option key={year} value={year}>
                  {year}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Плановая выручка"
                value={summary.totalPlanned}
                precision={0}
                prefix={<DollarOutlined />}
                suffix="₽"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Фактическая выручка"
                value={summary.totalActual}
                precision={0}
                prefix={<DollarOutlined />}
                suffix="₽"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Отклонение"
                value={summary.variance}
                precision={0}
                prefix={summary.variance >= 0 ? <RiseOutlined /> : <FallOutlined />}
                suffix="₽"
                valueStyle={{ color: summary.variance >= 0 ? '#52c41a' : '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Отклонение, %"
                value={summary.variancePercent}
                precision={1}
                prefix={summary.variance >= 0 ? <RiseOutlined /> : <FallOutlined />}
                suffix="%"
                valueStyle={{ color: summary.variancePercent >= 0 ? '#52c41a' : '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Tabs with different analytics views */}
      <Card>
        <Tabs
          defaultActiveKey="trends"
          items={[
            {
              key: 'trends',
              label: (
                <span>
                  <LineChartOutlined />
                  Месячные тренды
                </span>
              ),
              children: (
                <div>
                  {isLoadingTrends ? (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Spin tip="Загрузка данных..." />
                    </div>
                  ) : trendsData ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={trendsData.monthly_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month_name" />
                        <YAxis />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="planned"
                          stroke="#1890ff"
                          name="План"
                          strokeWidth={2}
                          dot={{ r: 4 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="actual"
                          stroke="#52c41a"
                          name="Факт"
                          strokeWidth={2}
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40, color: '#8c8c8c' }}>
                      Нет данных для отображения
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: 'regional',
              label: (
                <span>
                  <BarChartOutlined />
                  Региональная разбивка
                </span>
              ),
              children: (
                <div>
                  {isLoadingRegional ? (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Spin tip="Загрузка данных..." />
                    </div>
                  ) : regionalData && regionalData.regions.length > 0 ? (
                    <>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={regionalData.regions}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="stream_name" />
                          <YAxis />
                          <Tooltip
                            formatter={(value: number) => formatCurrency(value)}
                            labelStyle={{ color: '#000' }}
                          />
                          <Legend />
                          <Bar dataKey="planned_revenue" fill="#1890ff" name="План" />
                          <Bar dataKey="actual_revenue" fill="#52c41a" name="Факт" />
                        </BarChart>
                      </ResponsiveContainer>

                      <div style={{ marginTop: 24 }}>
                        <Table
                          columns={regionalColumns}
                          dataSource={regionalData.regions}
                          rowKey="stream_id"
                          pagination={false}
                          scroll={{ x: 1000 }}
                        />
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40, color: '#8c8c8c' }}>
                      Нет данных для отображения
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: 'product-mix',
              label: (
                <span>
                  <PieChartOutlined />
                  Продуктовый микс
                </span>
              ),
              children: (
                <div>
                  {isLoadingProductMix ? (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Spin tip="Загрузка данных..." />
                    </div>
                  ) : productMixData && productMixData.categories.length > 0 ? (
                    <>
                      <Row gutter={16}>
                        <Col span={12}>
                          <h3 style={{ textAlign: 'center' }}>План (по категориям)</h3>
                          <ResponsiveContainer width="100%" height={350}>
                            <PieChart>
                              <Pie
                                data={productMixData.categories}
                                dataKey="planned_revenue"
                                nameKey="category_name"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label={(entry) => `${entry.category_name}: ${entry.planned_share.toFixed(1)}%`}
                              >
                                {productMixData.categories.map((_: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(value: number) => formatCurrency(value)} />
                            </PieChart>
                          </ResponsiveContainer>
                        </Col>
                        <Col span={12}>
                          <h3 style={{ textAlign: 'center' }}>Факт (по категориям)</h3>
                          <ResponsiveContainer width="100%" height={350}>
                            <PieChart>
                              <Pie
                                data={productMixData.categories}
                                dataKey="actual_revenue"
                                nameKey="category_name"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label={(entry) => `${entry.category_name}: ${entry.actual_share.toFixed(1)}%`}
                              >
                                {productMixData.categories.map((_: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(value: number) => formatCurrency(value)} />
                            </PieChart>
                          </ResponsiveContainer>
                        </Col>
                      </Row>

                      <div style={{ marginTop: 24 }}>
                        <Table
                          columns={productMixColumns}
                          dataSource={productMixData.categories}
                          rowKey="category_id"
                          pagination={false}
                          scroll={{ x: 1000 }}
                        />
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40, color: '#8c8c8c' }}>
                      Нет данных для отображения
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: 'top-performers',
              label: (
                <span>
                  <TrophyOutlined />
                  Топ регионов и продуктов
                </span>
              ),
              children: (
                <div>
                  {isLoadingTopPerformers ? (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <Spin tip="Загрузка данных..." />
                    </div>
                  ) : topPerformersData ? (
                    <Row gutter={16}>
                      <Col span={12}>
                        <Card title="Топ-5 регионов по фактической выручке" size="small">
                          {topPerformersData.top_regions.length > 0 ? (
                            topPerformersData.top_regions.map((region, index) => (
                              <div
                                key={region.id}
                                style={{
                                  padding: '12px 0',
                                  borderBottom:
                                    index < topPerformersData.top_regions.length - 1
                                      ? '1px solid #f0f0f0'
                                      : 'none',
                                }}
                              >
                                <Row justify="space-between" align="middle">
                                  <Col>
                                    <span style={{ fontSize: 16, fontWeight: 'bold', marginRight: 8 }}>
                                      #{index + 1}
                                    </span>
                                    <span>{region.name}</span>
                                  </Col>
                                  <Col>
                                    <span style={{ fontSize: 16, fontWeight: 'bold', color: '#52c41a' }}>
                                      {formatCurrency(region.total_revenue)}
                                    </span>
                                  </Col>
                                </Row>
                              </div>
                            ))
                          ) : (
                            <div style={{ textAlign: 'center', padding: 20, color: '#8c8c8c' }}>
                              Нет данных
                            </div>
                          )}
                        </Card>
                      </Col>
                      <Col span={12}>
                        <Card title="Топ-5 категорий по фактической выручке" size="small">
                          {topPerformersData.top_categories.length > 0 ? (
                            topPerformersData.top_categories.map((category, index) => (
                              <div
                                key={category.id}
                                style={{
                                  padding: '12px 0',
                                  borderBottom:
                                    index < topPerformersData.top_categories.length - 1
                                      ? '1px solid #f0f0f0'
                                      : 'none',
                                }}
                              >
                                <Row justify="space-between" align="middle">
                                  <Col>
                                    <span style={{ fontSize: 16, fontWeight: 'bold', marginRight: 8 }}>
                                      #{index + 1}
                                    </span>
                                    <span>{category.name}</span>
                                  </Col>
                                  <Col>
                                    <span style={{ fontSize: 16, fontWeight: 'bold', color: '#52c41a' }}>
                                      {formatCurrency(category.total_revenue)}
                                    </span>
                                  </Col>
                                </Row>
                              </div>
                            ))
                          ) : (
                            <div style={{ textAlign: 'center', padding: 20, color: '#8c8c8c' }}>
                              Нет данных
                            </div>
                          )}
                        </Card>
                      </Col>
                    </Row>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40, color: '#8c8c8c' }}>
                      Нет данных для отображения
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default RevenueAnalyticsPage
