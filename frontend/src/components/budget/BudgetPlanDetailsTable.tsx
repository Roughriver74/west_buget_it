/**
 * Budget Plan Details Table Component
 * Editable table for monthly budget planning by category
 */
import React, { useState, useEffect } from 'react'
import { Table, InputNumber, Button, Space, message, Typography } from 'antd'
import { SaveOutlined, UndoOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { usePlanDetails, useCreatePlanDetail, useUpdatePlanDetail } from '@/hooks/useBudgetPlanning'
import type { BudgetPlanDetail, BudgetPlanDetailCreate } from '@/types/budgetPlanning'

const { Text } = Typography

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
  type: 'OPEX' | 'CAPEX'
}

interface BudgetPlanDetailsTableProps {
  versionId: number
  categories: Category[]
  isEditable: boolean
}

interface CategoryRow {
  categoryId: number
  categoryName: string
  categoryType: 'OPEX' | 'CAPEX'
  [key: string]: any // For month values (month_1, month_2, etc.)
}

export const BudgetPlanDetailsTable: React.FC<BudgetPlanDetailsTableProps> = ({
  versionId,
  categories,
  isEditable,
}) => {
  const { data: planDetails = [], isLoading } = usePlanDetails(versionId)
  const createMutation = useCreatePlanDetail()
  const updateMutation = useUpdatePlanDetail()

  const [data, setData] = useState<CategoryRow[]>([])
  const [changedCells, setChangedCells] = useState<Set<string>>(new Set())

  // Initialize data from categories and plan details
  useEffect(() => {
    if (categories.length === 0) return

    const rows: CategoryRow[] = categories.map((category) => {
      const row: CategoryRow = {
        categoryId: category.id,
        categoryName: category.name,
        categoryType: category.type,
      }

      // Initialize all months with 0
      MONTHS.forEach((month) => {
        row[`month_${month.key}`] = 0
      })

      // Fill in values from planDetails
      const categoryDetails = planDetails.filter((d) => d.category_id === category.id)
      categoryDetails.forEach((detail) => {
        row[`month_${detail.month}`] = detail.planned_amount
        row[`detail_${detail.month}_id`] = detail.id
      })

      return row
    })

    setData(rows)
  }, [categories, planDetails])

  const handleCellChange = (categoryId: number, month: number, value: number | null) => {
    setData((prevData) =>
      prevData.map((row) => {
        if (row.categoryId === categoryId) {
          const cellKey = `${categoryId}_${month}`
          setChangedCells((prev) => new Set(prev).add(cellKey))
          return {
            ...row,
            [`month_${month}`]: value || 0,
          }
        }
        return row
      })
    )
  }

  const handleSave = async () => {
    const updates: Array<{ id?: number; data: BudgetPlanDetailCreate }> = []

    // Collect all changed cells
    changedCells.forEach((cellKey) => {
      const [categoryIdStr, monthStr] = cellKey.split('_')
      const categoryId = parseInt(categoryIdStr)
      const month = parseInt(monthStr)

      const row = data.find((r) => r.categoryId === categoryId)
      if (!row) return

      const detailId = row[`detail_${month}_id`]
      const plannedAmount = row[`month_${month}`] || 0

      if (detailId) {
        // Update existing detail
        updates.push({
          id: detailId,
          data: {
            version_id: versionId,
            category_id: categoryId,
            month,
            planned_amount: plannedAmount,
          },
        })
      } else {
        // Create new detail
        updates.push({
          data: {
            version_id: versionId,
            category_id: categoryId,
            month,
            planned_amount: plannedAmount,
          },
        })
      }
    })

    try {
      // Execute all updates
      for (const update of updates) {
        if (update.id) {
          await updateMutation.mutateAsync({ id: update.id, data: update.data })
        } else {
          await createMutation.mutateAsync(update.data)
        }
      }

      setChangedCells(new Set())
      message.success(`Сохранено ${updates.length} изменений`)
    } catch (error) {
      message.error('Ошибка при сохранении')
    }
  }

  const handleReset = () => {
    setChangedCells(new Set())
    // Reset data from planDetails
    const rows: CategoryRow[] = categories.map((category) => {
      const row: CategoryRow = {
        categoryId: category.id,
        categoryName: category.name,
        categoryType: category.type,
      }

      MONTHS.forEach((month) => {
        row[`month_${month.key}`] = 0
      })

      const categoryDetails = planDetails.filter((d) => d.category_id === category.id)
      categoryDetails.forEach((detail) => {
        row[`month_${detail.month}`] = detail.planned_amount
        row[`detail_${detail.month}_id`] = detail.id
      })

      return row
    })

    setData(rows)
    message.info('Изменения отменены')
  }

  // Calculate row total
  const getRowTotal = (row: CategoryRow) => {
    return MONTHS.reduce((sum, month) => sum + (row[`month_${month.key}`] || 0), 0)
  }

  // Calculate column total
  const getColumnTotal = (month: number) => {
    return data.reduce((sum, row) => sum + (row[`month_${month}`] || 0), 0)
  }

  // Calculate grand total
  const getGrandTotal = () => {
    return data.reduce((sum, row) => sum + getRowTotal(row), 0)
  }

  const columns: ColumnsType<CategoryRow> = [
    {
      title: 'Категория',
      dataIndex: 'categoryName',
      key: 'categoryName',
      fixed: 'left',
      width: 200,
      render: (text, record) => (
        <div>
          <div>{text}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.categoryType}
          </Text>
        </div>
      ),
    },
    ...MONTHS.map((month) => ({
      title: month.label,
      dataIndex: `month_${month.key}`,
      key: `month_${month.key}`,
      width: 120,
      align: 'right' as const,
      render: (value: number, record: CategoryRow) => {
        if (!isEditable) {
          return <Text>{value?.toLocaleString('ru-RU') || 0}</Text>
        }

        const cellKey = `${record.categoryId}_${month.key}`
        const isChanged = changedCells.has(cellKey)

        return (
          <InputNumber
            value={value}
            onChange={(val) => handleCellChange(record.categoryId, month.key, val)}
            style={{
              width: '100%',
              backgroundColor: isChanged ? '#fff7e6' : undefined,
            }}
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => (value || '').replace(/\s/g, '')}
            min={0}
          />
        )
      },
    })),
    {
      title: 'Итого',
      key: 'total',
      fixed: 'right',
      width: 150,
      align: 'right' as const,
      render: (_, record) => (
        <Text strong>{getRowTotal(record).toLocaleString('ru-RU')} ₽</Text>
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
            <Text strong>{getColumnTotal(month.key).toLocaleString('ru-RU')}</Text>
          </Table.Summary.Cell>
        ))}
        <Table.Summary.Cell index={13} align="right">
          <Text strong style={{ fontSize: 16 }}>
            {getGrandTotal().toLocaleString('ru-RU')} ₽
          </Text>
        </Table.Summary.Cell>
      </Table.Summary.Row>
    </Table.Summary>
  )

  return (
    <div>
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
        dataSource={data}
        rowKey="categoryId"
        loading={isLoading}
        pagination={false}
        scroll={{ x: 1800 }}
        summary={() => summaryRow}
        bordered
        size="small"
      />
    </div>
  )
}
