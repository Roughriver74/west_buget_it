import { useState, useMemo } from 'react'
import { Card, Row, Col, Statistic, Select, Spin, Empty, Typography, Table, Button } from 'antd'
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
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { kpiApi, type KPIDashboardData } from '@/api/kpi'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { EmployeeKpiTrendChart } from './EmployeeKpiTrendChart'
import {
  TrophyOutlined,
  TeamOutlined,
  DollarOutlined,
  PercentageOutlined,
  AimOutlined,
  CheckCircleOutlined,
  LineChartOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography
const { Option } = Select

// Цвета для графиков
const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#f5222d',
  purple: '#722ed1',
  cyan: '#13c2c2',
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: COLORS.warning,
  UNDER_REVIEW: COLORS.cyan,
  APPROVED: COLORS.success,
  REJECTED: COLORS.error,
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Черновик',
  UNDER_REVIEW: 'На проверке',
  APPROVED: 'Утверждено',
  REJECTED: 'Отклонено',
}

interface KpiDashboardProps {
  departmentId?: number
}

export const KpiDashboard = ({ departmentId }: KpiDashboardProps) => {
  const { user } = useAuth()
  const { selectedDepartment } = useDepartment()
  const [selectedYear, setSelectedYear] = useState(dayjs().year())
  const [trendDrawerOpen, setTrendDrawerOpen] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<{
    id: number
    name: string
  } | null>(null)

  // Определяем department_id для запроса
  const targetDepartmentId = useMemo(() => {
    if (departmentId !== undefined) return departmentId
    if (selectedDepartment?.id) return selectedDepartment.id
    if (user?.department_id) return user.department_id
    return undefined
  }, [departmentId, selectedDepartment, user])

  // Fetch dashboard data
  const { data: dashboardData, isLoading } = useQuery<KPIDashboardData>({
    queryKey: ['kpi-dashboard', selectedYear, targetDepartmentId],
    queryFn: () =>
      kpiApi.getDashboardData({
        year: selectedYear,
        department_id: targetDepartmentId,
      }),
    enabled: !!selectedYear,
  })

  // Годы для выбора (текущий год ± 2 года)
  const yearOptions = useMemo(() => {
    const currentYear = dayjs().year()
    return Array.from({ length: 5 }, (_, i) => currentYear - 2 + i)
  }, [])

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Загрузка дашборда...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <Empty description="Нет данных для отображения" style={{ marginTop: 100 }} />
    )
  }

  const { overview, status_distribution, monthly_trends, top_employees } = dashboardData

  // Prepare data for pie chart
  const statusPieData = status_distribution.map((item) => ({
    name: STATUS_LABELS[item.status] || item.status,
    value: item.count,
    percentage: item.percentage,
  }))

  // Handle opening trend chart for employee
  const handleViewTrend = (employeeId: number, employeeName: string) => {
    setSelectedEmployee({ id: employeeId, name: employeeName })
    setTrendDrawerOpen(true)
  }

  return (
    <div style={{ padding: '0 24px' }}>
      {/* Заголовок и фильтры */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>
            KPI Dashboard
          </Title>
        </Col>
        <Col>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 120 }}
            placeholder="Выберите год"
          >
            {yearOptions.map((year) => (
              <Option key={year} value={year}>
                {year}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* Общая статистика */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Средний KPI%"
              value={overview.avg_kpi_percentage}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: COLORS.primary }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Всего бонусов"
              value={overview.total_bonuses}
              precision={2}
              suffix="₽"
              prefix={<DollarOutlined />}
              valueStyle={{ color: COLORS.success }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Сотрудников"
              value={overview.unique_employees}
              prefix={<TeamOutlined />}
              valueStyle={{ color: COLORS.cyan }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Всего целей"
              value={overview.total_goals}
              prefix={<AimOutlined />}
              valueStyle={{ color: COLORS.purple }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Активных целей"
              value={overview.active_goals}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: COLORS.success }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Всего KPI"
              value={overview.total_kpis}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Графики */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* График динамики KPI по месяцам */}
        <Col xs={24} lg={16}>
          <Card title="Динамика KPI по месяцам" style={{ height: 400 }}>
            {monthly_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={monthly_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month_name" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === 'Средний KPI%') return `${value.toFixed(2)}%`
                      if (name === 'Бонусы') return `${value.toFixed(2)} ₽`
                      return value
                    }}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="avg_kpi"
                    stroke={COLORS.primary}
                    strokeWidth={2}
                    name="Средний KPI%"
                    dot={{ r: 4 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="total_bonus"
                    stroke={COLORS.success}
                    strokeWidth={2}
                    name="Бонусы"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных по месяцам" style={{ marginTop: 80 }} />
            )}
          </Card>
        </Col>

        {/* Круговая диаграмма статусов */}
        <Col xs={24} lg={8}>
          <Card title="Распределение по статусам" style={{ height: 400 }}>
            {statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={statusPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusPieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={STATUS_COLORS[entry.name] || COLORS.primary}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string, props: any) => [
                      `${value} (${props.payload.percentage.toFixed(1)}%)`,
                      name,
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных по статусам" style={{ marginTop: 80 }} />
            )}
          </Card>
        </Col>
      </Row>

      {/* Количество сотрудников по месяцам */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="Количество сотрудников с KPI по месяцам" style={{ height: 400 }}>
            {monthly_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={monthly_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month_name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="employee_count"
                    fill={COLORS.cyan}
                    name="Количество сотрудников"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Нет данных" style={{ marginTop: 80 }} />
            )}
          </Card>
        </Col>
      </Row>

      {/* Топ-10 сотрудников */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="Топ-10 сотрудников по среднему KPI%">
            {top_employees.length > 0 ? (
              <Table
                dataSource={top_employees}
                rowKey="employee_id"
                pagination={false}
                columns={[
                  {
                    title: '№',
                    key: 'index',
                    width: 60,
                    render: (_, __, index) => index + 1,
                  },
                  {
                    title: 'Сотрудник',
                    dataIndex: 'employee_name',
                    key: 'employee_name',
                  },
                  {
                    title: 'Средний KPI%',
                    dataIndex: 'avg_kpi',
                    key: 'avg_kpi',
                    width: 150,
                    render: (value: number) => (
                      <Text strong style={{ color: COLORS.primary }}>
                        {value.toFixed(2)}%
                      </Text>
                    ),
                    sorter: (a, b) => a.avg_kpi - b.avg_kpi,
                  },
                  {
                    title: 'Всего бонусов',
                    dataIndex: 'total_bonus',
                    key: 'total_bonus',
                    width: 180,
                    render: (value: number) => (
                      <Text style={{ color: COLORS.success }}>
                        {value.toFixed(2)} ₽
                      </Text>
                    ),
                    sorter: (a, b) => a.total_bonus - b.total_bonus,
                  },
                  {
                    title: 'Количество KPI',
                    dataIndex: 'kpi_count',
                    key: 'kpi_count',
                    width: 150,
                    align: 'center',
                    sorter: (a, b) => a.kpi_count - b.kpi_count,
                  },
                  {
                    title: 'Действия',
                    key: 'actions',
                    width: 180,
                    align: 'center',
                    render: (_, record) => (
                      <Button
                        type="link"
                        icon={<LineChartOutlined />}
                        onClick={() => handleViewTrend(record.employee_id, record.employee_name)}
                      >
                        Динамика
                      </Button>
                    ),
                  },
                ]}
              />
            ) : (
              <Empty description="Нет данных о сотрудниках" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Drawer с графиками динамики сотрудника */}
      {selectedEmployee && (
        <EmployeeKpiTrendChart
          employeeId={selectedEmployee.id}
          employeeName={selectedEmployee.name}
          year={selectedYear}
          open={trendDrawerOpen}
          onClose={() => setTrendDrawerOpen(false)}
        />
      )}
    </div>
  )
}
