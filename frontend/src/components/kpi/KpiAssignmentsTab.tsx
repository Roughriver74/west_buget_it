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
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import type {
  EmployeeKPIGoal,
  EmployeeKPIGoalCreate,
  EmployeeKPIGoalUpdate,
  KPIGoal,
  KPIGoalStatus,
} from '@/api/kpi'
import { employeeAPI } from '@/api/payroll'
import type { Employee } from '@/api/payroll'

const { Option } = Select

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)

const statusColor: Record<KPIGoalStatus, string> = {
  DRAFT: 'default',
  ACTIVE: 'processing',
  ACHIEVED: 'success',
  NOT_ACHIEVED: 'error',
  CANCELLED: 'warning',
}

const monthLabel = (month: number | null | undefined) =>
  typeof month === 'number' ? dayjs().month(month - 1).format('MMMM') : 'Годовая'

interface KpiAssignmentsTabProps {
  departmentId?: number
  year?: number
}

export const KpiAssignmentsTab: React.FC<KpiAssignmentsTabProps> = ({ departmentId, year }) => {
  const queryClient = useQueryClient()
  const currentYear = year || dayjs().year()

  const [assignmentModal, setAssignmentModal] = useState<{
    open: boolean
    editing?: EmployeeKPIGoal
  }>({ open: false })

  const [assignmentForm] = Form.useForm<EmployeeKPIGoalCreate | EmployeeKPIGoalUpdate>()

  // Queries
  const assignmentsQuery = useQuery({
    queryKey: ['kpi-assignments', departmentId, currentYear],
    queryFn: () =>
      kpiApi.listAssignments({
        year: currentYear,
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

  const employeeKpiQuery = useQuery({
    queryKey: ['kpi-employee', departmentId, currentYear],
    queryFn: () =>
      kpiApi.listEmployeeKpis({
        department_id: departmentId,
        year: currentYear,
      }),
    enabled: !!departmentId,
  })

  // Mutations
  const upsertAssignmentMutation = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id?: number
      payload: EmployeeKPIGoalCreate | EmployeeKPIGoalUpdate
    }) => {
      if (id) {
        return kpiApi.updateAssignment(id, payload as EmployeeKPIGoalUpdate)
      }
      return kpiApi.createAssignment(payload as EmployeeKPIGoalCreate)
    },
    onSuccess: () => {
      message.success('Назначение KPI обновлено')
      queryClient.invalidateQueries({ queryKey: ['kpi-assignments'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-summary'] })
    },
  })

  const deleteAssignmentMutation = useMutation({
    mutationFn: (id: number) => kpiApi.deleteAssignment(id),
    onSuccess: () => {
      message.success('Назначение KPI удалено')
      queryClient.invalidateQueries({ queryKey: ['kpi-assignments'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-summary'] })
    },
  })

  const assignments = assignmentsQuery.data || []
  const goals = goalsQuery.data || []
  const employees = employeesQuery.data || []
  const employeeKpis = employeeKpiQuery.data || []

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

  const filteredAssignments = useMemo(() => {
    if (!employees.length) {
      return assignments
    }
    const allowedEmployees = new Set(employees.map((employee) => employee.id))
    return assignments.filter((assignment) => allowedEmployees.has(assignment.employee_id))
  }, [assignments, employees])

  const onEditAssignment = (assignment?: EmployeeKPIGoal) => {
    setAssignmentModal({ open: true, editing: assignment })
    assignmentForm.resetFields()
    if (assignment) {
      assignmentForm.setFieldsValue({
        employee_id: assignment.employee_id,
        goal_id: assignment.goal_id,
        employee_kpi_id: assignment.employee_kpi_id || undefined,
        year: assignment.year,
        month: assignment.month ?? undefined,
        target_value:
          assignment.target_value !== null && assignment.target_value !== undefined
            ? Number(assignment.target_value)
            : undefined,
        actual_value:
          assignment.actual_value !== null && assignment.actual_value !== undefined
            ? Number(assignment.actual_value)
            : undefined,
        achievement_percentage:
          assignment.achievement_percentage !== null &&
          assignment.achievement_percentage !== undefined
            ? Number(assignment.achievement_percentage)
            : undefined,
        status: assignment.status,
      })
    } else {
      assignmentForm.setFieldsValue({
        year: currentYear,
        status: 'ACTIVE',
      })
    }
  }

  const handleAssignmentSubmit = async () => {
    const values = await assignmentForm.validateFields()
    const payload = {
      ...values,
      target_value: values.target_value ?? null,
      actual_value: values.actual_value ?? null,
      achievement_percentage: values.achievement_percentage ?? null,
      month: values.month ?? null,
    } as EmployeeKPIGoalCreate | EmployeeKPIGoalUpdate

    await upsertAssignmentMutation.mutateAsync({
      id: assignmentModal.editing?.id,
      payload,
    })

    setAssignmentModal({ open: false })
    assignmentForm.resetFields()
  }

  const assignmentColumns: ColumnsType<EmployeeKPIGoal> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_id',
      key: 'employee',
      render: (_, record) =>
        employeeMap.get(record.employee_id)?.full_name || `ID ${record.employee_id}`,
    },
    {
      title: 'Цель',
      dataIndex: 'goal_id',
      key: 'goal',
      render: (_, record) =>
        record.goal?.name || goalMap.get(record.goal_id)?.name || `Цель #${record.goal_id}`,
    },
    {
      title: 'Период',
      dataIndex: 'month',
      key: 'month',
      render: (value, record) => `${monthLabel(value)} ${record.year}`,
    },
    {
      title: 'Прогресс',
      dataIndex: 'achievement_percentage',
      key: 'achievement',
      render: (value) =>
        value !== null && value !== undefined ? `${Number(value).toFixed(1)} %` : '—',
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (value: KPIGoalStatus) => <Tag color={statusColor[value]}>{value}</Tag>,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => onEditAssignment(record)}>
            Редактировать
          </Button>
          <Button
            danger
            size="small"
            onClick={() =>
              Modal.confirm({
                title: 'Удалить назначение цели?',
                onOk: () => deleteAssignmentMutation.mutate(record.id),
              })
            }
          >
            Удалить
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="Назначения KPI целей сотрудникам"
        extra={
          <Button type="primary" onClick={() => onEditAssignment()}>
            Назначить цель
          </Button>
        }
      >
        <Table<EmployeeKPIGoal>
          rowKey="id"
          columns={assignmentColumns}
          dataSource={filteredAssignments}
          loading={assignmentsQuery.isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Assignment Modal */}
      <Modal
        title={assignmentModal.editing ? 'Редактировать назначение цели' : 'Назначить цель'}
        open={assignmentModal.open}
        onCancel={() => setAssignmentModal({ open: false })}
        onOk={handleAssignmentSubmit}
        confirmLoading={upsertAssignmentMutation.isPending}
        destroyOnClose
        width={600}
      >
        <Form form={assignmentForm} layout="vertical">
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
              disabled={!!assignmentModal.editing}
            >
              {employees.map((employee) => (
                <Option key={employee.id} value={employee.id}>
                  {employee.full_name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="goal_id" label="Цель" rules={[{ required: true }]}>
            <Select
              placeholder="Выберите цель"
              optionFilterProp="children"
              showSearch
              filterOption={(input, option) => {
                const children = option?.children as any
                if (typeof children === 'string') {
                  return (children as string).toLowerCase().includes(input.toLowerCase())
                }
                return true
              }}
            >
              {goals.map((goal) => (
                <Option key={goal.id} value={goal.id}>
                  {goal.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="employee_kpi_id" label="Запись KPI сотрудника">
            <Select allowClear placeholder="Без привязки">
              {employeeKpis.map((kpi) => {
                const employeeName =
                  employeeMap.get(kpi.employee_id)?.full_name || `ID ${kpi.employee_id}`
                const goalNames =
                  kpi.goal_achievements?.map(
                    (assignment) =>
                      goalMap.get(assignment.goal_id)?.name || `Цель #${assignment.goal_id}`
                  ) ?? []
                const label = [
                  employeeName,
                  `${monthLabel(kpi.month)} ${kpi.year}`,
                  goalNames.length ? goalNames.join(', ') : null,
                ]
                  .filter(Boolean)
                  .join(' • ')
                return (
                  <Option key={kpi.id} value={kpi.id}>
                    {label}
                  </Option>
                )
              })}
            </Select>
          </Form.Item>

          <Form.Item name="year" label="Год" rules={[{ required: true }]}>
            <InputNumber min={2020} max={2100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="month" label="Месяц">
            <Select allowClear placeholder="Годовое назначение">
              {MONTH_OPTIONS.map((month) => (
                <Option key={month} value={month}>
                  {monthLabel(month)}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="target_value" label="Цель" tooltip="Числовое значение цели">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="actual_value" label="Факт">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="achievement_percentage" label="% выполнения">
            <InputNumber min={0} max={200} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>

          <Form.Item name="status" label="Статус">
            <Select>
              {(Object.keys(statusColor) as KPIGoalStatus[]).map((status) => (
                <Option key={status} value={status}>
                  {status}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="notes" label="Комментарии">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
