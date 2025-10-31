import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography,
  Card,
  Space,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import { revenueActualsApi, revenueStreamsApi, revenueCategoriesApi } from '@/api'
import type { RevenueActual, RevenueActualCreate, RevenueActualUpdate } from '@/types/revenue'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import dayjs from 'dayjs'

const { Title } = Typography

const RevenueActualsPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingActual, setEditingActual] = useState<RevenueActual | null>(null)
  const [form] = Form.useForm()

  // Fetch revenue actuals
  const { data: actuals, isLoading, error } = useQuery({
    queryKey: ['revenue-actuals', year, selectedDepartment?.id],
    queryFn: () => revenueActualsApi.getAll({ year, department_id: selectedDepartment?.id }),
  })

  // Fetch streams for select
  const { data: streams } = useQuery({
    queryKey: ['revenue-streams', selectedDepartment?.id],
    queryFn: () =>
      revenueStreamsApi.getAll({ is_active: true, department_id: selectedDepartment?.id }),
  })

  // Fetch categories for select
  const { data: categories } = useQuery({
    queryKey: ['revenue-categories', selectedDepartment?.id],
    queryFn: () =>
      revenueCategoriesApi.getAll({ is_active: true, department_id: selectedDepartment?.id }),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: RevenueActualCreate) => revenueActualsApi.create(data),
    onSuccess: () => {
      message.success('Фактический доход добавлен')
      queryClient.invalidateQueries({ queryKey: ['revenue-actuals'] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при добавлении дохода')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RevenueActualUpdate }) =>
      revenueActualsApi.update(id, data),
    onSuccess: () => {
      message.success('Фактический доход обновлен')
      queryClient.invalidateQueries({ queryKey: ['revenue-actuals'] })
      setIsModalOpen(false)
      setEditingActual(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении дохода')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => revenueActualsApi.delete(id),
    onSuccess: () => {
      message.success('Фактический доход удален')
      queryClient.invalidateQueries({ queryKey: ['revenue-actuals'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении дохода')
    },
  })

  const handleCreate = () => {
    setEditingActual(null)
    form.resetFields()
    form.setFieldsValue({ year: currentYear })
    setIsModalOpen(true)
  }

  const handleEdit = (actual: RevenueActual) => {
    setEditingActual(actual)
    form.setFieldsValue(actual)
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingActual) {
        updateMutation.mutate({ id: editingActual.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const formatCurrency = (value?: number | null) => {
    if (!value) return '0 ₽'
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  const getMonthName = (month: number) => {
    const months = [
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
    return months[month - 1]
  }

  const columns = [
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 80,
    },
    {
      title: 'Месяц',
      dataIndex: 'month',
      key: 'month',
      width: 120,
      render: (month: number) => getMonthName(month),
    },
    {
      title: 'Поток доходов',
      dataIndex: 'revenue_stream_id',
      key: 'revenue_stream_id',
      render: (streamId: number | null) => {
        if (!streamId) return '-'
        const stream = streams?.find((s) => s.id === streamId)
        return stream?.name || '-'
      },
    },
    {
      title: 'Категория',
      dataIndex: 'revenue_category_id',
      key: 'revenue_category_id',
      render: (categoryId: number | null) => {
        if (!categoryId) return '-'
        const category = categories?.find((c) => c.id === categoryId)
        return category?.name || '-'
      },
    },
    {
      title: 'Факт',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      width: 150,
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: 'План',
      dataIndex: 'planned_amount',
      key: 'planned_amount',
      width: 150,
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: 'Отклонение',
      dataIndex: 'variance',
      key: 'variance',
      width: 150,
      render: (_: any, record: RevenueActual) => {
        const variance = record.variance || 0
        const isPositive = variance >= 0
        return (
          <Space>
            {isPositive ? (
              <ArrowUpOutlined style={{ color: '#52c41a' }} />
            ) : (
              <ArrowDownOutlined style={{ color: '#f5222d' }} />
            )}
            <span style={{ color: isPositive ? '#52c41a' : '#f5222d' }}>
              {formatCurrency(Math.abs(variance))}
            </span>
          </Space>
        )
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: RevenueActual) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          </Tooltip>
          <Tooltip title="Удалить">
            <Popconfirm
              title="Удалить фактический доход?"
              description="Это действие нельзя отменить"
              onConfirm={() => handleDelete(record.id)}
              okText="Удалить"
              cancelText="Отмена"
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  // Calculate totals
  const totalActual = actuals?.reduce((sum, a) => sum + Number(a.actual_amount), 0) || 0
  const totalPlanned = actuals?.reduce((sum, a) => sum + Number(a.planned_amount || 0), 0) || 0
  const totalVariance = totalActual - totalPlanned

  return (
    <div>
      <Title level={2}>Фактические доходы</Title>

      {/* Year selector and summary */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Select
            value={year}
            onChange={setYear}
            style={{ width: '100%' }}
            options={[
              { value: 2024, label: '2024' },
              { value: 2025, label: '2025' },
              { value: 2026, label: '2026' },
            ]}
          />
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>Факт за год</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: '#52c41a' }}>
              {formatCurrency(totalActual)}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>План за год</div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>{formatCurrency(totalPlanned)}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>Отклонение</div>
            <div
              style={{
                fontSize: 18,
                fontWeight: 600,
                color: totalVariance >= 0 ? '#52c41a' : '#f5222d',
              }}
            >
              {formatCurrency(totalVariance)}
            </div>
          </Card>
        </Col>
      </Row>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Добавить доход
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={actuals}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
          }}
        />
      </Card>

      <Modal
        title={editingActual ? 'Редактировать фактический доход' : 'Добавить фактический доход'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingActual(null)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="year"
                label="Год"
                rules={[{ required: true, message: 'Выберите год' }]}
              >
                <Select
                  options={[
                    { value: 2024, label: '2024' },
                    { value: 2025, label: '2025' },
                    { value: 2026, label: '2026' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="month"
                label="Месяц"
                rules={[{ required: true, message: 'Выберите месяц' }]}
              >
                <Select
                  options={Array.from({ length: 12 }, (_, i) => ({
                    value: i + 1,
                    label: getMonthName(i + 1),
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="revenue_stream_id" label="Поток доходов">
            <Select
              placeholder="Выберите поток"
              allowClear
              showSearch
              optionFilterProp="label"
              options={streams?.map((s) => ({ value: s.id, label: s.name }))}
            />
          </Form.Item>

          <Form.Item name="revenue_category_id" label="Категория доходов">
            <Select
              placeholder="Выберите категорию"
              allowClear
              showSearch
              optionFilterProp="label"
              options={categories?.map((c) => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="actual_amount"
                label="Фактическая сумма"
                rules={[{ required: true, message: 'Введите сумму' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="0.00"
                  min={0}
                  step={1000}
                  formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(value) => value?.replace(/\s/g, '') as any}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="planned_amount" label="Плановая сумма">
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="0.00"
                  min={0}
                  step={1000}
                  formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(value) => value?.replace(/\s/g, '') as any}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="comment" label="Комментарий">
            <Input.TextArea rows={3} placeholder="Дополнительная информация" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RevenueActualsPage
