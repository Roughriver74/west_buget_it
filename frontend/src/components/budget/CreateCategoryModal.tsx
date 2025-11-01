/**
 * Create Category Modal
 * Quick modal for creating new budget categories
 */
import React from 'react'
import { Modal, Form, Input, Select, message } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api/categories'
import { ExpenseType } from '@/types/budgetPlanning'

interface CreateCategoryModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
  categories?: Array<{
    id: number
    name: string
    type: ExpenseType
    parentId: number | null
  }>
}

export const CreateCategoryModal: React.FC<CreateCategoryModalProps> = ({
  open,
  onClose,
  onSuccess,
  categories = [],
}) => {
  const queryClient = useQueryClient()
  const [form] = Form.useForm()

  // Create category mutation
  const createCategoryMutation = useMutation({
    mutationFn: (data: { name: string; type: ExpenseType; parent_id?: number | null }) =>
      categoriesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Категория создана успешно')
      form.resetFields()
      onClose()
      onSuccess?.()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании категории')
    },
  })

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      await createCategoryMutation.mutateAsync({
        name: values.name,
        type: values.type,
        parent_id: values.parent_id || null,
      })
    } catch (error) {
      console.error('Validation error:', error)
    }
  }

  const handleClose = () => {
    form.resetFields()
    onClose()
  }

  // Get parent category options
  const parentCategoryOptions = categories
    .filter(cat => {
      // Include root categories and categories that have children
      const hasChildren = categories.some(c => c.parentId === cat.id)
      return hasChildren || cat.parentId === null
    })
    .map(cat => ({
      label: cat.name,
      value: cat.id,
    }))

  return (
    <Modal
      open={open}
      title="Создать новую категорию"
      width={600}
      onCancel={handleClose}
      onOk={handleCreate}
      confirmLoading={createCategoryMutation.isPending}
      okText="Создать"
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
        style={{ marginTop: 24 }}
      >
        <Form.Item
          name="name"
          label="Название категории"
          rules={[
            { required: true, message: 'Введите название категории' },
            { min: 2, message: 'Минимум 2 символа' },
            { max: 255, message: 'Максимум 255 символов' },
          ]}
        >
          <Input
            placeholder="Например: Облачные сервисы, Лицензии ПО"
            autoFocus
          />
        </Form.Item>

        <Form.Item
          name="type"
          label="Тип расходов"
          rules={[{ required: true, message: 'Выберите тип расходов' }]}
          tooltip="OPEX - операционные расходы, CAPEX - капитальные расходы"
        >
          <Select placeholder="Выберите тип расходов">
            <Select.Option value={ExpenseType.OPEX}>
              <div>
                <div style={{ fontWeight: 500 }}>OPEX</div>
                <div style={{ fontSize: 12, color: '#999' }}>Операционные расходы</div>
              </div>
            </Select.Option>
            <Select.Option value={ExpenseType.CAPEX}>
              <div>
                <div style={{ fontWeight: 500 }}>CAPEX</div>
                <div style={{ fontSize: 12, color: '#999' }}>Капитальные расходы</div>
              </div>
            </Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="parent_id"
          label="Родительская категория"
          tooltip="Оставьте пустым для создания корневой категории"
        >
          <Select
            placeholder="Выберите родительскую категорию (опционально)"
            allowClear
            options={parentCategoryOptions}
            showSearch
            optionFilterProp="label"
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}
