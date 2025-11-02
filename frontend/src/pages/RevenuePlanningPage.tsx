import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  CopyOutlined,
  SyncOutlined,
  FolderOutlined,
} from '@ant-design/icons'
import { useDepartment } from '@/contexts/DepartmentContext'
import { revenueApi } from '@/api/revenue'
import type { RevenuePlan, RevenuePlanCreate, RevenuePlanStatus } from '@/types/revenue'
import CopyRevenuePlanModal from '@/components/revenue/CopyRevenuePlanModal'
import dayjs from 'dayjs'

const { Option } = Select

const RevenuePlanningPage = () => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isCopyModalVisible, setIsCopyModalVisible] = useState(false)
  const [editingPlan, setEditingPlan] = useState<RevenuePlan | null>(null)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [selectedStatus, setSelectedStatus] = useState<RevenuePlanStatus | undefined>()

  // Fetch revenue plans
  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['revenue-plans', selectedYear, selectedStatus, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.plans.getAll({
        year: selectedYear,
        status: selectedStatus,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Create plan mutation
  const createPlanMutation = useMutation({
    mutationFn: (data: RevenuePlanCreate) => revenueApi.plans.create(data),
    onSuccess: () => {
      message.success('План доходов успешно создан')
      queryClient.invalidateQueries({ queryKey: ['revenue-plans'] })
      setIsModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка создания плана: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Update plan mutation
  const updatePlanMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => revenueApi.plans.update(id, data),
    onSuccess: () => {
      message.success('План доходов успешно обновлен')
      queryClient.invalidateQueries({ queryKey: ['revenue-plans'] })
      setIsModalVisible(false)
      setEditingPlan(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления плана: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Delete plan mutation
  const deletePlanMutation = useMutation({
    mutationFn: (id: number) => revenueApi.plans.delete(id),
    onSuccess: () => {
      message.success('План доходов успешно удален')
      queryClient.invalidateQueries({ queryKey: ['revenue-plans'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления плана: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Approve plan mutation
  const approvePlanMutation = useMutation({
    mutationFn: (id: number) => revenueApi.plans.approve(id),
    onSuccess: () => {
      message.success('План доходов успешно утвержден')
      queryClient.invalidateQueries({ queryKey: ['revenue-plans'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка утверждения плана: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Calculate summary statistics
  const summary = useMemo(() => {
    const total = plans.reduce((sum, p) => sum + Number(p.total_planned_revenue || 0), 0)
    const approvedCount = plans.filter((p) => p.status === 'APPROVED').length
    const draftCount = plans.filter((p) => p.status === 'DRAFT').length

    return {
      total,
      approvedCount,
      draftCount,
      totalCount: plans.length,
    }
  }, [plans])

  const handleOpenModal = useCallback((plan?: RevenuePlan) => {
    if (plan) {
      setEditingPlan(plan)
      form.setFieldsValue({
        name: plan.name,
        year: plan.year,
        description: plan.description,
      })
    } else {
      setEditingPlan(null)
      form.setFieldsValue({
        year: selectedYear,
      })
    }
    setIsModalVisible(true)
  }, [form, selectedYear])

  const handleCloseModal = useCallback(() => {
    setIsModalVisible(false)
    setEditingPlan(null)
    form.resetFields()
  }, [form])

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()

      if (editingPlan) {
        updatePlanMutation.mutate({
          id: editingPlan.id,
          data: values,
        })
      } else {
        createPlanMutation.mutate({
          ...values,
          department_id: selectedDepartment?.id,
        })
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }, [form, editingPlan, selectedDepartment, createPlanMutation, updatePlanMutation])

  const getStatusTag = (status: RevenuePlanStatus) => {
    const statusConfig: Record<RevenuePlanStatus, { color: string; icon: React.ReactElement | null; text: string }> = {
      DRAFT: { color: 'default', icon: <ClockCircleOutlined />, text: 'Черновик' },
      PENDING_APPROVAL: { color: 'processing', icon: <SyncOutlined spin />, text: 'На согласовании' },
      APPROVED: { color: 'success', icon: <CheckCircleOutlined />, text: 'Утвержден' },
      ACTIVE: { color: 'blue', icon: <CheckCircleOutlined />, text: 'Активный' },
      ARCHIVED: { color: 'default', icon: <FolderOutlined />, text: 'Архивный' },
    }

    const config = statusConfig[status] || { color: 'default', icon: null, text: status }

    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    )
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
    },
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 100,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: RevenuePlanStatus) => getStatusTag(status),
    },
    {
      title: 'Плановая выручка',
      dataIndex: 'total_planned_revenue',
      key: 'total_planned_revenue',
      width: 180,
      align: 'right' as const,
      render: (value: number) => {
        if (!value) return '—'
        return new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value)
      },
    },
    {
      title: 'Создан',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: RevenuePlan) => (
        <Space size="small">
          <Tooltip title="Просмотр версий и детальное планирование">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/revenue/planning/${record.id}`)}
            >
              Версии
            </Button>
          </Tooltip>

          {record.status === 'DRAFT' && (
            <>
              <Tooltip title="Редактировать">
                <Button
                  type="link"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => handleOpenModal(record)}
                />
              </Tooltip>

              <Tooltip title="Утвердить план">
                <Popconfirm
                  title="Утвердить план доходов?"
                  description="После утверждения план нельзя будет редактировать"
                  onConfirm={() => approvePlanMutation.mutate(record.id)}
                  okText="Утвердить"
                  cancelText="Отмена"
                >
                  <Button type="link" size="small" icon={<CheckCircleOutlined />}>
                    Утвердить
                  </Button>
                </Popconfirm>
              </Tooltip>

              <Popconfirm
                title="Удалить план?"
                description="Это действие нельзя отменить"
                onConfirm={() => deletePlanMutation.mutate(record.id)}
                okText="Удалить"
                cancelText="Отмена"
              >
                <Button type="link" danger size="small" icon={<DeleteOutlined />} />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  if (!selectedDepartment) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin tip="Загрузка данных отдела..." />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, marginBottom: 8 }}>Планирование доходов</h1>
        <p style={{ margin: 0, color: '#8c8c8c' }}>
          Управление планами доходов с версионированием и утверждением
        </p>
      </div>

      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего планов"
              value={summary.totalCount}
              prefix={<CopyOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Утверждено"
              value={summary.approvedCount}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Черновиков"
              value={summary.draftCount}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Общая плановая выручка"
              value={summary.total}
              precision={0}
              prefix="₽"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space size="middle">
              <span>Год:</span>
              <Select
                value={selectedYear}
                onChange={setSelectedYear}
                style={{ width: 120 }}
              >
                {[2024, 2025, 2026, 2027].map((year) => (
                  <Option key={year} value={year}>
                    {year}
                  </Option>
                ))}
              </Select>

              <span>Статус:</span>
              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                style={{ width: 150 }}
                allowClear
                placeholder="Все статусы"
              >
                <Option value="DRAFT">Черновик</Option>
                <Option value="APPROVED">Утвержден</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<CopyOutlined />}
                onClick={() => setIsCopyModalVisible(true)}
              >
                Скопировать план
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => handleOpenModal()}
              >
                Создать план
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Plans Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          loading={isLoading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
            defaultPageSize: 20,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingPlan ? 'Редактировать план' : 'Создать план доходов'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={600}
        confirmLoading={createPlanMutation.isPending || updatePlanMutation.isPending}
        okText={editingPlan ? 'Сохранить' : 'Создать'}
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            name="name"
            label="Название плана"
            rules={[{ required: true, message: 'Введите название плана' }]}
          >
            <Input placeholder="Например: План доходов 2025" />
          </Form.Item>

          <Form.Item
            name="year"
            label="Год"
            rules={[{ required: true, message: 'Выберите год' }]}
          >
            <DatePicker picker="year" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea
              rows={4}
              placeholder="Описание плана (необязательно)"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Copy Plan Modal */}
      <CopyRevenuePlanModal
        open={isCopyModalVisible}
        targetYear={selectedYear}
        departmentId={selectedDepartment?.id}
        onClose={() => setIsCopyModalVisible(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['revenue-plans'] })
        }}
      />
    </div>
  )
}

export default RevenuePlanningPage
