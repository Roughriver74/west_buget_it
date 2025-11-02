/**
 * БДР (Бюджет доходов и расходов) - Budget Income Statement
 *
 * Comprehensive financial report showing:
 * - Revenue (planned vs actual)
 * - Expenses (planned vs actual)
 * - Profit (Revenue - Expenses)
 * - Profitability metrics (ROI, Profit Margin)
 * - Monthly breakdown
 * - Category breakdown
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
} from 'recharts'
import { analyticsApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs from 'dayjs'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  PercentageOutlined,
} from '@ant-design/icons'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import ExportButton from '@/components/common/ExportButton'
import { generateExportFilename } from '@/utils/downloadUtils'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

// Type definitions (matching backend schemas)
interface BudgetIncomeStatementMonthly {
  month: number
  month_name: string
  revenue_planned: number
  revenue_actual: number
  expenses_planned: number
  expenses_actual: number
  profit_planned: number
  profit_actual: number
  profit_margin_planned: number
  profit_margin_actual: number
}

interface BudgetIncomeStatementCategory {
  category_id: number
  category_name: string
  category_type: string
  planned: number
  actual: number
  difference: number
  execution_percent: number
}

interface BudgetIncomeStatement {
  year: number
  department_id?: number
  department_name?: string
  revenue_planned: number
  revenue_actual: number
  revenue_difference: number
  revenue_execution_percent: number
  expenses_planned: number
  expenses_actual: number
  expenses_difference: number
  expenses_execution_percent: number
  profit_planned: number
  profit_actual: number
  profit_difference: number
  profit_margin_planned: number
  profit_margin_actual: number
  roi_planned: number
  roi_actual: number
  by_month: BudgetIncomeStatementMonthly[]
  revenue_by_category?: BudgetIncomeStatementCategory[]
  expenses_by_category?: BudgetIncomeStatementCategory[]
}

// Chart data types
interface MonthlyChartData {
  month: string
  'Доходы (план)': number
  'Доходы (факт)': number
  'Расходы (план)': number
  'Расходы (факт)': number
  'Прибыль (план)': number
  'Прибыль (факт)': number
}

const BudgetIncomeStatementPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const { selectedDepartment } = useDepartment()

  // Fetch БДР data
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<BudgetIncomeStatement>({
    queryKey: ['budget-income-statement', year, selectedDepartment?.id],
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

  // Prepare chart data
  const monthlyChartData: MonthlyChartData[] = data.by_month.map((item) => ({
    month: item.month_name,
    'Доходы (план)': item.revenue_planned,
    'Доходы (факт)': item.revenue_actual,
    'Расходы (план)': item.expenses_planned,
    'Расходы (факт)': item.expenses_actual,
    'Прибыль (план)': item.profit_planned,
    'Прибыль (факт)': item.profit_actual,
  }))

  // Monthly table columns
  const monthlyColumns = [
    {
      title: 'Месяц',
      dataIndex: 'month_name',
      key: 'month_name',
      width: 100,
      fixed: 'left' as const,
    },
    {
      title: 'Доходы (план)',
      dataIndex: 'revenue_planned',
      key: 'revenue_planned',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Доходы (факт)',
      dataIndex: 'revenue_actual',
      key: 'revenue_actual',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Расходы (план)',
      dataIndex: 'expenses_planned',
      key: 'expenses_planned',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Расходы (факт)',
      dataIndex: 'expenses_actual',
      key: 'expenses_actual',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Прибыль (план)',
      dataIndex: 'profit_planned',
      key: 'profit_planned',
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Прибыль (факт)',
      dataIndex: 'profit_actual',
      key: 'profit_actual',
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Рентабельность (план)',
      dataIndex: 'profit_margin_planned',
      key: 'profit_margin_planned',
      align: 'right' as const,
      render: (value: number) => formatPercent(value),
    },
    {
      title: 'Рентабельность (факт)',
      dataIndex: 'profit_margin_actual',
      key: 'profit_margin_actual',
      align: 'right' as const,
      render: (value: number) => formatPercent(value),
    },
  ]

  // Category columns
  const categoryColumns = [
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 200,
    },
    {
      title: 'Тип',
      dataIndex: 'category_type',
      key: 'category_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'revenue' ? 'green' : 'blue'}>
          {type === 'revenue' ? 'Доход' : 'Расход'}
        </Tag>
      ),
    },
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Факт',
      dataIndex: 'actual',
      key: 'actual',
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Отклонение',
      dataIndex: 'difference',
      key: 'difference',
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Исполнение',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      align: 'right' as const,
      render: (value: number) => formatPercent(value),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>БДР (Бюджет доходов и расходов)</Title>
        <Paragraph>
          Комплексный финансовый отчет, показывающий доходы, расходы, прибыль и показатели
          рентабельности.
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
                  exportFn={() => analyticsApi.exportBudgetIncomeStatement({
                    year,
                    department_id: selectedDepartment?.id
                  })}
                  filename={generateExportFilename('BDR', year)}
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
              title="Доходы (план)"
              value={data.revenue_planned}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Факт: </Text>
              <Text strong>{formatCurrency(data.revenue_actual)}</Text>
              <div>
                <Text type="secondary">Исполнение: </Text>
                <Text>{formatPercent(data.revenue_execution_percent)}</Text>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Расходы (план)"
              value={data.expenses_planned}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<FallOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Факт: </Text>
              <Text strong>{formatCurrency(data.expenses_actual)}</Text>
              <div>
                <Text type="secondary">Исполнение: </Text>
                <Text>{formatPercent(data.expenses_execution_percent)}</Text>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Прибыль (план)"
              value={data.profit_planned}
              precision={0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={
                data.profit_planned >= 0 ? (
                  <RiseOutlined style={{ color: '#1890ff' }} />
                ) : (
                  <FallOutlined style={{ color: '#ff4d4f' }} />
                )
              }
              valueStyle={{
                color: data.profit_planned >= 0 ? '#1890ff' : '#ff4d4f',
              }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Факт: </Text>
              <Text
                strong
                style={{ color: data.profit_actual >= 0 ? '#52c41a' : '#ff4d4f' }}
              >
                {formatCurrency(data.profit_actual)}
              </Text>
              <div>
                <Text type="secondary">Отклонение: </Text>
                <Text
                  style={{
                    color: data.profit_difference >= 0 ? '#52c41a' : '#ff4d4f',
                  }}
                >
                  {formatCurrency(data.profit_difference)}
                </Text>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Рентабельность (план)"
              value={data.profit_margin_planned}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Факт: </Text>
              <Text strong>{formatPercent(data.profit_margin_actual)}</Text>
              <div>
                <Text type="secondary">ROI (план): </Text>
                <Text>{formatPercent(data.roi_planned)}</Text>
              </div>
              <div>
                <Text type="secondary">ROI (факт): </Text>
                <Text>{formatPercent(data.roi_actual)}</Text>
              </div>
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
                <Col xs={24}>
                  <Card title="Динамика доходов, расходов и прибыли">
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={monthlyChartData}>
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
                          dataKey="Доходы (план)"
                          stroke="#b7eb8f"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                        />
                        <Line
                          type="monotone"
                          dataKey="Доходы (факт)"
                          stroke="#52c41a"
                          strokeWidth={3}
                        />
                        <Line
                          type="monotone"
                          dataKey="Расходы (план)"
                          stroke="#ff9c6e"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                        />
                        <Line
                          type="monotone"
                          dataKey="Расходы (факт)"
                          stroke="#ff4d4f"
                          strokeWidth={3}
                        />
                        <Line
                          type="monotone"
                          dataKey="Прибыль (план)"
                          stroke="#91d5ff"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                        />
                        <Line
                          type="monotone"
                          dataKey="Прибыль (факт)"
                          stroke="#1890ff"
                          strokeWidth={3}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24}>
                  <Card title="Сравнение план vs факт">
                    <ResponsiveContainer width="100%" height={400}>
                      <ComposedChart data={monthlyChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Bar dataKey="Доходы (план)" fill="#b7eb8f" />
                        <Bar dataKey="Доходы (факт)" fill="#52c41a" />
                        <Bar dataKey="Расходы (план)" fill="#ff9c6e" />
                        <Bar dataKey="Расходы (факт)" fill="#ff4d4f" />
                        <Line
                          type="monotone"
                          dataKey="Прибыль (факт)"
                          stroke="#1890ff"
                          strokeWidth={3}
                        />
                      </ComposedChart>
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
                <Table
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
            key: 'revenue',
            label: 'Доходы по категориям',
            children: data.revenue_by_category && data.revenue_by_category.length > 0 ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Структура доходов">
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={data.revenue_by_category}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="category_name" angle={-45} textAnchor="end" height={100} />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Bar dataKey="planned" name="План" fill="#b7eb8f" />
                        <Bar dataKey="actual" name="Факт" fill="#52c41a" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Детализация доходов">
                    <Table
                      dataSource={data.revenue_by_category}
                      columns={categoryColumns}
                      rowKey="category_id"
                      pagination={false}
                      scroll={{ x: 800 }}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card>
                <Text type="secondary">Нет данных по категориям доходов</Text>
              </Card>
            ),
          },
          {
            key: 'expenses',
            label: 'Расходы по категориям',
            children: data.expenses_by_category && data.expenses_by_category.length > 0 ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Структура расходов">
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={data.expenses_by_category}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="category_name" angle={-45} textAnchor="end" height={100} />
                        <YAxis tickFormatter={(value) => formatNumber(value)} />
                        <Tooltip
                          formatter={(value: number) => formatCurrency(value)}
                          labelStyle={{ color: '#000' }}
                        />
                        <Legend />
                        <Bar dataKey="planned" name="План" fill="#ff9c6e" />
                        <Bar dataKey="actual" name="Факт" fill="#ff4d4f" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Детализация расходов">
                    <Table
                      dataSource={data.expenses_by_category}
                      columns={categoryColumns}
                      rowKey="category_id"
                      pagination={false}
                      scroll={{ x: 800 }}
                    />
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card>
                <Text type="secondary">Нет данных по категориям расходов</Text>
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}

export default BudgetIncomeStatementPage
