import { useState, useMemo } from 'react'
import { Card, Calendar, Select, Space, Badge, Typography, Spin } from 'antd'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import { useQuery } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import { formatCurrency } from '@/utils/formatters'

const { Option } = Select
const { Text } = Typography

interface KpiCalendarProps {
  departmentId?: number
}

export const KpiCalendar: React.FC<KpiCalendarProps> = ({ departmentId }) => {
  const [selectedYear, setSelectedYear] = useState<number>(dayjs().year())

  // Query employee KPIs for the selected year
  const employeeKpiQuery = useQuery({
    queryKey: ['kpi-employee-calendar', departmentId, selectedYear],
    queryFn: () =>
      kpiApi.listEmployeeKpis({
        department_id: departmentId,
        year: selectedYear,
      }),
    enabled: !!departmentId,
  })

  const employeeKpis = employeeKpiQuery.data || []

  // Group bonuses by month
  const bonusesByMonth = useMemo(() => {
    const monthMap = new Map<number, { count: number; totalBonus: number }>()

    employeeKpis.forEach((kpi) => {
      if (kpi.month) {
        const existing = monthMap.get(kpi.month) || { count: 0, totalBonus: 0 }
        const totalBonus =
          Number(kpi.monthly_bonus_calculated || 0) +
          Number(kpi.quarterly_bonus_calculated || 0) +
          Number(kpi.annual_bonus_calculated || 0)

        monthMap.set(kpi.month, {
          count: existing.count + 1,
          totalBonus: existing.totalBonus + totalBonus,
        })
      }
    })

    return monthMap
  }, [employeeKpis])

  // Get list data for a specific date
  const getListData = (value: Dayjs) => {
    const month = value.month() + 1 // dayjs months are 0-indexed
    const year = value.year()

    if (year !== selectedYear) {
      return []
    }

    const monthData = bonusesByMonth.get(month)
    if (!monthData) {
      return []
    }

    return [
      {
        type: 'success',
        content: `${monthData.count} сотрудников`,
      },
      {
        type: 'warning',
        content: formatCurrency(monthData.totalBonus),
      },
    ]
  }

  // Custom month cell renderer
  const monthCellRender = (value: Dayjs) => {
    const listData = getListData(value)
    if (listData.length === 0) {
      return null
    }

    return (
      <div style={{ padding: '8px' }}>
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          {listData.map((item, index) => (
            <div key={index}>
              <Badge
                status={item.type as any}
                text={
                  <Text style={{ fontSize: 12 }} type={index === 1 ? 'warning' : 'secondary'}>
                    {item.content}
                  </Text>
                }
              />
            </div>
          ))}
        </Space>
      </div>
    )
  }

  // Custom date cell renderer (for day view - not used much, but required)
  const dateCellRender = (_value: Dayjs) => {
    // We don't show daily data for KPI bonuses
    return null
  }

  // Handle panel change (year/month navigation)
  const handlePanelChange = (value: Dayjs) => {
    setSelectedYear(value.year())
  }

  return (
    <Card
      title="Календарь бонусов"
      extra={
        <Space>
          <Select
            value={selectedYear}
            onChange={(value) => setSelectedYear(value)}
            style={{ width: 120 }}
          >
            {Array.from({ length: 5 }, (_, i) => dayjs().year() - 2 + i).map((year) => (
              <Option key={year} value={year}>
                {year}
              </Option>
            ))}
          </Select>
        </Space>
      }
    >
      {employeeKpiQuery.isLoading ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: 400,
          }}
        >
          <Spin size="large" tip="Загрузка данных...">
            <div style={{ minHeight: 200 }} />
          </Spin>
        </div>
      ) : (
        <>
          <Calendar
            value={dayjs().year(selectedYear).month(0)}
            mode="year"
            cellRender={(current, info) => {
              if (info.type === 'month') {
                return monthCellRender(current)
              }
              return dateCellRender(current)
            }}
            onPanelChange={handlePanelChange}
            headerRender={({ value }) => {
              return (
                <div style={{ padding: 8 }}>
                  <Space>
                    <Text strong style={{ fontSize: 16 }}>
                      {value.format('YYYY')} год
                    </Text>
                  </Space>
                </div>
              )
            }}
          />

          {bonusesByMonth.size === 0 && (
            <div
              style={{
                textAlign: 'center',
                padding: 40,
                color: '#999',
              }}
            >
              <Text type="secondary">Нет данных по бонусам за {selectedYear} год</Text>
            </div>
          )}
        </>
      )}
    </Card>
  )
}
