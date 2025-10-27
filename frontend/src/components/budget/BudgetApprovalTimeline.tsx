/**
 * Budget Approval Timeline Component
 * Displays approval history with timeline visualization
 */
import React from 'react'
import { Timeline, Typography, Empty, Spin } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  SendOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useApprovalLogs } from '@/hooks/useBudgetPlanning'
import { ApprovalAction } from '@/types/budgetPlanning'

const { Text, Paragraph } = Typography

interface BudgetApprovalTimelineProps {
  versionId: number
}

export const BudgetApprovalTimeline: React.FC<BudgetApprovalTimelineProps> = ({
  versionId,
}) => {
  const { data: logs = [], isLoading } = useApprovalLogs(versionId)

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin />
      </div>
    )
  }

  if (logs.length === 0) {
    return <Empty description="История согласования пуста" />
  }

  const getActionConfig = (action: ApprovalAction | string) => {
    switch (action) {
      case ApprovalAction.SUBMITTED:
        return {
          color: 'blue',
          icon: <SendOutlined />,
          label: 'Отправлено на согласование',
        }
      case ApprovalAction.APPROVED:
        return {
          color: 'green',
          icon: <CheckCircleOutlined />,
          label: 'Утверждено',
        }
      case ApprovalAction.REJECTED:
        return {
          color: 'red',
          icon: <CloseCircleOutlined />,
          label: 'Отклонено',
        }
      case ApprovalAction.REVISION_REQUESTED:
        return {
          color: 'orange',
          icon: <EditOutlined />,
          label: 'Запрошены изменения',
        }
      default:
        return {
          color: 'gray',
          icon: null,
          label: action,
        }
    }
  }

  const timelineItems = logs
    .sort((a, b) => new Date(b.decision_date).getTime() - new Date(a.decision_date).getTime())
    .map((log) => {
      const config = getActionConfig(log.action)

      return {
        color: config.color,
        dot: config.icon,
        children: (
          <div>
            <div style={{ marginBottom: 4 }}>
              <Text strong>{config.label}</Text>
              {log.iteration_number > 1 && (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  (итерация {log.iteration_number})
                </Text>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {dayjs(log.decision_date).format('DD.MM.YYYY HH:mm')} • {log.reviewer_name}
            </Text>
            {log.comments && (
              <Paragraph
                style={{
                  marginTop: 8,
                  marginBottom: 0,
                  padding: '8px 12px',
                  background: '#fafafa',
                  borderRadius: 4,
                  fontSize: '13px',
                }}
              >
                {log.comments}
              </Paragraph>
            )}
          </div>
        ),
      }
    })

  return <Timeline items={timelineItems} style={{ marginTop: 24 }} />
}
