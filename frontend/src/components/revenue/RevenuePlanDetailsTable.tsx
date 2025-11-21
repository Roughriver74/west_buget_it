/**
 * Revenue Plan Details Table Component
 * Editable table for monthly revenue planning by stream/category
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Table, InputNumber, Button, Space, message, Typography, Spin, Tag } from 'antd'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { SaveOutlined, UndoOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import { revenueApi } from '@/api/revenue'
import type {
  RevenuePlanDetail,
  RevenuePlanDetailCreate,
  RevenuePlanDetailUpdate,
  RevenueStream,
  RevenueCategory
} from '@/types/revenue'

const { Text } = Typography

const STREAM_COLUMN_WIDTH = 250
const CATEGORY_COLUMN_WIDTH = 200
const MONTH_COLUMN_WIDTH = 130
const TOTAL_COLUMN_WIDTH = 150

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

const formatCurrency = (value: number) =>
  currencyFormatter.format(Number.isFinite(value) ? value : 0)

const MONTHS = [
  { key: 1, label: 'Январь', short: 'Янв' },
  { key: 2, label: 'Февраль', short: 'Фев' },
  { key: 3, label: 'Март', short: 'Мар' },
  { key: 4, label: 'Апрель', short: 'Апр' },
  { key: 5, label: 'Май', short: 'Май' },
  { key: 6, label: 'Июнь', short: 'Июн' },
  { key: 7, label: 'Июль', short: 'Июл' },
  { key: 8, label: 'Август', short: 'Авг' },
  { key: 9, label: 'Сентябрь', short: 'Сен' },
  { key: 10, label: 'Октябрь', short: 'Окт' },
  { key: 11, label: 'Ноябрь', short: 'Ноя' },
  { key: 12, label: 'Декабрь', short: 'Дек' },
]

interface RevenuePlanDetailsTableProps {
  versionId: number
  streams: RevenueStream[]
  categories: RevenueCategory[]
  isEditable: boolean
  onAfterSave?: () => void
}

interface DetailRow extends RevenuePlanDetail {
  key: string
  streamName?: string
  categoryName?: string
  isNew?: boolean
}

export const RevenuePlanDetailsTable: React.FC<RevenuePlanDetailsTableProps> = ({
  versionId,
  streams,
  categories,
  isEditable,
  onAfterSave,
}) => {
  const queryClient = useQueryClient()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  // Fetch plan details
  const { data: planDetails = [], isLoading } = useQuery({
    queryKey: ['revenue-plan-details', versionId],
    queryFn: () => revenueApi.planDetails.getAll({ version_id: versionId }),
    enabled: !!versionId,
  })

  const [data, setData] = useState<DetailRow[]>([])
  const [changedCells, setChangedCells] = useState<Set<string>>(new Set())

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (detail: RevenuePlanDetailCreate) => revenueApi.planDetails.create(detail),
    onSuccess: () => {
      message.success('Строка добавлена')
      queryClient.invalidateQueries({ queryKey: ['revenue-plan-details'] })
      if (onAfterSave) onAfterSave()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, detail }: { id: number; detail: RevenuePlanDetailUpdate }) =>
      revenueApi.planDetails.update(id, detail),
    onSuccess: () => {
      message.success('Изменения сохранены')
      queryClient.invalidateQueries({ queryKey: ['revenue-plan-details'] })
      if (onAfterSave) onAfterSave()
    },
  })

  // Create stream/category lookup maps
  const streamMap = useMemo(() => {
    const map = new Map<number, RevenueStream>()
    streams.forEach((s) => map.set(s.id, s))
    return map
  }, [streams])

  const categoryMap = useMemo(() => {
    const map = new Map<number, RevenueCategory>()
    categories.forEach((c) => map.set(c.id, c))
    return map
  }, [categories])

  // Initialize data from planDetails
  useEffect(() => {
    const rows: DetailRow[] = planDetails.map((detail) => ({
      ...detail,
      key: `${detail.id}`,
      streamName: detail.revenue_stream_id ? streamMap.get(detail.revenue_stream_id)?.name : '—',
      categoryName: detail.revenue_category_id ? categoryMap.get(detail.revenue_category_id)?.name : '—',
    }))
    setData(rows)
    setChangedCells(new Set())
  }, [planDetails, streamMap, categoryMap])

  // Calculate totals
  const totals = useMemo(() => {
    const monthTotals: Record<string, number> = {}
    let grandTotal = 0

    MONTHS.forEach((month) => {
      const monthKey = `month_${String(month.key).padStart(2, '0')}`
      const monthSum = data.reduce((sum, row) => {
        const value = Number(row[monthKey as keyof DetailRow]) || 0
        return sum + value
      }, 0)
      monthTotals[monthKey] = monthSum
      grandTotal += monthSum
    })

    return { monthTotals, grandTotal }
  }, [data])

  // Handle cell change
  const handleCellChange = useCallback(
    (recordKey: string, field: string, value: number | null) => {
      const numValue = value ?? 0

      setData((prev) =>
        prev.map((row) => {
          if (row.key !== recordKey) return row

          const updated = { ...row, [field]: numValue }

          // Recalculate row total
          let rowTotal = 0
          MONTHS.forEach((month) => {
            const monthKey = `month_${String(month.key).padStart(2, '0')}`
            rowTotal += Number(updated[monthKey as keyof DetailRow]) || 0
          })
          updated.total = rowTotal

          return updated
        })
      )

      setChangedCells((prev) => new Set(prev).add(`${recordKey}_${field}`))
    },
    []
  )

  // Save changes
  const handleSave = useCallback(async () => {
    const changedRows = data.filter((row) =>
      MONTHS.some((month) => {
        const monthKey = `month_${String(month.key).padStart(2, '0')}`
        return changedCells.has(`${row.key}_${monthKey}`)
      })
    )

    if (changedRows.length === 0) {
      message.info('Нет изменений для сохранения')
      return
    }

    try {
      for (const row of changedRows) {
        if (row.isNew) {
          // Create new detail
          await createMutation.mutateAsync({
            version_id: versionId,
            revenue_stream_id: row.revenue_stream_id || undefined,
            revenue_category_id: row.revenue_category_id || undefined,
            month_01: Number(row.month_01) || 0,
            month_02: Number(row.month_02) || 0,
            month_03: Number(row.month_03) || 0,
            month_04: Number(row.month_04) || 0,
            month_05: Number(row.month_05) || 0,
            month_06: Number(row.month_06) || 0,
            month_07: Number(row.month_07) || 0,
            month_08: Number(row.month_08) || 0,
            month_09: Number(row.month_09) || 0,
            month_10: Number(row.month_10) || 0,
            month_11: Number(row.month_11) || 0,
            month_12: Number(row.month_12) || 0,
          })
        } else {
          // Update existing detail
          await updateMutation.mutateAsync({
            id: row.id,
            detail: {
              month_01: Number(row.month_01) || undefined,
              month_02: Number(row.month_02) || undefined,
              month_03: Number(row.month_03) || undefined,
              month_04: Number(row.month_04) || undefined,
              month_05: Number(row.month_05) || undefined,
              month_06: Number(row.month_06) || undefined,
              month_07: Number(row.month_07) || undefined,
              month_08: Number(row.month_08) || undefined,
              month_09: Number(row.month_09) || undefined,
              month_10: Number(row.month_10) || undefined,
              month_11: Number(row.month_11) || undefined,
              month_12: Number(row.month_12) || undefined,
            },
          })
        }
      }

      setChangedCells(new Set())
      message.success(`Сохранено ${changedRows.length} строк`)
    } catch (error: any) {
      message.error(`Ошибка сохранения: ${error.message}`)
    }
  }, [data, changedCells, versionId, createMutation, updateMutation])

  // Reset changes
  const handleReset = useCallback(() => {
    const rows: DetailRow[] = planDetails.map((detail) => ({
      ...detail,
      key: `${detail.id}`,
      streamName: detail.revenue_stream_id ? streamMap.get(detail.revenue_stream_id)?.name : '—',
      categoryName: detail.revenue_category_id ? categoryMap.get(detail.revenue_category_id)?.name : '—',
    }))
    setData(rows)
    setChangedCells(new Set())
    message.info('Изменения отменены')
  }, [planDetails, streamMap, categoryMap])

  // Add new row
  const handleAddRow = useCallback(() => {
    const newRow: DetailRow = {
      id: Date.now(), // Temporary ID
      version_id: versionId,
      department_id: 0, // Will be set by backend
      revenue_stream_id: null,
      revenue_category_id: null,
      month_01: 0,
      month_02: 0,
      month_03: 0,
      month_04: 0,
      month_05: 0,
      month_06: 0,
      month_07: 0,
      month_08: 0,
      month_09: 0,
      month_10: 0,
      month_11: 0,
      month_12: 0,
      total: 0,
      created_at: new Date().toISOString(),
      key: `new_${Date.now()}`,
      isNew: true,
      streamName: '—',
      categoryName: '—',
    }
    setData((prev) => [...prev, newRow])
    message.info('Добавлена новая строка. Заполните данные и нажмите "Сохранить"')
  }, [versionId])

  // Columns definition
  const columns: ColumnsType<DetailRow> = useMemo(() => {
    const cols: ColumnsType<DetailRow> = [
      {
        title: 'Поток доходов',
        dataIndex: 'streamName',
        key: 'streamName',
        width: STREAM_COLUMN_WIDTH,
        fixed: 'left',
        render: (text: string, record: DetailRow) => (
          <Text strong={!record.revenue_category_id}>{text}</Text>
        ),
      },
      {
        title: 'Категория',
        dataIndex: 'categoryName',
        key: 'categoryName',
        width: CATEGORY_COLUMN_WIDTH,
        fixed: 'left',
      },
    ]

    // Add month columns
    MONTHS.forEach((month) => {
      const monthKey = `month_${String(month.key).padStart(2, '0')}`
      cols.push({
        title: month.short,
        dataIndex: monthKey,
        key: monthKey,
        width: MONTH_COLUMN_WIDTH,
        align: 'right',
        render: (value: number, record: DetailRow) => {
          const cellKey = `${record.key}_${monthKey}`
          const hasChanges = changedCells.has(cellKey)

          if (!isEditable) {
            return formatCurrency(value || 0)
          }

          return (
            <InputNumber
              value={value || 0}
              onChange={(val) => handleCellChange(record.key, monthKey, val)}
              style={{
                width: '100%',
                backgroundColor: hasChanges ? '#fff7e6' : 'transparent',
                borderColor: hasChanges ? '#ffa940' : undefined,
              }}
              formatter={(val) => `${val}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
              parser={(val) => Number(val?.replace(/\s/g, '') || 0)}
              min={0}
              precision={0}
            />
          )
        },
      })
    })

    // Add total column
    cols.push({
      title: 'Итого',
      dataIndex: 'total',
      key: 'total',
      width: TOTAL_COLUMN_WIDTH,
      fixed: 'right',
      align: 'right',
      render: (value: number) => (
        <Text strong style={{ color: '#1890ff' }}>
          {formatCurrency(value || 0)}
        </Text>
      ),
    })

    return cols
  }, [isEditable, changedCells, handleCellChange])

  // Summary row
  const summaryRow = useMemo(() => {
    const row: any = {
      streamName: <Text strong>ИТОГО</Text>,
      categoryName: '',
    }

    MONTHS.forEach((month) => {
      const monthKey = `month_${String(month.key).padStart(2, '0')}`
      row[monthKey] = (
        <Text strong style={{ color: '#1890ff' }}>
          {formatCurrency(totals.monthTotals[monthKey] || 0)}
        </Text>
      )
    })

    row.total = (
      <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
        {formatCurrency(totals.grandTotal)}
      </Text>
    )

    return row
  }, [totals])

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400, padding: 48 }}>
        <Spin size="large" tip="Загрузка данных планирования...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  return (
    <div>
      {/* Control Panel */}
      {isEditable && (
        <div
          style={{
            marginBottom: 16,
            padding: 16,
            backgroundColor: '#fafafa',
            borderRadius: 8,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            {changedCells.size > 0 && (
              <Tag color="orange">Несохраненных изменений: {changedCells.size}</Tag>
            )}
          </Space>
          <Space>
            <Button icon={<PlusOutlined />} onClick={handleAddRow}>
              Добавить строку
            </Button>
            <Button
              icon={<UndoOutlined />}
              onClick={handleReset}
              disabled={changedCells.size === 0}
            >
              Отменить
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              disabled={changedCells.size === 0}
              loading={createMutation.isPending || updateMutation.isPending}
            >
              Сохранить ({changedCells.size})
            </Button>
          </Space>
        </div>
      )}

      {/* Table */}
      <ResponsiveTable
        columns={columns}
        dataSource={data}
        rowKey="key"
        pagination={false}
        scroll={{ x: 'max-content', y: 600 }}
        bordered
        size="small"
        summary={() => (
          <ResponsiveTable.Summary fixed>
            <ResponsiveTable.Summary.Row style={{ backgroundColor: '#f0f0f0' }}>
              {columns.map((col, index) => (
                <ResponsiveTable.Summary.Cell key={index} index={index} align={col.align as any}>
                  {summaryRow[col.key as string]}
                </ResponsiveTable.Summary.Cell>
              ))}
            </ResponsiveTable.Summary.Row>
          </ResponsiveTable.Summary>
        )}
      />
    </div>
  )
}
