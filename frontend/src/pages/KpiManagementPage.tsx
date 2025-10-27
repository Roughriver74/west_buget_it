import { useMemo, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  Tabs,
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
  DatePicker,
  message,
  Divider,
  Calendar,
  Tooltip,
  Typography,
  Radio,
  Drawer,
  Descriptions,
  Empty,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { kpiApi } from '@/api/kpi'
import type {
  KPIGoal,
  KPIGoalStatus,
  KPIGoalCreate,
  KPIGoalUpdate,
  EmployeeKPI,
  EmployeeKPICreate,
  EmployeeKPIUpdate,
  EmployeeKPIGoal,
  EmployeeKPIGoalCreate,
  EmployeeKPIGoalUpdate,
  KPIEmployeeSummary,
  BonusType,
} from '@/api/kpi'
import { employeeAPI } from '@/api/payroll'
import type { Employee } from '@/api/payroll'
import type { Dayjs } from 'dayjs'
import { formatCurrency } from '@/utils/formatters'
import { UploadOutlined } from '@ant-design/icons'

const { Option } = Select
const { Title, Text } = Typography

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => i + 1)

const statusColor: Record<KPIGoalStatus, string> = {
  DRAFT: 'default',
  ACTIVE: 'processing',
  ACHIEVED: 'success',
  NOT_ACHIEVED: 'error',
  CANCELLED: 'warning',
}

const BONUS_TYPE_OPTIONS: BonusType[] = ['PERFORMANCE_BASED', 'FIXED', 'MIXED']
const bonusTypeLabels: Record<BonusType, string> = {
  PERFORMANCE_BASED: 'Performance',
  FIXED: 'Fixed',
  MIXED: 'Mixed',
}

const employeeStatusColor: Record<Employee['status'], string> = {
  ACTIVE: 'green',
  ON_VACATION: 'gold',
  ON_LEAVE: 'orange',
  FIRED: 'red',
}
const monthLabel = (month: number | null | undefined) =>
  typeof month === 'number' ? dayjs().month(month - 1).format('MMMM') : 'Годовая цель'

