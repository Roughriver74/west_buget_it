import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography,
  Card,
  Space,
  Button,
  Table,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { revenueStreamsApi } from '@/api'
import type {
  RevenueStream,
  RevenueStreamCreate,
  RevenueStreamUpdate,
  RevenueStreamType,
} from '@/types/revenue'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title } = Typography

const RevenueStreamsPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingStream, setEditingStream] = useState<RevenueStream | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [form] = Form.useForm()

  // Fetch revenue streams
  const { data: streams, isLoading, error } = useQuery({
    queryKey: ['revenue-streams', selectedDepartment?.id],
    queryFn: () => revenueStreamsApi.getAll({ department_id: selectedDepartment?.id }),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: RevenueStreamCreate) => revenueStreamsApi.create(data),
    onSuccess: () => {
      message.success('Поток доходов создан')
      queryClient.invalidateQueries({ queryKey: ['revenue-streams'] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании потока доходов')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RevenueStreamUpdate }) =>
      revenueStreamsApi.update(id, data),
    onSuccess: () => {
      message.success('Поток доходов обновлен')
      queryClient.invalidateQueries({ queryKey: ['revenue-streams'] })
      setIsModalOpen(false)
      setEditingStream(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении потока доходов')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => revenueStreamsApi.delete(id),
    onSuccess: () => {
      message.success('Поток доходов удален')
      queryClient.invalidateQueries({ queryKey: ['revenue-streams'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении потока доходов')
    },
  })

  // Bulk update mutation
  const bulkUpdateMutation = useMutation({
    mutationFn: (params: { ids: number[]; is_active?: boolean }) =>
      revenueStreamsApi.bulkUpdate(params),
    onSuccess: () => {
      message.success('Потоки доходов обновлены')
      queryClient.invalidateQueries({ queryKey: ['revenue-streams'] })
      setSelectedRowKeys([])
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении потоков доходов')
    },
  })

  const handleCreate = () => {
    setEditingStream(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (stream: RevenueStream) => {
    setEditingStream(stream)
    form.setFieldsValue(stream)
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // Add selected department_id to ensure multi-tenancy
      const dataWithDepartment = {
        ...values,
        department_id: selectedDepartment?.id,
      }

      if (editingStream) {
        updateMutation.mutate({ id: editingStream.id, data: dataWithDepartment })
      } else {
        createMutation.mutate(dataWithDepartment)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleBulkActivate = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите потоки для активации')
      return
    }
    bulkUpdateMutation.mutate({ ids: selectedRowKeys as number[], is_active: true })
  }

  const handleBulkDeactivate = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите потоки для деактивации')
      return
    }
    bulkUpdateMutation.mutate({ ids: selectedRowKeys as number[], is_active: false })
  }

  const getStreamTypeLabel = (type: RevenueStreamType) => {
    const labels = {
      REGIONAL: 'Региональный',
      CHANNEL: 'Канал продаж',
      PRODUCT: 'Продуктовый',
    }
    return labels[type]
  }

  const getStreamTypeColor = (type: RevenueStreamType) => {
    const colors = {
      REGIONAL: 'blue',
      CHANNEL: 'green',
      PRODUCT: 'orange',
    }
    return colors[type]
  }

  const columns = [
    {
      title: 'Код',
      dataIndex: 'code',
      key: 'code',
      width: 100,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Тип',
      dataIndex: 'stream_type',
      key: 'stream_type',
      width: 150,
      render: (type: RevenueStreamType) => (
        <Tag color={getStreamTypeColor(type)}>{getStreamTypeLabel(type)}</Tag>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Активен' : 'Неактивен'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: RevenueStream) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Удалить">
            <Popconfirm
              title="Удалить поток доходов?"
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

  return (
    <div>
      <Title level={2}>Потоки доходов</Title>

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Создать поток
          </Button>
          <Button
            icon={<CheckOutlined />}
            onClick={handleBulkActivate}
            disabled={selectedRowKeys.length === 0}
            loading={bulkUpdateMutation.isPending}
          >
            Активировать выбранные
          </Button>
          <Button
            icon={<CloseOutlined />}
            onClick={handleBulkDeactivate}
            disabled={selectedRowKeys.length === 0}
            loading={bulkUpdateMutation.isPending}
          >
            Деактивировать выбранные
          </Button>
        </Space>

        <Table
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          columns={columns}
          dataSource={streams}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
          }}
        />
      </Card>

      <Modal
        title={editingStream ? 'Редактировать поток доходов' : 'Создать поток доходов'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingStream(null)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            name="code"
            label="Код"
            rules={[{ required: true, message: 'Введите код потока' }]}
          >
            <Input placeholder="Например: SPB" />
          </Form.Item>

          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название потока' }]}
          >
            <Input placeholder="Например: СПБ и ЛО" />
          </Form.Item>

          <Form.Item
            name="stream_type"
            label="Тип потока"
            rules={[{ required: true, message: 'Выберите тип потока' }]}
          >
            <Select
              placeholder="Выберите тип"
              options={[
                { value: 'REGIONAL', label: 'Региональный' },
                { value: 'CHANNEL', label: 'Канал продаж' },
                { value: 'PRODUCT', label: 'Продуктовый' },
              ]}
            />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} placeholder="Описание потока доходов" />
          </Form.Item>

          {!editingStream && (
            <Form.Item name="department_id" label="Отдел" hidden>
              <Input type="hidden" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default RevenueStreamsPage
