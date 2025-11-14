import { Card, Table, Empty, Spin } from 'antd'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import type { MonthlyStats } from '@/api/creditPortfolio'

export default function CreditPortfolioCashFlowPage() {
  const { selectedDepartment } = useDepartment()

  const { data: monthlyStats, isLoading } = useQuery({
    queryKey: ['credit-portfolio-monthly', selectedDepartment?.id],
    queryFn: () =>
      creditPortfolioApi.getMonthlyStats({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  if (isLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!monthlyStats || monthlyStats.length === 0) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 24 }}>Кредитный портфель - Денежные потоки</h1>
        <Empty description="Нет данных" />
      </div>
    )
  }

  // Prepare chart data with cumulative balance
  let cumulativeBalance = 0
  const chartData = monthlyStats.map((stat) => {
    cumulativeBalance += stat.net
    return {
      month: stat.month,
      receipts: stat.receipts,
      expenses: stat.expenses,
      net: stat.net,
      cumulative: cumulativeBalance,
    }
  })

  const tableColumns = [
    {
      title: 'Месяц',
      dataIndex: 'month',
      key: 'month',
    },
    {
      title: 'Поступления',
      dataIndex: 'receipts',
      key: 'receipts',
      render: (value: number) => (
        <span style={{ color: '#52c41a' }}>
          {value.toLocaleString('ru-RU')} ₽
        </span>
      ),
    },
    {
      title: 'Списания',
      dataIndex: 'expenses',
      key: 'expenses',
      render: (value: number) => (
        <span style={{ color: '#ff4d4f' }}>
          {value.toLocaleString('ru-RU')} ₽
        </span>
      ),
    },
    {
      title: 'Чистый поток',
      dataIndex: 'net',
      key: 'net',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          {value >= 0 ? '+' : ''}
          {value.toLocaleString('ru-RU')} ₽
        </span>
      ),
    },
  ]

  // Calculate totals
  const totalReceipts = chartData.reduce((sum, item) => sum + item.receipts, 0)
  const totalExpenses = chartData.reduce((sum, item) => sum + item.expenses, 0)
  const totalNet = totalReceipts - totalExpenses

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>Кредитный портфель - Денежные потоки</h1>

      {/* Summary Cards */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 14, color: '#8c8c8c' }}>Всего поступлений</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
              {totalReceipts.toLocaleString('ru-RU')} ₽
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 14, color: '#8c8c8c' }}>Всего списаний</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
              {totalExpenses.toLocaleString('ru-RU')} ₽
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 14, color: '#8c8c8c' }}>Чистый поток</div>
            <div
              style={{
                fontSize: 24,
                fontWeight: 'bold',
                color: totalNet >= 0 ? '#52c41a' : '#ff4d4f',
              }}
            >
              {totalNet >= 0 ? '+' : ''}
              {totalNet.toLocaleString('ru-RU')} ₽
            </div>
          </div>
        </div>
      </Card>

      {/* Monthly Flow Chart */}
      <Card title="Помесячная динамика" style={{ marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis
              tickFormatter={(value) =>
                `${(value / 1000000).toFixed(1)}M`
              }
            />
            <Tooltip
              formatter={(value: number) => `${value.toLocaleString('ru-RU')} ₽`}
            />
            <Legend />
            <Bar dataKey="receipts" name="Поступления" fill="#52c41a" />
            <Bar dataKey="expenses" name="Списания" fill="#ff4d4f" />
            <Line
              type="monotone"
              dataKey="net"
              name="Чистый поток"
              stroke="#1890ff"
              strokeWidth={2}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      {/* Cumulative Balance Chart */}
      <Card title="Накопительный баланс" style={{ marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis
              tickFormatter={(value) =>
                `${(value / 1000000).toFixed(1)}M`
              }
            />
            <Tooltip
              formatter={(value: number) => `${value.toLocaleString('ru-RU')} ₽`}
            />
            <Legend />
            <Bar
              dataKey="cumulative"
              name="Накопительный баланс"
              fill="#722ed1"
            />
            <Line
              type="monotone"
              dataKey="cumulative"
              stroke="#722ed1"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>

      {/* Monthly Table */}
      <Card title="Детализация по месяцам">
        <Table
          columns={tableColumns}
          dataSource={chartData}
          pagination={false}
          rowKey="month"
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row>
                <Table.Summary.Cell index={0}>
                  <strong>ИТОГО</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={1}>
                  <strong style={{ color: '#52c41a' }}>
                    {totalReceipts.toLocaleString('ru-RU')} ₽
                  </strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2}>
                  <strong style={{ color: '#ff4d4f' }}>
                    {totalExpenses.toLocaleString('ru-RU')} ₽
                  </strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3}>
                  <strong style={{ color: totalNet >= 0 ? '#52c41a' : '#ff4d4f' }}>
                    {totalNet >= 0 ? '+' : ''}
                    {totalNet.toLocaleString('ru-RU')} ₽
                  </strong>
                </Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </Card>
    </div>
  )
}
