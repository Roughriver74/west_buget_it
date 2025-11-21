import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Typography,
  Spin,
  Alert,
  Tag,
} from 'antd'
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts'
import dayjs, { Dayjs } from 'dayjs'
import { analyticsApi, categoriesApi } from '@/api'
import type { ForecastMethod } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'

const { RangePicker } = DatePicker
const { Title, Text } = Typography
const { Option } = Select

interface PaymentForecastChartProps {
  defaultMethod?: ForecastMethod
}

const PaymentForecastChart: React.FC<PaymentForecastChartProps> = ({
  defaultMethod = 'simple_average',
}) => {
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().add(1, 'day'),
    dayjs().add(30, 'days'),
  ])
  const [method, setMethod] = useState<ForecastMethod>(defaultMethod)
  const [lookbackDays, setLookbackDays] = useState<number>(90)
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [showComparison, setShowComparison] = useState(false)

  // Fetch forecast data
  const { data: forecastData, isLoading: forecastLoading } = useQuery({
    queryKey: [
      'payment-forecast',
      dateRange[0].format('YYYY-MM-DD'),
      dateRange[1].format('YYYY-MM-DD'),
      method,
      lookbackDays,
      categoryId,
    ],
    queryFn: () =>
      analyticsApi.getPaymentForecast({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        method,
        lookback_days: lookbackDays,
        category_id: categoryId,
      }),
  })

  // Fetch comparison data (all methods)
  const { data: comparisonData, isLoading: comparisonLoading } = useQuery({
    queryKey: [
      'forecast-summary',
      dateRange[0].format('YYYY-MM-DD'),
      dateRange[1].format('YYYY-MM-DD'),
      categoryId,
    ],
    queryFn: () =>
      analyticsApi.getForecastSummary({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        category_id: categoryId,
      }),
    enabled: showComparison,
  })

  // Fetch categories for filter
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  // Prepare chart data
  const chartData =
    forecastData?.forecast.map((item) => ({
      date: dayjs(item.date).format('DD.MM'),
      fullDate: item.date,
      amount: item.predicted_amount,
      confidence: item.confidence,
    })) || []

  // Get confidence color
  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'green'
      case 'medium':
        return 'orange'
      case 'low':
        return 'red'
      default:
        return 'default'
    }
  }

  // Get confidence tag
  const getConfidenceTag = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'Высокая'
      case 'medium':
        return 'Средняя'
      case 'low':
        return 'Низкая'
      default:
        return confidence
    }
  }

  // Comparison table columns
  const comparisonColumns = [
    {
      title: 'Метод',
      dataIndex: 'method',
      key: 'method',
      render: (text: string) => {
        const labels: Record<string, string> = {
          simple_average: 'Простое среднее',
          moving_average: 'Скользящее среднее',
          seasonal: 'Сезонный анализ',
        }
        return labels[text] || text
      },
    },
    {
      title: 'Общий прогноз',
      dataIndex: 'total',
      key: 'total',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Средний день',
      dataIndex: 'daily_avg',
      key: 'daily_avg',
      render: (value: number) => formatCurrency(value),
    },
  ]

  const comparisonTableData = comparisonData
    ? [
        {
          key: 'simple_average',
          method: 'simple_average',
          ...comparisonData.forecasts.simple_average,
        },
        {
          key: 'moving_average',
          method: 'moving_average',
          ...comparisonData.forecasts.moving_average,
        },
        {
          key: 'seasonal',
          method: 'seasonal',
          ...comparisonData.forecasts.seasonal,
        },
      ]
    : []

  return (
    <div>
      <Title level={3}>Прогноз платежей</Title>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Text strong>Период прогноза:</Text>
            <RangePicker
              style={{ width: '100%', marginTop: 8 }}
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
              format="DD.MM.YYYY"
            />
          </Col>

          <Col xs={24} md={5}>
            <Text strong>Метод прогноза:</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={method}
              onChange={setMethod}
            >
              <Option value="simple_average">Простое среднее</Option>
              <Option value="moving_average">Скользящее среднее</Option>
              <Option value="seasonal">Сезонный анализ</Option>
            </Select>
          </Col>

          <Col xs={24} md={5}>
            <Text strong>Глубина анализа (дней):</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              value={lookbackDays}
              onChange={setLookbackDays}
            >
              <Option value={30}>30 дней</Option>
              <Option value={60}>60 дней</Option>
              <Option value={90}>90 дней</Option>
              <Option value={180}>180 дней</Option>
            </Select>
          </Col>

          <Col xs={24} md={6}>
            <Text strong>Категория:</Text>
            <Select
              style={{ width: '100%', marginTop: 8 }}
              placeholder="Все категории"
              allowClear
              value={categoryId}
              onChange={setCategoryId}
            >
              {categories?.map((cat) => (
                <Option key={cat.id} value={cat.id}>
                  {cat.name}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Summary Statistics */}
      {forecastData && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={8}>
            <Card>
              <Statistic
                title="Общий прогноз"
                value={forecastData.summary.total_predicted}
                formatter={(value) => formatCurrency(value as number)}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic
                title="Средний день"
                value={forecastData.summary.average_daily}
                formatter={(value) => formatCurrency(value as number)}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic title="Дней в прогнозе" value={forecastData.period.days} />
            </Card>
          </Col>
        </Row>
      )}

      {/* Alert for low confidence */}
      {forecastData &&
        forecastData.forecast.some((item) => item.confidence === 'low') && (
          <Alert
            message="Низкая достоверность прогноза"
            description="Недостаточно исторических данных для точного прогноза. Рекомендуется использовать прогноз с осторожностью."
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

      {/* Chart */}
      <Card style={{ marginBottom: 24 }}>
        <Spin spinning={forecastLoading}>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelFormatter={(label) => `Дата: ${label}`}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="amount"
                fill="#1890ff"
                fillOpacity={0.3}
                stroke="none"
                name="Доверительный интервал"
              />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#1890ff"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Прогноз платежей"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </Spin>
      </Card>

      {/* Comparison Table */}
      <Card
        title="Сравнение методов прогнозирования"
        extra={
          <Select
            value={showComparison}
            onChange={setShowComparison}
            style={{ width: 120 }}
          >
            <Option value={false}>Скрыть</Option>
            <Option value={true}>Показать</Option>
          </Select>
        }
      >
        {showComparison && (
          <Spin spinning={comparisonLoading}>
            <ResponsiveTable
              dataSource={comparisonTableData}
              columns={comparisonColumns}
              pagination={false}
              size="small"
            />
          </Spin>
        )}
      </Card>

      {/* Detailed Forecast Table */}
      <Card title="Детальный прогноз" style={{ marginTop: 24 }}>
        <ResponsiveTable
          dataSource={forecastData?.forecast || []}
          columns={[
            {
              title: 'Дата',
              dataIndex: 'date',
              key: 'date',
              render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
            },
            {
              title: 'Прогноз',
              dataIndex: 'predicted_amount',
              key: 'predicted_amount',
              render: (amount: number) => formatCurrency(amount),
            },
            {
              title: 'Достоверность',
              dataIndex: 'confidence',
              key: 'confidence',
              render: (confidence: string) => (
                <Tag color={getConfidenceColor(confidence)}>
                  {getConfidenceTag(confidence)}
                </Tag>
              ),
            },
          ]}
          rowKey="date"
          pagination={{ pageSize: 10 }}
          size="small"
          loading={forecastLoading}
        />
      </Card>
    </div>
  )
}

export default PaymentForecastChart
