import React, { useState } from 'react'
import { Modal, DatePicker, Radio, Table, Button, message, Space, Statistic, Row, Col, Alert, Descriptions } from 'antd'
import { DollarOutlined, UserOutlined, CheckCircleOutlined, CalendarOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs, { Dayjs } from 'dayjs'
import { payrollAnalyticsAPI } from '@/api/payroll'
import { useDepartment } from '@/contexts/DepartmentContext'

interface RegisterPayrollPaymentModalProps {
  open: boolean
  onClose: () => void
}

const RegisterPayrollPaymentModal: React.FC<RegisterPayrollPaymentModalProps> = ({ open, onClose }) => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs())
  const [paymentType, setPaymentType] = useState<'advance' | 'final'>('advance')
  const [previewData, setPreviewData] = useState<any>(null)

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

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: () =>
      payrollAnalyticsAPI.registerPayrollPayment({
        year: selectedDate.year(),
        month: selectedDate.month() + 1,
        payment_type: paymentType,
        department_id: selectedDepartment?.id,
        dry_run: false,
      }),
    onSuccess: (data) => {
      message.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['payroll-actuals'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      onClose()
      setPreviewData(null)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при регистрации выплат')
    },
  })

  const handlePreview = () => {
    previewMutation.mutate()
  }

  const handleRegister = () => {
    Modal.confirm({
      title: 'Зарегистрировать выплаты зарплаты?',
      content: (
        <div>
          <p>Тип выплаты: <strong>{paymentType === 'advance' ? 'Аванс (50% оклада)' : 'Окончательный расчет (50% оклада + премии)'}</strong></p>
          <p>Период: <strong>{selectedDate.format('MMMM YYYY')}</strong></p>
          <p>Дата выплаты: <strong>{previewData?.payment_date}</strong></p>
          <p>Будет зарегистрировано <strong>{previewData?.statistics?.employee_count || 0}</strong> выплат на общую сумму <strong>{previewData?.statistics?.total_amount?.toLocaleString('ru-RU') || 0} ₽</strong></p>
        </div>
      ),
      okText: 'Зарегистрировать',
      cancelText: 'Отмена',
      onOk: () => registerMutation.mutate(),
    })
  }

  const handleClose = () => {
    setPreviewData(null)
    onClose()
  }

  const columns = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
    },
    {
      title: 'Должность',
      dataIndex: 'position',
      key: 'position',
    },
    {
      title: 'Оклад',
      dataIndex: 'base_salary_paid',
      key: 'base_salary_paid',
      render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Месячные премии',
      dataIndex: 'monthly_bonus_paid',
      key: 'monthly_bonus_paid',
      render: (val: number) => val > 0 ? `${val.toLocaleString('ru-RU')} ₽` : '-',
    },
    {
      title: 'Квартальные премии',
      dataIndex: 'quarterly_bonus_paid',
      key: 'quarterly_bonus_paid',
      render: (val: number) => val > 0 ? `${val.toLocaleString('ru-RU')} ₽` : '-',
    },
    {
      title: 'Годовые премии',
      dataIndex: 'annual_bonus_paid',
      key: 'annual_bonus_paid',
      render: (val: number) => val > 0 ? `${val.toLocaleString('ru-RU')} ₽` : '-',
    },
    {
      title: 'Всего к выплате',
      dataIndex: 'total_paid',
      key: 'total_paid',
      render: (val: number) => (
        <strong>{val.toLocaleString('ru-RU')} ₽</strong>
      ),
    },
  ]

  return (
    <Modal
      title="Регистрация выплаты зарплаты"
      open={open}
      onCancel={handleClose}
      width={1400}
      footer={[
        <Button key="close" onClick={handleClose}>
          Закрыть
        </Button>,
        <Button
          key="preview"
          type="default"
          onClick={handlePreview}
          loading={previewMutation.isPending}
          disabled={!!previewData}
        >
          Предпросмотр
        </Button>,
        <Button
          key="register"
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={handleRegister}
          loading={registerMutation.isPending}
          disabled={!previewData || previewData.statistics.employee_count === 0}
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
            />
          </Col>
          <Col span={12}>
            <label style={{ display: 'block', marginBottom: 8 }}>Тип выплаты:</label>
            <Radio.Group
              value={paymentType}
              onChange={(e) => setPaymentType(e.target.value)}
              style={{ width: '100%' }}
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
              message={previewData.message}
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
              type="info"
              showIcon
            />

            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Сотрудников"
                  value={previewData.statistics.employee_count}
                  prefix={<UserOutlined />}
                />
              </Col>
              <Col span={16}>
                <Statistic
                  title="Общая сумма выплат"
                  value={previewData.statistics.total_amount}
                  precision={2}
                  suffix="₽"
                  prefix={<DollarOutlined />}
                />
              </Col>
            </Row>

            <Table
              dataSource={previewData.preview}
              columns={columns}
              rowKey="employee_id"
              pagination={{ pageSize: 10 }}
              size="small"
              scroll={{ x: 1200 }}
            />
          </>
        )}
      </Space>
    </Modal>
  )
}

export default RegisterPayrollPaymentModal
