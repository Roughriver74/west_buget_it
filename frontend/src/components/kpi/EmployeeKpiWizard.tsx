import { useState, useEffect, useMemo } from 'react'
import {
  Modal,
  Steps,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Space,
  Row,
  Col,
  Card,
  Typography,
  Alert,
  Divider,
  message,
} from 'antd'
import {
  UserOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  AimOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type {
  EmployeeKPIExtended,
  EmployeeKPICreateExtended,
  EmployeeKPIUpdateExtended,
  KPIGoal,
} from '@/api/kpi'
import { kpiApi } from '@/api/kpi'
import { employeeAPI } from '@/api/payroll'
import dayjs from 'dayjs'

const { Text } = Typography
const { Option } = Select
const { Step } = Steps

interface EmployeeKpiWizardProps {
  open: boolean
  onClose: () => void
  editingKpi?: EmployeeKPIExtended
  departmentId?: number
  defaultYear?: number
  defaultMonth?: number
}

interface WizardFormData {
  // Step 1: Basic Info
  employee_id: number
  year: number
  month: number
  status: string

  // Step 2: Bonus Settings
  bonus_base: number
  bonus_type: string
  monthly_bonus_multiplier: number
  quarterly_bonus_multiplier: number
  annual_bonus_multiplier: number
  depremium_threshold: number
  kpi_percentage?: number
  comment?: string

  // Step 3: Goals Assignment
  goals: Array<{
    goal_id: number
    weight: number
    target_value?: number
  }>
}

type WizardPayload = EmployeeKPICreateExtended | EmployeeKPIUpdateExtended

const BONUS_TYPES = [
  { value: 'FIXED', label: 'Фиксированная' },
  { value: 'PERFORMANCE_BASED', label: 'Результативная' },
  { value: 'MIXED', label: 'Смешанная' },
]

const STATUS_OPTIONS = [
  { value: 'DRAFT', label: 'Черновик' },
  { value: 'UNDER_REVIEW', label: 'На проверке' },
  { value: 'APPROVED', label: 'Утверждено' },
  { value: 'REJECTED', label: 'Отклонено' },
]

export const EmployeeKpiWizard = ({
  open,
  onClose,
  editingKpi,
  departmentId,
  defaultYear,
  defaultMonth,
}: EmployeeKpiWizardProps) => {
  const [form] = Form.useForm<WizardFormData>()
  const [currentStep, setCurrentStep] = useState(0)
  const queryClient = useQueryClient()

  const isEditMode = !!editingKpi

  // Fetch employees
  const { data: employees = [] } = useQuery({
    queryKey: ['employees', departmentId],
    queryFn: () => employeeAPI.list({ department_id: departmentId }),
    enabled: open,
  })

  // Fetch available goals
  const { data: availableGoals = [] } = useQuery({
    queryKey: ['kpi-goals', departmentId],
    queryFn: () => kpiApi.listGoals({ department_id: departmentId }),
    enabled: open,
  })

  // Initialize form with existing data or defaults
  useEffect(() => {
    if (open) {
      if (isEditMode && editingKpi) {
        form.setFieldsValue({
          employee_id: editingKpi.employee_id,
          year: editingKpi.year,
          month: editingKpi.month,
          status: editingKpi.status || 'DRAFT',
          bonus_base: Number(editingKpi.bonus_base || 0),
          bonus_type: editingKpi.bonus_type || 'PERFORMANCE_BASED',
          monthly_bonus_multiplier: editingKpi.monthly_bonus_multiplier || 1,
          quarterly_bonus_multiplier: editingKpi.quarterly_bonus_multiplier || 0,
          annual_bonus_multiplier: editingKpi.annual_bonus_multiplier || 0,
          depremium_threshold: editingKpi.depremium_threshold || 0,
          kpi_percentage:
            editingKpi.kpi_percentage !== null && editingKpi.kpi_percentage !== undefined
              ? Number(editingKpi.kpi_percentage)
              : undefined,
          comment: editingKpi.comment ?? editingKpi.notes ?? undefined,
          goals: [], // Will be loaded separately
        })
      } else {
        // Defaults for new KPI
        form.setFieldsValue({
          employee_id: undefined,
          year: defaultYear || dayjs().year(),
          month: defaultMonth || dayjs().month() + 1,
          status: 'DRAFT',
          bonus_base: 0,
          bonus_type: 'PERFORMANCE_BASED',
          monthly_bonus_multiplier: 1,
          quarterly_bonus_multiplier: 0,
          annual_bonus_multiplier: 0,
          depremium_threshold: 0,
          goals: [],
        })
      }
    }
  }, [open, isEditMode, editingKpi, form, defaultYear, defaultMonth])

  // Create/Update mutation
  const createMutation = useMutation({
    mutationFn: (data: EmployeeKPICreateExtended) => kpiApi.createEmployeeKpi(data),
    onSuccess: () => {
      message.success('KPI успешно создан!')
      queryClient.invalidateQueries({ queryKey: ['employee-kpis'] })
      handleClose()
    },
    onError: (error: any) => {
      message.error(`Ошибка создания: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: EmployeeKPIUpdateExtended }) =>
      kpiApi.updateEmployeeKpi(id, data),
    onSuccess: () => {
      message.success('KPI успешно обновлён!')
      queryClient.invalidateQueries({ queryKey: ['employee-kpis'] })
      handleClose()
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления: ${error.message}`)
    },
  })

  // Calculate total weight
  const totalWeight = useMemo(() => {
    const goals = form.getFieldValue('goals') || []
    return goals.reduce((sum: number, g: any) => sum + (g?.weight || 0), 0)
  }, [form.getFieldValue('goals')])

  const handleNext = async () => {
    try {
      // Validate current step fields
      if (currentStep === 0) {
        await form.validateFields(['employee_id', 'year', 'month'])
      } else if (currentStep === 1) {
        await form.validateFields([
          'bonus_base',
          'bonus_type',
          'monthly_bonus_multiplier',
          'quarterly_bonus_multiplier',
          'annual_bonus_multiplier',
          'depremium_threshold',
        ])
      }

      setCurrentStep(currentStep + 1)
    } catch (error) {
      message.warning('Пожалуйста, заполните все обязательные поля')
    }
  }

  const handlePrev = () => {
    setCurrentStep(currentStep - 1)
  }

  const handleClose = () => {
    form.resetFields()
    setCurrentStep(0)
    onClose()
  }

  const handleFinish = async () => {
    try {
      const values = await form.validateFields()

      // Validate total weight
      if (totalWeight !== 100) {
        message.error('Сумма весов целей должна быть равна 100%')
        return
      }

      const payload: WizardPayload = {
        employee_id: values.employee_id,
        year: values.year,
        month: values.month,
        status: values.status,
        bonus_base: values.bonus_base,
        bonus_type: values.bonus_type,
        monthly_bonus_multiplier: values.monthly_bonus_multiplier,
        quarterly_bonus_multiplier: values.quarterly_bonus_multiplier,
        annual_bonus_multiplier: values.annual_bonus_multiplier,
        depremium_threshold: values.depremium_threshold,
        kpi_percentage: values.kpi_percentage,
        comment: values.comment,
      }

      if (isEditMode && editingKpi) {
        updateMutation.mutate({ id: editingKpi.id, data: payload as EmployeeKPIUpdateExtended })
      } else {
        createMutation.mutate(payload as EmployeeKPICreateExtended)
      }
    } catch (error) {
      message.error('Пожалуйста, заполните все обязательные поля')
    }
  }

  const steps = [
    {
      title: 'Основная информация',
      icon: <UserOutlined />,
      description: 'Сотрудник и период',
    },
    {
      title: 'Настройка бонусов',
      icon: <SettingOutlined />,
      description: 'Параметры премирования',
    },
    {
      title: 'Назначение целей',
      icon: <AimOutlined />,
      description: 'Цели и веса',
    },
  ]

  return (
    <Modal
      title={
        <Space>
          {isEditMode ? '✏️ Редактирование KPI' : '➕ Создание нового KPI'}
        </Space>
      }
      open={open}
      onCancel={handleClose}
      width={900}
      footer={null}
      destroyOnHidden
    >
      <Steps current={currentStep} style={{ marginBottom: 32 }}>
        {steps.map((step) => (
          <Step
            key={step.title}
            title={step.title}
            description={step.description}
            icon={step.icon}
          />
        ))}
      </Steps>

      <Form form={form} layout="vertical">
        {/* Step 1: Basic Info */}
        {currentStep === 0 && (
          <Card>
            <Alert
              message="Шаг 1: Основная информация"
              description="Выберите сотрудника и укажите период для оценки KPI"
              type="info"
              icon={<InfoCircleOutlined />}
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item
                  label="Сотрудник"
                  name="employee_id"
                  rules={[{ required: true, message: 'Выберите сотрудника' }]}
                >
                  <Select
                    showSearch
                    placeholder="Выберите сотрудника"
                    optionFilterProp="children"
                    filterOption={(input, option) => {
                      const label = option?.children
                      if (!label) return false
                      const text = typeof label === 'string' ? label : String(label)
                      return text.toLowerCase().includes(input.toLowerCase())
                    }}
                    disabled={isEditMode}
                  >
                    {employees.map((emp: any) => (
                      <Option key={emp.id} value={emp.id}>
                        {emp.full_name} - {emp.position}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Год"
                  name="year"
                  rules={[{ required: true, message: 'Укажите год' }]}
                >
                  <InputNumber
                    min={2020}
                    max={2100}
                    style={{ width: '100%' }}
                    disabled={isEditMode}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="Месяц"
                  name="month"
                  rules={[{ required: true, message: 'Укажите месяц' }]}
                >
                  <Select placeholder="Выберите месяц" disabled={isEditMode}>
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                      <Option key={m} value={m}>
                        {dayjs().month(m - 1).format('MMMM')}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Статус" name="status">
                  <Select>
                    {STATUS_OPTIONS.map((opt) => (
                      <Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="KPI %" name="kpi_percentage">
                  <InputNumber
                    min={0}
                    max={200}
                    precision={2}
                    style={{ width: '100%' }}
                    suffix="%"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="Комментарий" name="comment">
              <Input.TextArea rows={3} placeholder="Дополнительные замечания" />
            </Form.Item>
          </Card>
        )}

        {/* Step 2: Bonus Settings */}
        {currentStep === 1 && (
          <Card>
            <Alert
              message="Шаг 2: Настройка бонусов"
              description="Укажите базовую премию и множители для расчёта бонусов"
              type="info"
              icon={<InfoCircleOutlined />}
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Базовая премия (₽)"
                  name="bonus_base"
                  rules={[{ required: true, message: 'Укажите базовую премию' }]}
                >
                  <InputNumber
                    min={0}
                    precision={2}
                    style={{ width: '100%' }}
                    placeholder="0.00"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="Тип премии"
                  name="bonus_type"
                  rules={[{ required: true, message: 'Выберите тип премии' }]}
                >
                  <Select>
                    {BONUS_TYPES.map((type) => (
                      <Option key={type.value} value={type.value}>
                        {type.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Divider orientation="left">Множители бонусов</Divider>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="Месячный бонус (x)"
                  name="monthly_bonus_multiplier"
                  tooltip="Множитель для расчёта месячного бонуса"
                >
                  <InputNumber
                    min={0}
                    max={10}
                    precision={2}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label="Квартальный бонус (x)"
                  name="quarterly_bonus_multiplier"
                  tooltip="Множитель для расчёта квартального бонуса"
                >
                  <InputNumber
                    min={0}
                    max={10}
                    precision={2}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label="Годовой бонус (x)"
                  name="annual_bonus_multiplier"
                  tooltip="Множитель для расчёта годового бонуса"
                >
                  <InputNumber
                    min={0}
                    max={10}
                    precision={2}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider orientation="left">Депремирование</Divider>

            <Form.Item
              label="Порог депремирования (%)"
              name="depremium_threshold"
              tooltip="Если KPI% ниже этого значения, применяется депремирование"
            >
              <InputNumber
                min={0}
                max={100}
                precision={2}
                style={{ width: '100%' }}
                suffix="%"
              />
            </Form.Item>

            <Alert
              message="Формулы расчёта"
              description={
                <div>
                  <Text>• Месячный бонус = Базовая премия × Множитель × (KPI% / 100)</Text>
                  <br />
                  <Text>
                    • Квартальный бонус = Базовая премия × Множитель × (KPI% / 100)
                  </Text>
                  <br />
                  <Text>• Годовой бонус = Базовая премия × Множитель × (KPI% / 100)</Text>
                </div>
              }
              type="success"
              showIcon
            />
          </Card>
        )}

        {/* Step 3: Goals Assignment */}
        {currentStep === 2 && (
          <Card>
            <Alert
              message="Шаг 3: Назначение целей"
              description="Назначьте цели KPI с весами. Сумма весов должна быть 100%"
              type="info"
              icon={<InfoCircleOutlined />}
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Alert
              message={`Текущая сумма весов: ${totalWeight}%`}
              type={totalWeight === 100 ? 'success' : 'warning'}
              icon={totalWeight === 100 ? <CheckCircleOutlined /> : <WarningOutlined />}
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Form.List name="goals">
              {(fields, { add, remove }) => (
                <>
                  <Button
                    type="dashed"
                    onClick={() => add({ weight: 0 })}
                    block
                    style={{ marginBottom: 16 }}
                  >
                    + Добавить цель
                  </Button>

                  {fields.map((field) => (
                    <Card
                      key={field.key}
                      size="small"
                      style={{ marginBottom: 16 }}
                      extra={
                        <Button
                          type="link"
                          danger
                          onClick={() => remove(field.name)}
                        >
                          Удалить
                        </Button>
                      }
                    >
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            {...field}
                            label="Цель"
                            name={[field.name, 'goal_id']}
                            rules={[{ required: true, message: 'Выберите цель' }]}
                          >
                            <Select placeholder="Выберите цель">
                              {availableGoals.map((goal: KPIGoal) => (
                                <Option key={goal.id} value={goal.id}>
                                  {goal.name}
                                </Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            {...field}
                            label="Вес (%)"
                            name={[field.name, 'weight']}
                            rules={[
                              { required: true, message: 'Укажите вес' },
                              {
                                type: 'number',
                                min: 0,
                                max: 100,
                                message: 'От 0 до 100',
                              },
                            ]}
                          >
                            <InputNumber
                              min={0}
                              max={100}
                              precision={2}
                              style={{ width: '100%' }}
                              suffix="%"
                            />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            {...field}
                            label="Целевое значение"
                            name={[field.name, 'target_value']}
                          >
                            <InputNumber
                              min={0}
                              precision={2}
                              style={{ width: '100%' }}
                              placeholder="Опционально"
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </>
              )}
            </Form.List>

            {totalWeight !== 100 && (
              <Alert
                message="Внимание"
                description={`Сумма весов должна быть 100%. Текущая сумма: ${totalWeight}%`}
                type="error"
                showIcon
              />
            )}
          </Card>
        )}
      </Form>

      {/* Navigation Buttons */}
      <div style={{ marginTop: 24, textAlign: 'right' }}>
        <Space>
          <Button onClick={handleClose}>Отмена</Button>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>Назад</Button>
          )}
          {currentStep < steps.length - 1 && (
            <Button type="primary" onClick={handleNext}>
              Далее
            </Button>
          )}
          {currentStep === steps.length - 1 && (
            <Button
              type="primary"
              onClick={handleFinish}
              loading={createMutation.isPending || updateMutation.isPending}
              disabled={totalWeight !== 100}
            >
              {isEditMode ? 'Сохранить' : 'Создать'}
            </Button>
          )}
        </Space>
      </div>
    </Modal>
  )
}
