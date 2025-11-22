import React, { useState, useEffect } from 'react'
import { Table,  Typography, Card, Select, Space, Tag, Spin, Alert } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { analyticsApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Title, Paragraph } = Typography
const { Option } = Select

interface CategoryBalance {
  category_id: number
  category_name: string
  category_type: 'OPEX' | 'CAPEX'
  parent_id: number | null
  planned: number
  actual: number
  remaining: number
  execution_percent: number
  expense_count: number
  isParent?: boolean
  isChild?: boolean
}

interface BalanceData {
  year: number
  month: number | null
  categories: CategoryBalance[]
}

const BalanceAnalyticsPage: React.FC = () => {
  const currentYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<BalanceData | null>(null)
  const { selectedDepartment } = useDepartment()

  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i)
  const months = [
    { value: null, label: 'Весь год' },
    { value: 1, label: 'Январь' },
    { value: 2, label: 'Февраль' },
    { value: 3, label: 'Март' },
    { value: 4, label: 'Апрель' },
    { value: 5, label: 'Май' },
    { value: 6, label: 'Июнь' },
    { value: 7, label: 'Июль' },
    { value: 8, label: 'Август' },
    { value: 9, label: 'Сентябрь' },
    { value: 10, label: 'Октябрь' },
    { value: 11, label: 'Ноябрь' },
    { value: 12, label: 'Декабрь' },
  ]

  useEffect(() => {
    fetchBalanceData()
  }, [selectedYear, selectedMonth, selectedDepartment?.id])

  const fetchBalanceData = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = { year: selectedYear }
      if (selectedMonth !== null) {
        params.month = selectedMonth
      }
      if (selectedDepartment?.id) {
        params.department_id = selectedDepartment?.id
      }

      const response = await analyticsApi.getByCategory(params)
      setData(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка загрузки данных')
      console.error('Error fetching balance data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getBalanceStatus = (remaining: number, planned: number) => {
    if (planned === 0) return { color: 'default', text: 'Нет плана' }

    const percent = (remaining / planned) * 100

    if (remaining < 0) {
      return { color: 'error', text: '⚫ Перерасход' }
    } else if (percent < 5) {
      return { color: 'error', text: '🔴 Критично' }
    } else if (percent < 20) {
      return { color: 'warning', text: '🟡 Внимание' }
    } else {
      return { color: 'success', text: '🟢 Хорошо' }
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const columns: ColumnsType<CategoryBalance> = [
    {
      title: 'Статья расходов',
      dataIndex: 'category_name',
      key: 'category_name',
      width: '25%',
      fixed: 'left',
      render: (text: string, record: CategoryBalance) => {
        const isParent = record.isParent === true
        const isChild = record.isChild === true

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
                fontWeight: isParent ? 600 : 'normal',
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
      title: 'Тип',
      dataIndex: 'category_type',
      key: 'category_type',
      width: 100,
      render: (type: string, record: CategoryBalance) => {
        // Показываем тег только для дочерних категорий
        if (record.isChild) {
          return <Tag color={type === 'OPEX' ? 'blue' : 'green'}>{type}</Tag>
        }
        return null
      },
    },
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      align: 'right',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Факт',
      dataIndex: 'actual',
      key: 'actual',
      align: 'right',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Остаток',
      dataIndex: 'remaining',
      key: 'remaining',
      align: 'right',
      render: (value: number, record: CategoryBalance) => {
        return (
          <span style={{
            color: value < 0 ? '#ff4d4f' : value < record.planned * 0.2 ? '#faad14' : '#52c41a',
            fontWeight: 'bold'
          }}>
            {formatCurrency(value)}
          </span>
        )
      },
    },
    {
      title: '% исполнения',
      dataIndex: 'execution_percent',
      key: 'execution_percent',
      align: 'center',
      render: (value: number, record: CategoryBalance) => {
        const status = getBalanceStatus(record.remaining, record.planned)
        return (
          <Tag color={status.color}>
            {value}%
          </Tag>
        )
      },
    },
    {
      title: 'Статус',
      key: 'status',
      align: 'center',
      render: (_: any, record: CategoryBalance) => {
        const status = getBalanceStatus(record.remaining, record.planned)
        return <span>{status.text}</span>
      },
    },
    {
      title: 'Кол-во заявок',
      dataIndex: 'expense_count',
      key: 'expense_count',
      align: 'center',
    },
  ]

  // Group categories by parent
  const groupedCategories = React.useMemo(() => {
    if (!data?.categories) return []

    const parents = data.categories.filter(cat => cat.parent_id === null)
    const childrenMap = new Map<number, CategoryBalance[]>()

    data.categories.forEach(cat => {
      if (cat.parent_id !== null) {
        if (!childrenMap.has(cat.parent_id)) {
          childrenMap.set(cat.parent_id, [])
        }
        childrenMap.get(cat.parent_id)!.push(cat)
      }
    })

    const result: CategoryBalance[] = []

    parents.forEach(parent => {
      const children = childrenMap.get(parent.category_id) || []

      // Calculate parent totals from children
      const parentTotals = children.reduce(
        (acc, child) => ({
          planned: acc.planned + child.planned,
          actual: acc.actual + child.actual,
          remaining: acc.remaining + child.remaining,
          expense_count: acc.expense_count + child.expense_count,
        }),
        { planned: 0, actual: 0, remaining: 0, expense_count: 0 }
      )

      // Add parent with aggregated data
      result.push({
        ...parent,
        planned: parentTotals.planned,
        actual: parentTotals.actual,
        remaining: parentTotals.remaining,
        execution_percent: parentTotals.planned > 0 ? Math.round((parentTotals.actual / parentTotals.planned) * 100) : 0,
        expense_count: parentTotals.expense_count,
        isParent: true,
        isChild: false,
      })

      // Add children
      children.forEach(child => {
        result.push({
          ...child,
          isParent: false,
          isChild: true,
        })
      })
    })

    return result
  }, [data])

  // Calculate totals
  const totals = data?.categories.reduce(
    (acc, cat) => ({
      planned: acc.planned + cat.planned,
      actual: acc.actual + cat.actual,
      remaining: acc.remaining + cat.remaining,
      opex_planned: acc.opex_planned + (cat.category_type === 'OPEX' ? cat.planned : 0),
      opex_actual: acc.opex_actual + (cat.category_type === 'OPEX' ? cat.actual : 0),
      capex_planned: acc.capex_planned + (cat.category_type === 'CAPEX' ? cat.planned : 0),
      capex_actual: acc.capex_actual + (cat.category_type === 'CAPEX' ? cat.actual : 0),
    }),
    {
      planned: 0,
      actual: 0,
      remaining: 0,
      opex_planned: 0,
      opex_actual: 0,
      capex_planned: 0,
      capex_actual: 0,
    }
  )

  const summaryData = totals ? [
    {
      key: 'opex',
      category_name: 'ИТОГО OPEX',
      category_type: 'OPEX' as const,
      planned: totals.opex_planned,
      actual: totals.opex_actual,
      remaining: totals.opex_planned - totals.opex_actual,
      execution_percent: totals.opex_planned > 0 ? Math.round((totals.opex_actual / totals.opex_planned) * 100) : 0,
      expense_count: data?.categories.filter(c => c.category_type === 'OPEX').reduce((sum, c) => sum + c.expense_count, 0) || 0,
      category_id: -1,
    },
    {
      key: 'capex',
      category_name: 'ИТОГО CAPEX',
      category_type: 'CAPEX' as const,
      planned: totals.capex_planned,
      actual: totals.capex_actual,
      remaining: totals.capex_planned - totals.capex_actual,
      execution_percent: totals.capex_planned > 0 ? Math.round((totals.capex_actual / totals.capex_planned) * 100) : 0,
      expense_count: data?.categories.filter(c => c.category_type === 'CAPEX').reduce((sum, c) => sum + c.expense_count, 0) || 0,
      category_id: -2,
    },
    {
      key: 'total',
      category_name: 'ВСЕГО',
      category_type: '' as any,
      planned: totals.planned,
      actual: totals.actual,
      remaining: totals.remaining,
      execution_percent: totals.planned > 0 ? Math.round((totals.actual / totals.planned) * 100) : 0,
      expense_count: data?.categories.reduce((sum, c) => sum + c.expense_count, 0) || 0,
      category_id: -3,
    },
  ] : []

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={2}>Остатки по статьям (План-Факт-Остаток)</Title>
          <Paragraph>
            Анализ исполнения бюджета по статьям расходов с цветовой индикацией состояния.
          </Paragraph>
        </div>

        <Space align="center" size="large">
          <Space align="center">
            <span style={{ fontSize: 16, fontWeight: 500 }}>Период:</span>
            <Select
              value={selectedMonth}
              onChange={setSelectedMonth}
              style={{ width: 150 }}
              size="large"
            >
              {months.map((m) => (
                <Option key={m.value ?? 'all'} value={m.value}>
                  {m.label}
                </Option>
              ))}
            </Select>
          </Space>

          <Space align="center">
            <span style={{ fontSize: 16, fontWeight: 500 }}>Год:</span>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              style={{ width: 120 }}
              size="large"
            >
              {years.map((year) => (
                <Option key={year} value={year}>
                  {year}
                </Option>
              ))}
            </Select>
          </Space>
        </Space>
      </div>

      {error && (
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card>
        <Spin spinning={loading}>
          <ResponsiveTable<CategoryBalance>
            columns={columns}
            dataSource={groupedCategories}
            rowKey="category_id"
            pagination={false}
            scroll={{ x: 1200 }}
            rowClassName={(record) => {
              if (record.isParent === true) return 'parent-row'
              if (record.isChild === true) return 'child-row'
              return ''
            }}
            mobileLayout="card"
            summary={() => (
              <Table.Summary fixed>
                {summaryData.map((row) => (
                  <Table.Summary.Row
                    key={row.key}
                    style={{
                      backgroundColor: row.key === 'total' ? '#fafafa' : '#f0f5ff',
                      fontWeight: row.key === 'total' ? 'bold' : '600'
                    }}
                  >
                    <Table.Summary.Cell index={0}>{row.category_name}</Table.Summary.Cell>
                    <Table.Summary.Cell index={1}>
                      {row.category_type && <Tag color={row.category_type === 'OPEX' ? 'blue' : 'green'}>{row.category_type}</Tag>}
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={2} align="right">{formatCurrency(row.planned)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={3} align="right">{formatCurrency(row.actual)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={4} align="right">
                      <span style={{
                        color: row.remaining < 0 ? '#ff4d4f' : row.remaining < row.planned * 0.2 ? '#faad14' : '#52c41a',
                        fontWeight: 'bold'
                      }}>
                        {formatCurrency(row.remaining)}
                      </span>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={5} align="center">
                      <Tag color={getBalanceStatus(row.remaining, row.planned).color}>
                        {row.execution_percent}%
                      </Tag>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={6} align="center">
                      {getBalanceStatus(row.remaining, row.planned).text}
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={7} align="center">{row.expense_count}</Table.Summary.Cell>
                  </Table.Summary.Row>
                ))}
              </Table.Summary>
            )}
          />
        </Spin>
      </Card>

      <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8 }}>
        <Title level={5}>Цветовая индикация:</Title>
        <ul style={{ marginBottom: 0 }}>
          <li>🟢 <strong>Хорошо</strong> — Остаток {'>'} 20% от плана</li>
          <li>🟡 <strong>Внимание</strong> — Остаток 5-20% от плана</li>
          <li>🔴 <strong>Критично</strong> — Остаток {'<'} 5% от плана</li>
          <li>⚫ <strong>Перерасход</strong> — Факт превышает план</li>
        </ul>
      </div>

      <style>{`
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
      `}</style>
    </div>
  )
}

export default BalanceAnalyticsPage
