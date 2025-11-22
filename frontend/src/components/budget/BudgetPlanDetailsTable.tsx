/**
 * Budget Plan Details Table Component
 * Editable table for monthly budget planning by category
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { InputNumber, Button, Space, message, Typography, Segmented, Checkbox, Tag, theme, Table } from 'antd'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { SaveOutlined, UndoOutlined, DownOutlined, RightOutlined, LeftOutlined, CalendarOutlined, DownloadOutlined, AppstoreAddOutlined, PlusOutlined } from '@ant-design/icons'
import { LoadBaselineModal } from './LoadBaselineModal'
import { ManageCategoriesModal } from './ManageCategoriesModal'
import { CreateCategoryModal } from './CreateCategoryModal'
import type { ColumnsType } from 'antd/es/table'
import { usePlanDetails, useCreatePlanDetail, useUpdatePlanDetail } from '@/hooks/useBudgetPlanning'
import type { BudgetPlanDetailCreate, BudgetPlanDetailUpdate } from '@/types/budgetPlanning'
import { ExpenseType, type NumericValue } from '@/types/budgetPlanning'
import { useTheme } from '@/contexts/ThemeContext'

const { Text } = Typography

const CATEGORY_COLUMN_WIDTH = 320
const MONTH_COLUMN_WIDTH = 140
const TOTAL_COLUMN_WIDTH = 180
const STICKY_HEADER_OFFSET = 64
const CONTROL_PANEL_HEIGHT = 100

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0})

const numberFormatter = new Intl.NumberFormat('ru-RU', {
  maximumFractionDigits: 0})

const formatCurrency = (value: number) => currencyFormatter.format(Number.isFinite(value) ? value : 0)
const formatNumber = (value: number) => numberFormatter.format(Number.isFinite(value) ? value : 0)

const MONTHS = [
  { key: 1, label: 'Январь' },
  { key: 2, label: 'Февраль' },
  { key: 3, label: 'Март' },
  { key: 4, label: 'Апрель' },
  { key: 5, label: 'Май' },
  { key: 6, label: 'Июнь' },
  { key: 7, label: 'Июль' },
  { key: 8, label: 'Август' },
  { key: 9, label: 'Сентябрь' },
  { key: 10, label: 'Октябрь' },
  { key: 11, label: 'Ноябрь' },
  { key: 12, label: 'Декабрь' },
]

const MONTH_SHORT_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const MONTH_SEGMENT_OPTIONS = MONTH_SHORT_NAMES.map((label, index) => ({ label, value: index + 1 }))

interface Category {
  id: number
  name: string
  type: ExpenseType
  parentId: number | null
}

interface PayrollMonthlySummary {
  month: number
  total_planned: NumericValue
}

interface PayrollYearlySummary {
  year: number
  total_employees: number
  total_planned_annual: NumericValue
  total_base_salary_annual: NumericValue
  total_bonuses_annual: NumericValue
  monthly_breakdown: PayrollMonthlySummary[]
}

interface BudgetPlanDetailsTableProps {
  versionId: number
  year: number
  categories: Category[]
  isEditable: boolean
  onAfterSave?: () => void
  onRiskPremiumChange?: (enabled: boolean) => void
  payrollSummary?: PayrollYearlySummary | null
}

interface CategoryRow {
  categoryId: number
  categoryName: string
  categoryType: ExpenseType
  categoryLevel: number
  hasChildren: boolean
  descendantIds: number[]
  parentId: number | null
  [key: string]: any // For month values (month_1, month_2, etc.)
}

export const BudgetPlanDetailsTable = React.forwardRef<
  { scrollBy: (direction: 'left' | 'right') => void },
  BudgetPlanDetailsTableProps
>(({
  versionId,
  year,
  categories,
  isEditable,
  onAfterSave,
  onRiskPremiumChange,
  payrollSummary}, ref) => {
  const { data: planDetails = [], isLoading } = usePlanDetails(versionId)
  const createMutation = useCreatePlanDetail()
  const updateMutation = useUpdatePlanDetail()

  const [data, setData] = useState<CategoryRow[]>([])
  const [changedCells, setChangedCells] = useState<Set<string>>(new Set())
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())

  const { mode } = useTheme()
  const { token } = theme.useToken()

  // Scroll state and refs
  const currentMonth = new Date().getMonth() + 1
  const [activeMonth, setActiveMonth] = useState<number>(currentMonth)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const scrollTargetRef = useRef<HTMLDivElement | null>(null)
  const isInitialMount = useRef(true)
  const sentinelRef = useRef<HTMLDivElement>(null)

  // Risk premium state
  const [riskEnabled, setRiskEnabled] = useState<boolean>(false)

  // Notify parent when risk premium changes
  useEffect(() => {
    onRiskPremiumChange?.(riskEnabled)
  }, [riskEnabled, onRiskPremiumChange])

  // Sticky state
  const [isSticky, setIsSticky] = useState<boolean>(false)

  // Load baseline modal state
  const [baselineModalOpen, setBaselineModalOpen] = useState<boolean>(false)

  // Manage categories modal state
  const [manageCategoriesOpen, setManageCategoriesOpen] = useState<boolean>(false)

  // Create category modal state
  const [createCategoryOpen, setCreateCategoryOpen] = useState<boolean>(false)

  const { orderedCategories, descendantsMap } = useMemo(() => {
    if (!categories.length) {
      return {
        orderedCategories: [] as Array<Category & { level: number; hasChildren: boolean }>,
        descendantsMap: new Map<number, number[]>()}
    }

    const byParent = new Map<number | null, Category[]>()
    categories.forEach((cat) => {
      const parentKey = cat.parentId ?? null
      if (!byParent.has(parentKey)) {
        byParent.set(parentKey, [])
      }
      byParent.get(parentKey)!.push(cat)
    })

    const result: Array<Category & { level: number; hasChildren: boolean }> = []
    const visited = new Set<number>()
    const descendantsMap = new Map<number, number[]>()

    const visit = (cat: Category, level: number): number[] => {
      if (visited.has(cat.id)) {
        return descendantsMap.get(cat.id) ?? []
      }
      visited.add(cat.id)
      const children = byParent.get(cat.id) ?? []
      result.push({ ...cat, level, hasChildren: children.length > 0 })
      const descendants: number[] = []
      children.forEach((child) => {
        const childDesc = visit(child, level + 1)
        if (childDesc.length > 0) {
          descendants.push(...childDesc)
        } else {
          descendants.push(child.id)
        }
      })
      descendantsMap.set(cat.id, descendants)
      return descendants
    }

    const rootNodes = byParent.get(null) ?? []
    rootNodes.forEach((root) => visit(root, 0))

    categories.forEach((cat) => {
      if (!visited.has(cat.id)) {
        visit(cat, 0)
      }
    })

    return { orderedCategories: result, descendantsMap }
  }, [categories])

  const buildRows = useCallback((): CategoryRow[] => {
    if (orderedCategories.length === 0) {
      return []
    }

    // Get set of category IDs that have plan details (used in this version)
    const categoriesWithData = new Set(planDetails.map(d => d.category_id))

    // Build all rows first
    const allRows = orderedCategories.map((category) => {
      const row: CategoryRow = {
        categoryId: category.id,
        categoryName: category.name,
        categoryType: category.type,
        categoryLevel: category.level,
        hasChildren: category.hasChildren,
        descendantIds: descendantsMap.get(category.id) ?? [],
        parentId: category.parentId ?? null}

      // Initialize all months with 0
      MONTHS.forEach((month) => {
        row[`month_${month.key}`] = 0
      })

      // Fill with actual data from plan details
      const categoryDetails = planDetails.filter((d) => d.category_id === category.id)
      categoryDetails.forEach((detail) => {
        const amount = Number(detail.planned_amount ?? 0)
        row[`month_${detail.month}`] = amount
        row[`detail_${detail.month}_id`] = detail.id
      })

      return row
    })

    // Filter: show only categories that have data OR parent categories with children that have data
    const hasDataInSubtree = (categoryId: number): boolean => {
      if (categoriesWithData.has(categoryId)) return true
      const descendants = descendantsMap.get(categoryId) ?? []
      return descendants.some(descId => categoriesWithData.has(descId))
    }

    return allRows.filter(row => hasDataInSubtree(row.categoryId))
  }, [orderedCategories, planDetails, descendantsMap])

  // Initialize data from categories and plan details
  useEffect(() => {
    setData(buildRows())
    setChangedCells(new Set())
  }, [buildRows])

  useEffect(() => {
    setCollapsed(new Set())
  }, [versionId])

  const dataById = useMemo(() => new Map(data.map((row) => [row.categoryId, row])), [data])

  const parentLookup = useMemo(() => new Map(data.map((row) => [row.categoryId, row.parentId])), [data])

  const isRowVisible = useCallback(
    (row: CategoryRow) => {
      let parentId = row.parentId
      while (parentId) {
        if (collapsed.has(parentId)) {
          return false
        }
        parentId = parentLookup.get(parentId) ?? null
      }
      return true
    },
    [collapsed, parentLookup]
  )

  // Create synthetic payroll row
  const payrollRow = useMemo((): CategoryRow | null => {
    if (!payrollSummary) return null

    const row: CategoryRow = {
      categoryId: -1, // Special ID for payroll
      categoryName: 'ФОТ (Фонд оплаты труда)',
      categoryType: ExpenseType.OPEX,
      categoryLevel: 0,
      hasChildren: false,
      descendantIds: [],
      parentId: null}

    // Initialize all months to 0
    MONTHS.forEach((month) => {
      row[`month_${month.key}`] = 0
    })

    // Fill with payroll data
    if (payrollSummary.monthly_breakdown) {
      payrollSummary.monthly_breakdown.forEach((monthData) => {
        row[`month_${monthData.month}`] = Number(monthData.total_planned ?? 0)
      })
    }

    return row
  }, [payrollSummary])

  const visibleData = useMemo(() => {
    const filtered = data.filter(isRowVisible)
    // Add payroll row at the end if it exists
    if (payrollRow) {
      return [...filtered, payrollRow]
    }
    return filtered
  }, [data, isRowVisible, payrollRow])

  const toggleCollapse = useCallback((categoryId: number) => {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(categoryId)) {
        next.delete(categoryId)
      } else {
        next.add(categoryId)
      }
      return next
    })
  }, [])

  const handleCellChange = (categoryId: number, month: number, value: number | null) => {
    const cellKey = `${categoryId}_${month}`
    setChangedCells((prev) => new Set(prev).add(cellKey))

    setData((prevData) =>
      prevData.map((row) => {
        if (row.categoryId === categoryId) {
          if (row.hasChildren) {
            return row
          }
          return {
            ...row,
            [`month_${month}`]: Number(value ?? 0)}
        }
        return row
      })
    )
  }

  const handleSave = async () => {
    const updates: Array<{ id: number; data: BudgetPlanDetailUpdate }> = []
    const creations: BudgetPlanDetailCreate[] = []

    // Collect all changed cells
    changedCells.forEach((cellKey) => {
      const [categoryIdStr, monthStr] = cellKey.split('_')
      const categoryId = parseInt(categoryIdStr)
      const month = parseInt(monthStr)

      const row = data.find((r) => r.categoryId === categoryId)
      if (!row) return

      const detailId = row[`detail_${month}_id`]
      const plannedAmount = Number(row[`month_${month}`] || 0)
      const baseCreatePayload: BudgetPlanDetailCreate = {
        version_id: versionId,
        category_id: categoryId,
        month,
        planned_amount: plannedAmount,
        type: row.categoryType}

      if (detailId) {
        if (row.hasChildren) {
          return
        }
        // Update existing detail
        updates.push({
          id: detailId,
          data: {
            planned_amount: plannedAmount,
            type: row.categoryType}})
      } else {
        if (row.hasChildren && plannedAmount === 0) {
          return
        }
        // Create new detail
        creations.push(baseCreatePayload)
      }
    })

    const totalChanges = updates.length + creations.length

    if (totalChanges === 0) {
      message.info('Нет изменений для сохранения')
      return
    }

    try {
      // Execute all updates in parallel
      const updatePromises = updates.map((update) =>
        updateMutation.mutateAsync({ id: update.id, data: update.data }).catch((err) => ({
          error: err,
          type: 'update' as const,
          id: update.id}))
      )

      const createPromises = creations.map((payload) =>
        createMutation.mutateAsync(payload).catch((err) => ({
          error: err,
          type: 'create' as const,
          payload}))
      )

      const results = await Promise.all([...updatePromises, ...createPromises])

      // Check for errors
      const errors = results.filter((r) => r && 'error' in r)

      if (errors.length > 0) {
        message.error(`Ошибка при сохранении ${errors.length} из ${totalChanges} изменений`)
        console.error('Ошибки сохранения:', errors)
        // Don't clear changed cells if there were errors
        return
      }

      setChangedCells(new Set())
      message.success(`Сохранено ${totalChanges} изменений`)
      onAfterSave?.()
    } catch (error) {
      message.error('Ошибка при сохранении')
      console.error('Ошибка сохранения:', error)
    }
  }

  const handleReset = () => {
    setChangedCells(new Set())
    setData(buildRows())
    message.info('Изменения отменены')
  }

  // Get month value for a row (handles both leaf and parent categories)
  const getMonthValue = useCallback(
    (row: CategoryRow, monthKey: number): number => {
      if (!row.hasChildren) {
        return Number(row[`month_${monthKey}`] || 0)
      }

      // For parent categories, sum values of all leaf descendants
      let sum = row.descendantIds.reduce((acc, id) => {
        const child = dataById.get(id)
        if (!child) return acc
        // Only sum leaf nodes (non-parent categories)
        if (!child.hasChildren) {
          return acc + Number(child[`month_${monthKey}`] || 0)
        }
        return acc
      }, 0)

      // Apply 10% risk premium if enabled for parent categories
      if (riskEnabled) {
        sum = sum * 1.1
      }

      return sum
    },
    [dataById, riskEnabled]
  )

  // Calculate row total (memoized)
  const getRowTotal = useCallback(
    (row: CategoryRow) => {
      return MONTHS.reduce((sum, month) => sum + getMonthValue(row, month.key), 0)
    },
    [getMonthValue]
  )

  // Calculate column totals (memoized)
  const columnTotals = useMemo(() => {
    const totals = new Map<number, number>()
    MONTHS.forEach((month) => {
      let total = data
        .filter((row) => !row.hasChildren)
        .reduce((sum, row) => sum + Number(row[`month_${month.key}`] || 0), 0)

      // Apply 10% risk premium if enabled
      if (riskEnabled) {
        total = total * 1.1
      }

      totals.set(month.key, total)
    })
    return totals
  }, [data, riskEnabled])

  // Calculate grand total (memoized)
  const grandTotal = useMemo(() => {
    let total = data
      .filter((row) => !row.hasChildren)
      .reduce((sum, row) => sum + getRowTotal(row), 0)

    // Apply 10% risk premium if enabled
    if (riskEnabled) {
      total = total * 1.1
    }

    return total
  }, [data, getRowTotal, riskEnabled])

  // Scroll functions (similar to BudgetPlanTable)
  const resolveScrollTarget = useCallback(() => {
    const container = scrollContainerRef.current
    if (!container) return null
    const content = container.querySelector<HTMLDivElement>('.ant-table-content')
    const body = container.querySelector<HTMLDivElement>('.ant-table-body')
    return content ?? body ?? container
  }, [])

  const scrollToMonth = useCallback((month: number, behavior: ScrollBehavior = 'smooth', retryCount: number = 0) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setTimeout(() => {
          const target = scrollTargetRef.current ?? scrollContainerRef.current
          if (!target) {
            console.warn('Scroll target not found')
            return
          }

          const tableBody = target.querySelector('.ant-table-body')
          if (!tableBody && retryCount < 5) {
            console.warn(`Table body not found, retrying... (${retryCount + 1}/5)`)
            setTimeout(() => {
              scrollToMonth(month, behavior, retryCount + 1)
            }, 100)
            return
          }

          const approximateCenterOffset = target.clientWidth * 0.25
          const columnOffset = Math.max(0, (month - 1) * MONTH_COLUMN_WIDTH - approximateCenterOffset)
          target.scrollTo({ left: columnOffset, behavior })
        }, 200)
      })
    })
  }, [])

  const handleMonthSelect = useCallback(
    (month: number) => {
      setActiveMonth(month)
      scrollToMonth(month)
    },
    [scrollToMonth]
  )

  const handleResetMonth = useCallback(() => {
    setActiveMonth(currentMonth)
    scrollToMonth(currentMonth)
  }, [currentMonth, scrollToMonth])

  // Scroll left/right by viewport width
  const scrollBy = useCallback((direction: 'left' | 'right') => {
    const target = scrollTargetRef.current ?? scrollContainerRef.current
    if (!target) return
    const step = target.clientWidth * 0.6
    const delta = direction === 'left' ? -step : step
    target.scrollBy({ left: delta, behavior: 'smooth' })
  }, [])

  // Expose scrollBy method to parent via ref
  React.useImperativeHandle(
    ref,
    () => ({
      scrollBy}),
    [scrollBy]
  )

  // Initialize scroll target and scroll to active month on mount
  useEffect(() => {
    const target = resolveScrollTarget()
    if (!target) return

    scrollTargetRef.current = target

    if (isInitialMount.current && planDetails.length > 0) {
      scrollToMonth(activeMonth, 'auto')
      isInitialMount.current = false
    }
  }, [planDetails, resolveScrollTarget, scrollToMonth, activeMonth])

  // Smooth scroll when active month changes
  useEffect(() => {
    if (!planDetails.length || isInitialMount.current) return

    const timer = setTimeout(() => {
      scrollToMonth(activeMonth, 'smooth')
    }, 50)

    return () => clearTimeout(timer)
  }, [activeMonth, planDetails, scrollToMonth])

  // IntersectionObserver for sticky behavior
  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        // When sentinel top crosses the sticky position threshold, make panel sticky
        // entry.boundingClientRect.top <= STICKY_HEADER_OFFSET means we've scrolled past it
        setIsSticky(entry.boundingClientRect.top <= STICKY_HEADER_OFFSET)
      },
      {
        threshold: [0, 1],
        // Check when sentinel crosses the sticky threshold (64px from top)
        rootMargin: '0px 0px 0px 0px'}
    )

    observer.observe(sentinel)

    return () => {
      observer.disconnect()
    }
  }, [])

  const columns: ColumnsType<CategoryRow> = [
    {
      title: 'Категория',
      dataIndex: 'categoryName',
      key: 'categoryName',
      fixed: 'left',
      width: CATEGORY_COLUMN_WIDTH,
      render: (_text, record) => {
        const isCollapsed = collapsed.has(record.categoryId)
        return (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              paddingLeft: record.categoryLevel * 16,
              fontWeight: record.hasChildren ? 600 : undefined,
              gap: 8}}
          >
            {record.hasChildren && (
              <span
                onClick={() => toggleCollapse(record.categoryId)}
                style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}
              >
                {isCollapsed ? <RightOutlined /> : <DownOutlined />}
              </span>
            )}
            {!record.hasChildren && <span style={{ width: 14 }} />}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>{record.categoryName}</span>
                {record.hasChildren && riskEnabled && (
                  <Tag color="orange" style={{ fontSize: 11 }}>Риск +10%</Tag>
                )}
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.categoryType}
              </Text>
            </div>
          </div>
        )
      }},
    ...MONTHS.map((month) => ({
      title: month.label,
      dataIndex: `month_${month.key}`,
      key: `month_${month.key}`,
      width: MONTH_COLUMN_WIDTH,
      align: 'right' as const,
      className: activeMonth === month.key ? 'active-month-header' : undefined,
      onHeaderCell: () => ({
        className: activeMonth === month.key ? 'active-month-header' : undefined}),
      onCell: () => ({
        className: activeMonth === month.key ? 'active-month-cell' : undefined}),
      render: (_value: number, record: CategoryRow) => {
        const displayValue = getMonthValue(record, month.key)
        const formatted = formatNumber(Number(displayValue ?? 0))

        // Make payroll row (id = -1) readonly, also parent rows and when not editable
        if (!isEditable || record.hasChildren || record.categoryId === -1) {
          return (
            <Text style={{
              fontWeight: record.categoryId === -1 ? 600 : undefined,
              color: record.categoryId === -1 ? (mode === 'dark' ? '#1890ff' : '#0050b3') : undefined
            }}>
              {formatted}
            </Text>
          )
        }

        const cellKey = `${record.categoryId}_${month.key}`
        const isChanged = changedCells.has(cellKey)
        const inputValue = Number(record[`month_${month.key}`] || 0)

        return (
          <InputNumber
            value={inputValue}
            onChange={(val) => handleCellChange(record.categoryId, month.key, val)}
            style={{
              width: '100%',
              backgroundColor: isChanged ? (mode === 'dark' ? 'rgba(250, 173, 20, 0.15)' : '#fff7e6') : undefined}}
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value || '').replace(/\s/g, ''))}
            min={0}
          />
        )
      }})),
    {
      title: 'Итого',
      key: 'total',
      fixed: 'right',
      width: TOTAL_COLUMN_WIDTH,
      align: 'right' as const,
      render: (_, record) => (
        <Text strong>{formatCurrency(getRowTotal(record))}</Text>
      )},
  ]

  const summaryRow = (
    <Table.Summary fixed>
      <Table.Summary.Row style={{ backgroundColor: mode === 'dark' ? '#262626' : '#fafafa' }}>
        <Table.Summary.Cell index={0}>
          <Text strong>Итого по месяцам</Text>
        </Table.Summary.Cell>
        {MONTHS.map((month, index) => (
          <Table.Summary.Cell key={month.key} index={index + 1} align="right">
            <Text strong>{formatCurrency(columnTotals.get(month.key) || 0)}</Text>
          </Table.Summary.Cell>
        ))}
        <Table.Summary.Cell index={13} align="right">
          <Text strong style={{ fontSize: 16 }}>{formatCurrency(grandTotal)}</Text>
        </Table.Summary.Cell>
      </Table.Summary.Row>
    </Table.Summary>
  )

  const tableScrollX =
    CATEGORY_COLUMN_WIDTH + MONTHS.length * MONTH_COLUMN_WIDTH + TOTAL_COLUMN_WIDTH + 120

  return (
    <div>
      {/* Sentinel element for IntersectionObserver - marks where sticky behavior should activate */}
      <div
        ref={sentinelRef}
        style={{
          height: 0,
          overflow: 'hidden',
          pointerEvents: 'none'}}
      />

      {/* Sticky Control Panel */}
      <div
        style={{
          position: isSticky ? 'sticky' : 'relative',
          top: isSticky ? STICKY_HEADER_OFFSET : undefined,
          zIndex: isSticky ? 10 : 1,
          backgroundColor: token.colorBgContainer,
          paddingTop: 1,
          paddingBottom: 12,
          marginTop: isSticky ? 0 : 60,
          marginBottom: isSticky ? 16 : 0,
          borderBottom: `2px solid ${token.colorBorderSecondary}`,
          boxShadow: isSticky ? '0 2px 8px rgba(0, 0, 0, 0.06)' : 'none'}}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 16,
            flexWrap: 'wrap',
            marginBottom: 12}}
        >
          <Space size="middle" align="center" wrap>
            <span style={{ fontWeight: 500 }}>Месяц:</span>
            <Space.Compact>
              <Button
                icon={<LeftOutlined />}
                onClick={() => scrollBy('left')}
                title="Прокрутить влево"
              />
              <div style={{ overflowX: 'auto', paddingBottom: 4 }}>
                <Segmented
                  options={MONTH_SEGMENT_OPTIONS}
                  value={activeMonth}
                  onChange={(value) => handleMonthSelect(Number(value))}
                />
              </div>
              <Button
                icon={<RightOutlined />}
                onClick={() => scrollBy('right')}
                title="Прокрутить вправо"
              />
            </Space.Compact>
          </Space>

          <Space size="middle">
            <Checkbox
              checked={riskEnabled}
              onChange={(e) => setRiskEnabled(e.target.checked)}
            >
              <span style={{ fontWeight: 500 }}>Риск +10%</span>
            </Checkbox>

            <Button
              type="link"
              icon={<CalendarOutlined />}
              onClick={handleResetMonth}
              style={{ padding: 0 }}
            >
              К текущему месяцу
            </Button>
          </Space>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
          <Space>
            {isEditable && (
              <>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateCategoryOpen(true)}
                >
                  Создать категорию
                </Button>
                <Button
                  icon={<AppstoreAddOutlined />}
                  onClick={() => setManageCategoriesOpen(true)}
                >
                  Управление категориями
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => setBaselineModalOpen(true)}
                >
                  Загрузить из {year - 1} года
                </Button>
              </>
            )}
          </Space>

          {isEditable && changedCells.size > 0 && (
            <Space>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={createMutation.isPending || updateMutation.isPending}
              >
                Сохранить ({changedCells.size})
              </Button>
              <Button icon={<UndoOutlined />} onClick={handleReset}>
                Отменить
              </Button>
            </Space>
          )}
        </div>
      </div>

      {/* Table Container with Scroll Ref */}
      <div
        ref={scrollContainerRef}
        style={{ width: '100%', maxWidth: '100%', position: 'relative' }}
      >
        <ResponsiveTable
          sticky={{ offsetHeader: STICKY_HEADER_OFFSET + CONTROL_PANEL_HEIGHT }}
          columns={columns}
          dataSource={visibleData}
          rowKey="categoryId"
          loading={isLoading}
          pagination={false}
          scroll={{ x: tableScrollX }}
          summary={() => summaryRow}
          bordered
          size="small"
          tableLayout="fixed"
        />
      </div>

      {/* CSS for Active Month Highlighting */}
      <style>{`
        ${mode === 'dark' ? `
          .active-month-header {
            background: linear-gradient(90deg, rgba(24, 144, 255, 0.25) 0%, rgba(24, 144, 255, 0.1) 100%) !important;
            color: #69b7ff !important;
            font-weight: 600 !important;
          }
          .active-month-cell {
            background-color: rgba(24, 144, 255, 0.15) !important;
            transition: background-color 0.2s ease;
          }
          .active-month-cell:hover {
            background-color: rgba(24, 144, 255, 0.25) !important;
          }
        ` : `
          .active-month-header {
            background: linear-gradient(90deg, rgba(24, 144, 255, 0.18) 0%, rgba(24, 144, 255, 0.05) 100%) !important;
            color: #0958d9 !important;
            font-weight: 600 !important;
          }
          .active-month-cell {
            background-color: rgba(222, 242, 255, 0.7) !important;
            transition: background-color 0.2s ease;
          }
          .active-month-cell:hover {
            background-color: rgba(184, 218, 255, 0.8) !important;
          }
        `}
      `}</style>

      {/* Load Baseline Modal */}
      <LoadBaselineModal
        open={baselineModalOpen}
        versionId={versionId}
        year={year}
        categories={categories}
        onClose={() => setBaselineModalOpen(false)}
        onSuccess={() => {
          onAfterSave?.()
        }}
      />

      {/* Manage Categories Modal */}
      <ManageCategoriesModal
        open={manageCategoriesOpen}
        versionId={versionId}
        categories={categories}
        planDetails={planDetails}
        onClose={() => setManageCategoriesOpen(false)}
        onSuccess={() => {
          onAfterSave?.()
        }}
      />

      {/* Create Category Modal */}
      <CreateCategoryModal
        open={createCategoryOpen}
        onClose={() => setCreateCategoryOpen(false)}
        onSuccess={() => {
          onAfterSave?.()
        }}
        categories={categories}
      />
    </div>
  )
})
