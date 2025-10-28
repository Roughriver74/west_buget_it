import React, { useState, useMemo, useCallback } from 'react'
import { Modal, DatePicker, Radio, Table, Button, message, Space, Statistic, Row, Col, Alert, Descriptions, InputNumber } from 'antd'
import { DollarOutlined, UserOutlined, CheckCircleOutlined, CalendarOutlined, EditOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs, { Dayjs } from 'dayjs'
import { payrollAnalyticsAPI, PayrollActualCreate } from '@/api/payroll'
import { useDepartment } from '@/contexts/DepartmentContext'

interface RegisterPayrollPaymentModalProps {
  open: boolean
  onClose: () => void
}

interface EditablePayment {
  employee_id: number
  employee_name: string
  position: string
  base_salary_paid: number
  monthly_bonus_paid: number
  quarterly_bonus_paid: number
  annual_bonus_paid: number
  total_paid: number
  payment_type: string
  payment_date: string
  department_id: number
  year: number
  month: number
}

const RegisterPayrollPaymentModal: React.FC<RegisterPayrollPaymentModalProps> = ({ open, onClose }) => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs())
  const [paymentType, setPaymentType] = useState<'advance' | 'final'>('advance')
  const [previewData, setPreviewData] = useState<any>(null)
  const [editableData, setEditableData] = useState<EditablePayment[]>([])
  const [isEditing, setIsEditing] = useState(false)

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: () =>
      payrollAnalyticsAPI.registerPayrollPayment({
        year: selectedDate.year(),
        month: selectedDate.month() + 1,
        payment_type: paymentType,
        department_id: selectedDepartment?.id,
        dry_run: true,
      }),
    onSuccess: (data) => {
      setPreviewData(data)
      // Add year and month to each item in preview data
      const enrichedData = (data.preview || []).map((item: any) => ({
        ...item,
        year: data.year,
        month: data.month,
      }))
      setEditableData(enrichedData)
      setIsEditing(false)
      if (data.statistics.employee_count === 0) {
        message.warning('Нет данных по ФОТ за выбранный период')
      } else if (data.statistics.skipped_existing > 0) {
        message.info(`${data.statistics.skipped_existing} выплат уже зарегистрированы`)
      }
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при предпросмотре')
    },
  })

  // Register mutation (bulk with custom data)
  const registerMutation = useMutation({
    mutationFn: (payments: PayrollActualCreate[]) =>
      payrollAnalyticsAPI.registerPayrollPaymentBulk(payments),
    onSuccess: (data) => {
      message.success(`Зарегистрировано ${data.created_count} выплат на сумму ${data.total_amount.toLocaleString('ru-RU')} ₽`)
      if (data.skipped_count > 0) {
        message.info(`Пропущено ${data.skipped_count} выплат (уже зарегистрированы ранее)`)
      }
      if (data.errors && data.errors.length > 0) {
        message.warning(`Ошибки: ${data.errors.join(', ')}`)
      }
      queryClient.invalidateQueries({ queryKey: ['payroll-actuals'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      onClose()
      setPreviewData(null)
      setEditableData([])
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при регистрации выплат')
    },
  })

  const handlePreview = () => {
    previewMutation.mutate()
  }

  const handleRegister = () => {
    // Prepare data for bulk registration
    const payments: PayrollActualCreate[] = editableData.map((item) => ({
      year: item.year,
      month: item.month,
      employee_id: item.employee_id,
      base_salary_paid: item.base_salary_paid,
      monthly_bonus_paid: item.monthly_bonus_paid,
      quarterly_bonus_paid: item.quarterly_bonus_paid,
      annual_bonus_paid: item.annual_bonus_paid,
      other_payments_paid: 0,
      payment_date: item.payment_date,
    }))

    // Validate that year and month are present
    const invalidItems = payments.filter(p => !p.year || !p.month)
    if (invalidItems.length > 0) {
      message.error('Ошибка: отсутствуют данные по периоду. Попробуйте создать предпросмотр заново.')
      console.error('Invalid payment items:', invalidItems)
      return
    }

    const totalAmount = editableData.reduce((sum, item) => sum + item.total_paid, 0)

    Modal.confirm({
      title: 'Зарегистрировать выплаты зарплаты?',
      content: (
        <div>
          <p>Тип выплаты: <strong>{paymentType === 'advance' ? 'Аванс (50% оклада)' : 'Окончательный расчет (50% оклада + премии)'}</strong></p>
          <p>Период: <strong>{selectedDate.format('MMMM YYYY')}</strong></p>
          <p>Дата выплаты: <strong>{previewData?.payment_date}</strong></p>
          <p>Будет зарегистрировано <strong>{editableData.length}</strong> выплат на общую сумму <strong>{totalAmount.toLocaleString('ru-RU')} ₽</strong></p>
          {isEditing && <p style={{ color: '#ff4d4f' }}><strong>⚠️ Внимание: суммы были отредактированы вручную</strong></p>}
        </div>
      ),
      okText: 'Зарегистрировать',
      cancelText: 'Отмена',
      onOk: () => registerMutation.mutate(payments),
    })
  }

  const handleClose = () => {
    setPreviewData(null)
    setEditableData([])
    setIsEditing(false)
    onClose()
  }

  const handleReset = () => {
    setPreviewData(null)
    setEditableData([])
    setIsEditing(false)
  }

  // Update editable data when cell is edited
  const handleCellEdit = useCallback((employeeId: number, field: keyof EditablePayment, value: number) => {
    setEditableData((prevData) => {
      const newData = prevData.map((item) => {
        if (item.employee_id === employeeId) {
          const updated = { ...item, [field]: value }
          // Recalculate total
          updated.total_paid =
            updated.base_salary_paid +
            updated.monthly_bonus_paid +
            updated.quarterly_bonus_paid +
            updated.annual_bonus_paid
          return updated
        }
        return item
      })
      return newData
    })
    setIsEditing(true)
  }, [])

  // Calculate total from editable data
  const totalAmount = useMemo(() => {
    return editableData.reduce((sum, item) => sum + item.total_paid, 0)
  }, [editableData])

  const columns = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
      width: 200,
      fixed: 'left' as const,
    },
    {
      title: 'Должность',
      dataIndex: 'position',
      key: 'position',
      width: 180,
    },
    {
      title: 'Оклад',
      dataIndex: 'base_salary_paid',
      key: 'base_salary_paid',
      width: 150,
      render: (val: number, record: EditablePayment) => (
        <InputNumber
          value={val}
          onChange={(value) => handleCellEdit(record.employee_id, 'base_salary_paid', value || 0)}
          min={0}
          precision={2}
          formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
          parser={(value) => value?.replace(/\s/g, '') as any}
          style={{ width: '100%' }}
          suffix="₽"
        />
      ),
    },
    {
      title: 'Месячные премии',
      dataIndex: 'monthly_bonus_paid',
      key: 'monthly_bonus_paid',
      width: 150,
      render: (val: number, record: EditablePayment) => (
        <InputNumber
          value={val}
          onChange={(value) => handleCellEdit(record.employee_id, 'monthly_bonus_paid', value || 0)}
          min={0}
          precision={2}
          formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
          parser={(value) => value?.replace(/\s/g, '') as any}
          style={{ width: '100%' }}
          suffix="₽"
        />
      ),
    },
    {
      title: 'Квартальные премии',
      dataIndex: 'quarterly_bonus_paid',
      key: 'quarterly_bonus_paid',
      width: 170,
      render: (val: number, record: EditablePayment) => (
        <InputNumber
          value={val}
          onChange={(value) => handleCellEdit(record.employee_id, 'quarterly_bonus_paid', value || 0)}
          min={0}
          precision={2}
          formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
          parser={(value) => value?.replace(/\s/g, '') as any}
          style={{ width: '100%' }}
          suffix="₽"
        />
      ),
    },
    {
      title: 'Годовые премии',
      dataIndex: 'annual_bonus_paid',
      key: 'annual_bonus_paid',
      width: 150,
      render: (val: number, record: EditablePayment) => (
        <InputNumber
          value={val}
          onChange={(value) => handleCellEdit(record.employee_id, 'annual_bonus_paid', value || 0)}
          min={0}
          precision={2}
          formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
          parser={(value) => value?.replace(/\s/g, '') as any}
          style={{ width: '100%' }}
          suffix="₽"
        />
      ),
    },
    {
      title: 'Всего к выплате',
      dataIndex: 'total_paid',
      key: 'total_paid',
      width: 150,
      fixed: 'right' as const,
      render: (val: number) => (
        <strong>{val.toLocaleString('ru-RU')} ₽</strong>
      ),
    },
  ]

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          Регистрация выплаты зарплаты
          {isEditing && <EditOutlined style={{ color: '#ff4d4f' }} />}
        </div>
      }
      open={open}
      onCancel={handleClose}
      width={1400}
      footer={[
        <Button key="close" onClick={handleClose}>
          Закрыть
        </Button>,
        previewData ? (
          <Button
            key="reset"
            type="default"
            onClick={handleReset}
          >
            Сброс / Новый предпросмотр
          </Button>
        ) : (
          <Button
            key="preview"
            type="default"
            onClick={handlePreview}
            loading={previewMutation.isPending}
          >
            Предпросмотр
          </Button>
        ),
        <Button
          key="register"
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={handleRegister}
          loading={registerMutation.isPending}
          disabled={!previewData || editableData.length === 0}
        >
          Зарегистрировать выплаты
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Row gutter={16}>
          <Col span={12}>
            <label style={{ display: 'block', marginBottom: 8 }}>Период:</label>
            <DatePicker
              picker="month"
              value={selectedDate}
              onChange={(date) => date && setSelectedDate(date)}
              format="MMMM YYYY"
              style={{ width: '100%' }}
              disabled={!!previewData}
            />
          </Col>
          <Col span={12}>
            <label style={{ display: 'block', marginBottom: 8 }}>Тип выплаты:</label>
            <Radio.Group
              value={paymentType}
              onChange={(e) => setPaymentType(e.target.value)}
              style={{ width: '100%' }}
              disabled={!!previewData}
            >
              <Radio.Button value="advance" style={{ width: '50%', textAlign: 'center' }}>
                <CalendarOutlined /> Аванс (50% оклада) - 25-е число
              </Radio.Button>
              <Radio.Button value="final" style={{ width: '50%', textAlign: 'center' }}>
                <CalendarOutlined /> Окончательный расчет (50% оклада + премии) - 10-е число
              </Radio.Button>
            </Radio.Group>
          </Col>
        </Row>

        {previewData && (
          <>
            <Alert
              message={
                <div>
                  {isEditing && <><EditOutlined /> Данные были изменены. </>}
                  {previewData.message}
                </div>
              }
              description={
                <Descriptions size="small" column={1}>
                  <Descriptions.Item label="Дата выплаты">
                    {dayjs(previewData.payment_date).format('DD.MM.YYYY')}
                  </Descriptions.Item>
                  <Descriptions.Item label="Тип">
                    {paymentType === 'advance' ? 'Аванс (50% оклада, без премий)' : 'Окончательный расчет (50% оклада + все премии)'}
                  </Descriptions.Item>
                  {previewData.statistics.skipped_existing > 0 && (
                    <Descriptions.Item label="Пропущено">
                      {previewData.statistics.skipped_existing} выплат уже зарегистрировано ранее
                    </Descriptions.Item>
                  )}
                </Descriptions>
              }
              type={isEditing ? 'warning' : 'info'}
              showIcon
            />

            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Сотрудников"
                  value={editableData.length}
                  prefix={<UserOutlined />}
                />
              </Col>
              <Col span={16}>
                <Statistic
                  title="Общая сумма выплат"
                  value={totalAmount}
                  precision={2}
                  suffix="₽"
                  prefix={<DollarOutlined />}
                  valueStyle={isEditing ? { color: '#ff4d4f' } : undefined}
                />
              </Col>
            </Row>

            <Alert
              message="Редактируемая таблица"
              description="Вы можете изменить суммы перед регистрацией. Кликните на любое поле с суммой для редактирования."
              type="info"
              showIcon
              icon={<EditOutlined />}
            />

            <Table
              dataSource={editableData}
              columns={columns}
              rowKey="employee_id"
              pagination={{ pageSize: 10 }}
              size="small"
              scroll={{ x: 1200 }}
              bordered
            />
          </>
        )}
      </Space>
    </Modal>
  )
}

export default RegisterPayrollPaymentModal
