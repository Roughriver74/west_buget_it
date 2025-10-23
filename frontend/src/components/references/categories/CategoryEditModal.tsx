import React, { useEffect } from 'react'
import { Modal, message, Form } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import type { BudgetCategory } from '@/types'
import CategoryForm from './CategoryForm'

interface CategoryEditModalProps {
  open: boolean
  category: BudgetCategory | null
  onClose: () => void
}

const CategoryEditModal: React.FC<CategoryEditModalProps> = ({ open, category, onClose }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (category && open) {
      form.setFieldsValue({
        name: category.name,
        type: category.type,
        description: category.description,
        is_active: category.is_active,
        parent_id: category.parent_id,
      })
    }
  }, [category, open, form])

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<BudgetCategory> }) =>
      categoriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Статья расходов успешно обновлена!')
      onClose()
      form.resetFields()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Произошла ошибка'
      message.error(`Ошибка при обновлении: ${errorMessage}`)
    },
  })

  const handleFinish = (values: any) => {
    if (category) {
      updateMutation.mutate({ id: category.id, data: values })
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      title="Редактировать статью расходов"
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={updateMutation.isPending}
      width={600}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <CategoryForm
        form={form}
        initialValues={category || undefined}
        onFinish={handleFinish}
        currentCategoryId={category?.id}
      />
    </Modal>
  )
}

export default CategoryEditModal
