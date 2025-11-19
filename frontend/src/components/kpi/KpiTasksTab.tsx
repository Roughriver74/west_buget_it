/**
 * KPI Tasks Tab Component
 *
 * Управление задачами KPI для декомпозиции целей.
 */

import React, { useState, useMemo } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Progress,
  Tooltip,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Card,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
  FlagOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

import * as kpiTasksApi from '@/api/kpiTasks'
import type {
  KPITaskResponse,
  KPITaskCreate,
  KPITaskUpdate,
  KPITaskStatus,
  KPITaskPriority,
} from '@/types/kpiTask'
import {
  TASK_STATUS_CONFIG,
  TASK_PRIORITY_CONFIG,
  COMPLEXITY_LABELS,
} from '@/types/kpiTask'

const { TextArea } = Input
const { Option } = Select

interface KpiTasksTabProps {
  employeeKpiGoalId: number
  employeeId: number
  _goalName?: string // Reserved for future use
}

const KpiTasksTab: React.FC<KpiTasksTabProps> = ({
  employeeKpiGoalId,
  employeeId,
}) => {
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [editingTask, setEditingTask] = useState<KPITaskResponse | null>(null)
  const [statusFilter, setStatusFilter] = useState<KPITaskStatus | 'ALL'>('ALL')
  const [priorityFilter, setPriorityFilter] = useState<KPITaskPriority | 'ALL'>('ALL')

  const [taskForm] = Form.useForm()
  const queryClient = useQueryClient()

  // Fetch tasks for this goal
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['kpi-tasks', employeeKpiGoalId],
    queryFn: () =>
      kpiTasksApi.getKPITasks({
        employee_kpi_goal_id: employeeKpiGoalId,
      }),
  })

  // Fetch statistics
  const { data: statistics } = useQuery({
    queryKey: ['kpi-task-statistics', employeeId],
    queryFn: () => kpiTasksApi.getKPITaskStatistics(employeeId),
  })

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: kpiTasksApi.createKPITask,
    onSuccess: () => {
      message.success('Задача создана успешно')
      queryClient.invalidateQueries({ queryKey: ['kpi-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-task-statistics'] })
      setTaskModalVisible(false)
      taskForm.resetFields()
    },
    onError: () => {
      message.error('Ошибка при создании задачи')
    },
  })

  // Update task mutation
  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: KPITaskUpdate }) =>
      kpiTasksApi.updateKPITask(taskId, data),
    onSuccess: () => {
      message.success('Задача обновлена успешно')
      queryClient.invalidateQueries({ queryKey: ['kpi-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-task-statistics'] })
      setTaskModalVisible(false)
      setEditingTask(null)
      taskForm.resetFields()
    },
    onError: () => {
      message.error('Ошибка при обновлении задачи')
    },
  })

  // Delete task mutation
  const deleteTaskMutation = useMutation({
    mutationFn: kpiTasksApi.deleteKPITask,
    onSuccess: () => {
      message.success('Задача удалена')
      queryClient.invalidateQueries({ queryKey: ['kpi-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-task-statistics'] })
    },
    onError: () => {
      message.error('Ошибка при удалении задачи')
    },
  })

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: number; status: KPITaskStatus }) =>
      kpiTasksApi.updateKPITaskStatus(taskId, { status }),
    onSuccess: () => {
      message.success('Статус обновлен')
      queryClient.invalidateQueries({ queryKey: ['kpi-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['kpi-task-statistics'] })
    },
    onError: () => {
      message.error('Ошибка при обновлении статуса')
    },
  })

  // Filtered tasks
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const statusMatch = statusFilter === 'ALL' || task.status === statusFilter
      const priorityMatch = priorityFilter === 'ALL' || task.priority === priorityFilter
      return statusMatch && priorityMatch
    })
  }, [tasks, statusFilter, priorityFilter])

  // Open create modal
  const handleCreateTask = () => {
    setEditingTask(null)
    taskForm.resetFields()
    taskForm.setFieldsValue({
      status: 'TODO',
      priority: 'MEDIUM',
    })
    setTaskModalVisible(true)
  }

  // Open edit modal
  const handleEditTask = (task: KPITaskResponse) => {
    setEditingTask(task)
    taskForm.setFieldsValue({
      title: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      complexity: task.complexity,
      estimated_hours: task.estimated_hours,
      due_date: task.due_date ? dayjs(task.due_date) : null,
      notes: task.notes,
    })
    setTaskModalVisible(true)
  }

  // Handle form submit
  const handleTaskSubmit = async () => {
    try {
      const values = await taskForm.validateFields()

      const taskData = {
        ...values,
        due_date: values.due_date ? values.due_date.toISOString() : null,
      }

      if (editingTask) {
        // Update existing task
        await updateTaskMutation.mutateAsync({
          taskId: editingTask.id,
          data: taskData,
        })
      } else {
        // Create new task
        const createData: KPITaskCreate = {
          ...taskData,
          employee_kpi_goal_id: employeeKpiGoalId,
          employee_id: employeeId,
        }
        await createTaskMutation.mutateAsync(createData)
      }
    } catch (error) {
      console.error('Form validation failed:', error)
    }
  }

  // Handle delete
  const handleDeleteTask = (taskId: number) => {
    deleteTaskMutation.mutate(taskId)
  }

  // Handle status change
  const handleStatusChange = (taskId: number, status: KPITaskStatus) => {
    updateStatusMutation.mutate({ taskId, status })
  }

  // Get status icon
  const getStatusIcon = (status: KPITaskStatus) => {
    const icons = {
      TODO: <ClockCircleOutlined />,
      IN_PROGRESS: <SyncOutlined spin />,
      DONE: <CheckCircleOutlined />,
      CANCELLED: <CloseCircleOutlined />,
    }
    return icons[status]
  }

  // Columns
  const columns: ColumnsType<KPITaskResponse> = [
    {
      title: 'Приоритет',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: KPITaskPriority) => {
        const config = TASK_PRIORITY_CONFIG[priority]
        return (
          <Tooltip title={config.label}>
            <Tag color={config.color}>
              <FlagOutlined /> {config.badge}
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: KPITaskResponse) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          {record.description && (
            <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: KPITaskStatus) => {
        const config = TASK_STATUS_CONFIG[status]
        return (
          <Tag color={config.color} icon={getStatusIcon(status)}>
            {config.label}
          </Tag>
        )
      },
    },
    {
      title: 'Прогресс',
      dataIndex: 'completion_percentage',
      key: 'completion_percentage',
      width: 150,
      render: (percentage: number | null) => {
        if (percentage === null) return '-'
        return (
          <Progress
            percent={Number(percentage)}
            size="small"
            status={percentage >= 100 ? 'success' : 'active'}
          />
        )
      },
    },
    {
      title: 'Сложность',
      dataIndex: 'complexity',
      key: 'complexity',
      width: 120,
      render: (complexity: number | null) => {
        if (!complexity) return '-'
        return (
          <Tooltip title={COMPLEXITY_LABELS[complexity]}>
            <Tag color={complexity >= 7 ? 'red' : complexity >= 4 ? 'orange' : 'green'}>
              {complexity}/10
            </Tag>
          </Tooltip>
        )
      },
    },
    {
      title: 'Срок',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 120,
      render: (date: string | null) => {
        if (!date) return '-'
        const dueDate = dayjs(date)
        const isOverdue = dueDate.isBefore(dayjs()) && dueDate.isValid()
        return (
          <Tooltip title={dueDate.format('DD.MM.YYYY HH:mm')}>
            <span style={{ color: isOverdue ? '#ff4d4f' : undefined }}>
              {dueDate.format('DD.MM.YYYY')}
            </span>
          </Tooltip>
        )
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      render: (_: any, record: KPITaskResponse) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEditTask(record)}
              size="small"
            />
          </Tooltip>

          {record.status !== 'DONE' && (
            <Tooltip title="Завершить">
              <Button
                type="link"
                icon={<CheckCircleOutlined />}
                onClick={() => handleStatusChange(record.id, 'DONE')}
                size="small"
                style={{ color: '#52c41a' }}
              />
            </Tooltip>
          )}

          {record.status === 'TODO' && (
            <Tooltip title="Начать работу">
              <Button
                type="link"
                icon={<SyncOutlined />}
                onClick={() => handleStatusChange(record.id, 'IN_PROGRESS')}
                size="small"
                style={{ color: '#1890ff' }}
              />
            </Tooltip>
          )}

          <Popconfirm
            title="Удалить задачу?"
            onConfirm={() => handleDeleteTask(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Tooltip title="Удалить">
              <Button type="link" danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Statistics Cards */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Всего задач"
                value={statistics.total_tasks}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Завершено"
                value={statistics.by_status.DONE || 0}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="В работе"
                value={statistics.by_status.IN_PROGRESS || 0}
                valueStyle={{ color: '#1890ff' }}
                prefix={<SyncOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Просрочено"
                value={statistics.overdue_tasks}
                valueStyle={{ color: statistics.overdue_tasks > 0 ? '#cf1322' : undefined }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters and Actions */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateTask}>
          Создать задачу
        </Button>

        <Select
          style={{ width: 180 }}
          placeholder="Фильтр по статусу"
          value={statusFilter}
          onChange={setStatusFilter}
        >
          <Option value="ALL">Все статусы</Option>
          <Option value="TODO">К выполнению</Option>
          <Option value="IN_PROGRESS">В работе</Option>
          <Option value="DONE">Выполнено</Option>
          <Option value="CANCELLED">Отменено</Option>
        </Select>

        <Select
          style={{ width: 180 }}
          placeholder="Фильтр по приоритету"
          value={priorityFilter}
          onChange={setPriorityFilter}
        >
          <Option value="ALL">Все приоритеты</Option>
          <Option value="CRITICAL">Критический</Option>
          <Option value="HIGH">Высокий</Option>
          <Option value="MEDIUM">Средний</Option>
          <Option value="LOW">Низкий</Option>
        </Select>
      </Space>

      {/* Tasks Table */}
      <Table
        columns={columns}
        dataSource={filteredTasks}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
        size="small"
      />

      {/* Task Form Modal */}
      <Modal
        title={editingTask ? 'Редактировать задачу' : 'Создать задачу'}
        open={taskModalVisible}
        onOk={handleTaskSubmit}
        onCancel={() => {
          setTaskModalVisible(false)
          setEditingTask(null)
          taskForm.resetFields()
        }}
        width={600}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={taskForm} layout="vertical">
          <Form.Item
            name="title"
            label="Название задачи"
            rules={[{ required: true, message: 'Введите название задачи' }]}
          >
            <Input placeholder="Название задачи" maxLength={255} />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <TextArea rows={3} placeholder="Подробное описание задачи" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="Статус" rules={[{ required: true }]}>
                <Select>
                  <Option value="TODO">К выполнению</Option>
                  <Option value="IN_PROGRESS">В работе</Option>
                  <Option value="DONE">Выполнено</Option>
                  <Option value="CANCELLED">Отменено</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item name="priority" label="Приоритет" rules={[{ required: true }]}>
                <Select>
                  <Option value="LOW">Низкий</Option>
                  <Option value="MEDIUM">Средний</Option>
                  <Option value="HIGH">Высокий</Option>
                  <Option value="CRITICAL">Критический</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="complexity"
                label="Сложность (1-10)"
                tooltip="Оценка сложности задачи по шкале от 1 до 10"
              >
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item name="estimated_hours" label="Оценка времени (часы)">
                <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="due_date" label="Срок выполнения">
            <DatePicker showTime style={{ width: '100%' }} format="DD.MM.YYYY HH:mm" />
          </Form.Item>

          <Form.Item name="notes" label="Комментарии">
            <TextArea rows={2} placeholder="Дополнительные заметки" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KpiTasksTab
