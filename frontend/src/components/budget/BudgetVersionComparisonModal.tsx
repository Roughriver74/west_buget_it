/**
 * Budget Version Comparison Modal
 * Displays side-by-side comparison of two budget versions
 */
import React, { useMemo } from 'react'
import { Modal, Table, Card, Row, Col, Statistic, Descriptions, Space, Tag, Spin, Alert } from 'antd'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useVersionComparison } from '@/hooks/useBudgetPlanning'
import type { VersionComparisonCategory } from '@/types/budgetPlanning'

interface BudgetVersionComparisonModalProps {
  open: boolean
  version1Id: number | null
  version2Id: number | null
  onClose: () => void
}

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

const percentFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

export const BudgetVersionComparisonModal: React.FC<BudgetVersionComparisonModalProps> = ({
  open,
  version1Id,
  version2Id,
  onClose,
}) => {
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const shouldFetch = open && !!version1Id && !!version2Id

  const {
    data: comparison,
    isLoading,
    isError,
    error,
  } = useVersionComparison(version1Id ?? 0, version2Id ?? 0, {
    enabled: shouldFetch,
  })

  const totalDifferencePercent = useMemo(() => {
    if (!comparison) return 0
    return Number(comparison.total_difference_percent || 0) / 100
  }, [comparison])

  const sortedCategories = useMemo(() => {
    if (!comparison?.category_comparisons) return []
    return [...comparison.category_comparisons].sort((a, b) => {
      const diffA = Math.abs(Number(a.difference_amount || 0))
      const diffB = Math.abs(Number(b.difference_amount || 0))
      return diffB - diffA
    })
  }, [comparison])

  const columns: ColumnsType<VersionComparisonCategory> = [
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 250,
      fixed: 'left',
    },
    {
      title: comparison?.version1.version_name || `Версия ${comparison?.version1.version_number}`,
      dataIndex: 'version1_amount',
      key: 'version1_amount',
      align: 'right',
      width: 180,
      render: (value: number) => currencyFormatter.format(Number(value || 0)),
    },
    {
      title: comparison?.version2.version_name || `Версия ${comparison?.version2.version_number}`,
      dataIndex: 'version2_amount',
      key: 'version2_amount',
      align: 'right',
      width: 180,
      render: (value: number) => currencyFormatter.format(Number(value || 0)),
    },
    {
      title: 'Разница, ₽',
      dataIndex: 'difference_amount',
      key: 'difference_amount',
      align: 'right',
      width: 180,
      render: (value: number) => {
        const diff = Number(value || 0)
        const color = diff > 0 ? '#cf1322' : diff < 0 ? '#3f8600' : undefined
        return (
          <span style={{ color, fontWeight: 500 }}>
            {diff > 0 && '+'}
            {currencyFormatter.format(diff)}
          </span>
        )
      },
    },
    {
      title: 'Изменение, %',
      dataIndex: 'difference_percent',
      key: 'difference_percent',
      align: 'right',
      width: 150,
      render: (value: number, record: VersionComparisonCategory) => {
        const percent = Number(value || 0) / 100
        const diff = Number(record.difference_amount || 0)

        if (Math.abs(diff) < 1) {
          return <Tag icon={<MinusOutlined />}>0%</Tag>
        }

        return (
          <Tag
            icon={diff > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            color={diff > 0 ? 'red' : 'green'}
          >
            {diff > 0 && '+'}
            {percentFormatter.format(percent)}
          </Tag>
        )
      },
    },
  ]

  return (
    <Modal
      title="Сравнение версий бюджета"
      open={open}
      onCancel={onClose}
      width={1200}
      footer={null}
      destroyOnHidden
    >
      {!shouldFetch ? (
        <Alert message="Выберите две версии для сравнения" type="info" showIcon />
      ) : isLoading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0' }}>
          <Spin size="large" tip="Загрузка сравнения...">
            <div style={{ minHeight: 200 }} />
          </Spin>
        </div>
      ) : isError || !comparison ? (
        <Alert
          message="Ошибка загрузки"
          description={error instanceof Error ? error.message : 'Не удалось загрузить сравнение версий'}
          type="error"
          showIcon
        />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Version Info */}
          <Row gutter={16}>
            <Col span={12}>
              <Card size="small">
                <Descriptions title="Версия 1" size="small" column={1}>
                  <Descriptions.Item label="Название">
                    {comparison.version1.version_name || `Версия ${comparison.version1.version_number}`}
                  </Descriptions.Item>
                  <Descriptions.Item label="Статус">
                    <Tag>{comparison.version1.status}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Итого">
                    {currencyFormatter.format(Number(comparison.version1.total_amount || 0))}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small">
                <Descriptions title="Версия 2" size="small" column={1}>
                  <Descriptions.Item label="Название">
                    {comparison.version2.version_name || `Версия ${comparison.version2.version_number}`}
                  </Descriptions.Item>
                  <Descriptions.Item label="Статус">
                    <Tag>{comparison.version2.status}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Итого">
                    {currencyFormatter.format(Number(comparison.version2.total_amount || 0))}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>

          {/* Summary */}
          <Card>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Общая разница"
                  value={Number(comparison.total_difference_amount || 0)}
                  precision={0}
                  valueStyle={{
                    color: Number(comparison.total_difference_amount || 0) > 0 ? '#cf1322' : '#3f8600',
                  }}
                  prefix={Number(comparison.total_difference_amount || 0) > 0 ? '+' : ''}
                  suffix="₽"
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Изменение"
                  value={Math.abs(totalDifferencePercent * 100)}
                  precision={1}
                  valueStyle={{
                    color: totalDifferencePercent > 0 ? '#cf1322' : '#3f8600',
                  }}
                  prefix={
                    totalDifferencePercent > 0 ? (
                      <ArrowUpOutlined />
                    ) : totalDifferencePercent < 0 ? (
                      <ArrowDownOutlined />
                    ) : null
                  }
                  suffix="%"
                />
              </Col>
            </Row>
          </Card>

          {/* Comparison Table */}
          <ResponsiveTable
            columns={columns}
            dataSource={sortedCategories}
            rowKey="category_id"
            pagination={false}
            scroll={{ y: 400 }}
            bordered
            size="small"
          />
        </Space>
      )}
    </Modal>
  )
}

export default BudgetVersionComparisonModal
