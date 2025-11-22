/**
 * Revenue Analytics Extended (Расширенная аналитика доходов)
 *
 * Comprehensive revenue analytics with:
 * - Regional breakdown (by revenue streams)
 * - Product mix (by revenue categories)
 * - Monthly trends
 * - Growth metrics (year-over-year)
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Typography, Card, Row, Col, Select, Statistic, Tabs, Space, Tag, Progress } from 'antd'
import {
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
  ResponsiveContainer} from 'recharts'
import { analyticsApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import dayjs from 'dayjs'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  CheckCircleOutlined} from '@ant-design/icons'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import ExportButton from '@/components/common/ExportButton'
import { generateExportFilename } from '@/utils/downloadUtils'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7c7c']

const RevenueAnalyticsExtendedPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const { selectedDepartment } = useDepartment()

  // Fetch revenue analytics
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['revenue-analytics', year, selectedDepartment?.id],
    queryFn: () =>
      analyticsApi.getRevenueAnalytics({
        year,
        department_id: selectedDepartment?.id})})

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0}).format(value)
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('ru-RU').format(value)
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

  // Prepare data
  const monthlyData = data.by_month.map((item: any) => ({
    month: item.month_name,
    'План': item.planned,
    'Факт': item.actual,
    'Отклонение': item.variance}))

  // Pie chart data for regional breakdown
  const regionalPieData = data.by_stream?.map((item: any) => ({
    name: item.revenue_stream_name,
    value: item.actual})) || []

  // Pie chart data for product mix
  const productPieData = data.by_category?.map((item: any) => ({
    name: item.revenue_category_name,
    value: item.actual})) || []

  // Table columns for streams
  const streamColumns = [
    {
      title: 'Поток доходов',
      dataIndex: 'revenue_stream_name',
      key: 'revenue_stream_name',
      width: 200},
    {
      title: 'Тип',
      dataIndex: 'stream_type',
      key: 'stream_type',
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>},
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value)},
    {
      title: 'Факт',
      dataIndex: 'actual',
      key: 'actual',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value)},
    {
      title: 'Отклонение',
      dataIndex: 'variance',
      key: 'variance',
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </Text>
      )},
    {
      title: 'Исполнение',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      align: 'right' as const,
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          format={(percent) => `${percent?.toFixed(1)}%`}
          status={value >= 100 ? 'success' : value >= 80 ? 'normal' : 'exception'}
        />
      )},
    {
      title: 'Доля',
      dataIndex: 'share_of_total',
      key: 'share_of_total',
      align: 'right' as const,
      render: (value: number) => formatPercent(value)},
  ]

  // Table columns for categories
  const categoryColumns = [
    {
      title: 'Категория',
      dataIndex: 'revenue_category_name',
      key: 'revenue_category_name',
      width: 200},
    {
      title: 'Тип',
      dataIndex: 'category_type',
      key: 'category_type',
      width: 120,
      render: (type: string) => <Tag color="blue">{type}</Tag>},
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value)},
    {
      title: 'Факт',
      dataIndex: 'actual',
      key: 'actual',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value)},
    {
      title: 'Отклонение',
      dataIndex: 'variance',
      key: 'variance',
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </Text>
      )},
    {
      title: 'Исполнение',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      align: 'right' as const,
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          format={(percent) => `${percent?.toFixed(1)}%`}
          status={value >= 100 ? 'success' : value >= 80 ? 'normal' : 'exception'}
        />
      )},
    {
      title: 'Доля',
      dataIndex: 'share_of_total',
      key: 'share_of_total',
      align: 'right' as const,
      render: (value: number) => formatPercent(value)},
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Расширенная аналитика доходов</Title>
        <Paragraph>
          Комплексная аналитика доходов с региональной разбивкой и продуктовым миксом.
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
                  exportFn={() => analyticsApi.exportRevenueAnalytics({
                    year,
                    department_id: selectedDepartment?.id
                  })}
                  filename={generateExportFilename('Revenue_Analytics', year)}
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
              title="План доходов"
              value={data.total_planned}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#91d5ff' }} />}
              valueStyle={{ color: '#91d5ff' }}
            />
            {data.planned_growth !== null && data.planned_growth !== undefined && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Рост г-к-г: </Text>
                <Text style={{ color: data.planned_growth >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {data.planned_growth >= 0 ? <RiseOutlined /> : <FallOutlined />}{' '}
                  {formatPercent(Math.abs(data.planned_growth))}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Факт доходов"
              value={data.total_actual}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            {data.actual_growth !== null && data.actual_growth !== undefined && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Рост г-к-г: </Text>
                <Text style={{ color: data.actual_growth >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {data.actual_growth >= 0 ? <RiseOutlined /> : <FallOutlined />}{' '}
                  {formatPercent(Math.abs(data.actual_growth))}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Отклонение"
              value={data.total_variance}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              valueStyle={{
                color: data.total_variance >= 0 ? '#52c41a' : '#ff4d4f'}}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">В процентах: </Text>
              <Text>{formatPercent(data.total_variance_percent)}</Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Исполнение плана"
              value={data.total_execution_percent}
              precision={2}
              suffix="%"
              prefix={<CheckCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts and Tables */}
      <Tabs
        defaultActiveKey="monthly"
        size="large"
        items={[
          {
            key: 'monthly',
            label: 'Помесячная динамика',
            children: (
              <Card>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => formatNumber(value)} />
                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="План"
                      stroke="#91d5ff"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Факт"
                      stroke="#52c41a"
                      strokeWidth={3}
                      dot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            )},
          {
            key: 'regional',
            label: 'Региональная разбивка',
            children: data.by_stream && data.by_stream.length > 0 ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Распределение доходов по потокам">
                    <ResponsiveContainer width="100%" height={400}>
                      <PieChart>
                        <Pie
                          data={regionalPieData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={(entry) => `${entry.name}: ${formatPercent(entry.value / data.total_actual * 100)}`}
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {regionalPieData.map((_entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      </PieChart>
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
                      size="small"
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card><Text type="secondary">Нет данных по потокам доходов</Text></Card>
            )},
          {
            key: 'product',
            label: 'Продуктовый микс',
            children: data.by_category && data.by_category.length > 0 ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Структура доходов по категориям">
                    <ResponsiveContainer width="100%" height={400}>
                      <PieChart>
                        <Pie
                          data={productPieData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={(entry) => `${entry.name}: ${formatPercent(entry.value / data.total_actual * 100)}`}
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {productPieData.map((_entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Детализация по категориям">
                    <ResponsiveTable
                      dataSource={data.by_category}
                      columns={categoryColumns}
                      rowKey="revenue_category_id"
                      pagination={false}
                      scroll={{ x: 1000 }}
                      size="small"
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card><Text type="secondary">Нет данных по категориям доходов</Text></Card>
            )},
        ]}
      />
    </div>
  )
}

export default RevenueAnalyticsExtendedPage
