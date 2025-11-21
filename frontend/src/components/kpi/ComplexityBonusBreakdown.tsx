/**
 * Complexity Bonus Breakdown Component
 *
 * Displays detailed breakdown of complexity-based bonus calculation
 * with completed tasks list, formulas, and tier visualization.
 */

import { useState } from 'react'
import {
  Modal,
  Descriptions,
  Table,
  Space,
  Tag,
  Typography,
  Alert,
  Divider,
  Spin,
  Button,
  message,
  Statistic,
  Row,
  Col,
  Card,
} from 'antd'
import {
  InfoCircleOutlined,
  CheckCircleOutlined,
  CalculatorOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

import * as complexityBonusApi from '@/api/complexityBonus'
import type { ComplexityBonusBreakdown as ComplexityBreakdownType } from '@/api/complexityBonus'
import { formatCurrency } from '@/utils/formatters'

const { Text, Title } = Typography

// Complexity tier configuration
const complexityTierConfig = {
  simple: {
    label: 'Простые',
    color: '#52c41a',
    range: '1-3',
    multiplierRange: '0.70-0.85',
  },
  medium: {
    label: 'Средние',
    color: '#1890ff',
    range: '4-6',
    multiplierRange: '0.85-1.00',
  },
  complex: {
    label: 'Сложные',
    color: '#fa8c16',
    range: '7-10',
    multiplierRange: '1.00-1.30',
  },
  unknown: {
    label: 'Неизвестно',
    color: '#d9d9d9',
    range: '—',
    multiplierRange: '—',
  },
}

interface ComplexityBonusBreakdownProps {
  open: boolean
  onClose: () => void
  employeeKpiId: number | null
}

export const ComplexityBonusBreakdown: React.FC<ComplexityBonusBreakdownProps> = ({
  open,
  onClose,
  employeeKpiId,
}) => {
  const queryClient = useQueryClient()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const [recalculating, setRecalculating] = useState(false)

  // Fetch breakdown data
  const {
    data: breakdown,
    isLoading,
    refetch,
  } = useQuery<ComplexityBreakdownType>({
    queryKey: ['complexity-breakdown', employeeKpiId],
    queryFn: () => complexityBonusApi.getComplexityBreakdown(employeeKpiId!),
    enabled: open && !!employeeKpiId,
  })

  // Recalculate mutation
  const recalculateMutation = useMutation({
    mutationFn: () => complexityBonusApi.calculateComplexityBonus(employeeKpiId!),
    onSuccess: () => {
      message.success('Премия по сложности пересчитана')
      refetch()
      queryClient.invalidateQueries({ queryKey: ['employee-kpis'] })
      setRecalculating(false)
    },
    onError: () => {
      message.error('Ошибка при пересчете премии')
      setRecalculating(false)
    },
  })

  const handleRecalculate = () => {
    setRecalculating(true)
    recalculateMutation.mutate()
  }

  // Table columns for completed tasks
  const taskColumns: ColumnsType<ComplexityBreakdownType['completed_tasks'][0]> = [
    {
      title: 'Задача',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Сложность',
      dataIndex: 'complexity',
      key: 'complexity',
      width: 110,
      align: 'center',
      render: (complexity: number) => {
        let color = '#d9d9d9'
        if (complexity >= 7) color = '#fa8c16'
        else if (complexity >= 4) color = '#1890ff'
        else if (complexity >= 1) color = '#52c41a'

        return (
          <Tag color={color} style={{ fontWeight: 600 }}>
            {complexity} / 10
          </Tag>
        )
      },
    },
    {
      title: 'Завершено',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 140,
      render: (date: string) => (date ? dayjs(date).format('DD.MM.YYYY HH:mm') : '—'),
    },
  ]

  if (!breakdown || isLoading) {
    return (
      <Modal title="Детали премии по сложности" open={open} onCancel={onClose} footer={null} width={900}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
        </div>
      </Modal>
    )
  }

  const tierConfig = complexityTierConfig[breakdown.complexity_tier]

  return (
    <Modal
      title={
        <Space>
          <CalculatorOutlined />
          <span>Детали премии по сложности задач</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="recalculate" icon={<ReloadOutlined />} loading={recalculating} onClick={handleRecalculate}>
          Пересчитать
        </Button>,
        <Button key="close" type="primary" onClick={onClose}>
          Закрыть
        </Button>,
      ]}
      width={1000}
      destroyOnHidden
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Employee and Period Info */}
        <Alert
          message={
            <Space>
              <Text strong>{breakdown.employee_name}</Text>
              <Text type="secondary">•</Text>
              <Text>{breakdown.period}</Text>
            </Space>
          }
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />

        {/* Complexity Statistics */}
        <Card size="small" title="Статистика сложности">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Завершено задач"
                value={breakdown.completed_tasks_count}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Средняя сложность"
                value={breakdown.avg_complexity?.toFixed(2) || '—'}
                suffix="/ 10"
                valueStyle={{ color: tierConfig.color }}
              />
            </Col>
            <Col span={6}>
              <Statistic title="Уровень" value={tierConfig.label} valueStyle={{ color: tierConfig.color }} />
            </Col>
            <Col span={6}>
              <Statistic
                title="Множитель"
                value={breakdown.complexity_multiplier?.toFixed(4) || '—'}
                valueStyle={{
                  color:
                    breakdown.complexity_multiplier && breakdown.complexity_multiplier > 1 ? '#52c41a' : '#fa8c16',
                }}
              />
            </Col>
          </Row>

          <Divider style={{ margin: '12px 0' }} />

          {/* Tier explanation */}
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <strong>Диапазон сложности:</strong> {tierConfig.range}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <strong>Диапазон множителя:</strong> {tierConfig.multiplierRange}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <strong>Вес в премии:</strong> {breakdown.complexity_weight}%
            </Text>
          </Space>
        </Card>

        {/* Completed Tasks */}
        {breakdown.completed_tasks_count > 0 ? (
          <div>
            <Title level={5}>Завершенные задачи</Title>
            <ResponsiveTable<ComplexityBreakdownType['completed_tasks'][0] mobileLayout="card">
              rowKey="id"
              columns={taskColumns}
              dataSource={breakdown.completed_tasks}
              pagination={false}
              scroll={{ x: 600 }}
              size="small"
            />
          </div>
        ) : (
          <Alert message="Нет завершенных задач за этот период" type="warning" showIcon />
        )}

        {/* Bonus Breakdown */}
        {breakdown.complexity_multiplier && (
          <>
            <Divider />
            <div>
              <Title level={5}>Расчет премии</Title>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {/* Monthly */}
                {breakdown.bonuses.monthly && (
                  <Card size="small" title="Месячная премия">
                    <Descriptions bordered column={1} size="small">
                      <Descriptions.Item label="Базовая премия">
                        {formatCurrency(breakdown.bonuses.monthly.base)}
                      </Descriptions.Item>
                      <Descriptions.Item label="Компонент по сложности">
                        <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
                          {formatCurrency(breakdown.bonuses.monthly.complexity_component)}
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Формула расчета">
                        <Text code style={{ fontSize: 12 }}>
                          {breakdown.bonuses.monthly.formula}
                        </Text>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>
                )}

                {/* Quarterly */}
                {breakdown.bonuses.quarterly && (
                  <Card size="small" title="Квартальная премия">
                    <Descriptions bordered column={1} size="small">
                      <Descriptions.Item label="Базовая премия">
                        {formatCurrency(breakdown.bonuses.quarterly.base)}
                      </Descriptions.Item>
                      <Descriptions.Item label="Компонент по сложности">
                        <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
                          {formatCurrency(breakdown.bonuses.quarterly.complexity_component)}
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Формула расчета">
                        <Text code style={{ fontSize: 12 }}>
                          {breakdown.bonuses.quarterly.formula}
                        </Text>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>
                )}

                {/* Annual */}
                {breakdown.bonuses.annual && (
                  <Card size="small" title="Годовая премия">
                    <Descriptions bordered column={1} size="small">
                      <Descriptions.Item label="Базовая премия">
                        {formatCurrency(breakdown.bonuses.annual.base)}
                      </Descriptions.Item>
                      <Descriptions.Item label="Компонент по сложности">
                        <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
                          {formatCurrency(breakdown.bonuses.annual.complexity_component)}
                        </Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Формула расчета">
                        <Text code style={{ fontSize: 12 }}>
                          {breakdown.bonuses.annual.formula}
                        </Text>
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>
                )}
              </Space>
            </div>
          </>
        )}

        {/* Info */}
        <Alert
          message="Формула: Базовая премия × Множитель сложности × (Вес компонента / 100)"
          description="Множитель зависит от средней сложности завершенных задач: простые (1-3) → 0.70-0.85, средние (4-6) → 0.85-1.00, сложные (7-10) → 1.00-1.30"
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
          style={{ fontSize: 12 }}
        />
      </Space>
    </Modal>
  )
}
