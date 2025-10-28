/**
 * Budget Plan vs Actual Dashboard
 * Comprehensive view of plan vs actual performance with variance analysis
 */
import React, { useState, useMemo } from 'react'
import {
  Typography,
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Select,
  Alert,
  Tag,
  Space,
  Tooltip,
  Spin,
} from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { planVsActualApi } from '@/api/budgetPlanning'
import type { CategoryPlanVsActual, MonthlyPlanVsActual } from '@/types/budgetPlanning'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Text } = Typography

const BudgetPlanVsActualPage: React.FC = () => {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())

  const departmentId = selectedDepartment?.id ?? user?.department_id

  // Fetch plan vs actual data
  const {
    data: planVsActual,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['plan-vs-actual', selectedYear, departmentId],
    queryFn: () =>
      planVsActualApi.get({
        year: selectedYear,
        department_id: departmentId,
      }),
    enabled: !!departmentId,
  })

  // Fetch alerts
  const { data: alerts = [] } = useQuery({
    queryKey: ['budget-alerts', selectedYear, departmentId],
    queryFn: () => planVsActualApi.getAlerts(selectedYear, departmentId, 10.0),
    enabled: !!departmentId,
  })

  // Generate year options
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear()
    return Array.from({ length: 5 }, (_, i) => currentYear - i).map((year) => ({
      label: `${year} год`,
      value: year,
    }))
  }, [])

  // Format currency
  const formatCurrency = (value: number | string): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num)
  }

  // Format percentage
  const formatPercent = (value: number | string): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return `${num.toFixed(1)}%`
  }

  // Get color for variance
  const getVarianceColor = (variance: number | string): string => {
    const num = typeof variance === 'string' ? parseFloat(variance) : variance
    if (num > 10) return '#ff4d4f' // Critical over budget
    if (num > 0) return '#faad14' // Warning over budget
    if (num > -10) return '#52c41a' // Good
    return '#1890ff' // Excellent - under budget
  }

  // Category columns for table
  const categoryColumns = [
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      fixed: 'left' as const,
      width: 200,
      render: (text: string, record: CategoryPlanVsActual) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Tag color={record.category_type === 'CAPEX' ? 'blue' : 'green'}>
            {record.category_type}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'План',
      dataIndex: 'planned_amount',
      key: 'planned_amount',
      width: 150,
      align: 'right' as const,
      render: (value: number | string) => formatCurrency(value),
    },
    {
      title: 'Факт',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      width: 150,
      align: 'right' as const,
      render: (value: number | string) => formatCurrency(value),
    },
    {
      title: 'Отклонение',
      dataIndex: 'variance_amount',
      key: 'variance_amount',
      width: 150,
      align: 'right' as const,
      render: (value: number | string, record: CategoryPlanVsActual) => {
        const num = typeof value === 'string' ? parseFloat(value) : value
        return (
          <Text
            style={{
              color: getVarianceColor(record.variance_percent),
              fontWeight: 500,
            }}
          >
            {num >= 0 ? '+' : ''}
            {formatCurrency(value)}
          </Text>
        )
      },
    },
    {
      title: 'Выполнение',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      width: 200,
      render: (value: number | string, record: CategoryPlanVsActual) => {
        const num = typeof value === 'string' ? parseFloat(value) : value
        return (
          <Tooltip title={`${formatPercent(value)} выполнения`}>
            <Progress
              percent={num}
              size="small"
              status={record.is_over_budget ? 'exception' : 'normal'}
              strokeColor={record.is_over_budget ? '#ff4d4f' : '#52c41a'}
            />
          </Tooltip>
        )
      },
    },
    {
      title: 'Статус',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: CategoryPlanVsActual) =>
        record.is_over_budget ? (
          <Tooltip title="Превышение бюджета">
            <WarningOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
          </Tooltip>
        ) : (
          <Tooltip title="В пределах бюджета">
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
          </Tooltip>
        ),
    },
  ]

  if (!departmentId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Необходимо выбрать отдел"
          description="Для просмотра план-факт отчета необходимо выбрать отдел в меню сверху."
          type="warning"
          showIcon
        />
      </div>
    )
  }

  if (isLoading) {
    return <LoadingState message="Загрузка план-факт отчета..." />
  }

  if (isError) {
    return (
      <ErrorState
        message="Ошибка загрузки данных"
        description={error?.message || 'Не удалось загрузить план-факт отчет'}
        onRetry={refetch}
      />
    )
  }

  if (!planVsActual) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Нет данных"
          description="Для выбранного года и отдела нет данных план-факт. Убедитесь что утверждена baseline версия бюджета."
          type="info"
          showIcon
        />
      </div>
    )
  }

  const criticalAlerts = alerts.filter((a) => a.severity === 'critical')
  const warningAlerts = alerts.filter((a) => a.severity === 'warning')

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2}>План vs Факт</Title>
          <Text type="secondary">
            Анализ исполнения бюджета за {selectedYear} год
            {planVsActual.baseline_version_name && ` (${planVsActual.baseline_version_name})`}
          </Text>
        </div>
        <Select
          value={selectedYear}
          onChange={setSelectedYear}
          options={yearOptions}
          style={{ width: 150 }}
        />
      </div>

      {/* Alerts */}
      {(criticalAlerts.length > 0 || warningAlerts.length > 0) && (
        <div style={{ marginBottom: 24 }}>
          {criticalAlerts.length > 0 && (
            <Alert
              message={`Критическое превышение бюджета: ${criticalAlerts.length} категорий/месяцев`}
              description={
                <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                  {criticalAlerts.slice(0, 3).map((alert, idx) => (
                    <li key={idx}>
                      {alert.entity_name}: превышение на {formatPercent(alert.variance_percent)}
                    </li>
                  ))}
                  {criticalAlerts.length > 3 && <li>и ещё {criticalAlerts.length - 3}...</li>}
                </ul>
              }
              type="error"
              showIcon
              icon={<WarningOutlined />}
              style={{ marginBottom: 16 }}
            />
          )}
          {warningAlerts.length > 0 && (
            <Alert
              message={`Предупреждение: ${warningAlerts.length} категорий/месяцев приближается к лимиту`}
              type="warning"
              showIcon
              closable
            />
          )}
        </div>
      )}

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Общий план"
              value={parseFloat(planVsActual.total_planned.toString())}
              precision={0}
              formatter={(value) => formatCurrency(value as number)}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Фактические расходы"
              value={parseFloat(planVsActual.total_actual.toString())}
              precision={0}
              formatter={(value) => formatCurrency(value as number)}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Отклонение"
              value={parseFloat(planVsActual.total_variance.toString())}
              precision={0}
              formatter={(value) => formatCurrency(value as number)}
              prefix={
                parseFloat(planVsActual.total_variance.toString()) >= 0 ? (
                  <ArrowUpOutlined />
                ) : (
                  <ArrowDownOutlined />
                )
              }
              valueStyle={{
                color: getVarianceColor(planVsActual.total_variance_percent),
              }}
              suffix={`(${formatPercent(planVsActual.total_variance_percent)})`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Выполнение"
              value={parseFloat(planVsActual.total_execution_percent.toString())}
              precision={1}
              suffix="%"
              valueStyle={{
                color:
                  parseFloat(planVsActual.total_execution_percent.toString()) > 100
                    ? '#ff4d4f'
                    : '#52c41a',
              }}
            />
            <Progress
              percent={parseFloat(planVsActual.total_execution_percent.toString())}
              size="small"
              status={
                parseFloat(planVsActual.total_execution_percent.toString()) > 100
                  ? 'exception'
                  : 'normal'
              }
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
      </Row>

      {/* CAPEX/OPEX Breakdown */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="CAPEX">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="План"
                  value={parseFloat(planVsActual.capex_planned.toString())}
                  formatter={(value) => formatCurrency(value as number)}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Факт"
                  value={parseFloat(planVsActual.capex_actual.toString())}
                  formatter={(value) => formatCurrency(value as number)}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="OPEX">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="План"
                  value={parseFloat(planVsActual.opex_planned.toString())}
                  formatter={(value) => formatCurrency(value as number)}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Факт"
                  value={parseFloat(planVsActual.opex_actual.toString())}
                  formatter={(value) => formatCurrency(value as number)}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Category Breakdown */}
      <Card title="Выполнение по категориям" style={{ marginBottom: 24 }}>
        <Table
          dataSource={planVsActual.category_data}
          columns={categoryColumns}
          rowKey="category_id"
          pagination={{ pageSize: 10, showSizeChanger: true }}
          scroll={{ x: 900 }}
        />
      </Card>

      {/* Monthly Trend - будет реализовано позже с тепловой картой */}
    </div>
  )
}

export default BudgetPlanVsActualPage
