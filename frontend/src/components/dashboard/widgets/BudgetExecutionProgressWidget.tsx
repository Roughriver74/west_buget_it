/**
 * Budget Execution Progress Widget
 * Shows progress bars for budget execution by category
 */
import React, { useMemo } from 'react'
import { Card, Progress, Row, Col, Typography, Tag, Space, Statistic } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import { ArrowUpOutlined, ArrowDownOutlined, CheckCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

interface BudgetExecutionProgressWidgetProps {
  year: number
  departmentId?: number
  height?: number
}

interface CategoryExecution {
  category_id: number
  category_name: string
  planned: number
  actual: number
  difference: number
  execution_percent: number
}

const BudgetExecutionProgressWidget: React.FC<BudgetExecutionProgressWidgetProps> = ({
  year,
  departmentId,
  height = 500,
}) => {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['plan-vs-actual', year, departmentId],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/analytics/plan-vs-actual`, {
        params: { year, department_id: departmentId },
      })
      return response.data
    },
  })

  const sortedCategories = useMemo(() => {
    if (!data?.by_category) return []

    // Sort by execution percentage (highest first)
    return [...data.by_category].sort(
      (a: CategoryExecution, b: CategoryExecution) => b.execution_percent - a.execution_percent
    )
  }, [data])

  const getProgressColor = (percent: number) => {
    if (percent > 100) return '#ff4d4f' // Red for over-budget
    if (percent > 90) return '#faad14'   // Orange for warning
    if (percent > 75) return '#1890ff'   // Blue for on-track
    return '#52c41a'                     // Green for under-budget
  }

  const getProgressStatus = (percent: number): 'success' | 'exception' | 'normal' => {
    if (percent > 100) return 'exception'
    if (percent > 90) return 'normal'
    return 'success'
  }

  if (isLoading) {
    return (
      <Card title={`Исполнение бюджета ${year} по категориям`}>
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title={`Исполнение бюджета ${year} по категориям`}>
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
        />
      </Card>
    )
  }

  if (!data || !sortedCategories.length) {
    return (
      <Card title={`Исполнение бюджета ${year} по категориям`}>
        <Text type="secondary">
          Нет базовой версии бюджета для {year} года. Установите утвержденную версию как baseline.
        </Text>
      </Card>
    )
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Card
      title={
        <Space>
          <span>{`Исполнение бюджета ${year} по категориям`}</span>
          {data.baseline_version_name && (
            <Tag color="blue">Baseline: {data.baseline_version_name}</Tag>
          )}
        </Space>
      }
      extra={
        <Tag color={data.execution_percent > 100 ? 'red' : data.execution_percent > 90 ? 'orange' : 'green'}>
          {data.execution_percent.toFixed(1)}% исполнено
        </Tag>
      }
    >
      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Statistic
            title="План"
            value={data.total_planned}
            precision={0}
            suffix="₽"
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Факт"
            value={data.total_actual}
            precision={0}
            suffix="₽"
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Отклонение"
            value={data.total_difference}
            precision={0}
            suffix="₽"
            prefix={data.total_difference > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            valueStyle={{
              color: data.total_difference > 0 ? '#cf1322' : '#52c41a',
            }}
          />
        </Col>
      </Row>

      {/* Category Progress Bars */}
      <div style={{ maxHeight: height - 200, overflowY: 'auto' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {sortedCategories.map((category: CategoryExecution) => {
            const percent = Math.min(category.execution_percent, 100)
            const isOverBudget = category.execution_percent > 100

            return (
              <div key={category.category_id} style={{ width: '100%' }}>
                <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
                  <Col span={12}>
                    <Space>
                      <Text strong>{category.category_name}</Text>
                      {isOverBudget && (
                        <Tag color="red">+{(category.execution_percent - 100).toFixed(1)}%</Tag>
                      )}
                      {category.execution_percent === 100 && (
                        <Tag color="green" icon={<CheckCircleOutlined />}>
                          Выполнено
                        </Tag>
                      )}
                    </Space>
                  </Col>
                  <Col span={12} style={{ textAlign: 'right' }}>
                    <Space>
                      <Text type="secondary">
                        {formatCurrency(category.actual)} / {formatCurrency(category.planned)}
                      </Text>
                      <Tag color={getProgressColor(category.execution_percent)}>
                        {category.execution_percent.toFixed(1)}%
                      </Tag>
                    </Space>
                  </Col>
                </Row>

                <Progress
                  percent={percent}
                  strokeColor={getProgressColor(category.execution_percent)}
                  status={getProgressStatus(category.execution_percent)}
                  showInfo={false}
                />

                {isOverBudget && (
                  <Row justify="space-between" style={{ marginTop: 4 }}>
                    <Col>
                      <Text type="danger" style={{ fontSize: 12 }}>
                        Превышение: {formatCurrency(category.difference)}
                      </Text>
                    </Col>
                  </Row>
                )}
              </div>
            )
          })}
        </Space>
      </div>
    </Card>
  )
}

export default BudgetExecutionProgressWidget
