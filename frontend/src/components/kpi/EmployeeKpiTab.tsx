import { useMemo, useState } from 'react'
import {
  Card,
  Button,
  Table,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Divider,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { UploadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import type {
  EmployeeKPI,
  EmployeeKPICreate,
  EmployeeKPIUpdate,
  BonusType,
  KPIGoal,
  KPIGoalStatus,
} from '@/api/kpi'
import { employeeAPI } from '@/api/payroll'
import type { Employee } from '@/api/payroll'
import { formatCurrency } from '@/utils/formatters'
import ImportKPIModal from './ImportKPIModal'

const { Option } = Select
const { Text } = Typography

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)

const BONUS_TYPE_OPTIONS: BonusType[] = ['PERFORMANCE_BASED', 'FIXED', 'MIXED']
const bonusTypeLabels: Record<BonusType, string> = {
  PERFORMANCE_BASED: 'Performance',
  FIXED: 'Fixed',
  MIXED: 'Mixed',
}

const statusColor: Record<KPIGoalStatus, string> = {
  DRAFT: 'default',
  ACTIVE: 'processing',
  ACHIEVED: 'success',
  NOT_ACHIEVED: 'error',
  CANCELLED: 'warning',
}

const monthLabel = (month: number | null | undefined) =>
  typeof month === 'number' ? dayjs().month(month - 1).format('MMMM') : 'Годовая цель'

interface EmployeeKpiTabProps {
  departmentId?: number
  year?: number
}

export const EmployeeKpiTab: React.FC<EmployeeKpiTabProps> = ({ departmentId, year }) => {
  const queryClient = useQueryClient()
  const currentYear = year || dayjs().year()

  const [kpiModal, setKpiModal] = useState<{ open: boolean; editing?: EmployeeKPI }>({
    open: false,
  })

  const [importModalVisible, setImportModalVisible] = useState(false)

  const [employeeKpiForm] = Form.useForm<EmployeeKPICreate | EmployeeKPIUpdate>()

  // Queries
  const employeeKpiQuery = useQuery({
    queryKey: ['kpi-employee', departmentId, currentYear],
    queryFn: () =>
      kpiApi.listEmployeeKpis({
        department_id: departmentId,
        year: currentYear,
      }),
    enabled: !!departmentId,
  })

  const employeesQuery = useQuery({
    queryKey: ['department-employees', departmentId],
    queryFn: () =>
      employeeAPI.list({
        department_id: departmentId,
        status: 'ACTIVE',
        limit: 500,
      }),
    enabled: !!departmentId,
  })

  const goalsQuery = useQuery({
    queryKey: ['kpi-goals', currentYear, departmentId],
    queryFn: () =>
      kpiApi.listGoals({
        year: currentYear,
        department_id: departmentId,
      }),
    enabled: !!departmentId,
  })

  // Mutations
  const upsertEmployeeKpiMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id?: number
      payload: EmployeeKPICreate | EmployeeKPIUpdate
    }) => {
      if (id) {
        return kpiApi.updateEmployeeKpi(id, payload as EmployeeKPIUpdate)
      }
      return kpiApi.createEmployeeKpi(payload as EmployeeKPICreate)
    },
    onSuccess: () => {
      message.success('Показатели сотрудника обновлены')
      queryClient.invalidateQueries({ queryKey: ['kpi-employee'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-summary'] })
    },
  })

  const employees = employeesQuery.data || []
  const employeeKpis = employeeKpiQuery.data || []
  const goals = goalsQuery.data || []

  const employeeMap = useMemo(() => {
    const map = new Map<number, Employee>()
    employees.forEach((employee) => {
      map.set(employee.id, employee)
    })
    return map
  }, [employees])

  const goalMap = useMemo(() => {
    const map = new Map<number, KPIGoal>()
    goals.forEach((goal) => {
      map.set(goal.id, goal)
    })
    return map
  }, [goals])

  const onEditEmployeeKpi = (record?: EmployeeKPI) => {
    setKpiModal({ open: true, editing: record })
    if (record) {
      employeeKpiForm.setFieldsValue({
        employee_id: record.employee_id,
        year: record.year,
        month: record.month,
        department_id: record.department_id,
        kpi_percentage:
          record.kpi_percentage !== null && record.kpi_percentage !== undefined
            ? Number(record.kpi_percentage)
            : undefined,
        monthly_bonus_base: Number(record.monthly_bonus_base),
        quarterly_bonus_base: Number(record.quarterly_bonus_base),
        annual_bonus_base: Number(record.annual_bonus_base),
        monthly_bonus_type: record.monthly_bonus_type,
        quarterly_bonus_type: record.quarterly_bonus_type,
        annual_bonus_type: record.annual_bonus_type,
        monthly_bonus_fixed_part:
          record.monthly_bonus_fixed_part !== null && record.monthly_bonus_fixed_part !== undefined
            ? Number(record.monthly_bonus_fixed_part)
            : undefined,
        quarterly_bonus_fixed_part:
          record.quarterly_bonus_fixed_part !== null &&
          record.quarterly_bonus_fixed_part !== undefined
            ? Number(record.quarterly_bonus_fixed_part)
            : undefined,
        annual_bonus_fixed_part:
          record.annual_bonus_fixed_part !== null && record.annual_bonus_fixed_part !== undefined
            ? Number(record.annual_bonus_fixed_part)
            : undefined,
      })
    } else {
      employeeKpiForm.resetFields()
      employeeKpiForm.setFieldsValue({
        year: currentYear,
        month: dayjs().month() + 1,
        department_id: departmentId,
      })
    }
  }

  const handleEmployeeKpiSubmit = async () => {
    const values = await employeeKpiForm.validateFields()
    if (!departmentId) {
      message.error('Отдел не выбран')
      return
    }
    const payload = {
      ...values,
      department_id: departmentId,
    } as EmployeeKPICreate | EmployeeKPIUpdate

    await upsertEmployeeKpiMutation.mutateAsync({
      id: kpiModal.editing?.id,
      payload,
    })

    setKpiModal({ open: false })
    employeeKpiForm.resetFields()
  }

  const handleImportClick = () => {
    setImportModalVisible(true)
  }

  const employeeColumns: ColumnsType<EmployeeKPI> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_id',
      key: 'employee',
      render: (_, record) => {
        const employee = employeeMap.get(record.employee_id)
        return (
          <Space direction="vertical" size={0}>
            <Text strong>{employee?.full_name || `ID ${record.employee_id}`}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {employee?.position || '—'}
            </Text>
          </Space>
        )
      },
    },
    {
      title: 'Период',
      dataIndex: 'month',
      key: 'month',
      width: 140,
      render: (_, record) => `${monthLabel(record.month)} ${record.year}`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      width: 110,
      render: (value, record) => (
        <InputNumber
          min={0}
          max={200}
          value={value !== null && value !== undefined ? Number(value) : undefined}
          addonAfter="%"
          onChange={(val) =>
            upsertEmployeeKpiMutation.mutate({
              id: record.id,
              payload: {
                kpi_percentage: val ?? null,
              },
            })
          }
        />
      ),
    },
    {
      title: 'Бонус расчет',
      dataIndex: 'total_bonus_calculated',
      key: 'total_bonus_calculated',
      width: 140,
      render: (_, record) =>
        formatCurrency(
          Number(record.monthly_bonus_calculated || 0) +
            Number(record.quarterly_bonus_calculated || 0) +
            Number(record.annual_bonus_calculated || 0)
        ),
    },
    {
      title: 'Назначенные цели',
      key: 'goals',
      render: (_, record) =>
        record.goal_achievements && record.goal_achievements.length > 0 ? (
          <Space direction="vertical" size={4}>
            {record.goal_achievements.map((assignment) => (
              <Tag key={assignment.id} color={statusColor[assignment.status as keyof typeof statusColor]}>
                {goalMap.get(assignment.goal_id)?.name || `Цель #${assignment.goal_id}`}
              </Tag>
            ))}
          </Space>
        ) : (
          <Text type="secondary">Цели не назначены</Text>
        ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button type="link" onClick={() => onEditEmployeeKpi(record)}>
          Настроить
        </Button>
      ),
    },
  ]

  return (
    <>
      <Card
        title="Показатели"
        extra={
          <Space>
            <Button
              icon={<UploadOutlined />}
              onClick={handleImportClick}
            >
              Импорт из Excel
            </Button>
            <Button type="primary" onClick={() => onEditEmployeeKpi()}>
              Добавить KPI
            </Button>
          </Space>
        }
      >
        <Table<EmployeeKPI>
          rowKey="id"
          columns={employeeColumns}
          dataSource={employeeKpis}
          loading={employeeKpiQuery.isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Employee KPI Modal */}
      <Modal
        title={kpiModal.editing ? 'Редактировать KPI сотрудника' : 'Добавить KPI сотруднику'}
        open={kpiModal.open}
        onCancel={() => setKpiModal({ open: false })}
        onOk={handleEmployeeKpiSubmit}
        confirmLoading={upsertEmployeeKpiMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={employeeKpiForm} layout="vertical">
          <Form.Item name="employee_id" label="Сотрудник" rules={[{ required: true }]}>
            <Select
              showSearch
              placeholder="Выберите сотрудника"
              optionFilterProp="children"
              filterOption={(input, option) => {
                const children = option?.children as any
                if (typeof children === 'string') {
                  return (children as string).toLowerCase().includes(input.toLowerCase())
                }
                return true
              }}
              disabled={!!kpiModal.editing}
            >
              {employees.map((employee) => (
                <Option key={employee.id} value={employee.id}>
                  {employee.full_name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="year" label="Год" rules={[{ required: true }]}>
            <InputNumber min={2020} max={2100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="month" label="Месяц" rules={[{ required: true, message: 'Выберите месяц' }]}>
            <Select placeholder="Выберите месяц">
              {MONTH_OPTIONS.map((month) => (
                <Option key={month} value={month}>
                  {monthLabel(month)}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="kpi_percentage" label="КПИ %">
            <InputNumber min={0} max={200} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>
          <Divider />
          <Form.Item name="monthly_bonus_base" label="База (месяц)" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="monthly_bonus_type"
            label="Тип бонуса (месяц)"
            initialValue={BONUS_TYPE_OPTIONS[0]}
          >
            <Select>
              {BONUS_TYPE_OPTIONS.map((type) => (
                <Option key={type} value={type}>
                  {bonusTypeLabels[type]}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="monthly_bonus_fixed_part" label="Фиксированная часть (месяц)">
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>
          <Divider />
          <Form.Item name="quarterly_bonus_base" label="База (квартал)" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="quarterly_bonus_type"
            label="Тип бонуса (квартал)"
            initialValue={BONUS_TYPE_OPTIONS[0]}
          >
            <Select>
              {BONUS_TYPE_OPTIONS.map((type) => (
                <Option key={type} value={type}>
                  {bonusTypeLabels[type]}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="quarterly_bonus_fixed_part" label="Фиксированная часть (квартал)">
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>
          <Divider />
          <Form.Item name="annual_bonus_base" label="База (год)" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="annual_bonus_type"
            label="Тип бонуса (год)"
            initialValue={BONUS_TYPE_OPTIONS[0]}
          >
            <Select>
              {BONUS_TYPE_OPTIONS.map((type) => (
                <Option key={type} value={type}>
                  {bonusTypeLabels[type]}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="annual_bonus_fixed_part" label="Фиксированная часть (год)">
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Import KPI Modal */}
      {importModalVisible && (
        <ImportKPIModal
          visible={importModalVisible}
          onClose={() => setImportModalVisible(false)}
        />
      )}
    </>
  )
}
