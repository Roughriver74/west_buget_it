import React, { useState } from 'react'
import { Table, Tag, Spin, message, Button, Space } from 'antd'
import { CopyOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetApi } from '@/api'
import EditableCell from './EditableCell'
import CopyPlanModal from './CopyPlanModal'

interface BudgetPlanTableProps {
  year: number
}

const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

const BudgetPlanTable: React.FC<BudgetPlanTableProps> = ({ year }) => {
  const [copyModalOpen, setCopyModalOpen] = useState(false)
  const [updatingCells, setUpdatingCells] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  // Загрузка плана на год
  const { data: planData, isLoading } = useQuery({
    queryKey: ['budget-plan', year],
    queryFn: () => budgetApi.getPlanForYear(year),
  })

  // Инициализация плана
  const initMutation = useMutation({
    mutationFn: () => budgetApi.initializePlan(year),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
      message.success(`План инициализирован! Создано записей: ${response.created_entries}`)
    },
    onError: (error: any) => {
      message.error(`Ошибка инициализации: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Обновление ячейки
  const updateCellMutation = useMutation({
    mutationFn: budgetApi.updateCell,
    onMutate: async (variables) => {
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => new Set(prev).add(cellKey))
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => {
        const newSet = new Set(prev)
        newSet.delete(cellKey)
        return newSet
      })
    },
    onError: (error: any, variables) => {
      message.error(`Ошибка обновления: ${error.response?.data?.detail || error.message}`)
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => {
        const newSet = new Set(prev)
        newSet.delete(cellKey)
        return newSet
      })
    },
  })

  const handleCellChange = (categoryId: number, month: number, value: number) => {
    updateCellMutation.mutate({
      year,
      month,
      category_id: categoryId,
      planned_amount: value,
    })
  }

  const isCellUpdating = (categoryId: number, month: number): boolean => {
    return updatingCells.has(`${categoryId}-${month}`)
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  // Расчёт итогов по строке
  const calculateRowTotal = (months: any) => {
    return Object.values(months).reduce((sum: number, month: any) => sum + (month.planned_amount || 0), 0)
  }

  // Расчёт итогов по колонке
  const calculateColumnTotal = (categories: any[], month: number) => {
    return categories.reduce((sum, cat) => {
      const monthData = cat.months[month.toString()]
      return sum + (monthData?.planned_amount || 0)
    }, 0)
  }

  // Расчёт итога OPEX
  const calculateOpexTotal = (categories: any[], month?: number) => {
    return categories
      .filter((cat) => cat.category_type === 'OPEX')
      .reduce((sum, cat) => {
        if (month) {
          const monthData = cat.months[month.toString()]
          return sum + (monthData?.planned_amount || 0)
        }
        return sum + calculateRowTotal(cat.months)
      }, 0)
  }

  // Расчёт итога CAPEX
  const calculateCapexTotal = (categories: any[], month?: number) => {
    return categories
      .filter((cat) => cat.category_type === 'CAPEX')
      .reduce((sum, cat) => {
        if (month) {
          const monthData = cat.months[month.toString()]
          return sum + (monthData?.planned_amount || 0)
        }
        return sum + calculateRowTotal(cat.months)
      }, 0)
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!planData || planData.categories.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <p>План на {year} год не найден</p>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => initMutation.mutate()}
          loading={initMutation.isPending}
        >
          Инициализировать план
        </Button>
      </div>
    )
  }

  const columns: any[] = [
    {
      title: 'Статья расходов',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 250,
      fixed: 'left',
      render: (text: string, record: any) => (
        <div>
          <div>{text}</div>
          <Tag color={record.category_type === 'OPEX' ? 'blue' : 'green'} style={{ marginTop: 4 }}>
            {record.category_type}
          </Tag>
        </div>
      ),
    },
    ...Array.from({ length: 12 }, (_, i) => i + 1).map((month) => ({
      title: MONTH_NAMES[month - 1],
      key: `month-${month}`,
      width: 100,
      align: 'right' as const,
      render: (_: any, record: any) => {
        const monthData = record.months[month.toString()]
        return (
          <EditableCell
            value={monthData?.planned_amount || 0}
            onChange={(value) => handleCellChange(record.category_id, month, value)}
            loading={isCellUpdating(record.category_id, month)}
          />
        )
      },
    })),
    {
      title: 'Итого',
      key: 'total',
      width: 120,
      align: 'right' as const,
      fixed: 'right',
      render: (_: any, record: any) => (
        <strong style={{ color: '#1890ff' }}>{formatNumber(calculateRowTotal(record.months))}</strong>
      ),
    },
  ]

  // Данные для таблицы
  const dataSource = planData.categories.map((cat) => ({
    key: cat.category_id,
    ...cat,
  }))

  // Строка итогов OPEX
  const opexRow = {
    key: 'opex-total',
    category_name: 'ИТОГО OPEX',
    category_type: 'OPEX',
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => [
        month.toString(),
        { planned_amount: calculateOpexTotal(planData.categories, month) },
      ])
    ),
  }

  // Строка итогов CAPEX
  const capexRow = {
    key: 'capex-total',
    category_name: 'ИТОГО CAPEX',
    category_type: 'CAPEX',
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => [
        month.toString(),
        { planned_amount: calculateCapexTotal(planData.categories, month) },
      ])
    ),
  }

  // Строка общих итогов
  const grandTotalRow = {
    key: 'grand-total',
    category_name: 'ВСЕГО',
    category_type: '',
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => [
        month.toString(),
        { planned_amount: calculateColumnTotal(planData.categories, month) },
      ])
    ),
  }

  // Добавляем строки итогов в таблицу
  const dataWithTotals = [...dataSource, opexRow, capexRow, grandTotalRow]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button
            icon={<CopyOutlined />}
            onClick={() => setCopyModalOpen(true)}
          >
            Скопировать из другого года
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={dataWithTotals}
        pagination={false}
        scroll={{ x: 1600 }}
        bordered
        size="small"
        rowClassName={(record) => {
          if (record.key === 'grand-total') return 'grand-total-row'
          if (record.key === 'opex-total' || record.key === 'capex-total') return 'subtotal-row'
          return ''
        }}
      />

      <CopyPlanModal
        open={copyModalOpen}
        targetYear={year}
        onClose={() => setCopyModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
        }}
      />

      <style>{`
        .subtotal-row {
          background-color: #f0f5ff !important;
          font-weight: 600;
        }
        .grand-total-row {
          background-color: #e6f7ff !important;
          font-weight: 700;
          font-size: 14px;
        }
        .ant-table-cell {
          padding: 8px !important;
        }
      `}</style>
    </div>
  )
}

export default BudgetPlanTable
