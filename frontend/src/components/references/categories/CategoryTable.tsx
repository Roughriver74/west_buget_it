import React, { useState } from 'react'
import { Table, Button, Space, Tag, Popconfirm, message, Select, Radio } from 'antd'
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import type { BudgetCategory, ExpenseType } from '@/types'
import CategoryCreateModal from './CategoryCreateModal'
import CategoryEditModal from './CategoryEditModal'

const { Option } = Select

const CategoryTable: React.FC = () => {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<BudgetCategory | null>(null)
  const [typeFilter, setTypeFilter] = useState<ExpenseType | 'ALL'>('ALL')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)

  const queryClient = useQueryClient()

  // Загрузка категорий
  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories', { is_active: activeFilter }],
    queryFn: () => categoriesApi.getAll({ is_active: activeFilter }),
  })

  // Удаление категории
  const deleteMutation = useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Статья расходов успешно удалена!')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Произошла ошибка'
      message.error(`Ошибка при удалении: ${errorMessage}`)
    },
  })

  const handleEdit = (category: BudgetCategory) => {
    setSelectedCategory(category)
    setEditModalOpen(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  // Фильтрация по типу на клиенте
  const filteredCategories = categories?.filter((cat) => {
    if (typeFilter === 'ALL') return true
    return cat.type === typeFilter
  })

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: ExpenseType) => (
        <Tag color={type === 'OPEX' ? 'blue' : 'green'}>{type}</Tag>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '—',
    },
    {
      title: 'Активна',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Да' : 'Нет'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: BudgetCategory) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить статью расходов?"
            description="Это действие нельзя отменить. Все связанные данные будут потеряны."
            onConfirm={() => handleDelete(record.id)}
            okText="Удалить"
            cancelText="Отмена"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <span>Тип:</span>
          <Radio.Group value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <Radio.Button value="ALL">Все</Radio.Button>
            <Radio.Button value="OPEX">OPEX</Radio.Button>
            <Radio.Button value="CAPEX">CAPEX</Radio.Button>
          </Radio.Group>

          <span style={{ marginLeft: 16 }}>Статус:</span>
          <Select
            value={activeFilter}
            onChange={setActiveFilter}
            style={{ width: 150 }}
          >
            <Option value={undefined}>Все</Option>
            <Option value={true}>Активные</Option>
            <Option value={false}>Неактивные</Option>
          </Select>
        </Space>

        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalOpen(true)}
        >
          Добавить статью
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={filteredCategories}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total} статей`,
        }}
      />

      <CategoryCreateModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
      />

      <CategoryEditModal
        open={editModalOpen}
        category={selectedCategory}
        onClose={() => {
          setEditModalOpen(false)
          setSelectedCategory(null)
        }}
      />
    </div>
  )
}

export default CategoryTable
