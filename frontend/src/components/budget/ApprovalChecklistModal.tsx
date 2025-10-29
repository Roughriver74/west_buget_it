/**
 * Approval Checklist Modal
 * Allows setting approval checkboxes for budget version presentation
 */
import React, { useState, useEffect } from 'react'
import { Modal, Checkbox, Space, Typography, message, Alert, Progress, Divider } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { versionsApi } from '@/api/budgetPlanning'
import type { BudgetVersion, SetApprovalsRequest } from '@/types/budgetPlanning'
import dayjs from 'dayjs'

const { Text } = Typography

interface ApprovalChecklistModalProps {
  open: boolean
  version: BudgetVersion
  onClose: () => void
}

interface ApprovalItem {
  key: keyof SetApprovalsRequest
  label: string
  approved: boolean
  approvedAt?: string
}

export const ApprovalChecklistModal: React.FC<ApprovalChecklistModalProps> = ({
  open,
  version,
  onClose,
}) => {
  const queryClient = useQueryClient()
  const [approvals, setApprovals] = useState<SetApprovalsRequest>({})

  // Initialize approvals from version
  useEffect(() => {
    if (version) {
      setApprovals({
        manager_approved: version.manager_approved,
        cfo_approved: version.cfo_approved,
        founder1_approved: version.founder1_approved,
        founder2_approved: version.founder2_approved,
        founder3_approved: version.founder3_approved,
      })
    }
  }, [version])

  // Mutation for setting approvals
  const setApprovalsMutation = useMutation({
    mutationFn: (data: SetApprovalsRequest) => versionsApi.setApprovals(version.id, data),
    onSuccess: () => {
      message.success('Статус согласования обновлен')
      queryClient.invalidateQueries({ queryKey: ['budgetVersion', version.id] })
      queryClient.invalidateQueries({ queryKey: ['budgetVersions'] })
      onClose()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении согласования')
      console.error('Set approvals error:', error)
    },
  })

  const handleCheckboxChange = (key: keyof SetApprovalsRequest, checked: boolean) => {
    setApprovals(prev => ({
      ...prev,
      [key]: checked,
    }))
  }

  const handleSave = () => {
    setApprovalsMutation.mutate(approvals)
  }

  const handleClose = () => {
    // Reset to version state
    setApprovals({
      manager_approved: version.manager_approved,
      cfo_approved: version.cfo_approved,
      founder1_approved: version.founder1_approved,
      founder2_approved: version.founder2_approved,
      founder3_approved: version.founder3_approved,
    })
    onClose()
  }

  // Calculate approval progress
  const approvalItems: ApprovalItem[] = [
    {
      key: 'manager_approved',
      label: 'Непосредственный руководитель',
      approved: version.manager_approved,
      approvedAt: version.manager_approved_at,
    },
    {
      key: 'cfo_approved',
      label: 'Финансовый директор',
      approved: version.cfo_approved,
      approvedAt: version.cfo_approved_at,
    },
    {
      key: 'founder1_approved',
      label: 'Учредитель 1',
      approved: version.founder1_approved,
      approvedAt: version.founder1_approved_at,
    },
    {
      key: 'founder2_approved',
      label: 'Учредитель 2',
      approved: version.founder2_approved,
      approvedAt: version.founder2_approved_at,
    },
    {
      key: 'founder3_approved',
      label: 'Учредитель 3',
      approved: version.founder3_approved,
      approvedAt: version.founder3_approved_at,
    },
  ]

  const approvedCount = approvalItems.filter(item => item.approved).length
  const totalCount = approvalItems.length
  const progressPercent = Math.round((approvedCount / totalCount) * 100)

  return (
    <Modal
      open={open}
      title="Презентация бюджета - Согласование"
      width={600}
      onCancel={handleClose}
      onOk={handleSave}
      confirmLoading={setApprovalsMutation.isPending}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Alert
          message="Режим презентации"
          description="Отметьте галочками согласовавших бюджет. Статус автоматически обновляется при сохранении."
          type="info"
          showIcon
        />

        <div>
          <Text strong>Прогресс согласования:</Text>
          <div style={{ marginTop: 8 }}>
            <Progress
              percent={progressPercent}
              status={approvedCount === totalCount ? 'success' : 'active'}
              format={() => `${approvedCount} из ${totalCount}`}
            />
          </div>
        </div>

        <Divider />

        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {approvalItems.map((item) => {
            const isChecked = approvals[item.key] ?? item.approved
            return (
              <div key={item.key} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <Checkbox
                  checked={isChecked}
                  onChange={(e) => handleCheckboxChange(item.key, e.target.checked)}
                  style={{ marginTop: 4 }}
                />
                <div style={{ flex: 1 }}>
                  <div>
                    <Text strong>{item.label}</Text>
                    {item.approved && (
                      <CheckCircleOutlined
                        style={{ color: '#52c41a', marginLeft: 8 }}
                      />
                    )}
                    {!item.approved && (
                      <ClockCircleOutlined
                        style={{ color: '#d9d9d9', marginLeft: 8 }}
                      />
                    )}
                  </div>
                  {item.approvedAt && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Согласовано: {dayjs(item.approvedAt).format('DD.MM.YYYY HH:mm')}
                    </Text>
                  )}
                </div>
              </div>
            )
          })}
        </Space>

        {approvedCount === totalCount && (
          <Alert
            message="Все согласования получены!"
            description="Бюджет полностью согласован всеми сторонами."
            type="success"
            showIcon
          />
        )}
      </Space>
    </Modal>
  )
}
