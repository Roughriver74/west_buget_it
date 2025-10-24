import { useEffect } from 'react'
import { Modal, Form, Input, message, Switch } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { contractorsApi } from '@/api'
import type { Contractor } from '@/types'

const { TextArea } = Input

interface ContractorFormModalProps {
  visible: boolean
  onCancel: () => void
  contractor?: Contractor | null
  mode: 'create' | 'edit'
}

const ContractorFormModal: React.FC<ContractorFormModalProps> = ({
  visible,
  onCancel,
  contractor,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (visible && contractor && mode === 'edit') {
      form.setFieldsValue({
        name: contractor.name,
        inn: contractor.inn || '',
        kpp: contractor.kpp || '',
        email: contractor.email || '',
        phone: contractor.phone || '',
        address: contractor.address || '',
        is_active: contractor.is_active ?? true,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
    }
  }, [visible, contractor, mode, form])

  const createMutation = useMutation({
    mutationFn: (values: any) => contractorsApi.create(values),
    onSuccess: () => {
      message.success('Контрагент успешно создан')
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(`Ошибка при создании: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      contractorsApi.update(id, values),
    onSuccess: () => {
      message.success('Контрагент успешно обновлен')
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
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
      } else if (mode === 'edit' && contractor) {
        updateMutation.mutate({ id: contractor.id, values })
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
      title={mode === 'create' ? 'Создать контрагента' : 'Редактировать контрагента'}
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
          <Input placeholder="Например: ООО Ромашка, ИП Иванов" />
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
          name="email"
          label="Email"
          rules={[
            { type: 'email', message: 'Введите корректный email' },
          ]}
        >
          <Input placeholder="info@company.ru" />
        </Form.Item>

        <Form.Item
          name="phone"
          label="Телефон"
        >
          <Input placeholder="+7 (999) 123-45-67" />
        </Form.Item>

        <Form.Item
          name="address"
          label="Адрес"
        >
          <TextArea
            rows={3}
            placeholder="Юридический адрес"
            maxLength={1000}
            showCount
          />
        </Form.Item>

        <Form.Item name="is_active" label="Активен" valuePropName="checked">
          <Switch checkedChildren="Да" unCheckedChildren="Нет" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default ContractorFormModal
