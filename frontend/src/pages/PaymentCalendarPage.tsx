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
  Typography,
  Space,
  Spin,
  Button,
  Tabs,
  Tooltip,
  Tag} from 'antd'
import { CalendarOutlined, DollarOutlined, LineChartOutlined, DownloadOutlined, RiseOutlined, CheckCircleOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import { analyticsApi, categoriesApi, forecastApi } from '@/api'
import type { PaymentCalendarDay, PaymentDetail, ForecastExpense } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import PaymentForecastChart from '@/components/forecast/PaymentForecastChart'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useTheme } from '@/contexts/ThemeContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { getApiBaseUrl } from '@/config/api'

const { Title, Text } = Typography
const { Option } = Select

const PaymentCalendarPage = () => {
  const { selectedDepartment } = useDepartment()
  const { mode } = useTheme()
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
        `${getApiBaseUrl()}/forecast/export/${currentYear}/${currentMonth}${departmentParam}`,
        {
          method: 'GET'}
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
        department_id: selectedDepartment?.id,
        category_id: categoryId})})

  // Fetch forecast data
  const { data: forecastData, isLoading: forecastLoading } = useQuery({
    queryKey: ['forecast-calendar', currentYear, currentMonth, selectedDepartment?.id],
    queryFn: () => forecastApi.getAll(currentYear, currentMonth, selectedDepartment?.id ?? 0),
    enabled: !!selectedDepartment?.id})

  // Fetch categories for filter
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true })})

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
      items: [...existing.items, forecast]})
  })

  // Calculate month statistics
  const monthStats = {
    totalAmount: calendarData?.days.reduce((sum, day) => sum + day.total_amount, 0) || 0,
    totalPayments: calendarData?.days.reduce((sum, day) => sum + day.payment_count, 0) || 0,
    totalPlanned: calendarData?.days.reduce((sum, day) => sum + (day.planned_amount || 0), 0) || 0,
    totalPlannedCount: calendarData?.days.reduce((sum, day) => sum + (day.planned_count || 0), 0) || 0,
    daysWithPayments: calendarData?.days.length || 0}

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

        {/* Planned payments (PENDING expenses) */}
        {payment?.planned_amount && payment?.planned_count ? (
          <Tooltip title={`${payment.planned_count} запланированных платежей на сумму ${formatCurrency(payment.planned_amount)} (заявки к оплате)`}>
            <div style={{
              marginTop: payment.total_amount > 0 ? 4 : 0,
              padding: '2px 4px',
              backgroundColor: '#fff7e6',
              borderRadius: '2px',
              border: '1px solid #ffd591'
            }}>
              <Space size={4}>
                <CalendarOutlined style={{ color: '#fa8c16', fontSize: '10px' }} />
                <span style={{ fontSize: '10px', color: '#fa8c16' }}>{payment.planned_count} запл.</span>
              </Space>
              <div style={{ fontWeight: 'bold', color: '#fa8c16' }}>
                {formatCurrency(payment.planned_amount)}
              </div>
            </div>
          </Tooltip>
        ) : null}

        {/* Forecast expenses */}
        {forecast && (
          <Tooltip title={`${forecast.count} прогнозных расходов на сумму ${formatCurrency(forecast.total)} (автоматический расчет)`}>
            <div style={{
              marginTop: (payment && (payment.total_amount > 0 || (payment.planned_amount && payment.planned_amount > 0))) ? 4 : 0,
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
            department_id: selectedDepartment?.id,
            category_id: categoryId})
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
      )},
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
      )},
    {
      title: 'Категория',
      dataIndex: 'category_name',
      key: 'category_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      )},
    {
      title: 'Контрагент',
      dataIndex: 'contractor_name',
      key: 'contractor_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      )},
    {
      title: 'Организация',
      dataIndex: 'organization_name',
      key: 'organization_name',
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit' }}>{text}</span>
      )},
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (text: string, record: any) => (
        <span style={{ color: record.is_forecast ? '#595959' : 'inherit', fontStyle: record.is_forecast ? 'italic' : 'normal' }}>{text}</span>
      )},
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
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Фактически оплачено"
                  value={monthStats.totalAmount}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  formatter={(value) => formatCurrency(value as number)}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {monthStats.totalPayments} платежей
                </Text>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Запланировано к оплате"
                  value={monthStats.totalPlanned}
                  valueStyle={{ color: '#fa8c16' }}
                  prefix={<CalendarOutlined style={{ color: '#fa8c16' }} />}
                  formatter={(value) => formatCurrency(value as number)}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {monthStats.totalPlannedCount} заявок
                </Text>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Дней с платежами"
                  value={monthStats.daysWithPayments}
                  prefix={<CalendarOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Общая сумма"
                  value={monthStats.totalAmount + monthStats.totalPlanned}
                  prefix={<DollarOutlined />}
                  formatter={(value) => formatCurrency(value as number)}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Оплачено + запланировано
                </Text>
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
              <Space size="large" wrap>
                <Tooltip title="Подтвержденные платежи с фактическими датами">
                  <Space>
                    <Badge status="success" />
                    <Text strong style={{ fontSize: '14px', color: '#262626' }}>
                      Фактические оплаты
                    </Text>
                  </Space>
                </Tooltip>
                <Tooltip title="Заявки к оплате со статусом PENDING">
                  <Space>
                    <CalendarOutlined style={{ color: '#fa8c16', fontSize: '14px' }} />
                    <Text strong style={{ fontSize: '14px', color: '#262626' }}>
                      Запланировано
                    </Text>
                    <Tag color="orange" style={{ margin: 0 }}>К оплате</Tag>
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
      )},
    {
      key: 'forecast',
      label: (
        <span>
          <LineChartOutlined />
          Прогноз
        </span>
      ),
      children: <PaymentForecastChart />},
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
        {selectedDayData && (() => {
          // Separate actual, planned, and forecast payments
          const actualPayments = selectedDayData.filter((p: any) => p.status !== 'PLANNED' && !p.is_forecast)
          const plannedPayments = selectedDayData.filter((p: any) => p.status === 'PLANNED')
          const forecastPayments = selectedDayData.filter((p: any) => p.is_forecast)

          const actualTotal = actualPayments.reduce((sum, p) => sum + p.amount, 0)
          const plannedTotal = plannedPayments.reduce((sum, p) => sum + p.amount, 0)
          const forecastTotal = forecastPayments.reduce((sum, p) => sum + p.amount, 0)

          return (
            <>
              {/* Summary Statistics */}
              <Row gutter={16} style={{ marginBottom: 24 }}>
                {actualPayments.length > 0 && (
                  <Col span={8}>
                    <Card size="small">
                      <Statistic
                        title="Фактически оплачено"
                        value={actualPayments.length}
                        suffix={`на ${formatCurrency(actualTotal)}`}
                        valueStyle={{ color: '#52c41a' }}
                        prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                      />
                    </Card>
                  </Col>
                )}
                {plannedPayments.length > 0 && (
                  <Col span={8}>
                    <Card size="small">
                      <Statistic
                        title="Запланировано к оплате"
                        value={plannedPayments.length}
                        suffix={`на ${formatCurrency(plannedTotal)}`}
                        valueStyle={{ color: '#fa8c16' }}
                        prefix={<CalendarOutlined style={{ color: '#fa8c16' }} />}
                      />
                    </Card>
                  </Col>
                )}
                {forecastPayments.length > 0 && (
                  <Col span={8}>
                    <Card size="small">
                      <Statistic
                        title="Прогнозные расходы"
                        value={forecastPayments.length}
                        suffix={`на ${formatCurrency(forecastTotal)}`}
                        valueStyle={{ color: '#1890ff' }}
                        prefix={<RiseOutlined style={{ color: '#1890ff' }} />}
                      />
                    </Card>
                  </Col>
                )}
              </Row>

              {/* Actual Payments */}
              {actualPayments.length > 0 && (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: '16px', color: '#52c41a' }}>
                      <CheckCircleOutlined /> Фактически оплачено ({actualPayments.length})
                    </Text>
                  </div>
                  <ResponsiveTable
                    dataSource={actualPayments}
                    columns={columns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    style={{ marginBottom: 24 }}
                    mobileLayout="card"
                  />
                </>
              )}

              {/* Planned Payments */}
              {plannedPayments.length > 0 && (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: '16px', color: '#fa8c16' }}>
                      <CalendarOutlined /> Запланировано к оплате ({plannedPayments.length})
                    </Text>
                  </div>
                  <ResponsiveTable
                    dataSource={plannedPayments}
                    columns={columns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    style={{ marginBottom: 24 }}
                    rowClassName={() => 'planned-row'}
                    mobileLayout="card"
                  />
                </>
              )}

              {/* Forecast Payments */}
              {forecastPayments.length > 0 && (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                      <RiseOutlined /> Прогнозные расходы ({forecastPayments.length})
                    </Text>
                  </div>
                  <ResponsiveTable
                    dataSource={forecastPayments}
                    columns={columns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    rowClassName={() => 'forecast-row'}
                    mobileLayout="card"
                  />
                </>
              )}
            </>
          )
        })()}
      </Modal>

      <style>{`
        ${mode === 'dark' ? `
          .forecast-row {
            background-color: #111a2c !important;
          }
          .forecast-row:hover {
            background-color: #1a2a3a !important;
          }
          .planned-row {
            background-color: #2b2111 !important;
          }
          .planned-row:hover {
            background-color: #3a2a1a !important;
          }
        ` : `
          .forecast-row {
            background-color: #e6f7ff !important;
          }
          .forecast-row:hover {
            background-color: #bae7ff !important;
          }
          .planned-row {
            background-color: #fff7e6 !important;
          }
          .planned-row:hover {
            background-color: #ffd591 !important;
          }
        `}
      `}</style>
    </div>
  )
}

export default PaymentCalendarPage
