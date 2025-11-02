/**
 * Payroll Tax Widget
 * Shows payroll structure with salary components and tax breakdown
 */
import React, { useMemo } from 'react'
import { Card, Statistic, Row, Col, Typography } from 'antd'
import { Pie } from '@ant-design/plots'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Text } = Typography

interface PayrollTaxWidgetProps {
  year: number
  departmentId?: number
  height?: number
}

interface MonthData {
  month: number
  month_name: string
  gross_payroll: number
  ndfl: number
  pfr: number
  foms: number
  fss: number
  total_taxes: number
  net_payroll: number
  employer_cost: number
}

const PayrollTaxWidget: React.FC<PayrollTaxWidgetProps> = ({
  year,
  departmentId,
  height = 500,
}) => {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['payroll-tax', year, departmentId],
    queryFn: async () => {
      const response = await apiClient.get('/payroll/analytics/tax-breakdown-by-month', {
        params: { year, department_id: departmentId },
      })
      return response.data
    },
  })

  // Calculate totals
  const totals = useMemo(() => {
    if (!data || !Array.isArray(data)) return null

    const totalGross = data.reduce((sum: number, m: MonthData) => sum + (m.gross_payroll || 0), 0)
    const totalNdfl = data.reduce((sum: number, m: MonthData) => sum + (m.ndfl || 0), 0)
    const totalPfr = data.reduce((sum: number, m: MonthData) => sum + (m.pfr || 0), 0)
    const totalFoms = data.reduce((sum: number, m: MonthData) => sum + (m.foms || 0), 0)
    const totalFss = data.reduce((sum: number, m: MonthData) => sum + (m.fss || 0), 0)
    const totalSocial = totalPfr + totalFoms + totalFss
    const totalNet = data.reduce((sum: number, m: MonthData) => sum + (m.net_payroll || 0), 0)
    const totalCost = data.reduce((sum: number, m: MonthData) => sum + (m.employer_cost || 0), 0)

    return {
      gross: totalGross,
      ndfl: totalNdfl,
      pfr: totalPfr,
      foms: totalFoms,
      fss: totalFss,
      social: totalSocial,
      net: totalNet,
      totalCost: totalCost,
      taxBurden: totalGross > 0 ? ((totalNdfl + totalSocial) / totalGross * 100) : 0,
    }
  }, [data])

  // Prepare pie chart data
  const pieData = useMemo(() => {
    if (!totals) return []

    return [
      {
        type: 'ЗП (нетто)',
        value: totals.net,
      },
      {
        type: 'НДФЛ',
        value: totals.ndfl,
      },
      {
        type: 'ПФР',
        value: totals.pfr,
      },
      {
        type: 'ФОМС',
        value: totals.foms,
      },
      {
        type: 'ФСС',
        value: totals.fss,
      },
    ].filter(item => item.value > 0)
  }, [totals])

  const pieConfig = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    innerRadius: 0.6,
    color: ['#52c41a', '#faad14', '#f5222d', '#ff7a45', '#fa541c'],
    label: {
      text: (item: any) => `${item.type} ${(item.percent * 100).toFixed(1)}%`,
      position: 'outside' as const,
    },
    statistic: {
      title: {
        content: 'Всего',
        style: {
          fontSize: '14px',
        },
      },
      content: {
        content: totals ? new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(totals.totalCost) : '',
        style: {
          fontSize: '20px',
          fontWeight: 'bold',
        },
      },
    },
    legend: {
      position: 'bottom' as const,
    },
    tooltip: {
      formatter: (datum: any) => {
        return {
          name: datum.type,
          value: new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(datum.value),
        }
      },
    },
  }

  if (isLoading) {
    return (
      <Card title="Структура ФОТ и налоги">
        <LoadingState />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card title="Структура ФОТ и налоги">
        <ErrorState
          description={error instanceof Error ? error.message : 'Не удалось загрузить данные'}
        />
      </Card>
    )
  }

  if (!data || !totals || pieData.length === 0) {
    return (
      <Card title="Структура ФОТ и налоги">
        <Text type="secondary">Нет данных о зарплатах для {year} года</Text>
      </Card>
    )
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Card title="Структура ФОТ и налоги">
      {/* Summary Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Statistic
            title="ФОТ (Брутто)"
            value={totals.gross}
            precision={0}
            suffix="₽"
            valueStyle={{ color: '#1890ff', fontSize: '18px' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Налоги (всего)"
            value={totals.ndfl + totals.social}
            precision={0}
            suffix="₽"
            valueStyle={{ color: '#f5222d', fontSize: '18px' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Налоговая нагрузка"
            value={totals.taxBurden}
            precision={1}
            suffix="%"
            valueStyle={{ color: '#faad14', fontSize: '18px' }}
          />
        </Col>
      </Row>

      {/* Pie Chart */}
      <div style={{ height: height - 200 }}>
        <Pie {...pieConfig} />
      </div>

      {/* Breakdown */}
      <Row gutter={[8, 8]} style={{ marginTop: 16, fontSize: '12px' }}>
        <Col span={12}>
          <Text type="secondary">НДФЛ:</Text> <Text strong>{formatCurrency(totals.ndfl)}</Text>
        </Col>
        <Col span={12}>
          <Text type="secondary">Всего взносов:</Text> <Text strong>{formatCurrency(totals.social)}</Text>
        </Col>
        <Col span={8}>
          <Text type="secondary">ПФР:</Text> <Text>{formatCurrency(totals.pfr)}</Text>
        </Col>
        <Col span={8}>
          <Text type="secondary">ФОМС:</Text> <Text>{formatCurrency(totals.foms)}</Text>
        </Col>
        <Col span={8}>
          <Text type="secondary">ФСС:</Text> <Text>{formatCurrency(totals.fss)}</Text>
        </Col>
      </Row>
    </Card>
  )
}

export default PayrollTaxWidget
