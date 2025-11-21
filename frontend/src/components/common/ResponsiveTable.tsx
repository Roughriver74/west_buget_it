import React, { useMemo } from 'react'
import { Table, Card, Space, Typography, Row, Col, TableProps } from 'antd'
import type { ColumnsType, ColumnType } from 'antd/es/table'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'

const { Text } = Typography

export interface ResponsiveTableProps<T = any> extends TableProps<T> {
  /**
   * Layout mode on mobile devices
   * - 'card': Display each row as a card (best for 5-10 columns)
   * - 'compact': Show table with reduced columns (best for 3-5 important columns)
   * - 'scroll': Keep table but allow horizontal scroll (default)
   */
  mobileLayout?: 'card' | 'compact' | 'scroll'

  /**
   * Columns to show in compact mode (by key)
   * If not provided, shows first 3 columns
   */
  compactColumns?: string[]

  /**
   * Custom card renderer for mobile
   */
  renderMobileCard?: (record: T, index: number) => React.ReactNode
}

/**
 * ResponsiveTable - Responsive wrapper around Ant Design Table
 *
 * Automatically switches layout based on screen size:
 * - Desktop: Full table
 * - Mobile: Card layout, Compact table, or Scrollable table
 *
 * @example
 * ```tsx
 * <ResponsiveTable
 *   columns={columns}
 *   dataSource={data}
 *   mobileLayout="card"
 *   sticky={{ offsetHeader: isMobile ? 48 : 64 }}
 * />
 * ```
 */
export function ResponsiveTable<T extends Record<string, any>>({
  mobileLayout = 'scroll',
  compactColumns,
  renderMobileCard,
  columns = [],
  dataSource = [],
  scroll,
  sticky,
  ...restProps
}: ResponsiveTableProps<T>) {
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  // Card Layout for Mobile
  const cardLayout = useMemo(() => {
    if (!isMobile || mobileLayout !== 'card') return null

    const renderCard = renderMobileCard || defaultCardRenderer

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {dataSource.map((record, index) => (
          <Card
            key={record.key || record.id || index}
            size="small"
            hoverable
            style={{ width: '100%' }}
          >
            {renderCard(record, index)}
          </Card>
        ))}
      </Space>
    )
  }, [isMobile, mobileLayout, dataSource, renderMobileCard])

  // Default card renderer
  const defaultCardRenderer = (record: T, _index: number) => {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {(columns as ColumnsType<T>).map((col: ColumnType<T>) => {
          if (!col.dataIndex && !col.render) return null

          const key = Array.isArray(col.dataIndex)
            ? col.dataIndex.join('.')
            : String(col.dataIndex || col.key)

          let value: React.ReactNode
          if (col.render) {
            value = col.render(record[key], record, _index)
          } else {
            value = record[key]
          }

          return (
            <Row key={key} gutter={[8, 8]}>
              <Col span={10}>
                <Text strong>{col.title as string}:</Text>
              </Col>
              <Col span={14}>
                <Text>{value}</Text>
              </Col>
            </Row>
          )
        })}
      </Space>
    )
  }

  // Compact Layout (show only important columns)
  const compactTableColumns = useMemo(() => {
    if (!isSmallScreen || mobileLayout !== 'compact') return columns

    if (compactColumns && compactColumns.length > 0) {
      return (columns as ColumnsType<T>).filter((col) => {
        const key = col.key || col.dataIndex
        return compactColumns.includes(String(key))
      })
    }

    // Show first 3 columns by default
    return (columns as ColumnsType<T>).slice(0, 3)
  }, [isSmallScreen, mobileLayout, columns, compactColumns])

  // Adjust scroll and sticky for mobile
  const responsiveScroll = useMemo(() => {
    if (!scroll) return undefined

    if (isMobile) {
      return {
        ...scroll,
        x: mobileLayout === 'scroll' ? scroll.x : undefined,
        y: 400, // Reduce height on mobile
      }
    }

    return scroll
  }, [isMobile, mobileLayout, scroll])

  const responsiveSticky = useMemo(() => {
    if (!sticky) return undefined

    if (isMobile) {
      return {
        ...sticky,
        offsetHeader: typeof sticky === 'object' ? 48 : sticky, // Mobile header height
      }
    }

    return sticky
  }, [isMobile, sticky])

  // Render card layout on mobile
  if (isMobile && mobileLayout === 'card') {
    return <>{cardLayout}</>
  }

  // Render compact or scroll table
  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <Table<T>
        {...restProps}
        columns={mobileLayout === 'compact' ? compactTableColumns : columns}
        dataSource={dataSource}
        scroll={responsiveScroll}
        sticky={responsiveSticky}
        pagination={
          restProps.pagination === false
            ? false
            : {
                ...restProps.pagination,
                // Reduce page size on mobile
                pageSize: isMobile ? 10 : (restProps.pagination as any)?.pageSize || 20,
                showSizeChanger: !isMobile,
                showQuickJumper: !isMobile,
                // Simple pagination on mobile
                simple: isMobile,
              }
        }
      />
    </div>
  )
}

export default ResponsiveTable
