import React, { useState } from 'react'
import { Table, Tag, Button, Spin, Space, message } from 'antd'
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { budgetApi } from '@/api'
import type { BudgetOverviewCategory } from '@/api/budget'
import QuickExpenseModal from './QuickExpenseModal'

interface BudgetOverviewTableProps {
  year: number
  month: number
}

const BudgetOverviewTable: React.FC<BudgetOverviewTableProps> = ({ year, month }) => {
  const [expenseModalOpen, setExpenseModalOpen] = useState(false)

  // Загрузка данных обзора
  const { data: overview, isLoading } = useQuery({
    queryKey: ['budget-overview', year, month],
    queryFn: () => budgetApi.getOverview(year, month),
  })

  const handleExport = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${apiUrl}/api/v1/budget/overview/${year}/${month}/export`
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
      width: 250,
      render: (text: string, record: BudgetOverviewCategory) => (
        <div>
          <div>{text}</div>
          <Tag color={record.category_type === 'OPEX' ? 'blue' : 'green'} style={{ marginTop: 4 }}>
            {record.category_type}
          </Tag>
        </div>
      ),
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

  // Данные для таблицы
  const dataSource = overview.categories.map((cat) => ({
    key: cat.category_id,
    ...cat,
  }))

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
        .subtotal-row {
          background-color: #f0f5ff !important;
          font-weight: 600;
        }
        .grand-total-row {
          background-color: #e6f7ff !important;
          font-weight: 700;
          font-size: 15px;
        }
      `}</style>
    </div>
  )
}

export default BudgetOverviewTable
