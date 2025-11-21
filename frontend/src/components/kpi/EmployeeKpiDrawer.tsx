import { useState } from 'react'
import { Drawer, Descriptions, Table, Space, Tag, Typography, Divider, Statistic, Row, Col, Button, Tooltip } from 'antd'
import { CalculatorOutlined, InfoCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import type { EmployeeKPI, KPIGoalStatus } from '@/api/kpi'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import type { Employee } from '@/api/payroll'
import { formatCurrency } from '@/utils/formatters'
import { ComplexityBonusBreakdown } from './ComplexityBonusBreakdown'

const { Text } = Typography

const statusColor: Record<KPIGoalStatus, string> = {
  DRAFT: 'default',
  ACTIVE: 'processing',
  ACHIEVED: 'success',
  NOT_ACHIEVED: 'error',
  CANCELLED: 'warning',
}

const monthLabel = (month: number | null | undefined) =>
  typeof month === 'number' ? dayjs().month(month - 1).format('MMMM') : 'Годовая'

interface EmployeeKpiDrawerProps {
  open: boolean
  onClose: () => void
  employee?: Employee | null
  employeeKpis: EmployeeKPI[]
}

export const EmployeeKpiDrawer: React.FC<EmployeeKpiDrawerProps> = ({
  open,
  onClose,
  employee,
  employeeKpis,
}) => {
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const [breakdownModalOpen, setBreakdownModalOpen] = useState(false)
  const [selectedKpiId, setSelectedKpiId] = useState<number | null>(null)

  if (!employee) {
    return null
  }

  // Filter KPIs for this employee
  const employeeRecords = employeeKpis.filter((kpi) => kpi.employee_id === employee.id)

  // Handler for opening complexity breakdown
  const handleViewComplexityBreakdown = (kpiId: number) => {
    setSelectedKpiId(kpiId)
    setBreakdownModalOpen(true)
  }

  // Calculate statistics
  const totalKpiRecords = employeeRecords.length
  const averageKpi =
    employeeRecords.length > 0
      ? employeeRecords.reduce(
          (sum, kpi) =>
            sum + (kpi.kpi_percentage !== null && kpi.kpi_percentage !== undefined ? Number(kpi.kpi_percentage) : 0),
          0
        ) / employeeRecords.length
      : 0

  const totalBonuses = employeeRecords.reduce((sum, kpi) => {
    const monthlyBonus = Number(kpi.monthly_bonus_calculated || 0)
    const quarterlyBonus = Number(kpi.quarterly_bonus_calculated || 0)
    const annualBonus = Number(kpi.annual_bonus_calculated || 0)
    return sum + monthlyBonus + quarterlyBonus + annualBonus
  }, 0)

  const achievedGoalsCount = employeeRecords.reduce((count, kpi) => {
    if (!kpi.goal_achievements) return count
    return (
      count +
      kpi.goal_achievements.filter((achievement) => achievement.status === 'ACHIEVED').length
    )
  }, 0)

  const totalGoalsCount = employeeRecords.reduce((count, kpi) => {
    if (!kpi.goal_achievements) return count
    return count + kpi.goal_achievements.length
  }, 0)

  // Table columns for KPI history
  const historyColumns: ColumnsType<EmployeeKPI> = [
    {
      title: 'Период',
      key: 'period',
      width: 140,
      render: (_, record) => `${monthLabel(record.month)} ${record.year}`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      width: 100,
      render: (value) =>
        value !== null && value !== undefined ? (
          <Text strong>{Number(value).toFixed(1)} %</Text>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: 'Бонус (месяц)',
      dataIndex: 'monthly_bonus_calculated',
      key: 'monthly_bonus',
      width: 130,
      render: (value) => formatCurrency(Number(value || 0)),
    },
    {
      title: 'Бонус (квартал)',
      dataIndex: 'quarterly_bonus_calculated',
      key: 'quarterly_bonus',
      width: 130,
      render: (value) => formatCurrency(Number(value || 0)),
    },
    {
      title: 'Бонус (год)',
      dataIndex: 'annual_bonus_calculated',
      key: 'annual_bonus',
      width: 130,
      render: (value) => formatCurrency(Number(value || 0)),
    },
    {
      title: (
        <Tooltip title="Средняя сложность завершенных задач">
          <Space size={4}>
            <span>Сложность</span>
            <InfoCircleOutlined style={{ fontSize: 12 }} />
          </Space>
        </Tooltip>
      ),
      key: 'complexity',
      width: 120,
      align: 'center',
      render: (_, record) => {
        if (!record.task_complexity_avg) {
          return <Text type="secondary">—</Text>
        }

        const complexity = Number(record.task_complexity_avg)
        let color = '#d9d9d9'
        if (complexity >= 7) color = '#fa8c16'
        else if (complexity >= 4) color = '#1890ff'
        else if (complexity >= 1) color = '#52c41a'

        return (
          <Tag color={color} style={{ fontWeight: 600 }}>
            {complexity.toFixed(1)} / 10
          </Tag>
        )
      },
    },
    {
      title: (
        <Tooltip title="Множитель премии по сложности (0.70-1.30)">
          <Space size={4}>
            <span>Множитель</span>
            <InfoCircleOutlined style={{ fontSize: 12 }} />
          </Space>
        </Tooltip>
      ),
      key: 'multiplier',
      width: 110,
      align: 'center',
      render: (_, record) => {
        if (!record.task_complexity_multiplier) {
          return <Text type="secondary">—</Text>
        }

        const multiplier = Number(record.task_complexity_multiplier)
        const color = multiplier > 1 ? '#52c41a' : multiplier < 1 ? '#fa8c16' : '#1890ff'

        return (
          <Text strong style={{ color }}>
            {multiplier.toFixed(2)}×
          </Text>
        )
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<CalculatorOutlined />}
          onClick={() => handleViewComplexityBreakdown(record.id)}
        >
          Детали
        </Button>
      ),
    },
    {
      title: 'Цели',
      key: 'goals',
      render: (_, record) =>
        record.goal_achievements && record.goal_achievements.length > 0 ? (
          <Space size={4} wrap>
            {record.goal_achievements.map((achievement) => (
              <Tag
                key={achievement.id}
                color={statusColor[achievement.status as keyof typeof statusColor]}
                style={{ fontSize: 11 }}
              >
                Цель #{achievement.goal_id}
              </Tag>
            ))}
          </Space>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>
            Нет целей
          </Text>
        ),
    },
  ]

  return (
    <Drawer
      title="Детали KPI сотрудника"
      placement="right"
      onClose={onClose}
      open={open}
      width={900}
      destroyOnHidden
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Employee Info */}
        <Descriptions title="Информация о сотруднике" bordered column={2} size="small">
          <Descriptions.Item label="ФИО">{employee.full_name}</Descriptions.Item>
          <Descriptions.Item label="Позиция">{employee.position || '—'}</Descriptions.Item>
          <Descriptions.Item label="Email">{employee.email || '—'}</Descriptions.Item>
          <Descriptions.Item label="Статус">
            <Tag color={employee.status === 'ACTIVE' ? 'success' : 'default'}>
              {employee.status}
            </Tag>
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        {/* Statistics */}
        <div>
          <Text strong style={{ fontSize: 16, marginBottom: 16, display: 'block' }}>
            Статистика
          </Text>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="Записей KPI" value={totalKpiRecords} />
            </Col>
            <Col span={6}>
              <Statistic
                title="Средний КПИ"
                value={averageKpi}
                precision={1}
                suffix="%"
                valueStyle={{ color: averageKpi >= 80 ? '#3f8600' : averageKpi >= 60 ? '#faad14' : '#cf1322' }}
              />
            </Col>
            <Col span={6}>
              <Statistic title="Всего бонусов" value={totalBonuses} formatter={(value) => formatCurrency(Number(value))} />
            </Col>
            <Col span={6}>
              <Statistic
                title="Выполнено целей"
                value={`${achievedGoalsCount} / ${totalGoalsCount}`}
                valueStyle={{
                  color: achievedGoalsCount === totalGoalsCount && totalGoalsCount > 0 ? '#3f8600' : undefined,
                }}
              />
            </Col>
          </Row>
        </div>

        <Divider />

        {/* KPI History Table */}
        <div>
          <Text strong style={{ fontSize: 16, marginBottom: 16, display: 'block' }}>
            История KPI
          </Text>
          <ResponsiveTable<EmployeeKPI mobileLayout="card">
            rowKey="id"
            columns={historyColumns}
            dataSource={employeeRecords}
            pagination={false}
            scroll={{ x: 1200 }}
            size="small"
          />
        </div>
      </Space>

      {/* Complexity Bonus Breakdown Modal */}
      <ComplexityBonusBreakdown
        open={breakdownModalOpen}
        onClose={() => setBreakdownModalOpen(false)}
        employeeKpiId={selectedKpiId}
      />
    </Drawer>
  )
}
