import { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Row,
  Segmented,
  Select,
  Space,
  Switch,
  Typography,
  message,
} from 'antd'
import {
  BankOutlined,
  BulbFilled,
  BulbOutlined,
  ColumnHeightOutlined,
  ClearOutlined,
  CloudSyncOutlined,
  PoweroffOutlined,
  ReloadOutlined,
  SettingOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import { useTheme } from '@/contexts/ThemeContext'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { API_OVERRIDE_STORAGE_KEY, getApiBaseUrl, getApiOverride } from '@/config/api'
import { adminConfigApi, type AdminConfig } from '@/api/adminConfig'

const { Title, Paragraph, Text } = Typography

const SettingsPage = () => {
  const { mode, setTheme, componentSize, setComponentSize } = useTheme()
  const { departments, selectedDepartment, setSelectedDepartment, refreshDepartments } = useDepartment()
  const { refreshUser, user, logout } = useAuth()
  const queryClient = useQueryClient()
  const isAdmin = user?.role === 'ADMIN'
  const [apiUrlOverride, setApiUrlOverride] = useState<string>(getApiOverride() || '')
  const [adminForm] = Form.useForm<AdminConfig>()

  const {
    data: adminConfig,
    isLoading: adminConfigLoading,
    isError: adminConfigError,
  } = useQuery<AdminConfig>({
    queryKey: ['admin-config'],
    queryFn: adminConfigApi.get,
    enabled: isAdmin,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (adminConfigError) {
      message.error('Не удалось загрузить конфигурацию администратора')
    }
  }, [adminConfigError])

  useEffect(() => {
    if (adminConfig) {
      adminForm.setFieldsValue(adminConfig)
    }
  }, [adminConfig, adminForm])

  const adminUpdateMutation = useMutation({
    mutationFn: adminConfigApi.update,
    onSuccess: (data) => {
      queryClient.setQueryData(['admin-config'], data)
      adminForm.setFieldsValue(data)
      message.success('Настройки сохранены')
    },
    onError: () => message.error('Не удалось сохранить настройки'),
  })

  const refreshUserMutation = useMutation({
    mutationFn: refreshUser,
    onSuccess: () => message.success('Данные профиля обновлены'),
    onError: () => message.error('Не удалось обновить данные профиля'),
  })

  const refreshDepartmentsMutation = useMutation({
    mutationFn: refreshDepartments,
    onSuccess: () => message.success('Список отделов обновлен'),
    onError: () => message.error('Не удалось обновить список отделов'),
  })

  const handleResetPreferences = () => {
    setTheme('light')
    setComponentSize('middle')
    message.success('Настройки интерфейса сброшены на значения по умолчанию')
  }

  const handleClearCache = () => {
    const token = localStorage.getItem('token')
    queryClient.clear()
    localStorage.removeItem('selectedDepartmentId')
    localStorage.removeItem('app-theme-mode')
    localStorage.removeItem('app-component-size')
    localStorage.removeItem(API_OVERRIDE_STORAGE_KEY)

    if (token) {
      localStorage.setItem('token', token)
    }

    message.success('Кэш и сохраненные настройки очищены')
  }

  const handleInvalidateQueries = () => {
    queryClient.invalidateQueries()
    message.success('Кэш запросов помечен на обновление')
  }

  const handleAdminFullReset = () => {
    queryClient.clear()
    localStorage.clear()
    sessionStorage.clear()
    message.success('Локальные данные очищены. Перенаправляем на вход...')
    logout()
    window.location.href = '/login'
  }

  const handleSaveApiOverride = () => {
    const trimmed = apiUrlOverride.trim()
    if (!trimmed) {
      localStorage.removeItem(API_OVERRIDE_STORAGE_KEY)
      message.success('Override API URL удален, используется стандартная конфигурация')
      return
    }

    if (!(trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('/'))) {
      message.error('Введите абсолютный URL (http/https) или путь начиная с "/"')
      return
    }

    localStorage.setItem(API_OVERRIDE_STORAGE_KEY, trimmed)
    message.success('Override API URL сохранен. Новые запросы будут использовать новое значение')
  }

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <SettingOutlined /> Настройки
          </Title>
          <Paragraph type="secondary">
            Управляйте внешним видом приложения и локальными предпочтениями для вашей учетной записи
          </Paragraph>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="Интерфейс">
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                  <Text strong>Тема</Text>
                  <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                    Переключение светлой и темной тем обеспечит комфортную работу в разных условиях
                  </Paragraph>
                  <Segmented
                    options={[
                      { label: 'Светлая', value: 'light', icon: <BulbOutlined /> },
                      { label: 'Темная', value: 'dark', icon: <BulbFilled /> },
                    ]}
                    value={mode}
                    onChange={(value) => setTheme(value as 'light' | 'dark')}
                  />
                </div>

                <div>
                  <Text strong>Размер элементов</Text>
                  <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                    Управляйте плотностью таблиц и форм — настройки применяются ко всему интерфейсу
                  </Paragraph>
                  <Segmented
                    value={componentSize}
                    onChange={(value) => setComponentSize(value as 'small' | 'middle' | 'large')}
                    options={[
                      { label: 'Компактный', value: 'small', icon: <ColumnHeightOutlined /> },
                      { label: 'Стандарт', value: 'middle', icon: <ColumnHeightOutlined /> },
                      { label: 'Крупный', value: 'large', icon: <ColumnHeightOutlined /> },
                    ]}
                  />
                </div>

                <Space>
                  <Button onClick={handleResetPreferences}>Сбросить интерфейс</Button>
                  <Button danger onClick={handleClearCache}>
                    Очистить локальные данные
                  </Button>
                </Space>
              </Space>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="Работа с отделами">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text strong>Отдел по умолчанию</Text>
                  <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                    Выбранный отдел используется во всех фильтрах и запросах
                  </Paragraph>
                  <Select
                    showSearch
                    placeholder="Выберите отдел"
                    value={selectedDepartment?.id}
                    onChange={(value) => {
                      const dept = departments.find((item) => item.id === value) || null
                      setSelectedDepartment(dept)
                      if (dept) {
                        message.success(`Отдел "${dept.name}" выбран по умолчанию`)
                      }
                    }}
                    style={{ width: '100%' }}
                    options={departments.map((dept) => ({
                      label: dept.name,
                      value: dept.id,
                    }))}
                    optionFilterProp="label"
                  />
                </div>

                <Space>
                  <Button
                    icon={<ReloadOutlined />}
                    loading={refreshDepartmentsMutation.isPending}
                    onClick={() => refreshDepartmentsMutation.mutate()}
                  >
                    Обновить список отделов
                  </Button>
                  <Button
                    icon={<ToolOutlined />}
                    loading={refreshUserMutation.isPending}
                    onClick={() => refreshUserMutation.mutate()}
                  >
                    Перезагрузить профиль
                  </Button>
                </Space>

                <Descriptions size="small" column={1} title="Текущие значения">
                  <Descriptions.Item label="Отдел">
                    {selectedDepartment ? (
                      <Space>
                        <BankOutlined />
                        <span>{selectedDepartment.name}</span>
                      </Space>
                    ) : (
                      <Text type="secondary">Не выбран</Text>
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="API">
                    <Text code>{getApiBaseUrl()}</Text>
                  </Descriptions.Item>
                </Descriptions>
              </Space>
            </Card>
          </Col>

          {isAdmin && (
            <Col xs={24}>
              <Card title="Администрирование">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Descriptions size="small" column={2}>
                    <Descriptions.Item label="Роль">
                      <Text strong>{user?.role}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="API">
                      <Text code>{getApiBaseUrl()}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="API override">
                      <Text code>{getApiOverride() || 'not set'}</Text>
                    </Descriptions.Item>
                  </Descriptions>

                  <Card size="small" type="inner" title="Override API URL (локально)">
                    <Form layout="vertical" onFinish={handleSaveApiOverride}>
                      <Form.Item
                        label="Базовый API URL"
                        tooltip='Абсолютный URL (https://api.example.com) или путь "/api/v1"'
                      >
                        <Input
                          placeholder="Пример: https://api.example.com/api/v1"
                          value={apiUrlOverride}
                          onChange={(e) => setApiUrlOverride(e.target.value)}
                        />
                      </Form.Item>
                      <Space>
                        <Button type="primary" htmlType="submit">
                          Сохранить override
                        </Button>
                        <Button
                          onClick={() => {
                            setApiUrlOverride('')
                            localStorage.removeItem(API_OVERRIDE_STORAGE_KEY)
                            message.success('Override удален')
                          }}
                        >
                          Сбросить override
                        </Button>
                      </Space>
                    </Form>
                  </Card>

                  <Card
                    size="small"
                    type="inner"
                    title="Настройки бэкенда (редактируемые)"
                    loading={adminConfigLoading}
                  >
                    <Form
                      form={adminForm}
                      layout="vertical"
                      onFinish={(values) => adminUpdateMutation.mutate(values)}
                      initialValues={adminConfig}
                    >
                      <Row gutter={[16, 16]}>
                        <Col xs={24} md={12}>
                          <Card size="small" bordered={false} title="1C OData">
                            <Form.Item name="odata_url" label="URL" rules={[{ required: true }]}>
                              <Input placeholder="http://..." />
                            </Form.Item>
                            <Form.Item name="odata_username" label="Username">
                              <Input placeholder="odata user" />
                            </Form.Item>
                            <Form.Item name="odata_password" label="Password">
                              <Input placeholder="Пароль 1C" />
                            </Form.Item>
                            <Form.Item name="odata_custom_auth_token" label="Custom token">
                              <Input placeholder="Basic ..." />
                            </Form.Item>
                          </Card>

                          <Card size="small" bordered={false} title="VseGPT">
                            <Form.Item name="vsegpt_api_key" label="API key">
                              <Input placeholder="API ключ" />
                            </Form.Item>
                            <Form.Item name="vsegpt_base_url" label="Base URL">
                              <Input placeholder="https://api.vsegpt.ru/v1" />
                            </Form.Item>
                            <Form.Item name="vsegpt_model" label="Model">
                              <Input placeholder="Модель" />
                            </Form.Item>
                          </Card>
                        </Col>

                        <Col xs={24} md={12}>
                          <Card size="small" bordered={false} title="Credit Portfolio FTP">
                            <Form.Item name="credit_portfolio_ftp_host" label="Host">
                              <Input placeholder="ftp.example.com" />
                            </Form.Item>
                            <Form.Item name="credit_portfolio_ftp_user" label="User">
                              <Input placeholder="ftp user" />
                            </Form.Item>
                            <Form.Item name="credit_portfolio_ftp_password" label="Password">
                              <Input placeholder="ftp password" />
                            </Form.Item>
                            <Form.Item name="credit_portfolio_ftp_remote_dir" label="Remote dir">
                              <Input placeholder="/path" />
                            </Form.Item>
                            <Form.Item name="credit_portfolio_ftp_local_dir" label="Local dir">
                              <Input placeholder="data/credit_portfolio" />
                            </Form.Item>
                          </Card>

                          <Card size="small" bordered={false} title="Scheduler">
                            <Form.Item name="app_name" label="APP_NAME">
                              <Input placeholder="Budget Manager" />
                            </Form.Item>
                            <Form.Item name="scheduler_enabled" label="Scheduler enabled" valuePropName="checked">
                              <Switch />
                            </Form.Item>
                            <Form.Item
                              name="credit_portfolio_import_enabled"
                              label="Credit portfolio import enabled"
                              valuePropName="checked"
                            >
                              <Switch />
                            </Form.Item>
                            <Form.Item label="Время импорта (часы/минуты)" style={{ marginBottom: 0 }}>
                              <Space>
                                <Form.Item
                                  name="credit_portfolio_import_hour"
                                  style={{ marginBottom: 0 }}
                                  rules={[{ type: 'number', min: 0, max: 23 }]}
                                >
                                  <InputNumber min={0} max={23} placeholder="HH" />
                                </Form.Item>
                                <Form.Item
                                  name="credit_portfolio_import_minute"
                                  style={{ marginBottom: 0 }}
                                  rules={[{ type: 'number', min: 0, max: 59 }]}
                                >
                                  <InputNumber min={0} max={59} placeholder="MM" />
                                </Form.Item>
                              </Space>
                            </Form.Item>
                          </Card>
                        </Col>
                      </Row>

                      <Space>
                        <Button type="primary" htmlType="submit" loading={adminUpdateMutation.isPending}>
                          Сохранить настройки
                        </Button>
                        <Button onClick={() => adminForm.resetFields()} disabled={adminUpdateMutation.isPending}>
                          Сбросить форму
                        </Button>
                      </Space>
                    </Form>
                  </Card>

                  <Space wrap>
                    <Button icon={<CloudSyncOutlined />} onClick={handleInvalidateQueries}>
                      Перезапросить данные (invalidate cache)
                    </Button>
                    <Button icon={<ClearOutlined />} danger onClick={handleClearCache}>
                      Очистить кэш без выхода
                    </Button>
                    <Button
                      icon={<PoweroffOutlined />}
                      danger
                      type="primary"
                      onClick={handleAdminFullReset}
                    >
                      Полный сброс и выход
                    </Button>
                  </Space>
                </Space>
              </Card>
            </Col>
          )}
        </Row>
      </Space>
    </div>
  )
}

export default SettingsPage