const KPIManagementPage = () => {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const [goalFilters, setGoalFilters] = useState<{ year: number; status?: KPIGoalStatus }>(() => ({
    year: dayjs().year(),
  }))
  const [summaryFilters, setSummaryFilters] = useState<{ year: number; month?: number }>({
    year: dayjs().year(),
  })
  const [activeTab, setActiveTab] = useState('summary')

  const departmentId = selectedDepartment?.id ?? user?.department_id ?? undefined

  const goalsQuery = useQuery({
    queryKey: ['kpi-goals', goalFilters, departmentId],
    queryFn: () =>
      kpiApi.listGoals({
        year: goalFilters.year,
        status: goalFilters.status,
        department_id: departmentId,
      }),
    enabled: !!departmentId,
  })

  const employeeKpiQuery = useQuery({
    queryKey: ['kpi-employee', departmentId, goalFilters.year],
    queryFn: () =>
      kpiApi.listEmployeeKpis({
        department_id: departmentId,
        year: goalFilters.year,
      }),
    enabled: !!departmentId,
  })

  const assignmentsQuery = useQuery({
    queryKey: ['kpi-assignments', departmentId, goalFilters.year],
    queryFn: () =>
      kpiApi.listAssignments({
        year: goalFilters.year,
      }),
    enabled: !!departmentId,
  })

  const summaryQuery = useQuery({
    queryKey: ['kpi-summary', summaryFilters, departmentId],
    queryFn: () =>
      kpiApi.getEmployeeSummary({
        year: summaryFilters.year,
        month: summaryFilters.month,
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

  const createGoalMutation = useMutation({
    mutationFn: (payload: KPIGoalCreate) => kpiApi.createGoal(payload),
    onSuccess: () => {
      message.success('Цель KPI создана')
      queryClient.invalidateQueries({ queryKey: ['kpi-goals'] })
    },
  })

  const updateGoalMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: KPIGoalUpdate }) =>
      kpiApi.updateGoal(id, payload),
    onSuccess: () => {
      message.success('Цель KPI обновлена')
      queryClient.invalidateQueries({ queryKey: ['kpi-goals'] })
    },
  })

  const deleteGoalMutation = useMutation({
    mutationFn: (id: number) => kpiApi.deleteGoal(id),
    onSuccess: () => {
      message.success('Цель KPI удалена')
      queryClient.invalidateQueries({ queryKey: ['kpi-goals'] })
    },
  })

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

  const importKpiMutation = useMutation({
    mutationFn: (file: File) => kpiApi.importEmployeeKpis(file),
    onSuccess: (result) => {
      message.success(
        `Импорт завершен за ${result.year} год: создано ${result.created}, обновлено ${result.updated}`
      )
      if (result.missing_employees?.length) {
        message.warning(
          `Не найдены сотрудники в системе: ${result.missing_employees.join(', ')}`
        )
      }
      if (result.missing_sheets?.length) {
        message.warning(
          `Листы с данными не найдены в файле для: ${result.missing_sheets.join(', ')}`
        )
      }
      if (result.no_access?.length) {
        message.warning(
          `Пропущены сотрудники без доступа: ${result.no_access.join(', ')}`
        )
      }
      queryClient.invalidateQueries({ queryKey: ['kpi-employee'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-summary'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-assignments'] })
    },
    onError: (error: any) => {
      const detail =
        error?.response?.data?.detail ||
        error?.message ||
        'Не удалось импортировать KPI данные'
      message.error(`Ошибка импорта: ${detail}`)
    },
  })

  const [goalModal, setGoalModal] = useState<{ open: boolean; editing?: KPIGoal }>({
    open: false,
  })

  const [kpiModal, setKpiModal] = useState<{ open: boolean; editing?: EmployeeKPI }>({
    open: false,
  })

  const [assignmentModal, setAssignmentModal] = useState<{
    open: boolean
    editing?: EmployeeKPIGoal
  }>({ open: false })

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [detailEmployeeId, setDetailEmployeeId] = useState<number | null>(null)

  const goalForm = Form.useForm<KPIGoalCreate | KPIGoalUpdate>()[0]
  const employeeKpiForm = Form.useForm<EmployeeKPICreate | EmployeeKPIUpdate>()[0]
  const assignmentForm = Form.useForm<EmployeeKPIGoalCreate | EmployeeKPIGoalUpdate>()[0]

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleImportFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      importKpiMutation.mutate(file)
    }
    event.target.value = ''
  }

  const employees = employeesQuery.data || []
  const goals = goalsQuery.data || []
  const employeeKpis = employeeKpiQuery.data || []
  const assignments = assignmentsQuery.data || []
  const summary = summaryQuery.data || []

  const goalMap = useMemo(() => {
    const map = new Map<number, KPIGoal>()
    goals.forEach((goal) => {
      map.set(goal.id, goal)
    })
    return map
  }, [goals])

  const employeeMap = useMemo(() => {
    const map = new Map<number, Employee>()
    employees.forEach((employee) => {
      map.set(employee.id, employee)
    })
    return map
  }, [employees])

  const filteredAssignments = useMemo(() => {
    if (!employees.length) {
      return assignments
    }
    const allowedEmployees = new Set(employees.map((employee) => employee.id))
    return assignments.filter((assignment) => allowedEmployees.has(assignment.employee_id))
  }, [assignments, employees])

  const detailEmployee = detailEmployeeId !== null ? employeeMap.get(detailEmployeeId) : undefined

  const detailEmployeeKpis = useMemo(() => {
    if (detailEmployeeId === null) {
      return []
    }

    return employeeKpis
      .filter((item) => item.employee_id === detailEmployeeId)
      .sort((a, b) => {
        const aKey = a.year * 100 + (a.month ?? 0)
        const bKey = b.year * 100 + (b.month ?? 0)
        return aKey - bKey
      })
  }, [detailEmployeeId, employeeKpis])

  const detailEmployeeAssignments = useMemo(() => {
    if (detailEmployeeId === null) {
      return []
    }
    return assignments
      .filter((item) => item.employee_id === detailEmployeeId)
      .sort((a, b) => {
        const aKey = a.year * 100 + (a.month ?? 0)
        const bKey = b.year * 100 + (b.month ?? 0)
        return aKey - bKey
      })
  }, [assignments, detailEmployeeId])

  const detailSummaryEntries = useMemo(() => {
    if (detailEmployeeId === null) {
      return []
    }
    return summary.filter((item) => item.employee_id === detailEmployeeId)
  }, [detailEmployeeId, summary])

  const detailStats = useMemo(() => {
    if (detailEmployeeId === null) {
      return null
    }
    if (!detailEmployeeKpis.length) {
      return {
        totalRecords: 0,
        avgKpi: null as number | null,
        totalBonus: 0,
        goalsAchieved: 0,
        goalsCount: 0,
        lastPeriod: null as string | null,
      }
    }

    const totalBonus = detailEmployeeKpis.reduce((acc, item) => {
      return (
        acc +
        Number(item.monthly_bonus_calculated || 0) +
        Number(item.quarterly_bonus_calculated || 0) +
        Number(item.annual_bonus_calculated || 0)
      )
    }, 0)

    const kpiSum = detailEmployeeKpis.reduce(
      (acc, item) => acc + Number(item.kpi_percentage || 0),
      0
    )

    const goalsAchieved = detailSummaryEntries.reduce(
      (acc, item) => acc + Number(item.goals_achieved || 0),
      0
    )
    const goalsCount = detailSummaryEntries.reduce(
      (acc, item) => acc + Number(item.goals_count || 0),
      0
    )

    const latest = detailEmployeeKpis[detailEmployeeKpis.length - 1]

    return {
      totalRecords: detailEmployeeKpis.length,
      avgKpi: detailEmployeeKpis.length ? kpiSum / detailEmployeeKpis.length : null,
      totalBonus,
      goalsAchieved,
      goalsCount,
      lastPeriod: latest ? `${monthLabel(latest.month)} ${latest.year}` : null,
    }
  }, [detailEmployeeId, detailEmployeeKpis, detailSummaryEntries])

  const onEditGoal = (goal: KPIGoal) => {
    setGoalModal({ open: true, editing: goal })
    goalForm.setFieldsValue({
      name: goal.name,
      description: goal.description ?? undefined,
      category: goal.category ?? undefined,
      metric_name: goal.metric_name ?? undefined,
      metric_unit: goal.metric_unit ?? undefined,
      target_value:
        goal.target_value !== null && goal.target_value !== undefined
          ? Number(goal.target_value)
          : undefined,
      weight:
        goal.weight !== null && goal.weight !== undefined ? Number(goal.weight) : undefined,
      year: goal.year,
      is_annual: goal.is_annual,
      status: goal.status,
      department_id: goal.department_id,
    })
  }

  const onCreateGoal = () => {
    setGoalModal({ open: true })
    goalForm.resetFields()
    goalForm.setFieldsValue({
      year: goalFilters.year,
      department_id: departmentId,
      is_annual: true,
      weight: 100,
      status: 'ACTIVE',
    })
  }

  const handleGoalSubmit = async () => {
    const values = await goalForm.validateFields()
    if (!departmentId) {
      message.error('Отдел не выбран')
      return
    }

    const payload = {
      ...values,
      target_value: values.target_value ?? null,
      weight: values.weight ?? 100,
      department_id: departmentId,
      is_annual: Boolean(values.is_annual),
    } as KPIGoalCreate

    if (goalModal.editing) {
      await updateGoalMutation.mutateAsync({
        id: goalModal.editing.id,
        payload,
      })
    } else {
      await createGoalMutation.mutateAsync(payload)
    }

    setGoalModal({ open: false })
    goalForm.resetFields()
  }

  const goalColumns: ColumnsType<KPIGoal> = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          {record.description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      key: 'category',
      width: 140,
      render: (value) => value || '—',
    },
    {
      title: 'Метрика',
      dataIndex: 'metric_name',
      key: 'metric_name',
      width: 160,
      render: (_, record) =>
        record.metric_name ? `${record.metric_name} (${record.metric_unit || ''})` : '—',
    },
    {
      title: 'Цель',
      dataIndex: 'target_value',
      key: 'target_value',
      width: 120,
      render: (value) =>
        value !== null && value !== undefined
          ? Number(value).toLocaleString('ru-RU')
          : '—',
    },
    {
      title: 'Вес',
      dataIndex: 'weight',
      key: 'weight',
      width: 80,
      render: (value) =>
        value !== null && value !== undefined ? `${Number(value)} %` : '—',
    },
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 80,
    },
    {
      title: 'Тип',
      dataIndex: 'is_annual',
      key: 'is_annual',
      width: 120,
      render: (value) => (value ? 'Годовая' : 'Месячная'),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (value: KPIGoalStatus) => <Tag color={statusColor[value]}>{value}</Tag>,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => onEditGoal(record)}>
            Редактировать
          </Button>
          <Button
            danger
            size="small"
            onClick={async () => {
              Modal.confirm({
                title: 'Удалить KPI цель?',
                onOk: () => deleteGoalMutation.mutate(record.id),
              })
            }}
          >
            Удалить
          </Button>
        </Space>
      ),
    },
  ]

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
        year: goalFilters.year,
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

  const employeeColumns: ColumnsType<EmployeeKPI> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_id',
      key: 'employee',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.employee?.full_name}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.employee?.position || '—'}
          </Text>
        </Space>
      ),
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
        record.goal_achievements?.length ? (
          <Space direction="vertical" size={4}>
            {record.goal_achievements.map((assignment) => (
              <Tag key={assignment.id} color={statusColor[assignment.status]}>
                {assignment.goal?.name ||
                  goalMap.get(assignment.goal_id)?.name ||
                  `Цель #${assignment.goal_id}`}
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
      width: 140,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" onClick={() => setDetailEmployeeId(record.employee_id)}>
            Детали
          </Button>
          <Button type="link" onClick={() => onEditEmployeeKpi(record)}>
            Настроить
          </Button>
        </Space>
      ),
    },
  ]

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
        year: goalFilters.year,
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

  const summaryColumns: ColumnsType<KPIEmployeeSummary> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.position || '—'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Период',
      dataIndex: 'month',
      key: 'period',
      width: 120,
      render: (_, record) =>
        record.month ? `${monthLabel(record.month)} ${record.year}` : `${record.year}`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      width: 100,
      render: (value) =>
        value !== null && value !== undefined ? `${Number(value).toFixed(1)} %` : '—',
    },
    {
      title: 'Бонус (всего)',
      dataIndex: 'total_bonus_calculated',
      key: 'total_bonus_calculated',
      width: 140,
      render: (value) => formatCurrency(Number(value || 0)),
    },
    {
      title: 'Целей выполнено',
      dataIndex: 'goals_achieved',
      key: 'goals_achieved',
      width: 160,
      render: (_, record) => `${record.goals_achieved}/${record.goals_count}`,
    },
  ]

  const detailKpiColumns: ColumnsType<EmployeeKPI> = [
    {
      title: 'Период',
      dataIndex: 'month',
      key: 'period',
      render: (value, record) => `${monthLabel(value)} ${record.year}`,
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      render: (value) =>
        value !== null && value !== undefined ? `${Number(value).toFixed(1)} %` : '—',
    },
    {
      title: 'Рассчитанные бонусы',
      key: 'calculated',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>Месяц: {formatCurrency(Number(record.monthly_bonus_calculated || 0))}</Text>
          <Text>Квартал: {formatCurrency(Number(record.quarterly_bonus_calculated || 0))}</Text>
          <Text>Год: {formatCurrency(Number(record.annual_bonus_calculated || 0))}</Text>
        </Space>
      ),
    },
    {
      title: 'Базы',
      key: 'bases',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>Месяц: {formatCurrency(Number(record.monthly_bonus_base || 0))}</Text>
          <Text>Квартал: {formatCurrency(Number(record.quarterly_bonus_base || 0))}</Text>
          <Text>Год: {formatCurrency(Number(record.annual_bonus_base || 0))}</Text>
        </Space>
      ),
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      render: (value) => value || '—',
    },
  ]

  const detailAssignmentColumns: ColumnsType<EmployeeKPIGoal> = [
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
      key: 'period',
      render: (value, record) => `${monthLabel(value)} ${record.year}`,
    },
    {
      title: 'Цель / Факт',
      key: 'values',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>Цель: {record.target_value !== null && record.target_value !== undefined ? Number(record.target_value).toLocaleString('ru-RU') : '—'}</Text>
          <Text>Факт: {record.actual_value !== null && record.actual_value !== undefined ? Number(record.actual_value).toLocaleString('ru-RU') : '—'}</Text>
        </Space>
      ),
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
  ]

  const calendarData = useMemo(() => {
    const map = new Map<string, { total: number; employees: Set<number> }>()
    employeeKpis.forEach((item) => {
      const key = `${item.year}-${String(item.month || 1).padStart(2, '0')}-01`
      const current = map.get(key) || { total: 0, employees: new Set() }
      const total =
        Number(item.monthly_bonus_calculated || 0) +
        Number(item.quarterly_bonus_calculated || 0) +
        Number(item.annual_bonus_calculated || 0)
      current.total += total
      current.employees.add(item.employee_id)
      map.set(key, current)
    })
    return map
  }, [employeeKpis])

  const monthCellRender = (value: Dayjs) => {
    const key = value.startOf('month').format('YYYY-MM-DD')
    const data = calendarData.get(key)
    if (!data) {
      return null
    }
    return (
      <div style={{ padding: 4 }}>
        <Tooltip title={`Сотрудников: ${data.employees.size}`}>
          <Tag color="purple">Бонусы: {formatCurrency(data.total)}</Tag>
        </Tooltip>
      </div>
    )
  }

  return (
    <div>
      <input
        type="file"
        accept=".xlsx,.xls"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleImportFileChange}
      />
      <Title level={2} style={{ marginBottom: 24 }}>
        KPI сотрудников
      </Title>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane tab="Сводка" key="summary">
          <Card
            title="Сводка по сотрудникам"
            extra={
              <Space>
                <Select
                  value={summaryFilters.year}
                  onChange={(value) => setSummaryFilters((prev) => ({ ...prev, year: value }))}
                  style={{ width: 120 }}
                >
                  {Array.from({ length: 5 }, (_, i) => dayjs().year() - 2 + i).map((year) => (
                    <Option key={year} value={year}>
                      {year}
                    </Option>
                  ))}
                </Select>
                <Select
                  allowClear
                  placeholder="Месяц"
                  value={summaryFilters.month}
                  onChange={(value) => setSummaryFilters((prev) => ({ ...prev, month: value }))}
                  style={{ width: 140 }}
                >
                  {MONTH_OPTIONS.map((month) => (
                    <Option key={month} value={month}>
                      {monthLabel(month)}
                    </Option>
                  ))}
                </Select>
              </Space>
            }
          >
            <Table<KPIEmployeeSummary>
              rowKey={(record) => `${record.employee_id}-${record.year}-${record.month ?? 'all'}`}
              columns={summaryColumns}
              dataSource={summary}
              loading={summaryQuery.isLoading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane tab="Цели KPI" key="goals">
          <Card
            title="Цели"
            extra={
              <Space>
                <Select
                  value={goalFilters.year}
                  onChange={(value) => setGoalFilters((prev) => ({ ...prev, year: value }))}
                  style={{ width: 120 }}
                >
                  {Array.from({ length: 5 }, (_, i) => dayjs().year() - 2 + i).map((year) => (
                    <Option key={year} value={year}>
                      {year}
                    </Option>
                  ))}
                </Select>
                <Select<KPIGoalStatus | undefined>
                  allowClear
                  placeholder="Статус"
                  style={{ width: 180 }}
                  value={goalFilters.status}
                  onChange={(value) => setGoalFilters((prev) => ({ ...prev, status: value }))}
                >
                  {Object.keys(statusColor).map((status) => (
                    <Option key={status} value={status as KPIGoalStatus}>
                      {status}
                    </Option>
                  ))}
                </Select>
                <Button type="primary" onClick={onCreateGoal}>
                  Добавить цель
                </Button>
              </Space>
            }
          >
            <Table<KPIGoal>
              rowKey="id"
              columns={goalColumns}
              dataSource={goals}
              loading={goalsQuery.isLoading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane tab="Показатели сотрудников" key="employee-kpi">
          <Card
            title="Показатели"
            extra={
              <Space>
                <Button
                  icon={<UploadOutlined />}
                  onClick={handleImportClick}
                  loading={importKpiMutation.isPending}
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
        </Tabs.TabPane>

        <Tabs.TabPane tab="Назначения целей" key="assignments">
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
        </Tabs.TabPane>

        <Tabs.TabPane tab="Календарь бонусов" key="calendar">
          <Card>
            <Calendar
              fullscreen={false}
              mode="year"
              value={dayjs(`${goalFilters.year}-01-01`)}
              headerRender={({ value, onChange }) => (
                <Space>
                  <DatePicker
                    picker="year"
                    value={value}
                    onChange={(val) => {
                      if (val) {
                        onChange(val.startOf('year'))
                      }
                    }}
                  />
                  <Text type="secondary">
                    Отображается сумма рассчитанных бонусов по KPI в разрезе месяцев.
                  </Text>
                </Space>
              )}
              monthCellRender={monthCellRender}
            />
          </Card>
        </Tabs.TabPane>
      </Tabs>

      {/* Goal Modal */}
      <Modal
        title={goalModal.editing ? 'Редактировать цель KPI' : 'Создать цель KPI'}
        open={goalModal.open}
        onCancel={() => setGoalModal({ open: false })}
        onOk={handleGoalSubmit}
        okText={goalModal.editing ? 'Обновить' : 'Создать'}
        confirmLoading={createGoalMutation.isPending || updateGoalMutation.isPending}
        destroyOnClose
      >
        <Form form={goalForm} layout="vertical">
          <Form.Item name="name" label="Название" rules={[{ required: true, message: 'Введите название' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="category" label="Категория">
            <Input placeholder="Например, Продажи, Проекты" />
          </Form.Item>
          <Form.Item name="metric_name" label="Метрика">
            <Input placeholder="Например, Количество релизов" />
          </Form.Item>
          <Form.Item name="metric_unit" label="Единица измерения">
            <Input placeholder="Например, шт., %" />
          </Form.Item>
          <Form.Item name="target_value" label="Целевое значение">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="weight" label="Вес цели">
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>
          <Form.Item name="year" label="Год" rules={[{ required: true }]}>
            <InputNumber min={2020} max={2100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="is_annual"
            label="Тип цели"
            rules={[{ required: true, message: 'Выберите тип цели' }]}
          >
            <Radio.Group style={{ width: '100%' }}>
              <Radio.Button value={true}>Годовая</Radio.Button>
              <Radio.Button value={false}>Месячная</Radio.Button>
            </Radio.Group>
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
        </Form>
      </Modal>

      {/* Employee KPI Modal */}
      <Modal
        title={kpiModal.editing ? 'Редактировать KPI сотрудника' : 'Добавить KPI сотруднику'}
        open={kpiModal.open}
        onCancel={() => setKpiModal({ open: false })}
        onOk={handleEmployeeKpiSubmit}
        confirmLoading={upsertEmployeeKpiMutation.isPending}
        destroyOnClose
      >
        <Form form={employeeKpiForm} layout="vertical">
          <Form.Item name="employee_id" label="Сотрудник" rules={[{ required: true }]}>
            <Select
              showSearch
              placeholder="Выберите сотрудника"
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.children as string).toLowerCase().includes(input.toLowerCase())
              }
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

      {/* Assignment Modal */}
      <Modal
        title={assignmentModal.editing ? 'Редактировать назначение цели' : 'Назначить цель'}
        open={assignmentModal.open}
        onCancel={() => setAssignmentModal({ open: false })}
        onOk={handleAssignmentSubmit}
        confirmLoading={upsertAssignmentMutation.isPending}
        destroyOnClose
      >
        <Form form={assignmentForm} layout="vertical">
          <Form.Item name="employee_id" label="Сотрудник" rules={[{ required: true }]}>
            <Select
              showSearch
              placeholder="Выберите сотрудника"
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.children as string).toLowerCase().includes(input.toLowerCase())
              }
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
              filterOption={(input, option) =>
                (option?.children as string).toLowerCase().includes(input.toLowerCase())
              }
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
                      assignment.goal?.name ||
                      goalMap.get(assignment.goal_id)?.name ||
                      `Цель #${assignment.goal_id}`
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

      <Drawer
        title={
          detailEmployee
            ? `KPI сотрудника — ${detailEmployee.full_name}`
            : 'KPI сотрудника'
        }
        width={780}
        open={detailEmployeeId !== null}
        onClose={() => setDetailEmployeeId(null)}
        destroyOnClose
      >
        {detailEmployee ? (
          <Space direction="vertical" size={24} style={{ width: '100%' }}>
            <Descriptions
              bordered
              size="small"
              column={2}
              labelStyle={{ width: '35%' }}
            >
              <Descriptions.Item label="ФИО">
                <Space>
                  <Text strong>{detailEmployee.full_name}</Text>
                  <Tag color={employeeStatusColor[detailEmployee.status]}>
                    {detailEmployee.status}
                  </Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Должность">
                {detailEmployee.position || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Email">
                {detailEmployee.email || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Телефон">
                {detailEmployee.phone || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="ID сотрудника">
                {detailEmployee.id}
              </Descriptions.Item>
              <Descriptions.Item label="ID отдела">
                {detailEmployee.department_id}
              </Descriptions.Item>
              <Descriptions.Item label="Базовый оклад">
                {formatCurrency(Number(detailEmployee.base_salary || 0))}
              </Descriptions.Item>
              <Descriptions.Item label="Премии (мес/кв/год)">
                <Space size="small">
                  <Tag>
                    М: {formatCurrency(Number(detailEmployee.monthly_bonus_base || 0))}
                  </Tag>
                  <Tag>
                    К: {formatCurrency(Number(detailEmployee.quarterly_bonus_base || 0))}
                  </Tag>
                  <Tag>
                    Г: {formatCurrency(Number(detailEmployee.annual_bonus_base || 0))}
                  </Tag>
                </Space>
              </Descriptions.Item>
            </Descriptions>

            <Card title="Сводка KPI" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Записей">
                  {detailStats?.totalRecords ?? 0}
                </Descriptions.Item>
                <Descriptions.Item label="Последний период">
                  {detailStats?.lastPeriod || '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Средний КПИ %">
                  {detailStats?.avgKpi !== null && detailStats?.avgKpi !== undefined
                    ? `${detailStats.avgKpi.toFixed(1)} %`
                    : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Всего бонусов">
                  {formatCurrency(detailStats?.totalBonus ?? 0)}
                </Descriptions.Item>
                <Descriptions.Item label="Целей выполнено">
                  {detailStats
                    ? `${detailStats.goalsAchieved}/${detailStats.goalsCount}`
                    : '—'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="Помесячные показатели" size="small">
              <Table<EmployeeKPI>
                rowKey="id"
                columns={detailKpiColumns}
                dataSource={detailEmployeeKpis}
                pagination={false}
                size="small"
                locale={{
                  emptyText: 'Нет записей KPI для сотрудника',
                }}
              />
            </Card>

            <Card title="Назначенные цели" size="small">
              <Table<EmployeeKPIGoal>
                rowKey="id"
                columns={detailAssignmentColumns}
                dataSource={detailEmployeeAssignments}
                pagination={false}
                size="small"
                locale={{
                  emptyText: 'Цели не назначены',
                }}
              />
            </Card>
          </Space>
        ) : (
          <Empty description="Данные о сотруднике недоступны" />
        )}
      </Drawer>
    </div>
  )
}

export default KPIManagementPage
