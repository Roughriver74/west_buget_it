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
import type { BudgetVersionStatus } from '@/types/budgetPlanning'

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
      case 'DRAFT':
        return {
          color: 'default',
          icon: <EditOutlined />,
          text: 'Черновик',
        }
      case 'SUBMITTED':
        return {
          color: 'processing',
          icon: <SendOutlined />,
          text: 'На согласовании',
        }
      case 'CHANGES_REQUESTED':
        return {
          color: 'warning',
          icon: <ClockCircleOutlined />,
          text: 'Требуются изменения',
        }
      case 'APPROVED':
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          text: 'Утверждено',
        }
      case 'REJECTED':
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
