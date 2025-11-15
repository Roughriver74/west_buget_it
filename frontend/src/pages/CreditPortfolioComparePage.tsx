import { useState } from 'react'
import { Card, Radio, Empty, Spin, Table, Tag } from 'antd'
import {
  BarChart,
  Bar,
  Line,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import CreditPortfolioFilters, {
  type CreditPortfolioFilterValues,
} from '@/components/bank/CreditPortfolioFilters'

type PeriodType = 'yearly' | 'quarterly'

interface YearlyData {
  year: string
  received: number
  principal: number
  interest: number
  paid: number
  totalPaid: number
}

interface QuarterlyData {
  quarter: string
  principal: number
  interest: number
}

interface YoYGrowth {
  year: string
  receivedGrowth: number
  principalGrowth: number
  interestGrowth: number
}

export default function CreditPortfolioComparePage() {
  const { selectedDepartment } = useDepartment()
  const [comparisonPeriod, setComparisonPeriod] = useState<PeriodType>('yearly')
  const [filters, setFilters] = useState<CreditPortfolioFilterValues>({})

  // Fetch yearly comparison data
  const { data: yearlyData, isLoading: yearlyLoading } = useQuery({
    queryKey: ['credit-portfolio-yearly-comparison', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getYearlyComparison({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch monthly efficiency for quarterly breakdown
  const { data: monthlyData, isLoading: monthlyLoading } = useQuery({
    queryKey: ['credit-portfolio-monthly-efficiency', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getMonthlyEfficiency({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        organization_id: filters.organizationIds?.[0],
        bank_account_id: filters.bankAccountIds?.[0],
      }),
    enabled: !!selectedDepartment,
  })

  const isLoading = yearlyLoading || monthlyLoading

  if (isLoading) {
    return (
      <div style={{ padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <Spin size="large" tip="Загрузка данных...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  if (!yearlyData || yearlyData.length === 0) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 24 }}>Кредитный портфель - Сравнительный анализ</h1>
        <Empty description="Нет данных для сравнения" />
      </div>
    )
  }

  // Process yearly data
  const yearlyComparison: YearlyData[] = yearlyData.map((y: any) => ({
    year: y.year,
    received: y.received || 0,
    principal: y.principal || 0,
    interest: y.interest || 0,
    paid: y.paid || 0,
    totalPaid: (y.paid || 0),
  }))

  // Get quarterly comparison from monthly data
  const getQuarterlyComparison = (): QuarterlyData[] => {
    if (!monthlyData) return []

    const quarters: Record<string, QuarterlyData> = {}

    monthlyData.forEach((m: any) => {
      const [year, month] = m.month.split('-')
      const monthNum = parseInt(month)
      const quarter = `Q${Math.floor((monthNum - 1) / 3) + 1} ${year}`

      if (!quarters[quarter]) {
        quarters[quarter] = { quarter, principal: 0, interest: 0 }
      }
      quarters[quarter].principal += m.principal || 0
      quarters[quarter].interest += m.interest || 0
    })

    return Object.values(quarters)
      .sort((a, b) => a.quarter.localeCompare(b.quarter))
      .slice(-8)
  }

  // Calculate year-over-year growth
  const calculateYoYGrowth = (): YoYGrowth[] => {
    if (yearlyComparison.length < 2) return []

    const growth: YoYGrowth[] = []
    for (let i = 1; i < yearlyComparison.length; i++) {
      const current = yearlyComparison[i]
      const previous = yearlyComparison[i - 1]

      const receivedGrowth =
        previous.received > 0
          ? ((current.received - previous.received) / previous.received) * 100
          : 0

      const principalGrowth =
        previous.principal > 0
          ? ((current.principal - previous.principal) / previous.principal) * 100
          : 0

      const interestGrowth =
        previous.interest > 0
          ? ((current.interest - previous.interest) / previous.interest) * 100
          : 0

      growth.push({
        year: current.year,
        receivedGrowth,
        principalGrowth,
        interestGrowth,
      })
    }

    return growth
  }

  // Calculate period comparison metrics
  const getPeriodMetrics = () => {
    if (yearlyComparison.length < 2) {
      return {
        currentReceived: 0,
        previousReceived: 0,
        receivedChange: 0,
        currentPaid: 0,
        previousPaid: 0,
        paidChange: 0,
        currentYear: '',
        previousYear: '',
      }
    }

    const current = yearlyComparison[yearlyComparison.length - 1]
    const previous = yearlyComparison[yearlyComparison.length - 2]

    return {
      currentReceived: current.received,
      previousReceived: previous.received,
      receivedChange:
        previous.received > 0
          ? ((current.received - previous.received) / previous.received) * 100
          : 0,
      currentPaid: current.principal + current.interest,
      previousPaid: previous.principal + previous.interest,
      paidChange:
        previous.principal + previous.interest > 0
          ? ((current.principal + current.interest - previous.principal - previous.interest) /
              (previous.principal + previous.interest)) *
            100
          : 0,
      currentYear: current.year,
      previousYear: previous.year,
    }
  }

  const quarterlyData = getQuarterlyComparison()
  const yoyGrowth = calculateYoYGrowth()
  const metrics = getPeriodMetrics()

  // Table columns for detailed comparison
  const tableColumns = [
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Получено',
      dataIndex: 'received',
      key: 'received',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Погашено тела',
      dataIndex: 'principal',
      key: 'principal',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Уплачено %',
      dataIndex: 'interest',
      key: 'interest',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Всего выплачено',
      dataIndex: 'totalPaid',
      key: 'totalPaid',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Эффективность',
      key: 'efficiency',
      render: (_: any, record: YearlyData) => {
        const efficiency =
          record.principal + record.interest > 0
            ? (record.principal / (record.principal + record.interest)) * 100
            : 0

        return (
          <Tag
            color={
              efficiency > 70 ? 'green' : efficiency > 50 ? 'orange' : 'red'
            }
          >
            {efficiency.toFixed(1)}%
          </Tag>
        )
      },
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0 }}>Кредитный портфель - Сравнительный анализ</h1>
          <p style={{ color: '#8c8c8c', marginTop: 4 }}>
            Year-over-Year и Period-over-Period сравнение
          </p>
        </div>
        <Radio.Group
          value={comparisonPeriod}
          onChange={(e) => setComparisonPeriod(e.target.value)}
          buttonStyle="solid"
        >
          <Radio.Button value="yearly">По годам</Radio.Button>
          <Radio.Button value="quarterly">По кварталам</Radio.Button>
        </Radio.Group>
      </div>

      {/* Filters */}
      <CreditPortfolioFilters
        onFilterChange={setFilters}
        initialValues={filters}
      />

      {/* Comparison Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, color: '#8c8c8c' }}>Получено кредитов</div>
              <div style={{ fontSize: 28, fontWeight: 'bold', marginTop: 8 }}>
                {metrics.currentReceived.toLocaleString('ru-RU')} ₽
              </div>
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
              {metrics.currentYear} vs {metrics.previousYear}
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 8, fontStyle: 'italic' }}>
            Сумма поступлений (receipts) за год/период
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
            <span style={{ fontSize: 13, color: '#8c8c8c' }}>
              Было: {metrics.previousReceived.toLocaleString('ru-RU')} ₽
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 14, fontWeight: 600, color: metrics.receivedChange >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {metrics.receivedChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              {Math.abs(metrics.receivedChange).toFixed(1)}%
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, color: '#8c8c8c' }}>Выплачено</div>
              <div style={{ fontSize: 28, fontWeight: 'bold', marginTop: 8 }}>
                {metrics.currentPaid.toLocaleString('ru-RU')} ₽
              </div>
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
              {metrics.currentYear} vs {metrics.previousYear}
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 8, fontStyle: 'italic' }}>
            Сумма тела долга + проценты (expenses) за год/период
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
            <span style={{ fontSize: 13, color: '#8c8c8c' }}>
              Было: {metrics.previousPaid.toLocaleString('ru-RU')} ₽
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 14, fontWeight: 600, color: metrics.paidChange >= 0 ? '#52c41a' : '#ff4d4f' }}>
              {metrics.paidChange >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              {Math.abs(metrics.paidChange).toFixed(1)}%
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      {comparisonPeriod === 'yearly' && (
        <>
          {/* Yearly Comparison Chart */}
          <Card title="Сравнение по годам" style={{ marginBottom: 24 }}>
            <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
              Получено кредитов vs Выплачено
            </p>
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={yearlyComparison}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis
                  tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                />
                <Tooltip
                  formatter={(value: number) => `${value.toLocaleString('ru-RU')} ₽`}
                />
                <Legend />
                <Bar dataKey="received" name="Получено" fill="#3B82F6" />
                <Bar dataKey="principal" name="Погашено тела" fill="#10B981" />
                <Bar dataKey="interest" name="Уплачено %" fill="#F59E0B" />
                <Line
                  type="monotone"
                  dataKey="totalPaid"
                  name="Всего выплачено"
                  stroke="#EF4444"
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>

          {/* YoY Growth Chart */}
          <Card title="Темпы роста (Year-over-Year)" style={{ marginBottom: 24 }}>
            <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
              Процентное изменение относительно предыдущего года
            </p>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={yoyGrowth}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="receivedGrowth" name="Рост получений">
                  {yoyGrowth.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.receivedGrowth >= 0 ? '#10B981' : '#EF4444'}
                    />
                  ))}
                </Bar>
                <Bar dataKey="principalGrowth" name="Рост погашений">
                  {yoyGrowth.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.principalGrowth >= 0 ? '#3B82F6' : '#F59E0B'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}

      {/* Quarterly Comparison */}
      {comparisonPeriod === 'quarterly' && (
        <Card title="Сравнение по кварталам" style={{ marginBottom: 24 }}>
          <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
            Последние 8 кварталов
          </p>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={quarterlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
              <YAxis
                tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
              />
              <Tooltip
                formatter={(value: number) => `${value.toLocaleString('ru-RU')} ₽`}
              />
              <Legend />
              <Bar dataKey="principal" name="Погашено тела" fill="#10B981" />
              <Bar dataKey="interest" name="Уплачено %" fill="#F59E0B" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Summary Table */}
      <Card title="Детальное сравнение по годам">
        <Table
          columns={tableColumns}
          dataSource={yearlyComparison}
          rowKey="year"
          pagination={false}
        />
      </Card>
    </div>
  )
}
