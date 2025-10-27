/**
 * Budget Version Status Badge Component
 * Displays version status with appropriate color and icon
 */
import React from 'react'
import { Tag } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EditOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { BudgetVersionStatus } from '@/types/budgetPlanning'

interface BudgetVersionStatusBadgeProps {
  status: BudgetVersionStatus
  style?: React.CSSProperties
}

export const BudgetVersionStatusBadge: React.FC<BudgetVersionStatusBadgeProps> = ({
  status,
  style,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case BudgetVersionStatus.DRAFT:
        return {
          color: 'default',
          icon: <EditOutlined />,
          text: 'Черновик',
        }
      case BudgetVersionStatus.IN_REVIEW:
        return {
          color: 'processing',
          icon: <SendOutlined />,
          text: 'На согласовании',
        }
      case BudgetVersionStatus.REVISION_REQUESTED:
        return {
          color: 'warning',
          icon: <ClockCircleOutlined />,
          text: 'Требуются изменения',
        }
      case BudgetVersionStatus.APPROVED:
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          text: 'Утверждено',
        }
      case BudgetVersionStatus.REJECTED:
        return {
          color: 'error',
          icon: <CloseCircleOutlined />,
          text: 'Отклонено',
        }
      default:
        return {
          color: 'default',
          icon: null,
          text: status,
        }
    }
  }

  const config = getStatusConfig()

  return (
    <Tag color={config.color} icon={config.icon} style={style}>
      {config.text}
    </Tag>
  )
}
