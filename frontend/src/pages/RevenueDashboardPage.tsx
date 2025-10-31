import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Statistic, Select, Alert, Typography, Empty } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import { revenueStreamsApi, revenueCategoriesApi, revenueActualsApi } from '@/api'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'
import dayjs from 'dayjs'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title } = Typography

const COLORS = ['#52c41a', '#1890ff', '#faad14', '#f5222d', '#722ed1', '#13c2c2']

const RevenueDashboardPage = () => {
  const currentYear = dayjs().year()
  const currentMonth = dayjs().month() + 1
  const [year, setYear] = useState(currentYear)
  const { selectedDepartment } = useDepartment()

  // Fetch revenue streams
  const { data: streams } = useQuery({
    queryKey: ['revenue-streams', selectedDepartment?.id],
    queryFn: () =>
      revenueStreamsApi.getAll({
        is_active: true,
        department_id: selectedDepartment?.id,
      }),
  })

  // Fetch revenue categories
  const { data: categories } = useQuery({
    queryKey: ['revenue-categories', selectedDepartment?.id],
    queryFn: () =>
      revenueCategoriesApi.getAll({
        is_active: true,
        department_id: selectedDepartment?.id,
      }),
  })

  // Fetch revenue actuals
  const {
    data: actuals,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['revenue-actuals', year, selectedDepartment?.id],
    queryFn: () =>
      revenueActualsApi.getAll({
        year,
        department_id: selectedDepartment?.id,
      }),
  })

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  // Calculate total revenue for current year
  const totalRevenue = actuals?.reduce((sum, actual) => sum + Number(actual.actual_amount), 0) || 0

  // Calculate revenue for current month
  const currentMonthRevenue =
    actuals
      ?.filter((a) => a.month === currentMonth)
      .reduce((sum, actual) => sum + Number(actual.actual_amount), 0) || 0

  // Calculate revenue for previous month
  const previousMonth = currentMonth === 1 ? 12 : currentMonth - 1
  const previousMonthRevenue =
    actuals
      ?.filter((a) => a.month === previousMonth)
      .reduce((sum, actual) => sum + Number(actual.actual_amount), 0) || 0

  // Calculate month-over-month growth
  const momGrowth =
    previousMonthRevenue > 0
      ? ((currentMonthRevenue - previousMonthRevenue) / previousMonthRevenue) * 100
      : 0

  // Prepare monthly trend data
  const monthlyTrendData = Array.from({ length: 12 }, (_, i) => {
    const month = i + 1
    const monthRevenue =
      actuals?.filter((a) => a.month === month).reduce((sum, a) => sum + Number(a.actual_amount), 0) ||
      0
    const monthPlan =
      actuals?.filter((a) => a.month === month).reduce((sum, a) => sum + Number(a.planned_amount || 0), 0) ||
      0

    return {
      month: dayjs().month(i).format('MMM'),
      actual: monthRevenue,
      plan: monthPlan,
    }
  })

  // Prepare revenue by stream data (pie chart)
  const revenueByStream =
    streams
      ?.map((stream) => {
        const streamRevenue =
          actuals
            ?.filter((a) => a.revenue_stream_id === stream.id)
            .reduce((sum, a) => sum + Number(a.actual_amount), 0) || 0

        return {
          name: stream.name,
          value: streamRevenue,
        }
      })
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 6) || []

  // Prepare revenue by category data
  const revenueByCategory =
    categories
      ?.map((category) => {
        const categoryRevenue =
          actuals
            ?.filter((a) => a.revenue_category_id === category.id)
            .reduce((sum, a) => sum + Number(a.actual_amount), 0) || 0

        return {
          name: category.name,
          value: categoryRevenue,
        }
      })
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 6) || []

  // Calculate plan vs actual
  const totalPlanned =
    actuals?.reduce((sum, actual) => sum + Number(actual.planned_amount || 0), 0) || 0
  const variance = totalRevenue - totalPlanned
  const variancePercent = totalPlanned > 0 ? (variance / totalPlanned) * 100 : 0

  return (
    <div>
      <Title level={2}>Дашборд доходов</Title>

      {/* Year selector */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Select
            value={year}
            onChange={setYear}
            style={{ width: '100%' }}
            options={[
              { value: 2024, label: '2024' },
              { value: 2025, label: '2025' },
              { value: 2026, label: '2026' },
            ]}
          />
        </Col>
      </Row>

      {/* Key metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Общая выручка (год)"
              value={totalRevenue}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Текущий месяц"
              value={currentMonthRevenue}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Рост м/м"
              value={Math.abs(momGrowth)}
              precision={1}
              suffix="%"
              prefix={momGrowth >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              valueStyle={{ color: momGrowth >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Отклонение от плана"
              value={Math.abs(variancePercent)}
              precision={1}
              suffix="%"
              prefix={variancePercent >= 0 ? <ArrowUpOutlined /> : <FallOutlined />}
              valueStyle={{ color: variancePercent >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Monthly trend */}
        <Col xs={24} lg={16}>
          <Card title="Динамика доходов по месяцам">
            {monthlyTrendData.some((d) => d.actual > 0 || d.plan > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={monthlyTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Legend />
                  <Line type="monotone" dataKey="plan" stroke="#8884d8" name="План" />
                  <Line type="monotone" dataKey="actual" stroke="#52c41a" name="Факт" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных за выбранный период" />
            )}
          </Card>
        </Col>

        {/* Plan vs Actual */}
        <Col xs={24} lg={8}>
          <Card title="План vs Факт">
            {totalPlanned > 0 || totalRevenue > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[
                    { name: 'Выручка', План: totalPlanned, Факт: totalRevenue },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Legend />
                  <Bar dataKey="План" fill="#8884d8" />
                  <Bar dataKey="Факт" fill="#52c41a" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных за выбранный период" />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Revenue by stream */}
        <Col xs={24} lg={12}>
          <Card title="Выручка по потокам доходов">
            {revenueByStream.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={revenueByStream}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {revenueByStream.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных о потоках доходов" />
            )}
          </Card>
        </Col>

        {/* Revenue by category */}
        <Col xs={24} lg={12}>
          <Card title="Выручка по категориям">
            {revenueByCategory.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={revenueByCategory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => formatCurrency(value)} />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Bar dataKey="value" fill="#1890ff" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных о категориях доходов" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Info alert */}
      {(!actuals || actuals.length === 0) && (
        <Alert
          message="Нет данных о доходах"
          description="Начните с добавления фактических доходов в разделе 'Фактические доходы'"
          type="info"
          showIcon
          style={{ marginTop: 24 }}
        />
      )}
    </div>
  )
}

export default RevenueDashboardPage
