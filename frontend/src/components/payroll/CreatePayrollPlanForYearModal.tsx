/**
 * Create Payroll Plan For Year Modal
 * Creates payroll plans for all 12 months of a year based on current employees
 */
import React, { useState, useMemo } from 'react'
import {
  Modal,
  Form,
  Select,
  Alert,
  Space,
  Statistic,
  Row,
  Col,
  Card,
  message,
  Table,
  Checkbox,
  InputNumber,
} from 'antd'
import { TeamOutlined, DollarOutlined, CalendarOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { employeeAPI, payrollPlanAPI, type Employee, type PayrollPlanCreate } from '@/api/payroll'
import { useDepartment } from '@/contexts/DepartmentContext'
import { formatCurrency } from '@/utils/formatters'

interface CreatePayrollPlanForYearModalProps {
  open: boolean
  onClose: () => void
}

const MONTHS = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
]

export const CreatePayrollPlanForYearModal: React.FC<CreatePayrollPlanForYearModalProps> = ({
  open,
  onClose,
}) => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const [form] = Form.useForm()
  const currentYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = useState(currentYear + 1)
  const [selectedEmployeeIds, setSelectedEmployeeIds] = useState<number[]>([])
  const [growthPercentage, setGrowthPercentage] = useState<number>(0)

  // Fetch active employees
  const { data: employees = [], isLoading: employeesLoading } = useQuery<Employee[]>({
    queryKey: ['employees', selectedDepartment?.id, 'ACTIVE'],
    queryFn: () =>
      employeeAPI.list({
        department_id: selectedDepartment?.id,
        status: 'ACTIVE',
      }),
    enabled: open,
  })

  // Create plans mutation
  const createPlansMutation = useMutation({
    mutationFn: async (plans: PayrollPlanCreate[]) => {
      const promises = plans.map((plan) => payrollPlanAPI.create(plan))
      return Promise.all(promises)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-plans'] })
      message.success(`Создано ${data.length} планов ФОТ на ${selectedYear} год`)
      handleClose()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании планов ФОТ')
    },
  })

  // Calculate statistics
  const statistics = useMemo(() => {
    const selectedEmployees = employees.filter((emp) => selectedEmployeeIds.includes(emp.id))

    const totalBaseSalary = selectedEmployees.reduce((sum, emp) => {
      const salary = emp.base_salary * (1 + growthPercentage / 100)
      return sum + salary
    }, 0)

    const totalMonthlyBonus = selectedEmployees.reduce((sum, emp) => {
      const bonus = (emp.monthly_bonus_base || 0) * (1 + growthPercentage / 100)
      return sum + bonus
    }, 0)

    const totalQuarterlyBonus = selectedEmployees.reduce((sum, emp) => {
      const bonus = (emp.quarterly_bonus_base || 0) * (1 + growthPercentage / 100)
      return sum + bonus
    }, 0)

    const totalAnnualBonus = selectedEmployees.reduce((sum, emp) => {
      const bonus = (emp.annual_bonus_base || 0) * (1 + growthPercentage / 100)
      return sum + bonus
    }, 0)

    const monthlyTotal = totalBaseSalary + totalMonthlyBonus
    const yearlyTotal = monthlyTotal * 12 + totalQuarterlyBonus * 4 + totalAnnualBonus

    return {
      employeeCount: selectedEmployees.length,
      totalBaseSalary,
      totalMonthlyBonus,
      totalQuarterlyBonus,
      totalAnnualBonus,
      monthlyTotal,
      yearlyTotal,
    }
  }, [employees, selectedEmployeeIds, growthPercentage])

  const handleCreate = async () => {
    try {
      const selectedEmployees = employees.filter((emp) => selectedEmployeeIds.includes(emp.id))

      if (selectedEmployees.length === 0) {
        message.warning('Выберите хотя бы одного сотрудника')
        return
      }

      const plans: PayrollPlanCreate[] = []

      // Create plans for all 12 months for each selected employee
      selectedEmployees.forEach((employee) => {
        for (let month = 1; month <= 12; month++) {
          const baseSalary = employee.base_salary * (1 + growthPercentage / 100)
          const monthlyBonus = (employee.monthly_bonus_base || 0) * (1 + growthPercentage / 100)
          const quarterlyBonus = (employee.quarterly_bonus_base || 0) * (1 + growthPercentage / 100)
          const annualBonus = (employee.annual_bonus_base || 0) * (1 + growthPercentage / 100)

          plans.push({
            year: selectedYear,
            month,
            employee_id: employee.id,
            base_salary: baseSalary,
            monthly_bonus: monthlyBonus,
            quarterly_bonus: month % 3 === 0 ? quarterlyBonus : 0, // Quarterly bonus on months 3, 6, 9, 12
            annual_bonus: month === 12 ? annualBonus : 0, // Annual bonus only in December
            other_payments: 0,
          })
        }
      })

      await createPlansMutation.mutateAsync(plans)
    } catch (error) {
      console.error('Create plans error:', error)
    }
  }

  const handleClose = () => {
    form.resetFields()
    setSelectedEmployeeIds([])
    setGrowthPercentage(0)
    onClose()
  }

  const columns = [
    {
      title: 'Сотрудник',
      dataIndex: 'full_name',
      key: 'full_name',
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
      render: (value: number) => {
        const adjusted = value * (1 + growthPercentage / 100)
        return (
          <div>
            <div>{formatCurrency(adjusted)}</div>
            {growthPercentage !== 0 && (
              <div style={{ fontSize: 11, color: '#999' }}>
                (было: {formatCurrency(value)})
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: 'Премия (мес)',
      dataIndex: 'monthly_bonus_base',
      key: 'monthly_bonus_base',
      render: (value: number) => {
        const adjusted = (value || 0) * (1 + growthPercentage / 100)
        return formatCurrency(adjusted)
      },
    },
    {
      title: 'Премия (квар)',
      dataIndex: 'quarterly_bonus_base',
      key: 'quarterly_bonus_base',
      render: (value: number) => {
        const adjusted = (value || 0) * (1 + growthPercentage / 100)
        return formatCurrency(adjusted)
      },
    },
    {
      title: 'Премия (год)',
      dataIndex: 'annual_bonus_base',
      key: 'annual_bonus_base',
      render: (value: number) => {
        const adjusted = (value || 0) * (1 + growthPercentage / 100)
        return formatCurrency(adjusted)
      },
    },
  ]

  return (
    <Modal
      open={open}
      title={`Создать план ФОТ на ${selectedYear} год`}
      width={1000}
      onCancel={handleClose}
      onOk={handleCreate}
      confirmLoading={createPlansMutation.isPending}
      okText="Создать планы"
      cancelText="Отмена"
      okButtonProps={{
        disabled: selectedEmployeeIds.length === 0,
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Alert
          message="Создание плана ФОТ на год"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Выберите год для создания плана</li>
              <li>Выберите сотрудников из списка</li>
              <li>Будут созданы планы на все 12 месяцев для каждого выбранного сотрудника</li>
              <li>Можно применить процент роста к базовым окладам и премиям</li>
              <li>Квартальные премии будут распределены по месяцам 3, 6, 9, 12</li>
              <li>Годовая премия будет добавлена в декабре</li>
            </ul>
          }
          type="info"
          showIcon
        />

        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Год планирования">
                <Select
                  value={selectedYear}
                  onChange={setSelectedYear}
                  style={{ width: '100%' }}
                >
                  {[currentYear, currentYear + 1, currentYear + 2].map((year) => (
                    <Select.Option key={year} value={year}>
                      {year} год
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Процент роста (%)"
                tooltip="Процент увеличения окладов и премий относительно текущих значений"
              >
                <InputNumber
                  value={growthPercentage}
                  onChange={(value) => setGrowthPercentage(value || 0)}
                  style={{ width: '100%' }}
                  min={-50}
                  max={100}
                  step={0.5}
                  precision={1}
                  suffix="%"
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>

        {/* Statistics */}
        {selectedEmployeeIds.length > 0 && (
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Сотрудников"
                  value={statistics.employeeCount}
                  prefix={<TeamOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="ФОТ в месяц"
                  value={statistics.monthlyTotal}
                  precision={0}
                  prefix={<DollarOutlined />}
                  suffix="₽"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="ФОТ за год"
                  value={statistics.yearlyTotal}
                  precision={0}
                  prefix={<CalendarOutlined />}
                  suffix="₽"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Планов будет создано"
                  value={statistics.employeeCount * 12}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* Employees Table */}
        <div>
          <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 500 }}>Выберите сотрудников:</span>
            <Space>
              <Checkbox
                checked={selectedEmployeeIds.length === employees.length && employees.length > 0}
                indeterminate={
                  selectedEmployeeIds.length > 0 && selectedEmployeeIds.length < employees.length
                }
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedEmployeeIds(employees.map((emp) => emp.id))
                  } else {
                    setSelectedEmployeeIds([])
                  }
                }}
              >
                Выбрать всех
              </Checkbox>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={employees}
            rowKey="id"
            loading={employeesLoading}
            pagination={{ pageSize: 10 }}
            size="small"
            rowSelection={{
              selectedRowKeys: selectedEmployeeIds,
              onChange: (selectedKeys) => {
                setSelectedEmployeeIds(selectedKeys as number[])
              },
            }}
            scroll={{ y: 300 }}
          />
        </div>
      </Space>
    </Modal>
  )
}
