import { useEffect } from 'react'
import { Modal, Form, Input, message, Switch, Select } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { usersApi, departmentsApi } from '@/api'
import type { User } from '@/api/users'

const { Option } = Select

interface UserFormModalProps {
  visible: boolean
  onCancel: () => void
  user?: User | null
  mode: 'create' | 'edit'
}

const UserFormModal: React.FC<UserFormModalProps> = ({
  visible,
  onCancel,
  user,
  mode,
}) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // Load departments for selection
  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: () => departmentsApi.getAll({ is_active: true }),
  })

  // Reset form when user changes
  useEffect(() => {
    if (visible && user && mode === 'edit') {
      form.setFieldsValue({
        username: user.username,
        email: user.email,
        full_name: user.full_name || '',
        role: user.role,
        department_id: user.department_id,
        position: user.position || '',
        phone: user.phone || '',
        is_active: user.is_active ?? true,
      })
    } else if (visible && mode === 'create') {
      form.resetFields()
    }
  }, [visible, user, mode, form])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: any) => usersApi.create(values),
    onSuccess: () => {
      message.success('Пользователь успешно создан')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при создании пользователя: ${errorMessage}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) =>
      usersApi.update(id, values),
    onSuccess: () => {
      message.success('Пользователь успешно обновлен')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при обновлении пользователя: ${errorMessage}`)
    },
  })

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (mode === 'create') {
        createMutation.mutate(values)
      } else if (mode === 'edit' && user) {
        // Don't send username and password on update
        const { username, password, ...updateValues } = values
        updateMutation.mutate({ id: user.id, values: updateValues })
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
      title={mode === 'create' ? 'Создать пользователя' : 'Редактировать пользователя'}
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
          role: 'USER',
        }}
      >
        <Form.Item
          name="username"
          label="Имя пользователя (логин)"
          rules={[
            { required: true, message: 'Введите имя пользователя' },
            { min: 3, message: 'Минимум 3 символа' },
            { max: 100, message: 'Максимум 100 символов' },
            {
              pattern: /^[a-zA-Z0-9_.-]+$/,
              message: 'Только латинские буквы, цифры и символы _.-'
            },
          ]}
        >
          <Input placeholder="username" disabled={mode === 'edit'} />
        </Form.Item>

        {mode === 'create' && (
          <Form.Item
            name="password"
            label="Пароль"
            rules={[
              { required: true, message: 'Введите пароль' },
              { min: 6, message: 'Минимум 6 символов' },
              {
                pattern: /^(?=.*[A-Za-z])(?=.*\d)/,
                message: 'Пароль должен содержать буквы и цифры'
              },
            ]}
          >
            <Input.Password placeholder="Минимум 6 символов" />
          </Form.Item>
        )}

        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Введите email' },
            { type: 'email', message: 'Введите корректный email' },
          ]}
        >
          <Input placeholder="user@example.com" />
        </Form.Item>

        <Form.Item
          name="full_name"
          label="Полное имя"
          rules={[
            { max: 255, message: 'Максимум 255 символов' },
          ]}
        >
          <Input placeholder="Иванов Иван Иванович" />
        </Form.Item>

        <Form.Item
          name="role"
          label="Роль"
          rules={[{ required: true, message: 'Выберите роль' }]}
        >
          <Select placeholder="Выберите роль">
            <Option value="USER">
              <span>USER</span> - Пользователь отдела (доступ только к своему отделу)
            </Option>
            <Option value="MANAGER">
              <span>MANAGER</span> - Руководитель (доступ ко всем отделам)
            </Option>
            <Option value="ADMIN">
              <span style={{ color: '#ff4d4f' }}>ADMIN</span> - Администратор (полный доступ)
            </Option>
            <Option value="ACCOUNTANT">
              <span>ACCOUNTANT</span> - Бухгалтер (доступ к финансам)
            </Option>
            <Option value="REQUESTER">
              <span>REQUESTER</span> - Заявитель (создание заявок)
            </Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="department_id"
          label="Отдел"
        >
          <Select
            placeholder="Выберите отдел"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {departments?.map(dept => (
              <Option key={dept.id} value={dept.id}>
                {dept.name} ({dept.code})
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="position"
          label="Должность"
          rules={[
            { max: 200, message: 'Максимум 200 символов' },
          ]}
        >
          <Input placeholder="Например: Менеджер, Бухгалтер" />
        </Form.Item>

        <Form.Item
          name="phone"
          label="Телефон"
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

export default UserFormModal
