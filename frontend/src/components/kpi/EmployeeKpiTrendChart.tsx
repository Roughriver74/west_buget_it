import { useMemo } from 'react'
import { Drawer, Spin, Empty, Card, Row, Col, Statistic, Typography, Divider } from 'antd'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import {
  TrophyOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

interface EmployeeKpiTrendChartProps {
  employeeId: number
  employeeName: string
  year: number
  open: boolean
  onClose: () => void
}

const MONTH_NAMES = [
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

const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#f5222d',
  purple: '#722ed1',
  cyan: '#13c2c2',
}

export const EmployeeKpiTrendChart = ({
  employeeId,
  employeeName,
  year,
  open,
  onClose,
}: EmployeeKpiTrendChartProps) => {
  // Fetch KPI trends for employee
  const { data: trendsData, isLoading } = useQuery({
    queryKey: ['kpi-trends', employeeId, year],
    queryFn: () =>
      kpiApi.getKpiTrends({
        year,
        employee_id: employeeId,
      }),
    enabled: open && !!employeeId,
  })

  // Prepare chart data with month names
  const chartData = useMemo(() => {
    if (!trendsData || trendsData.length === 0) return []

    return trendsData.map((item) => ({
      ...item,
      month_name: MONTH_NAMES[item.month - 1],
    }))
  }, [trendsData])

  // Calculate statistics
  const statistics = useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return {
        avgKpi: 0,
        maxKpi: 0,
        minKpi: 0,
        totalBonus: 0,
        trend: 0,
      }
    }

    const kpiValues = chartData.map((d) => d.avg_kpi).filter((v) => v > 0)
    const avgKpi = kpiValues.length > 0 ? kpiValues.reduce((a, b) => a + b, 0) / kpiValues.length : 0
    const maxKpi = Math.max(...kpiValues, 0)
    const minKpi = kpiValues.length > 0 ? Math.min(...kpiValues) : 0
    const totalBonus = chartData.reduce((sum, item) => sum + item.total_bonus, 0)

    // Calculate trend (first vs last month)
    const firstKpi = chartData[0]?.avg_kpi || 0
    const lastKpi = chartData[chartData.length - 1]?.avg_kpi || 0
    const trend = lastKpi - firstKpi

    return {
      avgKpi: Number(avgKpi.toFixed(2)),
      maxKpi: Number(maxKpi.toFixed(2)),
      minKpi: Number(minKpi.toFixed(2)),
      totalBonus: Number(totalBonus.toFixed(2)),
      trend: Number(trend.toFixed(2)),
    }
  }, [chartData])

  return (
    <Drawer
      title={
        <div>
          <Title level={4} style={{ margin: 0 }}>
            Динамика КПИ: {employeeName}
          </Title>
          <Text type="secondary">Год: {year}</Text>
        </div>
      }
      placement="right"
      width={900}
      open={open}
      onClose={onClose}
      destroyOnHidden
    >
      {isLoading ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 400,
          }}
        >
          <Spin size="large" tip="Загрузка данных...">
            <div style={{ minHeight: 200 }} />
          </Spin>
        </div>
      ) : !chartData || chartData.length === 0 ? (
        <Empty
          description="Нет данных по КПИ за этот год"
          style={{ marginTop: 100 }}
        />
      ) : (
        <div>
          {/* Статистика */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Средний KPI%"
                  value={statistics.avgKpi}
                  precision={2}
                  suffix="%"
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: COLORS.primary, fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Максимум"
                  value={statistics.maxKpi}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: COLORS.success, fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Минимум"
                  value={statistics.minKpi}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: COLORS.warning, fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Всего бонусов"
                  value={statistics.totalBonus}
                  precision={2}
                  suffix="₽"
                  prefix={<DollarOutlined />}
                  valueStyle={{ color: COLORS.success, fontSize: 20 }}
                />
              </Card>
            </Col>
          </Row>

          {/* Тренд */}
          <Card style={{ marginBottom: 24 }}>
            <Row align="middle">
              <Col>
                <Text strong>Тренд (первый → последний месяц): </Text>
              </Col>
              <Col>
                <Statistic
                  value={Math.abs(statistics.trend)}
                  precision={2}
                  suffix="%"
                  prefix={
                    statistics.trend >= 0 ? (
                      <RiseOutlined style={{ color: COLORS.success }} />
                    ) : (
                      <FallOutlined style={{ color: COLORS.error }} />
                    )
                  }
                  valueStyle={{
                    color: statistics.trend >= 0 ? COLORS.success : COLORS.error,
                    fontSize: 18,
                  }}
                />
              </Col>
            </Row>
          </Card>

          <Divider />

          {/* График KPI% по месяцам (Area Chart) */}
          <Card
            title="Динамика KPI% по месяцам"
            style={{ marginBottom: 24 }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorKpi" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)}%`}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="avg_kpi"
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorKpi)"
                  name="KPI%"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          {/* График бонусов по месяцам (Bar Chart) */}
          <Card
            title="Бонусы по месяцам"
            style={{ marginBottom: 24 }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)} ₽`}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Bar
                  dataKey="total_bonus"
                  fill={COLORS.success}
                  name="Сумма бонусов"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Комбинированный график (KPI% + Бонусы) */}
          <Card title="KPI% и Бонусы: сводный график">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === 'KPI%') return `${value.toFixed(2)}%`
                    return `${value.toFixed(2)} ₽`
                  }}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="avg_kpi"
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  name="KPI%"
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
          </Card>
        </div>
      )}
    </Drawer>
  )
}
