/**
 * Budget Version Detail Drawer
 * Displays version metadata, plan editor, and approval history
 */
import React, { useMemo } from 'react'
import { Drawer, Space, Descriptions, Divider, Spin, Typography } from 'antd'
import { useBudgetVersionWithDetails } from '@/hooks/useBudgetPlanning'
import { BudgetVersionStatus } from '@/types/budgetPlanning'
import { BudgetVersionStatusBadge } from './BudgetVersionStatusBadge'
import { BudgetPlanDetailsTable } from './BudgetPlanDetailsTable'
import { BudgetVersionActions } from './BudgetVersionActions'
import { BudgetApprovalTimeline } from './BudgetApprovalTimeline'

const { Text } = Typography

interface Category {
  id: number
  name: string
  type: 'OPEX' | 'CAPEX'
  parentId: number | null
}

interface BudgetVersionDetailDrawerProps {
  open: boolean
  mode: 'view' | 'edit'
  versionId: number | null
  categories: Category[]
  onClose: () => void
  onVersionUpdated?: () => void
}

export const BudgetVersionDetailDrawer: React.FC<BudgetVersionDetailDrawerProps> = ({
  open,
  mode,
  versionId,
  categories,
  onClose,
  onVersionUpdated,
}) => {
  const shouldFetch = open && !!versionId
  const {
    data: version,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useBudgetVersionWithDetails(versionId ?? undefined, { enabled: shouldFetch })

  const isEditable = useMemo(() => {
    if (!version || mode !== 'edit') {
      return false
    }
    return [BudgetVersionStatus.DRAFT, BudgetVersionStatus.REVISION_REQUESTED].includes(version.status)
  }, [mode, version])

  const handleAfterAction = () => {
    refetch()
    onVersionUpdated?.()
  }
  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        maximumFractionDigits: 0,
      }),
    []
  )

  return (
    <Drawer
      width={1100}
      open={open}
      onClose={onClose}
      destroyOnClose
      title={version ? `Версия бюджета v${version.version_number}` : 'Детали версии'}
    >
      {!shouldFetch ? (
        <div style={{ padding: '24px 0' }}>
          <Text type="secondary">Выберите версию для вывода подробностей.</Text>
        </div>
      ) : isLoading || isFetching ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
        </div>
      ) : isError || !version ? (
        <div style={{ padding: '24px 0' }}>
          <Text type="danger">
            Не удалось загрузить версию. {error instanceof Error ? error.message : ''}
          </Text>
        </div>
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="Название" span={2}>
              {version.version_name || `Версия ${version.version_number}`}
            </Descriptions.Item>
            <Descriptions.Item label="Статус">
              <BudgetVersionStatusBadge status={version.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Сценарий">
              {version.scenario?.scenario_name || '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Создана">
              {new Date(version.created_at).toLocaleString('ru-RU')}
            </Descriptions.Item>
            <Descriptions.Item label="Автор">
              {version.created_by || '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Сумма, ₽">
              {currencyFormatter.format(Number(version.total_amount || 0))}
            </Descriptions.Item>
            <Descriptions.Item label="CAPEX, ₽">
              {currencyFormatter.format(Number(version.total_capex || 0))}
            </Descriptions.Item>
            <Descriptions.Item label="OPEX, ₽">
              {currencyFormatter.format(Number(version.total_opex || 0))}
            </Descriptions.Item>
            {version.comments && (
              <Descriptions.Item label="Комментарии" span={2}>
                <Text>{version.comments}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>

          <BudgetVersionActions version={version} onActionComplete={handleAfterAction} />

          <Divider />
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>
                План по категориям
                {isEditable ? ' (редактирование включено)' : ''}
              </Text>
              <BudgetPlanDetailsTable
                versionId={version.id}
                categories={categories}
                isEditable={isEditable}
                onAfterSave={handleAfterAction}
              />
            </Space>
          </div>

          <Divider />
          <div>
            <Text strong>История согласования</Text>
            <BudgetApprovalTimeline versionId={version.id} />
          </div>
        </Space>
      )}
    </Drawer>
  )
}

export default BudgetVersionDetailDrawer
