/**
 * Budget Plan Details Table Component
 * Editable table for monthly budget planning by category
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Table, InputNumber, Button, Space, message, Typography } from 'antd'
import { SaveOutlined, UndoOutlined, DownOutlined, RightOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { usePlanDetails, useCreatePlanDetail, useUpdatePlanDetail } from '@/hooks/useBudgetPlanning'
import type { BudgetPlanDetailCreate, BudgetPlanDetailUpdate } from '@/types/budgetPlanning'
import { ExpenseType } from '@/types/budgetPlanning'

const { Text } = Typography

const CATEGORY_COLUMN_WIDTH = 320
const MONTH_COLUMN_WIDTH = 140
const TOTAL_COLUMN_WIDTH = 180

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat('ru-RU', {
  maximumFractionDigits: 0,
})

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

interface Category {
  id: number
  name: string
  type: ExpenseType
  parentId: number | null
}

interface BudgetPlanDetailsTableProps {
  versionId: number
  categories: Category[]
  isEditable: boolean
  onAfterSave?: () => void
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

export const BudgetPlanDetailsTable: React.FC<BudgetPlanDetailsTableProps> = ({
  versionId,
  categories,
  isEditable,
  onAfterSave,
}) => {
  const { data: planDetails = [], isLoading } = usePlanDetails(versionId)
  const createMutation = useCreatePlanDetail()
  const updateMutation = useUpdatePlanDetail()

  const [data, setData] = useState<CategoryRow[]>([])
  const [changedCells, setChangedCells] = useState<Set<string>>(new Set())
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())

  const { orderedCategories, descendantsMap } = useMemo(() => {
    if (!categories.length) {
      return {
        orderedCategories: [] as Array<Category & { level: number; hasChildren: boolean }>,
        descendantsMap: new Map<number, number[]>(),
      }
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

    return orderedCategories.map((category) => {
      const row: CategoryRow = {
        categoryId: category.id,
        categoryName: category.name,
        categoryType: category.type,
        categoryLevel: category.level,
        hasChildren: category.hasChildren,
        descendantIds: descendantsMap.get(category.id) ?? [],
        parentId: category.parentId ?? null,
      }

      MONTHS.forEach((month) => {
        row[`month_${month.key}`] = 0
      })

      const categoryDetails = planDetails.filter((d) => d.category_id === category.id)
      categoryDetails.forEach((detail) => {
        const amount = Number(detail.planned_amount ?? 0)
        row[`month_${detail.month}`] = amount
        row[`detail_${detail.month}_id`] = detail.id
      })

      return row
    })
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

  const visibleData = useMemo(() => data.filter(isRowVisible), [data, isRowVisible])

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
            [`month_${month}`]: Number(value ?? 0),
          }
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
        type: row.categoryType,
      }

      if (detailId) {
        if (row.hasChildren) {
          return
        }
        // Update existing detail
        updates.push({
          id: detailId,
          data: {
            planned_amount: plannedAmount,
            type: row.categoryType,
          },
        })
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
          id: update.id,
        }))
      )

      const createPromises = creations.map((payload) =>
        createMutation.mutateAsync(payload).catch((err) => ({
          error: err,
          type: 'create' as const,
          payload,
        }))
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
      return row.descendantIds.reduce((sum, id) => {
        const child = dataById.get(id)
        if (!child) return sum
        // Only sum leaf nodes (non-parent categories)
        if (!child.hasChildren) {
          return sum + Number(child[`month_${monthKey}`] || 0)
        }
        return sum
      }, 0)
    },
    [dataById]
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
      const total = data
        .filter((row) => !row.hasChildren)
        .reduce((sum, row) => sum + Number(row[`month_${month.key}`] || 0), 0)
      totals.set(month.key, total)
    })
    return totals
  }, [data])

  // Calculate grand total (memoized)
  const grandTotal = useMemo(() => {
    return data
      .filter((row) => !row.hasChildren)
      .reduce((sum, row) => sum + getRowTotal(row), 0)
  }, [data, getRowTotal])

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
              gap: 8,
            }}
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
            <div>
              <div>{record.categoryName}</div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.categoryType}
              </Text>
            </div>
          </div>
        )
      },
    },
    ...MONTHS.map((month) => ({
      title: month.label,
      dataIndex: `month_${month.key}`,
      key: `month_${month.key}`,
      width: MONTH_COLUMN_WIDTH,
      align: 'right' as const,
      render: (_value: number, record: CategoryRow) => {
        const displayValue = getMonthValue(record, month.key)
        const formatted = formatNumber(Number(displayValue ?? 0))

        if (!isEditable || record.hasChildren) {
          return <Text>{formatted}</Text>
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
              backgroundColor: isChanged ? '#fff7e6' : undefined,
            }}
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value || '').replace(/\s/g, ''))}
            min={0}
          />
        )
      },
    })),
    {
      title: 'Итого',
      key: 'total',
      fixed: 'right',
      width: TOTAL_COLUMN_WIDTH,
      align: 'right' as const,
      render: (_, record) => (
        <Text strong>{formatCurrency(getRowTotal(record))}</Text>
      ),
    },
  ]

  const summaryRow = (
    <Table.Summary fixed>
      <Table.Summary.Row style={{ backgroundColor: '#fafafa' }}>
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
    <div style={{ overflowX: 'auto' }}>
      {isEditable && changedCells.size > 0 && (
        <Space style={{ marginBottom: 16 }}>
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

      <Table
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
  )
}
