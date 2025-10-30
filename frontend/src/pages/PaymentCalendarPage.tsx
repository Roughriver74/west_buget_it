import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Calendar,
  Badge,
  Select,
  Row,
  Col,
  Statistic,
  Modal,
  Table,
  Typography,
  Space,
  Spin,
  Button,
  Tabs,
  Tooltip,
  Tag,
} from 'antd'
import { CalendarOutlined, DollarOutlined, FileTextOutlined, LineChartOutlined, DownloadOutlined, RiseOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import { analyticsApi, categoriesApi, forecastApi } from '@/api'
import type { PaymentCalendarDay, PaymentDetail, ForecastExpense } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import PaymentForecastChart from '@/components/forecast/PaymentForecastChart'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Title, Text } = Typography
const { Option } = Select

const PaymentCalendarPage = () => {
  const { selectedDepartment } = useDepartment()
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs())
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedDayData, setSelectedDayData] = useState<PaymentDetail[] | null>(null)
  const [selectedDayDate, setSelectedDayDate] = useState<string>('')

  const currentYear = selectedDate.year()
  const currentMonth = selectedDate.month() + 1

  // Handle forecast export
  const handleExportForecast = async () => {
    try {
      const departmentParam = selectedDepartment?.id ? `?department_id=${selectedDepartment.id}` : ''
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/forecast/export/${currentYear}/${currentMonth}${departmentParam}`,
        {
          method: 'GET',
        }
      )

      if (!response.ok) {
        throw new Error('Export failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Планирование_${String(currentMonth).padStart(2, '0')}.${currentYear}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error exporting forecast:', error)
    }
  }

  // Fetch calendar data
  const { data: calendarData, isLoading: calendarLoading } = useQuery({
    queryKey: ['payment-calendar', currentYear, currentMonth, selectedDepartment?.id, categoryId],
    queryFn: () =>
      analyticsApi.getPaymentCalendar({
        year: currentYear,
        month: currentMonth,
        category_id: categoryId,
      }),
  })

  // Fetch forecast data
  const { data: forecastData, isLoading: forecastLoading } = useQuery({
    queryKey: ['forecast-calendar', currentYear, currentMonth, selectedDepartment?.id],
    queryFn: () => forecastApi.getAll(currentYear, currentMonth, selectedDepartment?.id!),
    enabled: !!selectedDepartment?.id,
  })

  // Fetch categories for filter
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  // Create a map of dates to payment data for quick lookup
  const paymentMap = new Map<string, PaymentCalendarDay>()
  calendarData?.days.forEach((day) => {
    paymentMap.set(day.date, day)
  })

  // Create a map of dates to forecast data
  const forecastMap = new Map<string, { count: number; total: number; items: ForecastExpense[] }>()
  forecastData?.forEach((forecast) => {
    const dateStr = dayjs(forecast.forecast_date).format('YYYY-MM-DD')
    const existing = forecastMap.get(dateStr) || { count: 0, total: 0, items: [] }
    forecastMap.set(dateStr, {
      count: existing.count + 1,
      total: existing.total + Number(forecast.amount),
      items: [...existing.items, forecast],
    })
  })

  // Calculate month statistics
  const monthStats = {
    totalAmount: calendarData?.days.reduce((sum, day) => sum + day.total_amount, 0) || 0,
    totalPayments: calendarData?.days.reduce((sum, day) => sum + day.payment_count, 0) || 0,
    daysWithPayments: calendarData?.days.length || 0,
  }

  // Handle date cell rendering
  const dateCellRender = (value: Dayjs) => {
    const dateStr = value.format('YYYY-MM-DD')
    const payment = paymentMap.get(dateStr)
    const forecast = forecastMap.get(dateStr)

    if (value.month() !== currentMonth - 1) {
      return null
    }

    if (!payment && !forecast) {
      return null
    }

    return (
      <div style={{ fontSize: '11px' }}>
        {/* Actual payments */}
        {payment && (
          <Tooltip title={`${payment.payment_count} фактических платежей на сумму ${formatCurrency(payment.total_amount)}`}>
            <div>
              {/* Determine badge status based on amount */}
              {(() => {
                let status: 'success' | 'processing' | 'error' = 'success'
                if (payment.total_amount > 100000) {
                  status = 'error' // Red for large amounts
                } else if (payment.total_amount > 50000) {
                  status = 'processing' // Blue for medium amounts
                }
                return <Badge status={status} text={`${payment.payment_count} пл.`} />
              })()}
              <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
                {formatCurrency(payment.total_amount)}
              </div>
            </div>
          </Tooltip>
        )}

        {/* Forecast expenses */}
        {forecast && (
          <Tooltip title={`${forecast.count} прогнозных расходов на сумму ${formatCurrency(forecast.total)} (автоматический расчет)`}>
            <div style={{
              marginTop: payment ? 4 : 0,
              padding: '2px 4px',
              backgroundColor: '#e6f7ff',
              borderRadius: '2px',
              border: '1px dashed #91d5ff'
            }}>
              <Space size={4}>
                <RiseOutlined style={{ color: '#1890ff', fontSize: '10px' }} />
                <span style={{ fontSize: '10px', color: '#1890ff' }}>{forecast.count} прогн.</span>
              </Space>
              <div style={{ fontWeight: 'bold', color: '#1890ff', fontStyle: 'italic' }}>
                {formatCurrency(forecast.total)}
              </div>
            </div>
          </Tooltip>
        )}
      </div>
    )
  }

  // Handle date selection
  const handleDateSelect = async (value: Dayjs) => {
    const dateStr = value.format('YYYY-MM-DD')
    const payment = paymentMap.get(dateStr)
    const forecast = forecastMap.get(dateStr)

    if (payment || forecast) {
      try {
        let dayData: PaymentDetail[] = []

        // Fetch actual payments if they exist
        if (payment) {
          const result = await analyticsApi.getPaymentsByDay({
            date: dateStr,
            category_id: categoryId,
          })
          dayData = result.payments
        }

        // Add forecast items to the display (convert to PaymentDetail format)
        if (forecast) {
          const forecastItems = forecast.items.map((f) => ({
            id: -f.id, // Negative ID to distinguish from actual payments
            number: 'ПРОГНОЗ',
            amount: Number(f.amount),
            category_name: f.category?.name || '',
            contractor_name: f.contractor?.name || '-',
            organization_name: f.organization?.name || '',
            comment: f.comment || (f.is_regular ? 'Регулярный расход' : 'Прогнозный расход'),
            is_forecast: true, // Custom flag to style differently
          })) as any

          dayData = [...dayData, ...forecastItems]
        }

        setSelectedDayData(dayData)
        setSelectedDayDate(dateStr)
        setModalVisible(true)
      } catch (error) {
        console.error('Error fetching day payments:', error)
      }
    }
  }

  // Table columns for payment details modal
  const columns = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 150,
      render: (number: string, record: any) => (
        <Space>
          {record.is_forecast && (
            <Tooltip title="Прогнозный расход">
              <RiseOutlined style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
          <span style={{ color: record.is_forecast ? '#595959' : 'inherit', fontWeight: record.is_forecast ? 500 : 'normal' }}>
            {number}
          </span>
        </Space>
      ),
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: any) => (
        <span style={{
          color: record.is_forecast ? '#595959' : 'inherit',
          fontWeight: 'bold',
          fontStyle: record.is_forecast ? 'italic' : 'normal'
        }}>
          {formatCurrency(amount)}
        </span>
      ),
    },
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      ),
    },
    {
      title: 'Контрагент',
      dataIndex: 'contractor_name',
      key: 'contractor_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      ),
    },
    {
      title: 'Организация',
      dataIndex: 'organization_name',
      key: 'organization_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      ),
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit', fontStyle: record.is_forecast ? 'italic' : 'normal' }}>{text}</span>
      ),
    },
  ]

  const tabItems = [
    {
      key: 'calendar',
      label: (
        <span>
          <CalendarOutlined />
          Календарь
        </span>
      ),
      children: (
        <>
          {/* Filters and Statistics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} md={6}>
              <Card>
                <Statistic
                  title="Всего оплат за месяц"
                  value={monthStats.totalPayments}
                  prefix={<FileTextOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} md={6}>
              <Card>
                <Statistic
                  title="Дней с оплатами"
                  value={monthStats.daysWithPayments}
                  prefix={<CalendarOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card>
                <Statistic
                  title="Общая сумма за месяц"
                  value={monthStats.totalAmount}
                  prefix={<DollarOutlined />}
                  formatter={(value) => formatCurrency(value as number)}
                />
              </Card>
            </Col>
          </Row>

          {/* Filters */}
          <Card style={{ marginBottom: 24 }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  <Text strong>Фильтры:</Text>
                  <Select
                    style={{ width: 300 }}
                    placeholder="Все категории"
                    allowClear
                    value={categoryId}
                    onChange={setCategoryId}
                  >
                    {categories?.map((cat) => (
                      <Option key={cat.id} value={cat.id}>
                        {cat.name} ({cat.type})
                      </Option>
                    ))}
                  </Select>
                </Space>
              </Col>
              <Col>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleExportForecast}
                  disabled={!forecastData || forecastData.length === 0}
                >
                  Экспорт прогноза в Excel
                </Button>
              </Col>
            </Row>
          </Card>

          {/* Calendar */}
          <Card>
            <div style={{
              marginBottom: 16,
              padding: '12px 16px',
              backgroundColor: '#f5f5f5',
              borderRadius: '4px',
              border: '1px solid #d9d9d9'
            }}>
              <Space size="large">
                <Tooltip title="Подтвержденные платежи с фактическими датами">
                  <Space>
                    <Badge status="success" />
                    <Text strong style={{ fontSize: '14px', color: '#262626' }}>
                      Фактические оплаты
                    </Text>
                  </Space>
                </Tooltip>
                <Tooltip title="Прогнозируемые расходы на основе исторических данных">
                  <Space>
                    <RiseOutlined style={{ color: '#1890ff', fontSize: '14px' }} />
                    <Text strong style={{ fontSize: '14px', color: '#262626' }}>
                      Прогнозные расходы
                    </Text>
                    <Tag color="blue" style={{ margin: 0 }}>Автоматический расчет</Tag>
                  </Space>
                </Tooltip>
              </Space>
            </div>
            <Spin spinning={calendarLoading || forecastLoading}>
              <Calendar
                value={selectedDate}
                onSelect={handleDateSelect}
                onPanelChange={(date) => setSelectedDate(date)}
                cellRender={dateCellRender}
                fullscreen
              />
            </Spin>
          </Card>
        </>
      ),
    },
    {
      key: 'forecast',
      label: (
        <span>
          <LineChartOutlined />
          Прогноз
        </span>
      ),
      children: <PaymentForecastChart />,
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <CalendarOutlined /> Календарь оплат и прогнозы
      </Title>

      <Tabs defaultActiveKey="calendar" items={tabItems} />

      {/* Payment Details Modal */}
      <Modal
        title={`Оплаты за ${dayjs(selectedDayDate).format('DD.MM.YYYY')}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Закрыть
          </Button>,
        ]}
        width={1000}
      >
        {selectedDayData && (
          <>
            <div style={{ marginBottom: 16 }}>
              <Statistic
                title="Всего оплат"
                value={selectedDayData.length}
                suffix={`на сумму ${formatCurrency(
                  selectedDayData.reduce((sum, p) => sum + p.amount, 0)
                )}`}
              />
            </div>
            <Table
              dataSource={selectedDayData}
              columns={columns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
              rowClassName={(record: any) => record.is_forecast ? 'forecast-row' : ''}
            />
          </>
        )}
      </Modal>
    </div>
  )
}

export default PaymentCalendarPage
