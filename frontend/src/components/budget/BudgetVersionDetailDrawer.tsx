/**
 * Budget Version Detail Drawer
 * Displays version metadata, plan editor, and approval history
 */
import React, { useMemo, useRef, useState } from 'react'
import { Drawer, Descriptions, Divider, Spin, Typography, Button } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import { useBudgetVersionWithDetails } from '@/hooks/useBudgetPlanning'
import { BudgetVersionStatus, ExpenseType } from '@/types/budgetPlanning'
import { BudgetVersionStatusBadge } from './BudgetVersionStatusBadge'
import { BudgetPlanDetailsTable } from './BudgetPlanDetailsTable'

const { Text } = Typography

interface Category {
  id: number
  name: string
  type: ExpenseType
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
  const tableRef = useRef<{ scrollBy: (direction: 'left' | 'right') => void } | null>(null)
  const [riskPremiumEnabled, setRiskPremiumEnabled] = useState<boolean>(false)
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

  // Calculate totals with risk premium
  const displayTotals = useMemo(() => {
    if (!version) {
      return {
        total: 0,
        capex: 0,
        opex: 0,
      }
    }

    const total = Number(version.total_amount || 0)
    const capex = Number(version.total_capex || 0)
    const opex = Number(version.total_opex || 0)

    if (riskPremiumEnabled) {
      return {
        total: total * 1.1,
        capex: capex * 1.1,
        opex: opex * 1.1,
      }
    }

    return { total, capex, opex }
  }, [version, riskPremiumEnabled])

  return (
    <Drawer
      width="100%"
      height="100%"
      open={open}
      onClose={onClose}
      destroyOnClose
      title={version ? `Версия бюджета v${version.version_number}` : 'Детали версии'}
      styles={{
        body: {
          padding: 24,
          height: 'calc(100vh - 55px)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
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
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          {/* Compact Header Section */}
          <div style={{ flexShrink: 0, marginBottom: 16 }}>
            <Descriptions bordered size="small" column={3}>
              <Descriptions.Item label="Статус">
                <BudgetVersionStatusBadge status={version.status} />
              </Descriptions.Item>
              <Descriptions.Item label="Сумма, ₽">
                {currencyFormatter.format(displayTotals.total)}
                {riskPremiumEnabled && (
                  <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>
                    (+10%)
                  </Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Сценарий">
                {version.scenario?.scenario_name || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="CAPEX, ₽">
                {currencyFormatter.format(displayTotals.capex)}
                {riskPremiumEnabled && (
                  <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>
                    (+10%)
                  </Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="OPEX, ₽">
                {currencyFormatter.format(displayTotals.opex)}
                {riskPremiumEnabled && (
                  <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>
                    (+10%)
                  </Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Автор">
                {version.created_by || '—'}
              </Descriptions.Item>
              {version.payroll_summary && (
                <>
                  <Descriptions.Item label="ФОТ (год), ₽">
                    {currencyFormatter.format(
                      riskPremiumEnabled
                        ? Number(version.payroll_summary.total_planned_annual || 0) * 1.1
                        : Number(version.payroll_summary.total_planned_annual || 0)
                    )}
                    {riskPremiumEnabled && (
                      <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>
                        (+10%)
                      </Text>
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="Сотрудников">
                    {version.payroll_summary.total_employees || 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="Средн. ЗП/мес, ₽">
                    {version.payroll_summary.total_employees > 0
                      ? currencyFormatter.format(
                          (riskPremiumEnabled
                            ? Number(version.payroll_summary.total_planned_annual || 0) * 1.1
                            : Number(version.payroll_summary.total_planned_annual || 0)) /
                            12 /
                            version.payroll_summary.total_employees
                        )
                      : '—'}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>
          </div>

          <Divider style={{ margin: '8px 0 16px 0' }} />

          {/* Budget Table Section - Flexible, takes remaining space */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
            <div style={{ marginBottom: 12 }}>
              <Text strong>
                План по категориям
                {isEditable ? ' (редактирование включено)' : ''}
              </Text>
            </div>
            <div style={{ flex: 1, overflow: 'auto', minHeight: 0, position: 'relative' }}>
              {/* Floating scroll buttons */}
              <div
                style={{
                  position: 'sticky',
                  top: 64,
                  zIndex: 100,
                  pointerEvents: 'none',
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0 12px',
                  height: 0,
                  marginBottom: 0,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Button
                    shape="circle"
                    size="large"
                    icon={<LeftOutlined />}
                    onClick={() => tableRef.current?.scrollBy('left')}
                    style={{
                      pointerEvents: 'auto',
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Button
                    shape="circle"
                    size="large"
                    icon={<RightOutlined />}
                    onClick={() => tableRef.current?.scrollBy('right')}
                    style={{
                      pointerEvents: 'auto',
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                    }}
                  />
                </div>
              </div>

              <BudgetPlanDetailsTable
                ref={tableRef}
                versionId={version.id}
                year={version.year}
                categories={categories}
                isEditable={isEditable}
                onAfterSave={handleAfterAction}
                onRiskPremiumChange={setRiskPremiumEnabled}
                payrollSummary={version.payroll_summary}
              />
            </div>
          </div>
        </div>
      )}
    </Drawer>
  )
}

export default BudgetVersionDetailDrawer
