import { useState, useEffect } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Table, Button, Space, Select, message, Popconfirm, Card, Statistic, Row, Col } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons'
import { payrollActualAPI, employeeAPI, PayrollActualWithEmployee } from '@/api/payroll'
import { formatCurrency } from '@/utils/formatters'
import PayrollActualFormModal from '@/components/payroll/PayrollActualFormModal'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import dayjs from 'dayjs'

const { Option } = Select

const MONTHS = [
  { value: 1, label: 'Январь' },
  { value: 2, label: 'Февраль' },
  { value: 3, label: 'Март' },
  { value: 4, label: 'Апрель' },
  { value: 5, label: 'Май' },
  { value: 6, label: 'Июнь' },
  { value: 7, label: 'Июль' },
  { value: 8, label: 'Август' },
  { value: 9, label: 'Сентябрь' },
  { value: 10, label: 'Октябрь' },
  { value: 11, label: 'Ноябрь' },
  { value: 12, label: 'Декабрь' },
]

const PayrollActualsPage = () => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const currentYear = new Date().getFullYear()

  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedMonth, setSelectedMonth] = useState<number | undefined>()
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | undefined>()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingActual, setEditingActual] = useState<PayrollActualWithEmployee | null>(null)

  // Reset filters when department changes
  useEffect(() => {
    setSelectedMonth(undefined)
    setSelectedEmployeeId(undefined)
  }, [selectedDepartment?.id])

  // Fetch payroll actuals
  const { data: actuals = [], isLoading } = useQuery({
    queryKey: ['payroll-actuals', selectedDepartment?.id, selectedYear, selectedMonth, selectedEmployeeId],
    queryFn: () =>
      payrollActualAPI.list({
        department_id: selectedDepartment?.id,
        year: selectedYear,
        month: selectedMonth,
        employee_id: selectedEmployeeId,
      }),
  })

  // Fetch employees for filter
  const { data: employees = [] } = useQuery({
    queryKey: ['employees', selectedDepartment?.id],
    queryFn: () => employeeAPI.list({ department_id: selectedDepartment?.id }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => payrollActualAPI.delete(id),
    onSuccess: () => {
      message.success('Выплата удалена')
      queryClient.invalidateQueries({ queryKey: ['payroll-actuals'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении выплаты')
    },
  })

  // Calculate statistics
  const totalPaid = actuals.reduce((sum, a) => sum + Number(a.total_paid), 0)
  const totalEmployees = new Set(actuals.map(a => a.employee_id)).size
  const totalRecords = actuals.length

  const handleCreate = () => {
    setEditingActual(null)
    setModalVisible(true)
  }

  const handleEdit = (actual: PayrollActualWithEmployee) => {
    setEditingActual(actual)
    setModalVisible(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleExport = async () => {
    try {
      await payrollActualAPI.exportToExcel({
        year: selectedYear,
        month: selectedMonth,
        department_id: selectedDepartment?.id,
      })
      message.success('Экспорт выполнен успешно')
    } catch (error) {
      message.error('Ошибка при экспорте')
    }
  }

  const columns = [
    {
      title: 'Сотрудник',
      dataIndex: ['employee', 'full_name'],
      key: 'employee',
      width: 200,
      fixed: 'left' as const,
    },
    {
      title: 'Должность',
      dataIndex: ['employee', 'position'],
      key: 'position',
      width: 150,
    },
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 80,
      align: 'center' as const,
    },
    {
      title: 'Месяц',
      dataIndex: 'month',
      key: 'month',
      width: 120,
      render: (month: number) => MONTHS.find(m => m.value === month)?.label || month,
    },
    {
      title: 'Дата выплаты',
      dataIndex: 'payment_date',
      key: 'payment_date',
      width: 120,
      render: (date: string) => date ? dayjs(date).format('DD.MM.YYYY') : '-',
    },
    {
      title: 'Оклад',
      dataIndex: 'base_salary_paid',
      key: 'base_salary_paid',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Мес. премия',
      dataIndex: 'monthly_bonus_paid',
      key: 'monthly_bonus_paid',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Квар. премия',
      dataIndex: 'quarterly_bonus_paid',
      key: 'quarterly_bonus_paid',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Год. премия',
      dataIndex: 'annual_bonus_paid',
      key: 'annual_bonus_paid',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Прочее',
      dataIndex: 'other_payments_paid',
      key: 'other_payments_paid',
      width: 100,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'НДФЛ',
      dataIndex: 'income_tax_amount',
      key: 'income_tax_amount',
      width: 100,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Страховые',
      dataIndex: 'social_tax_amount',
      key: 'social_tax_amount',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Всего выплачено',
      dataIndex: 'total_paid',
      key: 'total_paid',
      width: 140,
      align: 'right' as const,
      render: (value: number) => (
        <span style={{ fontWeight: 'bold', color: '#52c41a' }}>
          {formatCurrency(value)}
        </span>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: PayrollActualWithEmployee) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить выплату?"
            description="Вы уверены, что хотите удалить эту выплату?"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Отмена"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Всего выплачено"
              value={totalPaid}
              precision={2}
              suffix="₽"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Количество сотрудников"
              value={totalEmployees}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Количество выплат"
              value={totalRecords}
            />
          </Card>
        </Col>
      </Row>

      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Select
          placeholder="Год"
          style={{ width: 120 }}
          value={selectedYear}
          onChange={setSelectedYear}
        >
          {[currentYear - 1, currentYear, currentYear + 1].map((year) => (
            <Option key={year} value={year}>
              {year}
            </Option>
          ))}
        </Select>

        <Select
          placeholder="Месяц"
          style={{ width: 150 }}
          value={selectedMonth}
          onChange={setSelectedMonth}
          allowClear
        >
          {MONTHS.map((month) => (
            <Option key={month.value} value={month.value}>
              {month.label}
            </Option>
          ))}
        </Select>

        <Select
          placeholder="Сотрудник"
          style={{ width: 250 }}
          value={selectedEmployeeId}
          onChange={setSelectedEmployeeId}
          allowClear
          showSearch
          filterOption={(input, option) => {
            const label = option?.label ?? option?.children
            return String(label ?? '')
              .toLowerCase()
              .includes(input.toLowerCase())
          }}
        >
          {employees.map((emp: any) => (
            <Option key={emp.id} value={emp.id}>
              {emp.full_name} - {emp.position}
            </Option>
          ))}
        </Select>

        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Добавить выплату
        </Button>

        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          Экспорт в Excel
        </Button>
      </div>

      <ResponsiveTable
        columns={columns}
        dataSource={actuals}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1800 }}
        mobileLayout="card"
        pagination={{
          pageSize: 50,
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total}`,
        }}
      />

      <PayrollActualFormModal
        visible={modalVisible}
        actualId={editingActual?.id}
        defaultValues={
          editingActual
            ? {
                year: editingActual.year,
                month: editingActual.month,
                employee_id: editingActual.employee_id,
              }
            : undefined
        }
        onCancel={() => {
          setModalVisible(false)
          setEditingActual(null)
        }}
      />
    </div>
  )
}

export default PayrollActualsPage
