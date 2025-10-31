/**
 * Payroll Summary Card - Display payroll (ФОТ) data for budget version
 */
import React, { useMemo } from 'react'
import { Card, Row, Col, Statistic } from 'antd'
import { TeamOutlined, DollarOutlined } from '@ant-design/icons'
import type { PayrollYearlySummary } from '@/types/budgetPlanning'

interface PayrollSummaryCardProps {
  payrollSummary: PayrollYearlySummary
}

export const PayrollSummaryCard: React.FC<PayrollSummaryCardProps> = ({
  payrollSummary,
}) => {
  const currencyFormatter = useMemo(
    () =>
      new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        maximumFractionDigits: 0,
      }),
    []
  )

  const formatCurrency = (value: number | string) => {
    const num = typeof value === 'string' ? parseFloat(value) : value
    return currencyFormatter.format(Number.isFinite(num) ? num : 0)
  }

  // Calculate average per month
  const avgPerMonth = useMemo(() => {
    const total = Number(payrollSummary.total_planned_annual || 0)
    return total / 12
  }, [payrollSummary])

  // Calculate bonus percentage
  const bonusPercentage = useMemo(() => {
    const total = Number(payrollSummary.total_planned_annual || 0)
    const bonuses = Number(payrollSummary.total_bonuses_annual || 0)
    return total > 0 ? (bonuses / total) * 100 : 0
  }, [payrollSummary])

  return (
    <Card
      title={
        <span>
          <TeamOutlined /> Фонд оплаты труда (ФОТ) - {payrollSummary.year} год
        </span>
      }
    >
      {/* Summary Statistics */}
      <Row gutter={16}>
        <Col xs={12} sm={6}>
          <Statistic
            title="Всего за год"
            value={Number(payrollSummary.total_planned_annual || 0)}
            formatter={(value) => formatCurrency(value as number)}
            valueStyle={{ fontSize: 20, fontWeight: 600, color: '#1890ff' }}
            prefix={<DollarOutlined />}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="Сотрудников"
            value={payrollSummary.total_employees}
            valueStyle={{ fontSize: 20, fontWeight: 600 }}
            prefix={<TeamOutlined />}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="Средний месяц"
            value={avgPerMonth}
            formatter={(value) => formatCurrency(value as number)}
            valueStyle={{ fontSize: 20, fontWeight: 600 }}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="Доля премий"
            value={bonusPercentage}
            precision={1}
            suffix="%"
            valueStyle={{
              fontSize: 20,
              fontWeight: 600,
              color: bonusPercentage > 20 ? '#cf1322' : bonusPercentage > 10 ? '#faad14' : '#3f8600',
            }}
          />
        </Col>
      </Row>
    </Card>
  )
}
