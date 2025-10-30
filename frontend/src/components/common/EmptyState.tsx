import type { ReactNode } from 'react'
import { Empty, Button, Space, Typography } from 'antd'
import {
  FileTextOutlined,
  DollarOutlined,
  TeamOutlined,
  FundOutlined,
  PlusOutlined,
  InboxOutlined,
} from '@ant-design/icons'

const { Text } = Typography

type EmptyStateType = 'expenses' | 'budget' | 'employees' | 'forecast' | 'categories' | 'default'

type EmptyStateProps = {
  type?: EmptyStateType
  title?: ReactNode
  description?: ReactNode
  onAction?: () => void
  actionLabel?: string
  actionIcon?: ReactNode
  extra?: ReactNode
  fullHeight?: boolean
}

const emptyConfigs: Record<
  EmptyStateType,
  {
    icon: ReactNode
    title: string
    description: string
    actionLabel?: string
  }
> = {
  expenses: {
    icon: <FileTextOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Нет заявок на расходы',
    description: 'Создайте первую заявку на расход, чтобы начать учет бюджета',
    actionLabel: 'Создать заявку',
  },
  budget: {
    icon: <DollarOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Бюджет не создан',
    description: 'Создайте план бюджета для начала работы с финансовым планированием',
    actionLabel: 'Создать план',
  },
  employees: {
    icon: <TeamOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Нет сотрудников',
    description: 'Добавьте сотрудников для планирования фонда оплаты труда',
    actionLabel: 'Добавить сотрудника',
  },
  forecast: {
    icon: <FundOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Нет данных для прогноза',
    description: 'Прогноз будет доступен после создания планов бюджета',
  },
  categories: {
    icon: <InboxOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Нет категорий',
    description: 'Создайте категории расходов для классификации бюджета',
    actionLabel: 'Создать категорию',
  },
  default: {
    icon: <InboxOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    title: 'Нет данных',
    description: 'Данные отсутствуют',
  },
}

const EmptyState = ({
  type = 'default',
  title,
  description,
  onAction,
  actionLabel,
  actionIcon,
  extra,
  fullHeight = true,
}: EmptyStateProps) => {
  const config = emptyConfigs[type]

  const actions = []
  if (onAction && (actionLabel || config.actionLabel)) {
    actions.push(
      <Button key="action" type="primary" icon={actionIcon || <PlusOutlined />} onClick={onAction}>
        {actionLabel || config.actionLabel}
      </Button>
    )
  }
  if (extra) {
    actions.push(extra)
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '48px 24px',
        minHeight: fullHeight ? '40vh' : undefined,
        textAlign: 'center',
      }}
    >
      <div style={{ marginBottom: 16 }}>{config.icon}</div>
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <Space direction="vertical" size={4}>
            <Text strong style={{ fontSize: 16 }}>
              {title || config.title}
            </Text>
            <Text type="secondary">{description || config.description}</Text>
          </Space>
        }
      >
        {actions.length > 0 && (
          <Space style={{ marginTop: 16 }} size="middle">
            {actions}
          </Space>
        )}
      </Empty>
    </div>
  )
}

export default EmptyState
