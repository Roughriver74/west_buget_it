import { useState } from 'react'
import {
  Card,
  Button,
  Table,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  message,
  Typography,
  Tag,
  Select,
  Tooltip,
  Popconfirm,
  Transfer,
  DatePicker,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import type {
  KPIGoalTemplate,
  KPIGoalTemplateCreate,
  KPIGoalTemplateUpdate,
  ApplyTemplateRequest,
} from '@/api/kpi'
import { employeeAPI, type Employee } from '@/api/payroll'

const { Text, Title } = Typography
const { Option } = Select
const { TextArea } = Input

interface KpiGoalTemplatesTabProps {
  departmentId?: number
}

interface TemplateGoalForm {
  goal_id: number
  weight: number
  default_target_value?: number
  display_order: number
}

export const KpiGoalTemplatesTab: React.FC<KpiGoalTemplatesTabProps> = ({ departmentId }) => {
  const queryClient = useQueryClient()

  const [templateModal, setTemplateModal] = useState<{
    open: boolean
    editing?: KPIGoalTemplate
  }>({
    open: false,
  })

  const [applyModal, setApplyModal] = useState<{
    open: boolean
    template?: KPIGoalTemplate
  }>({
    open: false,
  })

  const [selectedEmployees, setSelectedEmployees] = useState<number[]>([])
  const [applyYear, setApplyYear] = useState<number>(dayjs().year())
  const [applyMonth, setApplyMonth] = useState<number>(dayjs().month() + 1)

  const [templateForm] = Form.useForm<{
    name: string
    description?: string
    is_active: boolean
    template_goals: TemplateGoalForm[]
  }>()

  // Queries
  const templatesQuery = useQuery({
    queryKey: ['kpi-templates', departmentId],
    queryFn: () =>
      kpiApi.listTemplates({
        department_id: departmentId,
      }),
    enabled: !!departmentId,
  })

  const goalsQuery = useQuery({
    queryKey: ['kpi-goals', departmentId],
    queryFn: () =>
      kpiApi.listGoals({
        department_id: departmentId,
        year: dayjs().year(),
      }),
    enabled: !!departmentId,
  })

  const employeesQuery = useQuery({
    queryKey: ['employees', departmentId],
    queryFn: () =>
      employeeAPI.list({
        department_id: departmentId,
      }),
    enabled: !!departmentId && applyModal.open,
  })

  // Mutations
  const createTemplateMutation = useMutation({
    mutationFn: (payload: KPIGoalTemplateCreate) => kpiApi.createTemplate(payload),
    onSuccess: () => {
      message.success('Шаблон создан')
      queryClient.invalidateQueries({ queryKey: ['kpi-templates'] })
      setTemplateModal({ open: false })
      templateForm.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании шаблона')
    },
  })

  const updateTemplateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: KPIGoalTemplateUpdate }) =>
      kpiApi.updateTemplate(id, data),
    onSuccess: () => {
      message.success('Шаблон обновлен')
      queryClient.invalidateQueries({ queryKey: ['kpi-templates'] })
      setTemplateModal({ open: false })
      templateForm.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении шаблона')
    },
  })

  const deleteTemplateMutation = useMutation({
    mutationFn: (id: number) => kpiApi.deleteTemplate(id),
    onSuccess: () => {
      message.success('Шаблон удален')
      queryClient.invalidateQueries({ queryKey: ['kpi-templates'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении шаблона')
    },
  })

  const applyTemplateMutation = useMutation({
    mutationFn: ({ templateId, request }: { templateId: number; request: ApplyTemplateRequest }) =>
      kpiApi.applyTemplate(templateId, request),
    onSuccess: (response) => {
      if (response.success) {
        message.success(
          `Шаблон применен: ${response.employees_updated} сотрудников, ${response.goals_created} целей`
        )
      } else {
        message.warning(`Применено частично. Ошибки: ${response.errors.join(', ')}`)
      }
      queryClient.invalidateQueries({ queryKey: ['employee-kpis'] })
      setApplyModal({ open: false })
      setSelectedEmployees([])
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при применении шаблона')
    },
  })

  // Handlers
  const handleOpenTemplateModal = (template?: KPIGoalTemplate) => {
    if (template) {
      templateForm.setFieldsValue({
        name: template.name,
        description: template.description || '',
        is_active: template.is_active,
        template_goals: (template.template_goals || []).map((item: any) => ({
          goal_id: item.goal_id,
          weight: Number(item.weight),
          default_target_value: item.default_target_value
            ? Number(item.default_target_value)
            : undefined,
          display_order: item.display_order,
        })),
      })
    } else {
      templateForm.resetFields()
      templateForm.setFieldsValue({
        is_active: true,
        template_goals: [],
      })
    }
    setTemplateModal({ open: true, editing: template })
  }

  const handleSaveTemplate = async () => {
    const values = await templateForm.validateFields()

    // Validate total weight = 100%
    const totalWeight = values.template_goals.reduce((sum, goal) => sum + goal.weight, 0)
    if (Math.abs(totalWeight - 100) > 0.01) {
      message.error(`Сумма весов должна быть 100%, сейчас: ${totalWeight.toFixed(2)}%`)
      return
    }

    if (templateModal.editing) {
      updateTemplateMutation.mutate({
        id: templateModal.editing.id,
        data: values,
      })
    } else {
      createTemplateMutation.mutate({
        ...values,
        department_id: departmentId!,
      })
    }
  }

  const handleApplyTemplate = async () => {
    if (selectedEmployees.length === 0) {
      message.error('Выберите хотя бы одного сотрудника')
      return
    }

    if (!applyModal.template) return

    applyTemplateMutation.mutate({
      templateId: applyModal.template.id,
      request: {
        employee_ids: selectedEmployees,
        year: applyYear,
        month: applyMonth,
      },
    })
  }

  // Calculate total weight in form
  const calculateTotalWeight = () => {
    const goals = templateForm.getFieldValue('template_goals') || []
    return goals.reduce((sum: number, goal: TemplateGoalForm) => sum + (goal.weight || 0), 0)
  }

  // Table columns
  const columns: ColumnsType<KPIGoalTemplate> = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: KPIGoalTemplate) => (
        <Space>
          <Text strong>{text}</Text>
          {!record.is_active && <Tag color="red">Неактивен</Tag>}
        </Space>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Целей',
      key: 'goals_count',
      render: (_, record: KPIGoalTemplate) => (
        <Tag color="blue">{(record.template_goals || []).length} целей</Tag>
      ),
    },
    {
      title: 'Создан',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY HH:mm'),
      width: 150,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      render: (_, record: KPIGoalTemplate) => (
        <Space>
          <Tooltip title="Применить к сотрудникам">
            <Button
              type="primary"
              size="small"
              icon={<CheckOutlined />}
              onClick={() => {
                setApplyModal({ open: true, template: record })
                setSelectedEmployees([])
              }}
              disabled={!record.is_active}
            >
              Применить
            </Button>
          </Tooltip>
          <Tooltip title="Редактировать">
            <Button
              type="default"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenTemplateModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Удалить шаблон?"
            description="Это действие необратимо"
            onConfirm={() => deleteTemplateMutation.mutate(record.id)}
            okText="Удалить"
            cancelText="Отмена"
          >
            <Tooltip title="Удалить">
              <Button type="default" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title={<Title level={4}>Шаблоны целей КПИ</Title>}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenTemplateModal()}
            disabled={!departmentId}
          >
            Создать шаблон
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={templatesQuery.data || []}
          loading={templatesQuery.isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Template Create/Edit Modal */}
      <Modal
        title={templateModal.editing ? 'Редактировать шаблон' : 'Создать шаблон'}
        open={templateModal.open}
        onCancel={() => {
          setTemplateModal({ open: false })
          templateForm.resetFields()
        }}
        onOk={handleSaveTemplate}
        width={800}
        okText="Сохранить"
        cancelText="Отмена"
        confirmLoading={createTemplateMutation.isPending || updateTemplateMutation.isPending}
      >
        <Form form={templateForm} layout="vertical">
          <Form.Item
            name="name"
            label="Название шаблона"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder="Например: Продажи Q1, IT Стандарт" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <TextArea rows={2} placeholder="Краткое описание шаблона" />
          </Form.Item>

          <Form.Item name="is_active" label="Статус" initialValue={true}>
            <Select>
              <Option value={true}>Активен</Option>
              <Option value={false}>Неактивен</Option>
            </Select>
          </Form.Item>

          <Form.Item label={`Цели (Сумма весов: ${calculateTotalWeight().toFixed(1)}%)`}>
            <Form.List name="template_goals">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field, index) => (
                    <Card key={field.key} size="small" style={{ marginBottom: 8 }}>
                      <Space style={{ width: '100%' }} direction="vertical">
                        <Form.Item
                          {...field}
                          name={[field.name, 'goal_id']}
                          rules={[{ required: true, message: 'Выберите цель' }]}
                          style={{ marginBottom: 8 }}
                        >
                          <Select placeholder="Выберите цель КПИ" showSearch optionFilterProp="label">
                            {goalsQuery.data?.map((goal) => (
                              <Option key={goal.id} value={goal.id} label={goal.name}>
                                {goal.name} ({goal.category || 'Без категории'})
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>

                        <Space>
                          <Form.Item
                            {...field}
                            name={[field.name, 'weight']}
                            label="Вес (%)"
                            rules={[
                              { required: true, message: 'Укажите вес' },
                              { type: 'number', min: 0, max: 100, message: 'Вес от 0 до 100' },
                            ]}
                            style={{ marginBottom: 0 }}
                          >
                            <InputNumber
                              placeholder="30"
                              min={0}
                              max={100}
                              precision={2}
                              style={{ width: 100 }}
                            />
                          </Form.Item>

                          <Form.Item
                            {...field}
                            name={[field.name, 'default_target_value']}
                            label="Целевое значение (опц.)"
                            style={{ marginBottom: 0 }}
                          >
                            <InputNumber placeholder="100" min={0} style={{ width: 120 }} />
                          </Form.Item>

                          <Form.Item
                            {...field}
                            name={[field.name, 'display_order']}
                            label="Порядок"
                            initialValue={index}
                            style={{ marginBottom: 0 }}
                          >
                            <InputNumber min={0} style={{ width: 80 }} />
                          </Form.Item>

                          <Button type="link" danger onClick={() => remove(field.name)}>
                            Удалить
                          </Button>
                        </Space>
                      </Space>
                    </Card>
                  ))}

                  <Button
                    type="dashed"
                    onClick={() =>
                      add({
                        weight: 0,
                        display_order: fields.length,
                      })
                    }
                    block
                    icon={<PlusOutlined />}
                  >
                    Добавить цель
                  </Button>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>

      {/* Apply Template Modal */}
      <Modal
        title={`Применить шаблон: ${applyModal.template?.name}`}
        open={applyModal.open}
        onCancel={() => {
          setApplyModal({ open: false })
          setSelectedEmployees([])
        }}
        onOk={handleApplyTemplate}
        width={700}
        okText="Применить"
        cancelText="Отмена"
        confirmLoading={applyTemplateMutation.isPending}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>Период:</Text>
            <Space style={{ marginLeft: 16 }}>
              <DatePicker
                picker="year"
                value={dayjs().year(applyYear)}
                onChange={(date) => setApplyYear(date?.year() || dayjs().year())}
              />
              <DatePicker
                picker="month"
                value={dayjs().month(applyMonth - 1)}
                onChange={(date) => setApplyMonth((date?.month() || 0) + 1)}
                format="MMMM"
              />
            </Space>
          </div>

          <div>
            <Text strong>Выберите сотрудников ({selectedEmployees.length} выбрано):</Text>
            <div style={{ marginTop: 8 }}>
              <Transfer
                dataSource={
                  employeesQuery.data?.map((emp: Employee) => ({
                    key: String(emp.id),
                    title: emp.full_name,
                    description: emp.position || '',
                  })) || []
                }
                targetKeys={selectedEmployees.map((id) => String(id))}
                onChange={(targetKeys) => setSelectedEmployees(targetKeys.map((key) => parseInt(String(key))))}
                render={(item) => (
                  <div>
                    <div>{item.title}</div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.description}
                    </Text>
                  </div>
                )}
                listStyle={{
                  width: 300,
                  height: 400,
                }}
                showSearch
                filterOption={(input, item) =>
                  item.title?.toLowerCase().includes(input.toLowerCase()) ||
                  item.description?.toLowerCase().includes(input.toLowerCase())
                }
              />
            </div>
          </div>

          {applyModal.template && (
            <div>
              <Text strong>Цели в шаблоне:</Text>
              <ul>
                {(applyModal.template.template_goals || []).map((item: any) => (
                  <li key={item.id}>
                    {item.goal.name} - <Text strong>{item.weight}%</Text>
                    {item.default_target_value && (
                      <Text type="secondary"> (цель: {item.default_target_value})</Text>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Space>
      </Modal>
    </div>
  )
}
