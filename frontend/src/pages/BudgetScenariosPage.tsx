import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Select,
  Divider,
  Typography,
  Tabs,
  Progress,
  Alert,
} from 'antd'
import {
  PlusOutlined,
  BarChartOutlined,
  DollarOutlined,
  CompareOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { budgetScenariosApi, type BudgetScenarioSummary, type BudgetScenarioComparison } from '../api/budgetScenarios'
import { Column } from '@ant-design/plots'

const { Title, Text } = Typography
const { TabPane } = Tabs

const BudgetScenariosPage: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(2026)

  // Fetch scenarios summary
  const { data: summaries, isLoading: summariesLoading } = useQuery({
    queryKey: ['budget-scenarios-summary', selectedYear],
    queryFn: () => budgetScenariosApi.getSummary({ year: selectedYear }),
  })

  // Fetch comparison data
  const { data: comparison, isLoading: comparisonLoading } = useQuery({
    queryKey: ['budget-scenarios-comparison', selectedYear],
    queryFn: () => budgetScenariosApi.compareByYear(selectedYear),
  })

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  // Get priority color
  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      CRITICAL: 'red',
      HIGH: 'orange',
      MEDIUM: 'blue',
      LOW: 'default',
    }
    return colors[priority] || 'default'
  }

  // Get priority text
  const getPriorityText = (priority: string) => {
    const texts: Record<string, string> = {
      CRITICAL: 'Критический',
      HIGH: 'Высокий',
      MEDIUM: 'Средний',
      LOW: 'Низкий',
    }
    return texts[priority] || priority
  }

  // Prepare data for comparison chart
  const getComparisonChartData = () => {
    if (!comparison) return []

    const data: any[] = []

    comparison.scenarios.forEach((scenario) => {
      scenario.items.forEach((item) => {
        data.push({
          scenario: scenario.name,
          category: item.category_name,
          amount: Number(item.amount),
          type: item.category_type,
        })
      })
    })

    return data
  }

  // Summary cards
  const renderSummaryCards = () => {
    if (!summaries || summaries.length === 0) {
      return (
        <Alert
          message="Нет данных"
          description={`Сценарии для ${selectedYear} года не найдены. Создайте новый сценарий или выберите другой год.`}
          type="info"
          showIcon
        />
      )
    }

    return (
      <Row gutter={[16, 16]}>
        {summaries.map((summary) => (
          <Col xs={24} lg={8} key={summary.scenario_id}>
            <Card
              title={
                <Space>
                  {summary.scenario_name}
                  {summary.scenario_name.includes('Оптимистичный') && (
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  )}
                  {summary.scenario_name.includes('Пессимистичный') && (
                    <WarningOutlined style={{ color: '#ff4d4f' }} />
                  )}
                </Space>
              }
              extra={<Tag color="blue">{selectedYear}</Tag>}
            >
              <Statistic
                title="Общий бюджет"
                value={summary.total_budget}
                formatter={(value) => formatCurrency(Number(value))}
                prefix={<DollarOutlined />}
              />
              <Divider />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="OPEX"
                    value={summary.opex_total}
                    formatter={(value) => formatCurrency(Number(value))}
                    valueStyle={{ fontSize: '16px' }}
                  />
                  <Progress
                    percent={Number(summary.opex_percentage.toFixed(1))}
                    strokeColor="#1890ff"
                    size="small"
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="CAPEX"
                    value={summary.capex_total}
                    formatter={(value) => formatCurrency(Number(value))}
                    valueStyle={{ fontSize: '16px' }}
                  />
                  <Progress
                    percent={Number(summary.capex_percentage.toFixed(1))}
                    strokeColor="#52c41a"
                    size="small"
                  />
                </Col>
              </Row>
              <Divider />
              <Text type="secondary">Категорий: {summary.items_count}</Text>
            </Card>
          </Col>
        ))}
      </Row>
    )
  }

  // Comparison table
  const renderComparisonTable = () => {
    if (!comparison || comparison.scenarios.length === 0) return null

    // Collect all unique categories
    const categoriesSet = new Set<string>()
    comparison.scenarios.forEach((scenario) => {
      scenario.items.forEach((item) => {
        categoriesSet.add(item.category_name)
      })
    })

    const categories = Array.from(categoriesSet)

    const columns = [
      {
        title: 'Категория',
        dataIndex: 'category',
        key: 'category',
        fixed: 'left' as const,
        width: 200,
        render: (text: string, record: any) => (
          <Space direction="vertical" size={0}>
            <Text strong>{text}</Text>
            <Tag color={record.type === 'OPEX' ? 'blue' : 'green'}>{record.type}</Tag>
          </Space>
        ),
      },
      ...comparison.scenarios.map((scenario) => ({
        title: scenario.name,
        key: scenario.id,
        children: [
          {
            title: 'Сумма',
            key: `${scenario.id}-amount`,
            width: 150,
            render: (_: any, record: any) => {
              const item = scenario.items.find((i) => i.category_name === record.category)
              return item ? formatCurrency(Number(item.amount)) : '-'
            },
          },
          {
            title: '%',
            key: `${scenario.id}-percent`,
            width: 80,
            render: (_: any, record: any) => {
              const item = scenario.items.find((i) => i.category_name === record.category)
              return item ? formatPercent(Number(item.percentage)) : '-'
            },
          },
          {
            title: 'Изменение',
            key: `${scenario.id}-change`,
            width: 100,
            render: (_: any, record: any) => {
              const item = scenario.items.find((i) => i.category_name === record.category)
              if (!item || !item.change_from_previous) return '-'
              const change = Number(item.change_from_previous)
              return (
                <Tag color={change > 0 ? 'green' : change < 0 ? 'red' : 'default'}>
                  {change > 0 ? '+' : ''}
                  {formatPercent(change)}
                </Tag>
              )
            },
          },
        ],
      })),
    ]

    const dataSource = categories.map((category, index) => {
      const firstItem = comparison.scenarios[0].items.find((i) => i.category_name === category)
      return {
        key: index,
        category,
        type: firstItem?.category_type || 'OPEX',
      }
    })

    return (
      <Table
        columns={columns}
        dataSource={dataSource}
        scroll={{ x: 1200 }}
        pagination={false}
        bordered
      />
    )
  }

  // Comparison chart
  const renderComparisonChart = () => {
    const data = getComparisonChartData()
    if (data.length === 0) return null

    const config = {
      data,
      xField: 'category',
      yField: 'amount',
      seriesField: 'scenario',
      isGroup: true,
      columnStyle: {
        radius: [4, 4, 0, 0],
      },
      label: {
        position: 'top' as const,
        formatter: (datum: any) => {
          return formatCurrency(datum.amount).replace(/₽/, '')
        },
        style: {
          fontSize: 10,
        },
      },
      legend: {
        position: 'top' as const,
      },
      xAxis: {
        label: {
          autoRotate: true,
          autoHide: false,
        },
      },
      yAxis: {
        label: {
          formatter: (v: string) => formatCurrency(Number(v)).replace(/₽/, ''),
        },
      },
      tooltip: {
        formatter: (datum: any) => {
          return {
            name: datum.scenario,
            value: formatCurrency(datum.amount),
          }
        },
      },
    }

    return <Column {...config} />
  }

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <BarChartOutlined /> Сценарное планирование бюджета
          </Title>
        </Col>
        <Col>
          <Space>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              style={{ width: 120 }}
              options={[
                { value: 2024, label: '2024' },
                { value: 2025, label: '2025' },
                { value: 2026, label: '2026' },
                { value: 2027, label: '2027' },
              ]}
            />
            <Button type="primary" icon={<PlusOutlined />}>
              Создать сценарий
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs defaultActiveKey="summary">
        <TabPane
          tab={
            <span>
              <DollarOutlined />
              Обзор сценариев
            </span>
          }
          key="summary"
        >
          {renderSummaryCards()}
        </TabPane>

        <TabPane
          tab={
            <span>
              <CompareOutlined />
              Сравнение
            </span>
          }
          key="comparison"
        >
          <Card title="Сравнительная таблица" style={{ marginBottom: 16 }}>
            {renderComparisonTable()}
          </Card>
          <Card title="График сравнения">{renderComparisonChart()}</Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default BudgetScenariosPage
