/**
 * Budget Scenario Comparison Chart
 * Visual comparison of Base/Optimistic/Pessimistic scenarios
 */
import React, { useMemo } from 'react'
import { Card, Empty, Space, Statistic, Row, Col, Typography, Tag } from 'antd'
import { Column } from '@ant-design/plots'
import { useQuery } from '@tanstack/react-query'
import { versionsApi } from '@/api/budgetPlanning'
import { BudgetScenarioType, BudgetVersion } from '@/types/budgetPlanning'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

const { Text } = Typography

interface BudgetScenarioComparisonChartProps {
  year: number
  scenarioIds: {
    base?: number
    optimistic?: number
    pessimistic?: number
  }
}

const scenarioColors = {
  [BudgetScenarioType.BASE]: '#1890ff',
  [BudgetScenarioType.OPTIMISTIC]: '#52c41a',
  [BudgetScenarioType.PESSIMISTIC]: '#ff4d4f',
}

const scenarioNames = {
  [BudgetScenarioType.BASE]: 'Базовый',
  [BudgetScenarioType.OPTIMISTIC]: 'Оптимистичный',
  [BudgetScenarioType.PESSIMISTIC]: 'Пессимистичный',
}

const BudgetScenarioComparisonChart: React.FC<BudgetScenarioComparisonChartProps> = ({
  year,
  scenarioIds,
}) => {
  // Fetch versions for each scenario
  const {
    data: baseVersions,
    isLoading: baseLoading,
    isError: baseError,
  } = useQuery({
    queryKey: ['versions', year, scenarioIds.base],
    queryFn: () =>
      versionsApi.getAll({
        year,
        scenario_id: scenarioIds.base,
      }),
    enabled: !!scenarioIds.base,
  })

  const {
    data: optimisticVersions,
    isLoading: optimisticLoading,
    isError: optimisticError,
  } = useQuery({
    queryKey: ['versions', year, scenarioIds.optimistic],
    queryFn: () =>
      versionsApi.getAll({
        year,
        scenario_id: scenarioIds.optimistic,
      }),
    enabled: !!scenarioIds.optimistic,
  })

  const {
    data: pessimisticVersions,
    isLoading: pessimisticLoading,
    isError: pessimisticError,
  } = useQuery({
    queryKey: ['versions', year, scenarioIds.pessimistic],
    queryFn: () =>
      versionsApi.getAll({
        year,
        scenario_id: scenarioIds.pessimistic,
      }),
    enabled: !!scenarioIds.pessimistic,
  })

  const isLoading = baseLoading || optimisticLoading || pessimisticLoading
  const hasError = baseError || optimisticError || pessimisticError

  // Get latest (or approved) version for each scenario
  const getLatestVersion = (versions?: BudgetVersion[]): BudgetVersion | null => {
    if (!versions || versions.length === 0) return null

    // Prefer approved version
    const approved = versions.find((v) => v.status === 'APPROVED')
    if (approved) return approved

    // Otherwise take the latest version by version_number
    return versions.reduce((latest, current) =>
      parseFloat(String(current.version_number)) > parseFloat(String(latest.version_number))
        ? current
        : latest
    )
  }

  const baseVersion = getLatestVersion(baseVersions)
  const optimisticVersion = getLatestVersion(optimisticVersions)
  const pessimisticVersion = getLatestVersion(pessimisticVersions)

  // Prepare summary comparison data
  const summaryData = useMemo(() => {
    const data: Array<{
      scenario: string
      type: string
      amount: number
      scenarioType: BudgetScenarioType
    }> = []

    if (baseVersion) {
      data.push(
        {
          scenario: scenarioNames[BudgetScenarioType.BASE],
          type: 'OPEX',
          amount: parseFloat(String(baseVersion.total_opex || 0)),
          scenarioType: BudgetScenarioType.BASE,
        },
        {
          scenario: scenarioNames[BudgetScenarioType.BASE],
          type: 'CAPEX',
          amount: parseFloat(String(baseVersion.total_capex || 0)),
          scenarioType: BudgetScenarioType.BASE,
        }
      )
    }

    if (optimisticVersion) {
      data.push(
        {
          scenario: scenarioNames[BudgetScenarioType.OPTIMISTIC],
          type: 'OPEX',
          amount: parseFloat(String(optimisticVersion.total_opex || 0)),
          scenarioType: BudgetScenarioType.OPTIMISTIC,
        },
        {
          scenario: scenarioNames[BudgetScenarioType.OPTIMISTIC],
          type: 'CAPEX',
          amount: parseFloat(String(optimisticVersion.total_capex || 0)),
          scenarioType: BudgetScenarioType.OPTIMISTIC,
        }
      )
    }

    if (pessimisticVersion) {
      data.push(
        {
          scenario: scenarioNames[BudgetScenarioType.PESSIMISTIC],
          type: 'OPEX',
          amount: parseFloat(String(pessimisticVersion.total_opex || 0)),
          scenarioType: BudgetScenarioType.PESSIMISTIC,
        },
        {
          scenario: scenarioNames[BudgetScenarioType.PESSIMISTIC],
          type: 'CAPEX',
          amount: parseFloat(String(pessimisticVersion.total_capex || 0)),
          scenarioType: BudgetScenarioType.PESSIMISTIC,
        }
      )
    }

    return data
  }, [baseVersion, optimisticVersion, pessimisticVersion])

  // Calculate differences from base scenario
  const calculateDiff = (value: number, baseValue: number) => {
    if (baseValue === 0) return 0
    return ((value - baseValue) / baseValue) * 100
  }

  const baseTotal = baseVersion ? parseFloat(String(baseVersion.total_amount || 0)) : 0
  const optimisticTotal = optimisticVersion ? parseFloat(String(optimisticVersion.total_amount || 0)) : 0
  const pessimisticTotal = pessimisticVersion ? parseFloat(String(pessimisticVersion.total_amount || 0)) : 0

  const optimisticDiff = baseTotal ? calculateDiff(optimisticTotal, baseTotal) : 0
  const pessimisticDiff = baseTotal ? calculateDiff(pessimisticTotal, baseTotal) : 0

  const columnConfig = {
    data: summaryData,
    xField: 'scenario',
    yField: 'amount',
    seriesField: 'type',
    isGroup: true,
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
    color: ({ type }: { type: string }) => {
      return type === 'OPEX' ? '#597ef7' : '#95de64'
    },
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      formatter: (datum: any) => {
        return {
          name: datum.type,
          value: new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
          }).format(datum.amount),
        }
      },
    },
    yAxis: {
      label: {
        formatter: (v: string) => {
          const num = parseFloat(v)
          if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`
          }
          if (num >= 1000) {
            return `${(num / 1000).toFixed(0)}K`
          }
          return v
        },
      },
    },
  }

  if (isLoading) {
    return (
      <Card title={`Сравнение сценариев бюджета ${year}`}>
        <LoadingState />
      </Card>
    )
  }

  if (hasError) {
    return (
      <Card title={`Сравнение сценариев бюджета ${year}`}>
        <ErrorState description="Не удалось загрузить данные сценариев" />
      </Card>
    )
  }

  if (summaryData.length === 0) {
    return (
      <Card title={`Сравнение сценариев бюджета ${year}`}>
        <Empty description="Нет данных для сравнения. Создайте версии бюджета для разных сценариев." />
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <span>{`Сравнение сценариев бюджета ${year}`}</span>
          <Tag color="blue">OPEX vs CAPEX</Tag>
        </Space>
      }
    >
      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {baseVersion && (
          <Col xs={24} sm={8}>
            <Card size="small" style={{ backgroundColor: '#e6f7ff', borderColor: scenarioColors[BudgetScenarioType.BASE] }}>
              <Statistic
                title={
                  <Space>
                    <span>{scenarioNames[BudgetScenarioType.BASE]}</span>
                    <Tag color="blue">Базовый сценарий</Tag>
                  </Space>
                }
                value={baseTotal}
                precision={0}
                suffix="₽"
                valueStyle={{ color: scenarioColors[BudgetScenarioType.BASE] }}
              />
            </Card>
          </Col>
        )}

        {optimisticVersion && (
          <Col xs={24} sm={8}>
            <Card size="small" style={{ backgroundColor: '#f6ffed', borderColor: scenarioColors[BudgetScenarioType.OPTIMISTIC] }}>
              <Statistic
                title={
                  <Space>
                    <span>{scenarioNames[BudgetScenarioType.OPTIMISTIC]}</span>
                    {optimisticDiff > 0 && <ArrowUpOutlined style={{ color: '#52c41a' }} />}
                  </Space>
                }
                value={optimisticTotal}
                precision={0}
                suffix="₽"
                valueStyle={{ color: scenarioColors[BudgetScenarioType.OPTIMISTIC] }}
              />
              {baseVersion && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {optimisticDiff > 0 ? '+' : ''}
                  {optimisticDiff.toFixed(1)}% от базового
                </Text>
              )}
            </Card>
          </Col>
        )}

        {pessimisticVersion && (
          <Col xs={24} sm={8}>
            <Card size="small" style={{ backgroundColor: '#fff1f0', borderColor: scenarioColors[BudgetScenarioType.PESSIMISTIC] }}>
              <Statistic
                title={
                  <Space>
                    <span>{scenarioNames[BudgetScenarioType.PESSIMISTIC]}</span>
                    {pessimisticDiff < 0 && <ArrowDownOutlined style={{ color: '#ff4d4f' }} />}
                  </Space>
                }
                value={pessimisticTotal}
                precision={0}
                suffix="₽"
                valueStyle={{ color: scenarioColors[BudgetScenarioType.PESSIMISTIC] }}
              />
              {baseVersion && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {pessimisticDiff > 0 ? '+' : ''}
                  {pessimisticDiff.toFixed(1)}% от базового
                </Text>
              )}
            </Card>
          </Col>
        )}
      </Row>

      {/* OPEX/CAPEX Comparison Chart */}
      <Column {...columnConfig} height={350} />

      {/* Version details */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        {baseVersion && (
          <Col xs={24} sm={8}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong>{scenarioNames[BudgetScenarioType.BASE]}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Версия: v{baseVersion.version_number}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                OPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(baseVersion.total_opex || 0)))}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                CAPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(baseVersion.total_capex || 0)))}
              </Text>
            </Space>
          </Col>
        )}

        {optimisticVersion && (
          <Col xs={24} sm={8}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong>{scenarioNames[BudgetScenarioType.OPTIMISTIC]}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Версия: v{optimisticVersion.version_number}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                OPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(optimisticVersion.total_opex || 0)))}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                CAPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(optimisticVersion.total_capex || 0)))}
              </Text>
            </Space>
          </Col>
        )}

        {pessimisticVersion && (
          <Col xs={24} sm={8}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong>{scenarioNames[BudgetScenarioType.PESSIMISTIC]}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Версия: v{pessimisticVersion.version_number}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                OPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(pessimisticVersion.total_opex || 0)))}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                CAPEX: {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(parseFloat(String(pessimisticVersion.total_capex || 0)))}
              </Text>
            </Space>
          </Col>
        )}
      </Row>
    </Card>
  )
}

export default BudgetScenarioComparisonChart
