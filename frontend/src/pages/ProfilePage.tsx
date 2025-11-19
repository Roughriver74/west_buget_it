import { useEffect } from 'react'
import {
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  Row,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  IdcardOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { profileApi } from '@/api'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Title, Paragraph, Text } = Typography

type ProfileFormValues = {
  full_name: string
  email: string
  phone?: string
  position?: string
}

type PasswordFormValues = {
  old_password: string
  new_password: string
  confirm_password: string
}

const ProfilePage = () => {
  const { user, updateProfile, refreshUser } = useAuth()
  const { departments } = useDepartment()
  const [profileForm] = Form.useForm<ProfileFormValues>()
  const [passwordForm] = Form.useForm<PasswordFormValues>()

  useEffect(() => {
    if (user) {
      profileForm.setFieldsValue({
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || '',
        position: user.position || '',
      })
    }
  }, [user, profileForm])

  const profileMutation = useMutation({
    mutationFn: (values: ProfileFormValues) =>
      updateProfile({
        full_name: values.full_name?.trim() || null,
        email: values.email?.trim() || null,
        phone: values.phone?.trim() || null,
        position: values.position?.trim() || null,
      }),
    onSuccess: () => {
      refreshUser()
    },
  })

  const passwordMutation = useMutation({
    mutationFn: profileApi.changePassword,
    onSuccess: () => {
      message.success('Пароль успешно обновлен')
      passwordForm.resetFields()
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.detail || error.message || 'Не удалось сменить пароль'
      message.error(errorMessage)
    },
  })

  const departmentName = user?.department_id
    ? departments.find((dept) => dept.id === user.department_id)?.name
    : null

  if (!user) {
    return <Spin spinning fullscreen tip="Загружаем профиль..." />
  }

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <UserOutlined /> Профиль пользователя
          </Title>
          <Paragraph type="secondary">
            Обновите контактные данные и пароль для своей учетной записи
          </Paragraph>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={9}>
            <Card>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Space size="large">
                  <Avatar size={72} icon={<UserOutlined />} />
                  <div>
                    <Title level={4} style={{ margin: 0 }}>
                      {user.full_name || user.username}
                    </Title>
                    <Text type="secondary">{user.position || 'Должность не указана'}</Text>
                  </div>
                </Space>

                <Space wrap>
                  <Tag color="blue" icon={<IdcardOutlined />}>
                    {user.role}
                  </Tag>
                  <Tag color={user.is_active ? 'green' : 'default'} icon={<CheckCircleOutlined />}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </Tag>
                  <Tag
                    color={user.is_verified ? 'success' : 'warning'}
                    icon={<SafetyCertificateOutlined />}
                  >
                    {user.is_verified ? 'Подтвержден' : 'Не подтвержден'}
                  </Tag>
                </Space>

                <Divider style={{ margin: '12px 0' }} />

                <Descriptions column={1} size="small" colon={false}>
                  <Descriptions.Item label="Логин">
                    <Text strong>{user.username}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="Email">
                    {user.email || <Text type="secondary">Не указан</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="Телефон">
                    {user.phone || <Text type="secondary">Не указан</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="Отдел">
                    {departmentName || <Text type="secondary">Не привязан</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="Последний вход">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleString('ru-RU')
                      : <Text type="secondary">Нет данных</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="Создан">
                    {new Date(user.created_at).toLocaleString('ru-RU')}
                  </Descriptions.Item>
                  <Descriptions.Item label="Обновлен">
                    {new Date(user.updated_at).toLocaleString('ru-RU')}
                  </Descriptions.Item>
                </Descriptions>

                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refreshUser()}
                  block
                >
                  Обновить данные
                </Button>
              </Space>
            </Card>
          </Col>

          <Col xs={24} lg={15}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Card title="Контактная информация">
                <Form
                  layout="vertical"
                  form={profileForm}
                  onFinish={(values) => profileMutation.mutate(values)}
                >
                  <Form.Item
                    name="full_name"
                    label="Полное имя"
                    rules={[{ required: true, message: 'Укажите имя' }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="Ваше имя" autoComplete="name" />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Укажите email' },
                      { type: 'email', message: 'Некорректный email' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} placeholder="email@company.ru" autoComplete="email" />
                  </Form.Item>
                  <Form.Item name="phone" label="Телефон">
                    <Input prefix={<PhoneOutlined />} placeholder="+7 (___) ___-__-__" autoComplete="tel" />
                  </Form.Item>
                  <Form.Item name="position" label="Должность">
                    <Input prefix={<IdcardOutlined />} placeholder="Ваше положение в компании" />
                  </Form.Item>

                  <Space>
                    <Button type="primary" htmlType="submit" loading={profileMutation.isPending}>
                      Сохранить изменения
                    </Button>
                    <Button onClick={() => profileForm.resetFields()}>Сбросить</Button>
                  </Space>
                </Form>
              </Card>

              <Card title="Смена пароля">
                <Form
                  layout="vertical"
                  form={passwordForm}
                  onFinish={(values) =>
                    passwordMutation.mutate({
                      old_password: values.old_password,
                      new_password: values.new_password,
                    })
                  }
                >
                  <Form.Item
                    name="old_password"
                    label="Текущий пароль"
                    rules={[{ required: true, message: 'Введите текущий пароль' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
                  </Form.Item>
                  <Form.Item
                    name="new_password"
                    label="Новый пароль"
                    rules={[
                      { required: true, message: 'Введите новый пароль' },
                      { min: 6, message: 'Минимум 6 символов' },
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                  </Form.Item>
                  <Form.Item
                    name="confirm_password"
                    label="Подтверждение пароля"
                    dependencies={['new_password']}
                    rules={[
                      { required: true, message: 'Подтвердите пароль' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('new_password') === value) {
                            return Promise.resolve()
                          }
                          return Promise.reject(new Error('Пароли не совпадают'))
                        },
                      }),
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                  </Form.Item>

                  <Space>
                    <Button type="primary" htmlType="submit" loading={passwordMutation.isPending}>
                      Обновить пароль
                    </Button>
                    <Button onClick={() => passwordForm.resetFields()}>Очистить</Button>
                  </Space>
                </Form>
              </Card>
            </Space>
          </Col>
        </Row>
      </Space>
    </div>
  )
}

export default ProfilePage
