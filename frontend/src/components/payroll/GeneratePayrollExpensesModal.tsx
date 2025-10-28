import React, { useState } from 'react'
import { Modal, DatePicker, Table, Button, message, Space, Statistic, Row, Col, Alert } from 'antd'
import { DollarOutlined, UserOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs, { Dayjs } from 'dayjs'
import { payrollAnalyticsAPI } from '@/api/payroll'
import { useDepartment } from '@/contexts/DepartmentContext'

interface GeneratePayrollExpensesModalProps {
  open: boolean
  onClose: () => void
}

const GeneratePayrollExpensesModal: React.FC<GeneratePayrollExpensesModalProps> = ({ open, onClose }) => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs())
  const [previewData, setPreviewData] = useState<any>(null)

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: () =>
      payrollAnalyticsAPI.generatePayrollExpenses({
        year: selectedDate.year(),
        month: selectedDate.month() + 1,
        department_id: selectedDepartment?.id,
        dry_run: true,
      }),
    onSuccess: (data) => {
      setPreviewData(data)
      if (data.statistics.employee_count === 0) {
        message.warning('Нет данных по ФОТ за выбранный период')
      }
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при предпросмотре')
    },
  })

  // Generate mutation
  const generateMutation = useMutation({
    mutationFn: () =>
      payrollAnalyticsAPI.generatePayrollExpenses({
        year: selectedDate.year(),
        month: selectedDate.month() + 1,
        department_id: selectedDepartment?.id,
        dry_run: false,
      }),
    onSuccess: (data) => {
      message.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      onClose()
      setPreviewData(null)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании заявок')
    },
  })

  const handlePreview = () => {
    previewMutation.mutate()
  }

  const handleGenerate = () => {
    Modal.confirm({
      title: 'Создать заявки на зарплату?',
      content: `Будет создано ${previewData?.statistics?.employee_count || 0} заявок на общую сумму ${previewData?.statistics?.total_amount?.toLocaleString('ru-RU') || 0} ₽`,
      okText: 'Создать',
      cancelText: 'Отмена',
      onOk: () => generateMutation.mutate(),
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
      dataIndex: 'base_salary',
      key: 'base_salary',
      render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      render: (val: number | null) => val ? `${val.toFixed(1)}%` : '-',
    },
    {
      title: 'Премии КПИ',
      dataIndex: 'kpi_bonuses',
      key: 'kpi_bonuses',
      render: (val: number) => val > 0 ? `${val.toLocaleString('ru-RU')} ₽` : '-',
    },
    {
      title: 'Всего к выплате',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (val: number) => (
        <strong>{val.toLocaleString('ru-RU')} ₽</strong>
      ),
    },
  ]

  return (
    <Modal
      title="Генерация заявок на зарплату"
      open={open}
      onCancel={handleClose}
      width={1200}
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
          key="generate"
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={handleGenerate}
          loading={generateMutation.isPending}
          disabled={!previewData || previewData.statistics.employee_count === 0}
        >
          Создать заявки
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <label style={{ marginRight: 8 }}>Период:</label>
          <DatePicker
            picker="month"
            value={selectedDate}
            onChange={(date) => date && setSelectedDate(date)}
            format="MMMM YYYY"
            style={{ width: 200 }}
          />
        </div>

        {previewData && (
          <>
            <Alert
              message={previewData.message}
              description={`Категория расходов: ${previewData.salary_category_name}`}
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
                  title="Общая сумма"
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
              pagination={{ pageSize: 5 }}
              size="small"
            />
          </>
        )}
      </Space>
    </Modal>
  )
}

export default GeneratePayrollExpensesModal
