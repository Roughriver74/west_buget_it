import { useState } from 'react'
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
  Radio,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { UploadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kpiApi } from '@/api/kpi'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import type {
  KPIGoal,
  KPIGoalStatus,
  KPIGoalCreate,
  KPIGoalUpdate,
} from '@/api/kpi'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import ImportKPIModal from './ImportKPIModal'

const { Option } = Select
const { Text } = Typography

const statusColor: Record<KPIGoalStatus, string> = {
  DRAFT: 'default',
  ACTIVE: 'processing',
  ACHIEVED: 'success',
  NOT_ACHIEVED: 'error',
  CANCELLED: 'warning',
}

interface KpiGoalsTabProps {
  departmentId?: number
}

export const KpiGoalsTab: React.FC<KpiGoalsTabProps> = ({ departmentId }) => {
  const queryClient = useQueryClient()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  const [goalFilters, setGoalFilters] = useState<{ year: number; status?: KPIGoalStatus }>(() => ({
    year: dayjs().year(),
  }))

  const [goalModal, setGoalModal] = useState<{ open: boolean; editing?: KPIGoal }>({
    open: false,
  })

  const [importModalVisible, setImportModalVisible] = useState(false)

  const [goalForm] = Form.useForm<KPIGoalCreate | KPIGoalUpdate>()

  // Queries
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

  // Mutations
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

  const goals = goalsQuery.data || []

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

  const handleImportClick = () => {
    setImportModalVisible(true)
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

  return (
    <>
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
            <Button icon={<UploadOutlined />} onClick={handleImportClick}>
              Импорт
            </Button>
            <Button type="primary" onClick={onCreateGoal}>
              Добавить цель
            </Button>
          </Space>
        }
      >
        <ResponsiveTable<KPIGoal mobileLayout="card">
          rowKey="id"
          columns={goalColumns}
          dataSource={goals}
          loading={goalsQuery.isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Goal Modal */}
      <Modal
        title={goalModal.editing ? 'Редактировать цель KPI' : 'Создать цель KPI'}
        open={goalModal.open}
        onCancel={() => setGoalModal({ open: false })}
        onOk={handleGoalSubmit}
        okText={goalModal.editing ? 'Обновить' : 'Создать'}
        confirmLoading={createGoalMutation.isPending || updateGoalMutation.isPending}
        destroyOnHidden
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
            <Space.Compact style={{ width: '100%' }}>
              <InputNumber min={0} max={100} style={{ width: 'calc(100% - 30px)' }} />
              <div style={{ width: 30, border: '1px solid #d9d9d9', borderLeft: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#fafafa', borderRadius: '0 6px 6px 0' }}>%</div>
            </Space.Compact>
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

      {/* Import KPI Modal */}
      {importModalVisible && (
        <ImportKPIModal
          visible={importModalVisible}
          onCancel={() => setImportModalVisible(false)}
        />
      )}
    </>
  )
}
