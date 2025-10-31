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
import { revenueCategoriesApi } from '@/api'
import type {
  RevenueCategory,
  RevenueCategoryCreate,
  RevenueCategoryUpdate,
  RevenueCategoryType,
} from '@/types/revenue'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title } = Typography

const RevenueCategoriesPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<RevenueCategory | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [form] = Form.useForm()

  // Fetch revenue categories
  const { data: categories, isLoading, error } = useQuery({
    queryKey: ['revenue-categories', selectedDepartment?.id],
    queryFn: () => revenueCategoriesApi.getAll({ department_id: selectedDepartment?.id }),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: RevenueCategoryCreate) => revenueCategoriesApi.create(data),
    onSuccess: () => {
      message.success('Категория доходов создана')
      queryClient.invalidateQueries({ queryKey: ['revenue-categories'] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании категории')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RevenueCategoryUpdate }) =>
      revenueCategoriesApi.update(id, data),
    onSuccess: () => {
      message.success('Категория доходов обновлена')
      queryClient.invalidateQueries({ queryKey: ['revenue-categories'] })
      setIsModalOpen(false)
      setEditingCategory(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении категории')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => revenueCategoriesApi.delete(id),
    onSuccess: () => {
      message.success('Категория доходов удалена')
      queryClient.invalidateQueries({ queryKey: ['revenue-categories'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении категории')
    },
  })

  // Bulk update mutation
  const bulkUpdateMutation = useMutation({
    mutationFn: (params: { ids: number[]; is_active?: boolean }) =>
      revenueCategoriesApi.bulkUpdate(params),
    onSuccess: () => {
      message.success('Категории доходов обновлены')
      queryClient.invalidateQueries({ queryKey: ['revenue-categories'] })
      setSelectedRowKeys([])
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении категорий')
    },
  })

  const handleCreate = () => {
    setEditingCategory(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (category: RevenueCategory) => {
    setEditingCategory(category)
    form.setFieldsValue(category)
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingCategory) {
        updateMutation.mutate({ id: editingCategory.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleBulkActivate = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите категории для активации')
      return
    }
    bulkUpdateMutation.mutate({ ids: selectedRowKeys as number[], is_active: true })
  }

  const handleBulkDeactivate = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите категории для деактивации')
      return
    }
    bulkUpdateMutation.mutate({ ids: selectedRowKeys as number[], is_active: false })
  }

  const getCategoryTypeLabel = (type: RevenueCategoryType) => {
    const labels = {
      PRODUCT: 'Продукция',
      SERVICE: 'Услуги',
      EQUIPMENT: 'Оборудование',
      TENDER: 'Тендеры',
    }
    return labels[type]
  }

  const getCategoryTypeColor = (type: RevenueCategoryType) => {
    const colors = {
      PRODUCT: 'blue',
      SERVICE: 'green',
      EQUIPMENT: 'orange',
      TENDER: 'purple',
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
      dataIndex: 'category_type',
      key: 'category_type',
      width: 150,
      render: (type: RevenueCategoryType) => (
        <Tag color={getCategoryTypeColor(type)}>{getCategoryTypeLabel(type)}</Tag>
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
          {isActive ? 'Активна' : 'Неактивна'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: RevenueCategory) => (
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
              title="Удалить категорию доходов?"
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
      <Title level={2}>Категории доходов</Title>

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Создать категорию
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
          dataSource={categories}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
          }}
        />
      </Card>

      <Modal
        title={editingCategory ? 'Редактировать категорию доходов' : 'Создать категорию доходов'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingCategory(null)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            name="code"
            label="Код"
            rules={[{ required: true, message: 'Введите код категории' }]}
          >
            <Input placeholder="Например: ORTHO" />
          </Form.Item>

          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название категории' }]}
          >
            <Input placeholder="Например: Ортодонтия" />
          </Form.Item>

          <Form.Item
            name="category_type"
            label="Тип категории"
            rules={[{ required: true, message: 'Выберите тип категории' }]}
          >
            <Select
              placeholder="Выберите тип"
              options={[
                { value: 'PRODUCT', label: 'Продукция' },
                { value: 'SERVICE', label: 'Услуги' },
                { value: 'EQUIPMENT', label: 'Оборудование' },
                { value: 'TENDER', label: 'Тендеры' },
              ]}
            />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} placeholder="Описание категории доходов" />
          </Form.Item>

          {!editingCategory && (
            <Form.Item name="department_id" label="Отдел" hidden>
              <Input type="hidden" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default RevenueCategoriesPage
