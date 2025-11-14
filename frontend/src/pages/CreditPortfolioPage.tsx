import { useState } from 'react'
import { Card, Row, Col, Statistic, Table, Spin, Button, message, Space, Modal } from 'antd'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  BankOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import CreditPortfolioFilters, {
  type CreditPortfolioFilterValues,
} from '@/components/bank/CreditPortfolioFilters'
import dayjs from 'dayjs'

export default function CreditPortfolioPage() {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<CreditPortfolioFilterValues>({})

  // Summary statistics
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
    queryKey: ['credit-receipts', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getReceipts({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        limit: 10,
      }),
    enabled: !!selectedDepartment,
  })

  // Recent expenses
  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['credit-expenses', selectedDepartment?.id, filters],
    queryFn: () =>
      creditPortfolioApi.getExpenses({
        department_id: selectedDepartment?.id,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
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

  // Load test data mutation
  const loadTestDataMutation = useMutation({
    mutationFn: (force: boolean) => creditPortfolioApi.loadTestData(force),
    onSuccess: (data) => {
      message.success(`Тестовые данные загружены успешно! ${data.data.organizations} организаций, ${data.data.contracts} договоров, ${data.data.receipts} поступлений, ${data.data.expenses} списаний`)
      // Invalidate all credit portfolio queries
      queryClient.invalidateQueries({ queryKey: ['credit-portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['credit-contracts'] })
      queryClient.invalidateQueries({ queryKey: ['credit-receipts'] })
      queryClient.invalidateQueries({ queryKey: ['credit-expenses'] })
    },
    onError: (error: any) => {
      if (error.response?.status === 400) {
        // Test data already exists
        Modal.confirm({
          title: 'Тестовые данные уже существуют',
          content: error.response?.data?.detail || 'Хотите перезагрузить тестовые данные? Это удалит существующие тестовые данные и создаст новые.',
          okText: 'Да, перезагрузить',
          cancelText: 'Отмена',
          onOk: () => {
            loadTestDataMutation.mutate(true) // Force reload
          }
        })
      } else {
        message.error(error.response?.data?.detail || 'Ошибка при загрузке тестовых данных')
      }
    }
  })

  const handleLoadTestData = () => {
    Modal.confirm({
      title: 'Загрузить тестовые данные?',
      content: (
        <div>
          <p>Будут созданы тестовые данные:</p>
          <ul>
            <li>3 организации (Сбербанк, ВТБ, Альфа-Банк)</li>
            <li>3 банковских счета</li>
            <li>3 кредитных договора</li>
            <li>Поступления за 2023-2025 годы</li>
            <li>Списания (погашение кредитов) за 2023-2025</li>
            <li>Детализацию платежей (тело/проценты)</li>
          </ul>
        </div>
      ),
      okText: 'Загрузить',
      cancelText: 'Отмена',
      onOk: () => {
        loadTestDataMutation.mutate(false)
      }
    })
  }

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
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ margin: 0 }}>Кредитный портфель - Аналитика</h1>
          <p style={{ margin: '8px 0 0 0', color: '#8c8c8c' }}>
            Обзор поступлений и списаний по кредитному портфелю
          </p>
        </div>
        {user?.role === 'ADMIN' && (
          <Space>
            <Button
              type="primary"
              icon={<DatabaseOutlined />}
              onClick={handleLoadTestData}
              loading={loadTestDataMutation.isPending}
            >
              Загрузить тестовые данные
            </Button>
          </Space>
        )}
      </div>

      {/* Filters */}
      <div style={{ marginBottom: 24 }}>
        <CreditPortfolioFilters
          onFilterChange={setFilters}
          initialValues={filters}
        />
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
