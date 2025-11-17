import React, { useState } from 'react'
import { Table, Button, Space, Tag, Popconfirm, message, Select, Radio } from 'antd'
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import type { BudgetCategory, ExpenseType } from '@/types'
import CategoryCreateModal from './CategoryCreateModal'
import CategoryEditModal from './CategoryEditModal'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Option } = Select

interface CategoryTableProps {
  selectedRowKeys?: React.Key[]
  onSelectionChange?: (keys: React.Key[]) => void
}

const CategoryTable: React.FC<CategoryTableProps> = ({
  selectedRowKeys = [],
  onSelectionChange,
}) => {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<BudgetCategory | null>(null)
  const [typeFilter, setTypeFilter] = useState<ExpenseType | 'ALL'>('ALL')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const { selectedDepartment } = useDepartment()

  const queryClient = useQueryClient()

  // Загрузка категорий
  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories', { is_active: activeFilter, department_id: selectedDepartment?.id }],
    queryFn: () => categoriesApi.getAll({ is_active: activeFilter, department_id: selectedDepartment?.id }),
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

  // Построение древовидной структуры
  const buildTreeData = (categories: BudgetCategory[]) => {
    if (!categories) return []

    // Фильтрация по типу
    const filtered = categories.filter((cat) => {
      if (typeFilter === 'ALL') return true
      return cat.type === typeFilter
    })

    // Создаём map для быстрого поиска
    const categoryMap = new Map(filtered.map(cat => [cat.id, { ...cat, children: [] }]))

    // Массив для корневых элементов
    const rootCategories: any[] = []

    // Строим дерево
    filtered.forEach(cat => {
      const node = categoryMap.get(cat.id)
      if (!node) return

      if (cat.parent_id && categoryMap.has(cat.parent_id)) {
        // Это подкатегория, добавляем к родителю
        const parent = categoryMap.get(cat.parent_id)
        if (parent && node) {
          (parent.children as any[]).push(node)
        }
      } else {
        // Это корневая категория
        if (node) rootCategories.push(node)
      }
    })

    // Удаляем пустые массивы children
    const cleanTree = (nodes: any[]): any[] => {
      return nodes.map(node => {
        if (node.children.length === 0) {
          const { children: _unusedChildren, ...rest } = node
          return rest
        }
        return {
          ...node,
          children: cleanTree(node.children)
        }
      })
    }

    return cleanTree(rootCategories)
  }

  const treeData = buildTreeData(categories || [])

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      align: 'center' as const,
      render: (type: ExpenseType) => (
        <Tag color={type === 'OPEX' ? 'blue' : 'green'}>{type}</Tag>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
      render: (text: string) => text || '—',
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      align: 'center' as const,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Да' : 'Нет'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
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
        dataSource={treeData}
        loading={isLoading}
        rowKey="id"
        size="middle"
        scroll={{ x: 900 }}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total} статей`,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        expandable={{
          defaultExpandAllRows: false,
        }}
        rowSelection={
          onSelectionChange
            ? {
                selectedRowKeys,
                onChange: onSelectionChange,
                preserveSelectedRowKeys: true,
              }
            : undefined
        }
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
