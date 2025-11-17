import { useState } from 'react'
import { Card, Row, Col, Statistic, Table, Empty, Spin, Tag } from 'antd'
import {
  TrophyOutlined,
  PercentageOutlined,
  RiseOutlined,
  BankOutlined,
} from '@ant-design/icons'
import {
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import ExportButton from '@/legacy/components/ExportButton'
import CreditPortfolioFilters, {
  type CreditPortfolioFilterValues,
} from '@/components/bank/CreditPortfolioFilters'

export default function CreditPortfolioAnalyticsPage() {
  const { selectedDepartment } = useDepartment()
  const [filters, setFilters] = useState<CreditPortfolioFilterValues>({})

  // Fetch summary for KPI metrics
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['credit-portfolio-summary', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getSummary({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      }),
    enabled: !!selectedDepartment,
  })

  // Fetch monthly efficiency
  const { data: monthlyEfficiency, isLoading: monthlyLoading } = useQuery({
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

  // Fetch organization efficiency
  const { data: orgEfficiency, isLoading: orgLoading } = useQuery({
    queryKey: ['credit-portfolio-org-efficiency', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getOrgEfficiency({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        organization_id: filters.organizationIds?.[0],
      }),
    enabled: !!selectedDepartment,
  })

  const isLoading = summaryLoading || monthlyLoading || orgLoading

  if (isLoading) {
    return (
      <div
        style={{
          padding: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
        }}
      >
        <Spin size='large' tip='Загрузка аналитики...'>
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  if (!summary) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 24 }}>
          Кредитный портфель - Расширенная аналитика
        </h1>
        <Empty description='Нет данных' />
      </div>
    )
  }

  // Calculate KPI metrics
  const avgInterestRate =
    summary.total_expenses > 0
      ? ((summary.total_interest / summary.total_expenses) * 100).toFixed(2)
      : '0.00'

  const repaymentVelocity =
    summary.total_receipts > 0
      ? ((summary.total_expenses / summary.total_receipts) * 100).toFixed(1)
      : '0.0'

  const activeContracts = summary.active_contracts_count || 0

  const debtRatio =
    summary.total_receipts > 0
      ? ((summary.total_expenses / summary.total_receipts) * 100).toFixed(2)
      : '0.00'

  // Format monthly efficiency data for chart
  const monthlyChartData =
    monthlyEfficiency?.map((item: any) => ({
      month: item.month,
      principal: item.principal || 0,
      interest: item.interest || 0,
      efficiency:
        item.principal + item.interest > 0
          ? ((item.principal / (item.principal + item.interest)) * 100).toFixed(
              1
            )
          : 0,
    })) || []

  // Organization efficiency table columns
  const orgColumns = [
    {
      title: 'Организация',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Получено',
      dataIndex: 'received',
      key: 'received',
      render: (value: number) => (
        <span style={{ color: '#52c41a' }}>
          {value.toLocaleString('ru-RU')} ₽
        </span>
      ),
      sorter: (a: any, b: any) => a.received - b.received,
    },
    {
      title: 'Погашено тела',
      dataIndex: 'principal',
      key: 'principal',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
      sorter: (a: any, b: any) => a.principal - b.principal,
    },
    {
      title: 'Уплачено %',
      dataIndex: 'interest',
      key: 'interest',
      render: (value: number) => `${value.toLocaleString('ru-RU')} ₽`,
      sorter: (a: any, b: any) => a.interest - b.interest,
    },
    {
      title: 'Всего выплачено',
      key: 'total',
      render: (_: any, record: any) => {
        const total = (record.principal || 0) + (record.interest || 0)
        return `${total.toLocaleString('ru-RU')} ₽`
      },
      sorter: (a: any, b: any) =>
        a.principal + a.interest - (b.principal + b.interest),
    },
    {
      title: 'Эффективность',
      key: 'efficiency',
      render: (_: any, record: any) => {
        const total = (record.principal || 0) + (record.interest || 0)
        const efficiency =
          total > 0 ? ((record.principal / total) * 100).toFixed(1) : '0.0'
        const effNum = parseFloat(efficiency)

        return (
          <Tag color={effNum > 70 ? 'green' : effNum > 50 ? 'orange' : 'red'}>
            {efficiency}%
          </Tag>
        )
      },
      sorter: (a: any, b: any) => {
        const aEff =
          a.principal + a.interest > 0
            ? (a.principal / (a.principal + a.interest)) * 100
            : 0
        const bEff =
          b.principal + b.interest > 0
            ? (b.principal / (b.principal + b.interest)) * 100
            : 0
        return aEff - bEff
      },
    },
  ]

  const dateTickFormatter = (value: string) => {
    if (!value) return ''
    const [year, month] = value.split('-')
    const months = [
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
    return `${months[parseInt(month) - 1]} '${year.slice(-2)}`
  }

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 style={{ margin: 0 }}>
          Кредитный портфель - Расширенная аналитика
        </h1>
        <ExportButton
          targetId='analytics-content'
          fileName='credit-analytics'
          data={orgEfficiency || []}
        />
      </div>

      {/* Filters */}
      <CreditPortfolioFilters
        onFilterChange={setFilters}
        initialValues={filters}
      />

      <div id='analytics-content'>

      {/* KPI Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title='Средняя доля процентов'
              value={avgInterestRate}
              precision={2}
              suffix='%'
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Отношение процентов к общей сумме выплат
            </p>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title='Скорость погашения'
              value={repaymentVelocity}
              precision={1}
              suffix='%'
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Отношение списаний к поступлениям
            </p>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title='Активных договоров'
              value={activeContracts}
              prefix={<TrophyOutlined />}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Количество действующих кредитных договоров
            </p>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title='Коэффициент долга'
              value={debtRatio}
              precision={2}
              suffix='%'
              prefix={<BankOutlined />}
              valueStyle={{
                color: parseFloat(debtRatio) > 100 ? '#cf1322' : '#3f8600',
              }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Списания относительно поступлений
            </p>
          </Card>
        </Col>
      </Row>

      {/* Monthly Efficiency Chart */}
      <Card
        title='Помесячная эффективность погашения'
        style={{ marginBottom: 24 }}
      >
        <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
          Соотношение тела кредита и процентов по месяцам
        </p>
        <ResponsiveContainer width='100%' height={400}>
          <ComposedChart data={monthlyChartData}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis dataKey='month' tickFormatter={dateTickFormatter} />
            <YAxis
              yAxisId='left'
              tickFormatter={value => `${(value / 1000000).toFixed(1)}M`}
            />
            <YAxis
              yAxisId='right'
              orientation='right'
              tickFormatter={value => `${value}%`}
            />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (name === 'Эффективность') {
                  return `${value}%`
                }
                return `${Number(value).toLocaleString('ru-RU')} ₽`
              }}
            />
            <Legend />
            <Bar
              yAxisId='left'
              dataKey='principal'
              name='Погашено тела'
              fill='#10B981'
            />
            <Bar
              yAxisId='left'
              dataKey='interest'
              name='Уплачено %'
              fill='#F59E0B'
            />
            <Line
              yAxisId='right'
              type='monotone'
              dataKey='efficiency'
              name='Эффективность'
              stroke='#3B82F6'
              strokeWidth={2}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      {/* Organization Efficiency Table */}
      <Card title='Эффективность по организациям'>
        <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
          Детализация платежей и эффективности погашения по организациям
        </p>
        {!orgEfficiency || orgEfficiency.length === 0 ? (
          <Empty description='Нет данных по организациям' />
        ) : (
          <Table
            columns={orgColumns}
            dataSource={orgEfficiency}
            rowKey={(record: any, index) =>
              record.organization || record.name || index
            }
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>

      {/* Explanation Card */}
      <Card style={{ marginTop: 24 }} title='Расшифровка показателей'>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <h4>Средняя доля процентов</h4>
            <p>
              Показывает какой процент от общих выплат составляют проценты.
              Высокое значение указывает на высокую стоимость обслуживания
              долга.
            </p>
          </Col>
          <Col span={24}>
            <h4>Скорость погашения</h4>
            <p>
              Показывает как быстро погашается долг относительно полученных
              средств. Значение близкое к 100% означает равномерное погашение.
            </p>
          </Col>
          <Col span={24}>
            <h4>Эффективность погашения</h4>
            <p>
              Рассчитывается как отношение погашения тела кредита к общей сумме
              платежей. Высокая эффективность (&gt;70%) означает, что большая
              часть платежей идет на погашение основного долга, а не на
              проценты.
            </p>
          </Col>
        </Row>
      </Card>
      </div>
    </div>
  )
}
