import { useEffect } from 'react'
import { Modal, Form, Input, message, Switch } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { departmentsApi } from '@/api'
import type { Department } from '@/contexts/DepartmentContext'
import { useDepartment } from '@/contexts/DepartmentContext'

const { TextArea } = Input

interface DepartmentFormModalProps {
  visible: boolean
  onCancel: () => void
  department?: Department | null
  mode: 'create' | 'edit'
}

const DepartmentFormModal: React.FC<DepartmentFormModalProps> = ({
  visible,
  onCancel,
  department,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const { refreshDepartments } = useDepartment()

  // Reset form when department changes
  useEffect(() => {
    if (visible && department && mode === 'edit') {
      form.setFieldsValue({
        name: department.name,
        code: department.code,
        description: department.description || '',
        ftp_subdivision_name: department.ftp_subdivision_name || '',
        manager_name: department.manager_name || '',
        contact_email: department.contact_email || '',
        contact_phone: department.contact_phone || '',
        is_active: department.is_active ?? true,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
    }
  }, [visible, department, mode, form])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: any) => departmentsApi.create(values),
    onSuccess: async () => {
      message.success('Отдел успешно создан')
      // Force refetch all department queries
      await queryClient.refetchQueries({ queryKey: ['departments'] })
      await refreshDepartments() // Refresh DepartmentContext
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при создании отдела: ${errorMessage}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      departmentsApi.update(id, values),
    onSuccess: async () => {
      message.success('Отдел успешно обновлен')
      // Force refetch all department queries
      await queryClient.refetchQueries({ queryKey: ['departments'] })
      await refreshDepartments() // Refresh DepartmentContext
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при обновлении отдела: ${errorMessage}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (mode === 'create') {
        createMutation.mutate(values)
      } else if (mode === 'edit' && department) {
        updateMutation.mutate({ id: department.id, values })
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
      title={mode === 'create' ? 'Создать отдел' : 'Редактировать отдел'}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText={mode === 'create' ? 'Создать' : 'Сохранить'}
      cancelText="Отмена"
      width={700}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          is_active: true,
        }}
      >
        <Form.Item
          name="name"
          label="Название отдела"
          rules={[
            { required: true, message: 'Введите название отдела' },
            { min: 2, message: 'Минимум 2 символа' },
            { max: 255, message: 'Максимум 255 символов' },
          ]}
        >
          <Input placeholder="Например: IT отдел, Бухгалтерия, Отдел продаж" />
        </Form.Item>

        <Form.Item
          name="code"
          label="Код отдела"
          rules={[
            { required: true, message: 'Введите код отдела' },
            { min: 2, message: 'Минимум 2 символа' },
            { max: 50, message: 'Максимум 50 символов' },
            {
              pattern: /^[A-Za-z0-9_-]+$/,
              message: 'Только латинские буквы, цифры, дефис и подчеркивание'
            },
          ]}
        >
          <Input placeholder="Например: IT, ACC, SALES" />
        </Form.Item>

        <Form.Item name="description" label="Описание">
          <TextArea
            rows={3}
            placeholder="Опциональное описание отдела"
            maxLength={1000}
            showCount
          />
        </Form.Item>

        <Form.Item
          name="ftp_subdivision_name"
          label="Подразделение (для FTP импорта)"
          tooltip="Укажите название подразделения из FTP файла для автоматического сопоставления заявок с этим отделом"
          rules={[
            { max: 255, message: 'Максимум 255 символов' },
          ]}
        >
          <Input placeholder="Например: (ВЕСТ) IT" />
        </Form.Item>

        <Form.Item
          name="manager_name"
          label="Руководитель"
          rules={[
            { max: 200, message: 'Максимум 200 символов' },
          ]}
        >
          <Input placeholder="ФИО руководителя отдела" />
        </Form.Item>

        <Form.Item
          name="contact_email"
          label="Email для связи"
          rules={[
            { type: 'email', message: 'Введите корректный email' },
            { max: 200, message: 'Максимум 200 символов' },
          ]}
        >
          <Input placeholder="email@example.com" />
        </Form.Item>

        <Form.Item
          name="contact_phone"
          label="Телефон для связи"
          rules={[
            { max: 50, message: 'Максимум 50 символов' },
          ]}
        >
          <Input placeholder="+7 (xxx) xxx-xx-xx" />
        </Form.Item>

        <Form.Item name="is_active" label="Активен" valuePropName="checked">
          <Switch checkedChildren="Да" unCheckedChildren="Нет" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default DepartmentFormModal
