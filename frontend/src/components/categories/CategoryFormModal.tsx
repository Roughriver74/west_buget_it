import { useEffect } from 'react'
import { Modal, Form, Input, Select, message, Switch } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api'
import type { BudgetCategory } from '@/types'

const { TextArea } = Input
const { Option } = Select

interface CategoryFormModalProps {
  visible: boolean
  onCancel: () => void
  category?: BudgetCategory | null
  mode: 'create' | 'edit'
}

const CategoryFormModal: React.FC<CategoryFormModalProps> = ({
  visible,
  onCancel,
  category,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // Reset form when category changes
  useEffect(() => {
    if (visible && category && mode === 'edit') {
      form.setFieldsValue({
        name: category.name,
        type: category.type,
        description: category.description || '',
        is_active: category.is_active ?? true,
        parent_id: category.parent_id,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
    }
  }, [visible, category, mode, form])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: any) => categoriesApi.create(values),
    onSuccess: () => {
      message.success('Категория успешно создана')
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при создании категории: ${error.message}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      categoriesApi.update(id, values),
    onSuccess: () => {
      message.success('Категория успешно обновлена')
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при обновлении категории: ${error.message}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (mode === 'create') {
        createMutation.mutate(values)
      } else if (mode === 'edit' && category) {
        updateMutation.mutate({ id: category.id, values })
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title={mode === 'create' ? 'Создать категорию' : 'Редактировать категорию'}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText={mode === 'create' ? 'Создать' : 'Сохранить'}
      cancelText="Отмена"
      width={600}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          is_active: true,
          type: 'OPEX',
        }}
      >
        <Form.Item
          name="name"
          label="Название категории"
          rules={[
            { required: true, message: 'Введите название категории' },
            { max: 200, message: 'Максимум 200 символов' },
          ]}
        >
          <Input placeholder="Например: Техника, Связь, Серверы" />
        </Form.Item>

        <Form.Item
          name="type"
          label="Тип расходов"
          rules={[{ required: true, message: 'Выберите тип расходов' }]}
        >
          <Select placeholder="Выберите тип">
            <Option value="OPEX">
              <span style={{ color: '#1890ff' }}>OPEX</span> - Операционные расходы
            </Option>
            <Option value="CAPEX">
              <span style={{ color: '#52c41a' }}>CAPEX</span> - Капитальные расходы
            </Option>
          </Select>
        </Form.Item>

        <Form.Item name="description" label="Описание">
          <TextArea
            rows={3}
            placeholder="Опциональное описание категории"
            maxLength={500}
            showCount
          />
        </Form.Item>

        <Form.Item name="is_active" label="Активна" valuePropName="checked">
          <Switch checkedChildren="Да" unCheckedChildren="Нет" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CategoryFormModal
