/**
 * Budget Version Actions Component
 * Handles approval workflow actions (submit, approve, reject, request changes)
 */
import React, { useState } from 'react'
import { Button, Space, Modal, Input, message } from 'antd'
import {
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { useAuth } from '@/contexts/AuthContext'
import {
  useSubmitVersion,
  useApproveVersion,
  useRejectVersion,
  useRequestChanges,
} from '@/hooks/useBudgetPlanning'
import type { BudgetVersion } from '@/types/budgetPlanning'

const { TextArea } = Input

interface BudgetVersionActionsProps {
  version: BudgetVersion
  onActionComplete?: () => void
}

export const BudgetVersionActions: React.FC<BudgetVersionActionsProps> = ({
  version,
  onActionComplete,
}) => {
  const { user } = useAuth()
  const [commentsModalVisible, setCommentsModalVisible] = useState(false)
  const [comments, setComments] = useState('')
  const [currentAction, setCurrentAction] = useState<'approve' | 'reject' | 'request-changes' | null>(null)

  const submitMutation = useSubmitVersion()
  const approveMutation = useApproveVersion()
  const rejectMutation = useRejectVersion()
  const requestChangesMutation = useRequestChanges()

  const isAdmin = user?.role === 'ADMIN'
  const isManager = user?.role === 'MANAGER'
  const canApprove = isAdmin || isManager

  const handleSubmit = async () => {
    Modal.confirm({
      title: 'Отправить версию на согласование?',
      content: 'После отправки версия не будет доступна для редактирования до решения согласующего.',
      okText: 'Отправить',
      cancelText: 'Отмена',
      onOk: async () => {
        await submitMutation.mutateAsync(version.id)
        onActionComplete?.()
      },
    })
  }

  const openCommentsModal = (action: 'approve' | 'reject' | 'request-changes') => {
    setCurrentAction(action)
    setComments('')
    setCommentsModalVisible(true)
  }

  const handleCommentsSubmit = async () => {
    if (!currentAction) return

    try {
      if (currentAction === 'approve') {
        await approveMutation.mutateAsync({
          id: version.id,
          comments: comments || undefined,
        })
      } else if (currentAction === 'reject') {
        if (!comments.trim()) {
          message.warning('Укажите причину отклонения')
          return
        }
        await rejectMutation.mutateAsync({
          id: version.id,
          comments,
        })
      } else if (currentAction === 'request-changes') {
        if (!comments.trim()) {
          message.warning('Укажите какие изменения требуются')
          return
        }
        await requestChangesMutation.mutateAsync({
          id: version.id,
          comments,
        })
      }

      setCommentsModalVisible(false)
      setComments('')
      setCurrentAction(null)
      onActionComplete?.()
    } catch (error) {
      // Error handled by mutation
    }
  }

  const getModalTitle = () => {
    switch (currentAction) {
      case 'approve':
        return 'Утвердить версию бюджета'
      case 'reject':
        return 'Отклонить версию бюджета'
      case 'request-changes':
        return 'Запросить изменения'
      default:
        return ''
    }
  }

  const getModalPlaceholder = () => {
    switch (currentAction) {
      case 'approve':
        return 'Комментарий (необязательно)'
      case 'reject':
        return 'Укажите причину отклонения *'
      case 'request-changes':
        return 'Укажите какие изменения требуются *'
      default:
        return ''
    }
  }

  // Show actions based on version status and user role
  const renderActions = () => {
    switch (version.status) {
      case 'DRAFT':
        // Any user can submit their draft version
        return (
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSubmit}
            loading={submitMutation.isPending}
          >
            Отправить на согласование
          </Button>
        )

      case 'SUBMITTED':
      case 'CHANGES_REQUESTED':
        // Only ADMIN/MANAGER can approve/reject
        if (!canApprove) {
          return (
            <Button type="text" disabled>
              Ожидает согласования
            </Button>
          )
        }

        return (
          <Space>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={() => openCommentsModal('approve')}
              loading={approveMutation.isPending}
            >
              Утвердить
            </Button>
            <Button
              icon={<EditOutlined />}
              onClick={() => openCommentsModal('request-changes')}
              loading={requestChangesMutation.isPending}
            >
              Запросить изменения
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              onClick={() => openCommentsModal('reject')}
              loading={rejectMutation.isPending}
            >
              Отклонить
            </Button>
          </Space>
        )

      case 'APPROVED':
        return (
          <Button type="text" disabled icon={<CheckOutlined />}>
            Утверждено
          </Button>
        )

      case 'REJECTED':
        return (
          <Button type="text" disabled danger icon={<CloseOutlined />}>
            Отклонено
          </Button>
        )

      default:
        return null
    }
  }

  return (
    <>
      {renderActions()}

      <Modal
        title={getModalTitle()}
        open={commentsModalVisible}
        onOk={handleCommentsSubmit}
        onCancel={() => {
          setCommentsModalVisible(false)
          setComments('')
          setCurrentAction(null)
        }}
        okText={
          currentAction === 'approve'
            ? 'Утвердить'
            : currentAction === 'reject'
            ? 'Отклонить'
            : 'Запросить'
        }
        cancelText="Отмена"
        okButtonProps={{
          loading:
            approveMutation.isPending ||
            rejectMutation.isPending ||
            requestChangesMutation.isPending,
        }}
      >
        <TextArea
          rows={4}
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          placeholder={getModalPlaceholder()}
          style={{ marginTop: 16 }}
        />
      </Modal>
    </>
  )
}
