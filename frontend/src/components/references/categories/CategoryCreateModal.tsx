import React, { useEffect } from 'react'
import { Modal, message, Form } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import CategoryForm from './CategoryForm'
import type { BudgetCategory } from '@/types'

interface CategoryCreateModalProps {
  open: boolean
  onClose: () => void
  initialName?: string
  onCreated?: (category: BudgetCategory) => void
}

const CategoryCreateModal: React.FC<CategoryCreateModalProps> = ({ open, onClose, initialName, onCreated }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Статья расходов успешно создана!')
      onCreated?.(data)
      onClose()
      form.resetFields()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Произошла ошибка'
      message.error(`Ошибка при создании: ${errorMessage}`)
    },
  })

  const handleFinish = (values: any) => {
    createMutation.mutate(values)
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  useEffect(() => {
    if (open && initialName) {
      form.setFieldsValue({ name: initialName })
    }
  }, [open, initialName, form])

  return (
    <Modal
      title="Создать статью расходов"
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={createMutation.isPending}
      width={600}
      okText="Создать"
      cancelText="Отмена"
    >
      <CategoryForm form={form} onFinish={handleFinish} initialValues={{ name: initialName }} />
    </Modal>
  )
}

export default CategoryCreateModal
