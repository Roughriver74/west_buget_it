import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Statistic, Select, Alert } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, DollarOutlined, WarningOutlined } from '@ant-design/icons'
import { analyticsApi } from '@/api'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ExpenseStatus } from '@/types'
import { getExpenseStatusLabel } from '@/utils/formatters'
import dayjs from 'dayjs'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

const DashboardPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState<number | undefined>(undefined)
  const { selectedDepartment } = useDepartment()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', year, month, selectedDepartment?.id],
    queryFn: () => analyticsApi.getDashboard({ year, month, department_id: selectedDepartment?.id }),
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

  return (
    <div>
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
        <Col span={6}>
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

      {/* Алерт при превышении бюджета */}
      {data.totals.remaining < 0 && (
        <Alert
          message={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <WarningOutlined />
              <span>Превышение бюджета!</span>
            </div>
          }
          description={
            <div>
              <div>Фактические расходы превышают план на: <strong style={{ color: '#ff4d4f' }}>{formatCurrency(Math.abs(data.totals.remaining))}</strong></div>
              <div style={{ marginTop: 4, fontSize: 12 }}>
                Процент исполнения: <strong>{data.totals.execution_percent.toFixed(2)}%</strong>
              </div>
            </div>
          }
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Предупреждение при приближении к лимиту (>90% исполнения) */}
      {data.totals.remaining >= 0 && data.totals.execution_percent > 90 && (
        <Alert
          message="Внимание: бюджет почти исчерпан"
          description={
            <div>
              <div>Исполнено: <strong>{data.totals.execution_percent.toFixed(2)}%</strong> от плана</div>
              <div>Остаток бюджета: <strong>{formatCurrency(data.totals.remaining)}</strong></div>
            </div>
          }
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Основные метрики */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic
              title="План"
              value={data.totals.planned}
              precision={0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<DollarOutlined />}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic
              title="Факт"
              value={data.totals.actual}
              precision={0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<DollarOutlined />}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic
              title="Остаток"
              value={data.totals.remaining}
              precision={0}
              valueStyle={{ color: data.totals.remaining >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={data.totals.remaining >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic
              title="Исполнение"
              value={data.totals.execution_percent}
              precision={2}
              valueStyle={{ color: '#1890ff' }}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* CAPEX vs OPEX */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card title="CAPEX vs OPEX" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'CAPEX', value: data.capex_vs_opex.capex },
                    { name: 'OPEX', value: data.capex_vs_opex.opex },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {[0, 1].map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} sm={12}>
          <Card title="Топ-5 категорий по расходам" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.top_categories}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category_name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Распределение по статусам */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="Распределение заявок по статусам" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.status_distribution.map(item => ({
                ...item,
                status: getExpenseStatusLabel(item.status as ExpenseStatus)
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                <Tooltip formatter={(value: number, name: string) =>
                  name === 'amount' ? formatCurrency(value) : value
                } />
                <Legend />
                <Bar yAxisId="left" dataKey="count" fill="#8884d8" name="Количество" />
                <Bar yAxisId="right" dataKey="amount" fill="#82ca9d" name="Сумма" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
