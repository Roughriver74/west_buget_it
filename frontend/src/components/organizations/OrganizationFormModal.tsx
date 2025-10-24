import { useEffect } from 'react'
import { Modal, Form, Input, message, Switch } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { organizationsApi } from '@/api'
import type { Organization } from '@/types'

const { TextArea } = Input

interface OrganizationFormModalProps {
  visible: boolean
  onCancel: () => void
  organization?: Organization | null
  mode: 'create' | 'edit'
}

const OrganizationFormModal: React.FC<OrganizationFormModalProps> = ({
  visible,
  onCancel,
  organization,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (visible && organization && mode === 'edit') {
      form.setFieldsValue({
        name: organization.name,
        inn: organization.inn || '',
        kpp: organization.kpp || '',
        address: organization.address || '',
        is_active: organization.is_active ?? true,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
    }
  }, [visible, organization, mode, form])

  const createMutation = useMutation({
    mutationFn: (values: any) => organizationsApi.create(values),
    onSuccess: () => {
      message.success('Организация успешно создана')
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при создании: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      organizationsApi.update(id, values),
    onSuccess: () => {
      message.success('Организация успешно обновлена')
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при обновлении: ${error.message}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (mode === 'create') {
        createMutation.mutate(values)
      } else if (mode === 'edit' && organization) {
        updateMutation.mutate({ id: organization.id, values })
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
      title={mode === 'create' ? 'Создать организацию' : 'Редактировать организацию'}
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
          label="Название"
          rules={[
            { required: true, message: 'Введите название' },
            { max: 500, message: 'Максимум 500 символов' },
          ]}
        >
          <Input placeholder="Например: ООО Компания, АО Предприятие" />
        </Form.Item>

        <Form.Item
          name="inn"
          label="ИНН"
          rules={[
            { pattern: /^\d{10,12}$/, message: 'ИНН должен содержать 10 или 12 цифр' },
          ]}
        >
          <Input placeholder="1234567890" maxLength={12} />
        </Form.Item>

        <Form.Item
          name="kpp"
          label="КПП"
          rules={[
            { pattern: /^\d{9}$/, message: 'КПП должен содержать 9 цифр' },
          ]}
        >
          <Input placeholder="123456789" maxLength={9} />
        </Form.Item>

        <Form.Item
          name="address"
          label="Юридический адрес"
        >
          <TextArea
            rows={3}
            placeholder="Полный юридический адрес организации"
            maxLength={1000}
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

export default OrganizationFormModal
