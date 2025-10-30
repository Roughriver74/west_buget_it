import { useState } from 'react'
import { Card, Select, Space, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useQuery } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import type { KPIEmployeeSummary } from '@/api/kpi'
import { formatCurrency } from '@/utils/formatters'

const { Option } = Select
const { Text } = Typography

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)

const monthLabel = (month: number | null | undefined) =>
  typeof month === 'number' ? dayjs().month(month - 1).format('MMMM') : 'Годовая цель'

interface KpiSummaryTabProps {
  departmentId?: number
}

export const KpiSummaryTab: React.FC<KpiSummaryTabProps> = ({ departmentId }) => {
  const [summaryFilters, setSummaryFilters] = useState<{ year: number; month?: number }>({
    year: dayjs().year(),
  })

  const summaryQuery = useQuery({
    queryKey: ['kpi-employee-summary', summaryFilters, departmentId],
    queryFn: () =>
      kpiApi.getEmployeeSummary({
        year: summaryFilters.year,
        month: summaryFilters.month,
        department_id: departmentId,
      }),
    enabled: !!departmentId,
  })

  const summary = summaryQuery.data || []

  const summaryColumns: ColumnsType<KPIEmployeeSummary> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.position || '—'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Период',
      dataIndex: 'month',
      key: 'period',
      width: 120,
      render: (_, record) =>
        record.month ? `${monthLabel(record.month)} ${record.year}` : `${record.year}`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      width: 100,
      render: (value) =>
        value !== null && value !== undefined ? `${Number(value).toFixed(1)} %` : '—',
    },
    {
      title: 'Бонус (всего)',
      dataIndex: 'total_bonus_calculated',
      key: 'total_bonus_calculated',
      width: 140,
      render: (value) => formatCurrency(Number(value || 0)),
    },
    {
      title: 'Целей выполнено',
      dataIndex: 'goals_achieved',
      key: 'goals_achieved',
      width: 160,
      render: (_, record) => `${record.goals_achieved}/${record.goals_count}`,
    },
  ]

  return (
    <Card
      title="Сводка по сотрудникам"
      extra={
        <Space>
          <Select
            value={summaryFilters.year}
            onChange={(value) => setSummaryFilters((prev) => ({ ...prev, year: value }))}
            style={{ width: 120 }}
          >
            {Array.from({ length: 5 }, (_, i) => dayjs().year() - 2 + i).map((year) => (
              <Option key={year} value={year}>
                {year}
              </Option>
            ))}
          </Select>
          <Select
            allowClear
            placeholder="Месяц"
            value={summaryFilters.month}
            onChange={(value) => setSummaryFilters((prev) => ({ ...prev, month: value }))}
            style={{ width: 140 }}
          >
            {MONTH_OPTIONS.map((month) => (
              <Option key={month} value={month}>
                {monthLabel(month)}
              </Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table<KPIEmployeeSummary>
        rowKey={(record) => `${record.employee_id}-${record.year}-${record.month ?? 'all'}`}
        columns={summaryColumns}
        dataSource={summary}
        loading={summaryQuery.isLoading}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  )
}
