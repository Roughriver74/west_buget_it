import React from 'react'
import { Modal, message, Form } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import CategoryForm from './CategoryForm'

interface CategoryCreateModalProps {
  open: boolean
  onClose: () => void
}

const CategoryCreateModal: React.FC<CategoryCreateModalProps> = ({ open, onClose }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      message.success('Статья расходов успешно создана!')
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
      <CategoryForm form={form} onFinish={handleFinish} />
    </Modal>
  )
}

export default CategoryCreateModal
