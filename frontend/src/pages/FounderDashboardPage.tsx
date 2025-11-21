import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Col,
  Row,
  Statistic,
  Select,
  Alert,
  Table,
  Tag,
  Progress,
  Divider,
  Typography,
} from 'antd'
import {
  DollarOutlined,
  TeamOutlined,
  TrophyOutlined,
  BankOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import { founderDashboardApi } from '@/api/founderDashboard'
import {
  BarChart,
  Bar,
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
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Text } = Typography

const FounderDashboardPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState<number | undefined>(undefined)
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  const { data, isLoading, error } = useQuery({
    queryKey: ['founderDashboard', year, month],
    queryFn: () => founderDashboardApi.getDashboard({ year, month }),
  })

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  if (!data) {
    return null
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'overbudget':
        return 'error'
      case 'high_utilization':
        return 'warning'
      case 'low_utilization':
        return 'info'
      default:
        return 'info'
    }
  }

  const departmentColumns = [
    {
      title: 'Отдел',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 200,
      fixed: 'left' as const,
    },
    {
      title: 'Бюджет',
      dataIndex: 'budget_planned',
      key: 'budget_planned',
      render: (value: number) => formatCurrency(value),
      align: 'right' as const,
    },
    {
      title: 'Факт',
      dataIndex: 'budget_actual',
      key: 'budget_actual',
      render: (value: number) => formatCurrency(value),
      align: 'right' as const,
    },
    {
      title: 'Выполнение',
      dataIndex: 'budget_execution_percent',
      key: 'budget_execution_percent',
      render: (value: number) => (
        <Progress
          percent={value}
          size="small"
          status={value > 100 ? 'exception' : value >= 90 ? 'normal' : 'active'}
          format={(percent) => `${percent?.toFixed(1)}%`}
        />
      ),
      align: 'center' as const,
      width: 200,
    },
    {
      title: 'Сотрудники',
      dataIndex: 'employees_count',
      key: 'employees_count',
      align: 'center' as const,
    },
    {
      title: 'КПИ',
      dataIndex: 'avg_kpi_achievement',
      key: 'avg_kpi_achievement',
      render: (value: number | null) =>
        value !== null ? (
          <Tag color={value >= 100 ? 'success' : value >= 80 ? 'warning' : 'error'}>
            {formatPercent(value)}
          </Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
      align: 'center' as const,
    },
  ]

  return (
    <div>
      {/* Header with filters */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Title level={2}>
            <TrophyOutlined /> Дашборд учредителя
          </Title>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
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
        <Col xs={24} sm={12} md={8} lg={6}>
          <Select
            value={month}
            onChange={setMonth}
            allowClear
            placeholder="Все месяцы"
            style={{ width: '100%' }}
            options={[
              { value: 1, label: 'Январь' },
              { value: 2, label: 'Февраль' },
              { value: 3, label: 'Март' },
              { value: 4, label: 'Апрель' },
              { value: 5, label: 'Май' },
              { value: 6, label: 'Июнь' },
              { value: 7, label: 'Июль' },
              { value: 8, label: 'Август' },
              { value: 9, label: 'Сентябрь' },
              { value: 10, label: 'Октябрь' },
              { value: 11, label: 'Ноябрь' },
              { value: 12, label: 'Декабрь' },
            ]}
          />
        </Col>
      </Row>

      {/* Alerts */}
      {data.alerts.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {data.alerts.slice(0, 3).map((alert, index) => (
            <Col xs={24} key={index}>
              <Alert
                type={getAlertColor(alert.alert_type)}
                message={alert.message}
                description={`${alert.department_name}: ${formatCurrency(
                  alert.actual
                )} из ${formatCurrency(alert.planned)} (${formatPercent(alert.execution_percent)})`}
                showIcon
              />
            </Col>
          ))}
        </Row>
      )}

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Общий бюджет"
              value={data.company_summary.total_budget_planned}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<BankOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Фактические расходы"
              value={data.company_summary.total_budget_actual}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined />}
              valueStyle={{
                color:
                  data.company_summary.total_budget_execution_percent > 100 ? '#cf1322' : '#52c41a',
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Сотрудников"
              value={data.company_summary.total_employees}
              prefix={<TeamOutlined />}
            />
            <Text type="secondary">В {data.company_summary.departments_count} отделах</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Выполнение бюджета"
              value={data.company_summary.total_budget_execution_percent}
              precision={1}
              suffix="%"
              prefix={
                data.company_summary.total_budget_execution_percent > 100 ? (
                  <RiseOutlined />
                ) : (
                  <FallOutlined />
                )
              }
              valueStyle={{
                color:
                  data.company_summary.total_budget_execution_percent > 100 ? '#cf1322' : '#52c41a',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Expense Trends Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Динамика расходов по месяцам">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.expense_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" />
                <YAxis
                  tickFormatter={(value) =>
                    new Intl.NumberFormat('ru-RU', {
                      notation: 'compact',
                      compactDisplay: 'short',
                    }).format(value)
                  }
                />
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
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#52c41a"
                  name="Факт"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Department Performance Table */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Показатели по отделам">
            <ResponsiveTable
              columns={departmentColumns}
              dataSource={data.departments}
              rowKey="department_id"
              scroll={{ x: 1000 }}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>

      {/* Top Categories by Department */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Топ категории расходов по отделам">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.top_categories_by_department}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department_name" />
                <YAxis
                  tickFormatter={(value) =>
                    new Intl.NumberFormat('ru-RU', {
                      notation: 'compact',
                      compactDisplay: 'short',
                    }).format(value)
                  }
                />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  labelStyle={{ color: '#000' }}
                />
                <Legend />
                <Bar dataKey="amount" fill="#1890ff" name="Сумма расходов" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* KPI Overview */}
      {data.department_kpis.length > 0 && (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Обзор КПИ по отделам">
              <Row gutter={[16, 16]}>
                {data.department_kpis.map((kpi) => (
                  <Col xs={24} sm={12} lg={8} key={kpi.department_id}>
                    <Card size="small">
                      <Title level={5}>{kpi.department_name}</Title>
                      <Divider style={{ margin: '12px 0' }} />
                      <Row gutter={[8, 8]}>
                        <Col span={12}>
                          <Statistic
                            title="Средний КПИ"
                            value={kpi.avg_achievement}
                            precision={1}
                            suffix="%"
                            valueStyle={{
                              fontSize: 18,
                              color:
                                kpi.avg_achievement >= 100
                                  ? '#52c41a'
                                  : kpi.avg_achievement >= 80
                                  ? '#faad14'
                                  : '#f5222d',
                            }}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic
                            title="Охват"
                            value={kpi.coverage_percent}
                            precision={1}
                            suffix="%"
                            valueStyle={{ fontSize: 18 }}
                          />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {kpi.employees_with_kpi} из {kpi.total_employees}
                          </Text>
                        </Col>
                      </Row>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default FounderDashboardPage
