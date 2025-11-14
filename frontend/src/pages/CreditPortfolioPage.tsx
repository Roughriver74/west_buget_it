import { useState } from 'react'
import { Card, Row, Col, Statistic, Table, DatePicker, Button, Space, Spin } from 'antd'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  BankOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

export default function CreditPortfolioPage() {
  const { selectedDepartment } = useDepartment()
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null)

  // Summary statistics
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['credit-portfolio-summary', selectedDepartment?.id, dateRange],
    queryFn: () =>
      creditPortfolioApi.getSummary({
        department_id: selectedDepartment?.id,
        date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
      }),
    enabled: !!selectedDepartment,
  })

  // Monthly statistics
  const { data: monthlyStats, isLoading: monthlyLoading } = useQuery({
    queryKey: ['credit-portfolio-monthly', selectedDepartment?.id],
    queryFn: () =>
      creditPortfolioApi.getMonthlyStats({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Recent receipts
  const { data: receipts, isLoading: receiptsLoading } = useQuery({
    queryKey: ['credit-receipts', selectedDepartment?.id, dateRange],
    queryFn: () =>
      creditPortfolioApi.getReceipts({
        department_id: selectedDepartment?.id,
        date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
        limit: 10,
      }),
    enabled: !!selectedDepartment,
  })

  // Recent expenses
  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['credit-expenses', selectedDepartment?.id, dateRange],
    queryFn: () =>
      creditPortfolioApi.getExpenses({
        department_id: selectedDepartment?.id,
        date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
        date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
        limit: 10,
      }),
    enabled: !!selectedDepartment,
  })

  const receiptColumns = [
    {
      title: 'Дата',
      dataIndex: 'document_date',
      key: 'document_date',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Плательщик',
      dataIndex: 'payer',
      key: 'payer',
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `${amount.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Назначение',
      dataIndex: 'payment_purpose',
      key: 'payment_purpose',
      ellipsis: true,
    },
  ]

  const expenseColumns = [
    {
      title: 'Дата',
      dataIndex: 'document_date',
      key: 'document_date',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Получатель',
      dataIndex: 'recipient',
      key: 'recipient',
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `${amount.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Назначение',
      dataIndex: 'payment_purpose',
      key: 'payment_purpose',
      ellipsis: true,
    },
  ]

  const monthlyColumns = [
    {
      title: 'Месяц',
      dataIndex: 'month',
      key: 'month',
    },
    {
      title: 'Поступления',
      dataIndex: 'receipts',
      key: 'receipts',
      render: (amount: number) => `${amount.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Списания',
      dataIndex: 'expenses',
      key: 'expenses',
      render: (amount: number) => `${amount.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Чистый остаток',
      dataIndex: 'net',
      key: 'net',
      render: (amount: number) => (
        <span style={{ color: amount >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {amount.toLocaleString('ru-RU')} ₽
        </span>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>Кредитный портфель - Аналитика</h1>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
            placeholder={['Дата от', 'Дата до']}
          />
          <Button icon={<ReloadOutlined />} onClick={() => setDateRange(null)}>
            Сбросить
          </Button>
        </Space>
      </div>

      {/* Summary Cards */}
      {summaryLoading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Всего поступлений"
                  value={summary?.total_receipts || 0}
                  precision={2}
                  prefix={<RiseOutlined />}
                  suffix="₽"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Всего списаний"
                  value={summary?.total_expenses || 0}
                  precision={2}
                  prefix={<FallOutlined />}
                  suffix="₽"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Чистый баланс"
                  value={summary?.net_balance || 0}
                  precision={2}
                  prefix={<DollarOutlined />}
                  suffix="₽"
                  valueStyle={{ color: (summary?.net_balance || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Активных договоров"
                  value={summary?.active_contracts_count || 0}
                  prefix={<FileTextOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12}>
              <Card>
                <Statistic
                  title="Всего процентов"
                  value={summary?.total_interest || 0}
                  precision={2}
                  suffix="₽"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12}>
              <Card>
                <Statistic
                  title="Всего тела кредита"
                  value={summary?.total_principal || 0}
                  precision={2}
                  suffix="₽"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Monthly Statistics */}
          <Card
            title="Помесячная динамика"
            style={{ marginBottom: 24 }}
            loading={monthlyLoading}
          >
            <Table
              columns={monthlyColumns}
              dataSource={monthlyStats || []}
              pagination={false}
              size="small"
              rowKey="month"
            />
          </Card>

          {/* Recent Receipts */}
          <Card
            title="Последние поступления"
            extra={<BankOutlined />}
            style={{ marginBottom: 24 }}
            loading={receiptsLoading}
          >
            <Table
              columns={receiptColumns}
              dataSource={receipts || []}
              pagination={false}
              size="small"
              rowKey="id"
            />
          </Card>

          {/* Recent Expenses */}
          <Card
            title="Последние списания"
            extra={<BankOutlined />}
            loading={expensesLoading}
          >
            <Table
              columns={expenseColumns}
              dataSource={expenses || []}
              pagination={false}
              size="small"
              rowKey="id"
            />
          </Card>
        </>
      )}
    </div>
  )
}
