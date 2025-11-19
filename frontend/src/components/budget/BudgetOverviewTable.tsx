import React, { useState } from 'react'
import { Table, Tag, Button, Spin, Space, message } from 'antd'
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { budgetApi } from '@/api'
import type { BudgetOverviewCategory } from '@/api/budget'
import QuickExpenseModal from './QuickExpenseModal'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useTheme } from '@/contexts/ThemeContext'
import { getApiBaseUrl } from '@/config/api'

interface BudgetOverviewTableProps {
  year: number
  month: number
}

const BudgetOverviewTable: React.FC<BudgetOverviewTableProps> = ({ year, month }) => {
  const [expenseModalOpen, setExpenseModalOpen] = useState(false)
  const { selectedDepartment } = useDepartment()
  const { mode } = useTheme()

  // Загрузка данных обзора
  const { data: overview, isLoading } = useQuery({
    queryKey: ['budget-overview', year, month, selectedDepartment?.id],
    queryFn: () => budgetApi.getOverview(year, month, selectedDepartment?.id),
  })

  const handleExport = () => {
    const apiUrl = getApiBaseUrl()
    let url = `${apiUrl}/api/v1/budget/overview/${year}/${month}/export`
    if (selectedDepartment?.id) {
      url += `?department_id=${selectedDepartment.id}`
    }
    window.open(url, '_blank')
    message.success('Экспорт начат. Файл скоро будет загружен.')
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  const getRemainingColor = (remaining: number, planned: number) => {
    if (planned === 0) return '#999'
    const percent = (remaining / planned) * 100
    if (remaining < 0) return '#ff4d4f' // Красный - перерасход
    if (percent >= 20) return '#52c41a' // Зеленый - хорошо
    if (percent >= 5) return '#faad14' // Желтый - внимание
    return '#ff7875' // Светло-красный - критично
  }

  const getExecutionTag = (percent: number, isOverspent: boolean) => {
    if (isOverspent) {
      return <Tag color="red">Перерасход {percent}%</Tag>
    }
    if (percent >= 95) {
      return <Tag color="orange">{percent}%</Tag>
    }
    if (percent >= 80) {
      return <Tag color="blue">{percent}%</Tag>
    }
    return <Tag color="green">{percent}%</Tag>
  }

  // Группировка категорий по родителям (должно быть до early returns!)
  const groupedCategories = React.useMemo(() => {
    if (!overview?.categories) return []

    const parents = overview.categories.filter(cat => cat.parent_id === null)
    const childrenMap = new Map<number, BudgetOverviewCategory[]>()

    overview.categories.forEach(cat => {
      if (cat.parent_id !== null) {
        if (!childrenMap.has(cat.parent_id)) {
          childrenMap.set(cat.parent_id, [])
        }
        childrenMap.get(cat.parent_id)!.push(cat)
      }
    })

    const result: any[] = []

    parents.forEach(parent => {
      const children = childrenMap.get(parent.category_id) || []

      // Calculate parent totals from children
      const parentTotals = children.reduce(
        (acc, child) => ({
          planned: acc.planned + child.planned,
          actual: acc.actual + child.actual,
          remaining: acc.remaining + child.remaining,
        }),
        { planned: 0, actual: 0, remaining: 0 }
      )

      // Add parent with aggregated data
      result.push({
        key: `parent-${parent.category_id}`,
        category_id: parent.category_id,
        category_name: parent.category_name,
        category_type: parent.category_type,
        parent_id: null,
        planned: parentTotals.planned,
        actual: parentTotals.actual,
        remaining: parentTotals.remaining,
        execution_percent: parentTotals.planned > 0 ? Math.round((parentTotals.actual / parentTotals.planned) * 100) : 0,
        is_overspent: parentTotals.remaining < 0,
        isParent: true,
        isChild: false,
      })

      // Add children
      children.forEach(child => {
        result.push({
          key: `child-${child.category_id}`,
          ...child,
          isParent: false,
          isChild: true,
        })
      })
    })

    return result
  }, [overview])

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!overview) {
    return <div>Нет данных</div>
  }

  const columns = [
    {
      title: 'Статья расходов',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 300,
      render: (text: string, record: any) => {
        const isParent = record.isParent === true
        const isChild = record.isChild === true
        const isTotal = record.key && (record.key.includes('total') || record.key === 'grand-total')

        return (
          <div style={{
            paddingLeft: isChild ? 24 : 0,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            {isChild && <span style={{ color: '#999', fontSize: 12 }}>└─</span>}
            <div style={{ flex: 1 }}>
              <div style={{
                fontWeight: isParent || isTotal ? 600 : 'normal',
                fontSize: isParent ? 14 : 13,
                color: isParent ? '#1890ff' : 'inherit'
              }}>
                {text}
              </div>
              {isParent && (
                <Tag
                  color={record.category_type === 'OPEX' ? 'blue' : 'green'}
                  style={{ marginTop: 4, fontSize: 11 }}
                >
                  {record.category_type}
                </Tag>
              )}
            </div>
          </div>
        )
      },
    },
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Факт',
      dataIndex: 'actual',
      key: 'actual',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatNumber(value),
    },
    {
      title: 'Остаток',
      dataIndex: 'remaining',
      key: 'remaining',
      width: 120,
      align: 'right' as const,
      render: (value: number, record: BudgetOverviewCategory) => (
        <span style={{ color: getRemainingColor(value, record.planned), fontWeight: 'bold' }}>
          {formatNumber(value)}
        </span>
      ),
    },
    {
      title: 'Исполнение',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      width: 120,
      align: 'center' as const,
      render: (value: number, record: BudgetOverviewCategory) =>
        getExecutionTag(value, record.is_overspent),
    },
  ]

  // Данные для таблицы используют groupedCategories, который уже определен выше
  const dataSource = groupedCategories

  // Строки итогов
  const opexRow = {
    key: 'opex-total',
    category_id: -1,
    category_name: 'ИТОГО OPEX',
    category_type: 'OPEX' as const,
    parent_id: null,
    ...overview.opex_totals,
    is_overspent: overview.opex_totals.remaining < 0,
  }

  const capexRow = {
    key: 'capex-total',
    category_id: -2,
    category_name: 'ИТОГО CAPEX',
    category_type: 'CAPEX' as const,
    parent_id: null,
    ...overview.capex_totals,
    is_overspent: overview.capex_totals.remaining < 0,
  }

  const totalRow = {
    key: 'grand-total',
    category_id: -3,
    category_name: 'ВСЕГО',
    category_type: '' as any,
    parent_id: null,
    ...overview.totals,
    is_overspent: overview.totals.remaining < 0,
  }

  const dataWithTotals = [...dataSource, opexRow, capexRow, totalRow] as any[]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ margin: 0 }}>
            Бюджет за месяц: {new Date(year, month - 1).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
          </h3>
        </div>
        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            Экспорт в Excel
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setExpenseModalOpen(true)}
          >
            Добавить расход
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={dataWithTotals}
        pagination={false}
        bordered
        size="middle"
        rowClassName={(record: any) => {
          if (record.key === 'grand-total') return 'grand-total-row'
          if (record.key === 'opex-total' || record.key === 'capex-total') return 'subtotal-row'
          if (record.isParent === true) return 'parent-row'
          if (record.isChild === true) return 'child-row'
          return ''
        }}
      />

      <QuickExpenseModal
        open={expenseModalOpen}
        onClose={() => setExpenseModalOpen(false)}
        defaultYear={year}
        defaultMonth={month}
      />

      <style>{`
        ${mode === 'dark' ? `
          .parent-row {
            background-color: #262626 !important;
            font-weight: 500;
          }
          .parent-row:hover {
            background-color: #303030 !important;
          }
          .child-row {
            background-color: #1f1f1f !important;
          }
          .child-row:hover {
            background-color: #262626 !important;
          }
          .subtotal-row {
            background-color: #1a1a2e !important;
            font-weight: 600;
          }
          .grand-total-row {
            background-color: #252540 !important;
            font-weight: 700;
            font-size: 15px;
          }
        ` : `
          .parent-row {
            background-color: #fafafa !important;
            font-weight: 500;
          }
          .parent-row:hover {
            background-color: #f0f0f0 !important;
          }
          .child-row {
            background-color: #ffffff !important;
          }
          .child-row:hover {
            background-color: #f5f5f5 !important;
          }
          .subtotal-row {
            background-color: #f0f5ff !important;
            font-weight: 600;
          }
          .grand-total-row {
            background-color: #e6f7ff !important;
            font-weight: 700;
            font-size: 15px;
          }
        `}
      `}</style>
    </div>
  )
}

export default BudgetOverviewTable
