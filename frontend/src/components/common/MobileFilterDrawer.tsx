import React, { useState, ReactNode } from 'react'
import { Drawer, Button, Space, Badge } from 'antd'
import { FilterOutlined } from '@ant-design/icons'
import { useIsMobile } from '@/hooks/useMediaQuery'

export interface MobileFilterDrawerProps {
  /**
   * Filter panel content (form fields, selects, etc.)
   */
  children: ReactNode

  /**
   * Title of the filter drawer
   */
  title?: string

  /**
   * Number of active filters (for badge)
   */
  activeFilters?: number

  /**
   * Additional actions (Reset, Apply buttons)
   */
  actions?: ReactNode

  /**
   * Placement of drawer
   */
  placement?: 'top' | 'right' | 'bottom' | 'left'

  /**
   * Custom trigger button
   */
  triggerButton?: ReactNode

  /**
   * Callback when drawer opens
   */
  onOpen?: () => void

  /**
   * Callback when drawer closes
   */
  onClose?: () => void
}

/**
 * MobileFilterDrawer - Collapsible filter panel for mobile devices
 *
 * On desktop: Renders children directly (inline filters)
 * On mobile: Shows "Filters" button that opens a drawer
 *
 * @example
 * ```tsx
 * <MobileFilterDrawer
 *   title="Фильтры"
 *   activeFilters={3}
 *   actions={
 *     <Space>
 *       <Button onClick={handleReset}>Сбросить</Button>
 *       <Button type="primary" onClick={handleApply}>Применить</Button>
 *     </Space>
 *   }
 * >
 *   <Form layout="vertical">
 *     <Form.Item label="Статус">
 *       <Select options={statusOptions} />
 *     </Form.Item>
 *     <Form.Item label="Дата">
 *       <DatePicker.RangePicker />
 *     </Form.Item>
 *   </Form>
 * </MobileFilterDrawer>
 * ```
 */
export const MobileFilterDrawer: React.FC<MobileFilterDrawerProps> = ({
  children,
  title = 'Фильтры',
  activeFilters = 0,
  actions,
  placement = 'bottom',
  triggerButton,
  onOpen,
  onClose,
}) => {
  const isMobile = useIsMobile()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleOpen = () => {
    setDrawerOpen(true)
    onOpen?.()
  }

  const handleClose = () => {
    setDrawerOpen(false)
    onClose?.()
  }

  // On desktop, render filters inline
  if (!isMobile) {
    return (
      <div style={{ marginBottom: 16 }}>
        {children}
        {actions && (
          <div style={{ marginTop: 16 }}>
            {actions}
          </div>
        )}
      </div>
    )
  }

  // On mobile, render drawer
  return (
    <>
      {/* Trigger Button */}
      <div style={{ marginBottom: 16 }}>
        {triggerButton || (
          <Badge count={activeFilters} offset={[0, 0]}>
            <Button
              icon={<FilterOutlined />}
              onClick={handleOpen}
              block
              size="large"
            >
              {title}
              {activeFilters > 0 && ` (${activeFilters})`}
            </Button>
          </Badge>
        )}
      </div>

      {/* Filter Drawer */}
      <Drawer
        title={title}
        placement={placement}
        open={drawerOpen}
        onClose={handleClose}
        height={placement === 'top' || placement === 'bottom' ? '70vh' : undefined}
        width={placement === 'left' || placement === 'right' ? '85vw' : undefined}
        footer={
          actions ? (
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              {actions}
            </Space>
          ) : undefined
        }
        footerStyle={{ textAlign: 'right' }}
      >
        {children}
      </Drawer>
    </>
  )
}

export default MobileFilterDrawer
