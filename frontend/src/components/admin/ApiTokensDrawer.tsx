import { useState } from 'react'
import {
  Drawer,
  Button,
  Table,
  Space,
  Tag,
  Popconfirm,
  Form,
  Input,
  Select,
  DatePicker,
  message,
  Modal,
  Typography,
  Alert,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  StopOutlined,
  CopyOutlined,
  KeyOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTokens, createToken, updateToken, deleteToken, revokeToken } from '@/api/apiTokens'
import type { APIToken, CreateTokenRequest, UpdateTokenRequest, APITokenScope, APITokenStatus } from '@/types/apiToken'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography

interface ApiTokensDrawerProps {
  visible: boolean
  onClose: () => void
}

const ApiTokensDrawer: React.FC<ApiTokensDrawerProps> = ({ visible, onClose }) => {
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const [form] = Form.useForm()
  const [editingToken, setEditingToken] = useState<APIToken | null>(null)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [newTokenKey, setNewTokenKey] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Query для получения списка токенов
  const { data: tokens, isLoading } = useQuery({
    queryKey: ['apiTokens'],
    queryFn: () => getTokens(),
    enabled: visible,
  })

  // Mutation для создания токена
  const createMutation = useMutation({
    mutationFn: createToken,
    onSuccess: (data) => {
      message.success('Токен успешно создан!')
      setNewTokenKey(data.token_key)
      form.resetFields()
      setIsModalVisible(false)
      queryClient.invalidateQueries({ queryKey: ['apiTokens'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка создания токена: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation для обновления токена
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTokenRequest }) =>
      updateToken(id, data),
    onSuccess: () => {
      message.success('Токен успешно обновлен!')
      setEditingToken(null)
      setIsModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['apiTokens'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления токена: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation для отзыва токена
  const revokeMutation = useMutation({
    mutationFn: (tokenId: number) => revokeToken(tokenId),
    onSuccess: () => {
      message.success('Токен успешно отозван!')
      queryClient.invalidateQueries({ queryKey: ['apiTokens'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка отзыва токена: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation для удаления токена
  const deleteMutation = useMutation({
    mutationFn: deleteToken,
    onSuccess: () => {
      message.success('Токен успешно удален!')
      queryClient.invalidateQueries({ queryKey: ['apiTokens'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления токена: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleCreate = () => {
    setEditingToken(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  const handleEdit = (token: APIToken) => {
    setEditingToken(token)
    form.setFieldsValue({
      name: token.name,
      description: token.description,
      scopes: token.scopes, // Массив scope'ов
      expires_at: token.expires_at ? dayjs(token.expires_at) : null,
    })
    setIsModalVisible(true)
  }

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      const payload = {
        name: values.name,
        description: values.description,
        scopes: values.scopes, // Массив scope'ов
        expires_at: values.expires_at ? values.expires_at.toISOString() : undefined,
      }

      if (editingToken) {
        updateMutation.mutate({ id: editingToken.id, data: payload })
      } else {
        createMutation.mutate(payload as CreateTokenRequest)
      }
    })
  }

  const handleModalCancel = () => {
    setIsModalVisible(false)
    setEditingToken(null)
    form.resetFields()
  }

  const handleCopyToken = (token: string) => {
    navigator.clipboard.writeText(token)
    message.success('Токен скопирован в буфер обмена!')
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: APITokenStatus, record: APIToken) => {
        if (status === 'REVOKED') {
          return <Tag color="red">Отозван</Tag>
        }
        if (status === 'EXPIRED' || (record.expires_at && new Date(record.expires_at) < new Date())) {
          return <Tag color="orange">Истек</Tag>
        }
        return <Tag color="green">Активен</Tag>
      },
    },
    {
      title: 'Права доступа',
      dataIndex: 'scopes',
      key: 'scopes',
      width: 180,
      render: (scopes: APITokenScope[]) => {
        const colors = {
          READ: 'blue',
          WRITE: 'orange',
          DELETE: 'red',
          ADMIN: 'purple',
        }
        return (
          <Space size="small" wrap>
            {scopes.map(scope => (
              <Tag key={scope} color={colors[scope]}>{scope}</Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: 'Последнее использование',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 180,
      render: (date: string | null) =>
        date ? dayjs(date).format('DD.MM.YYYY HH:mm') : 'Не использовался',
    },
    {
      title: 'Истекает',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 180,
      render: (date: string | null) => (date ? dayjs(date).format('DD.MM.YYYY HH:mm') : 'Никогда'),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_: any, record: APIToken) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              disabled={record.status !== 'ACTIVE'}
            />
          </Tooltip>
          {record.status === 'ACTIVE' && (
            <Tooltip title="Отозвать токен">
              <Popconfirm
                title="Отозвать токен?"
                description="Токен перестанет работать. Это действие необратимо."
                onConfirm={() => revokeMutation.mutate(record.id)}
                okText="Отозвать"
                cancelText="Отмена"
              >
                <Button type="text" danger icon={<StopOutlined />} />
              </Popconfirm>
            </Tooltip>
          )}
          <Tooltip title="Удалить">
            <Popconfirm
              title="Удалить токен?"
              description="Это действие необратимо!"
              onConfirm={() => deleteMutation.mutate(record.id)}
              okText="Удалить"
              cancelText="Отмена"
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Drawer
        title={
          <Space>
            <KeyOutlined />
            <span>API Токены</span>
          </Space>
        }
        placement="right"
        width="90%"
        onClose={onClose}
        open={visible}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Создать токен
          </Button>
        }
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="Управление токенами для доступа к External API"
            description="API токены используются для интеграции с внешними системами (например, 1С). Храните токены в безопасном месте."
            type="info"
            showIcon
          />

          <ResponsiveTable
            columns={columns}
            dataSource={tokens}
            loading={isLoading}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1000 }}
          />
        </Space>
      </Drawer>

      {/* Модальное окно создания/редактирования токена */}
      <Modal
        title={editingToken ? 'Редактировать токен' : 'Создать новый токен'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        okText={editingToken ? 'Сохранить' : 'Создать'}
        cancelText="Отмена"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="name"
            label="Название"
            rules={[
              { required: true, message: 'Введите название токена' },
              { max: 100, message: 'Максимум 100 символов' },
            ]}
          >
            <Input placeholder="Например: 1C Integration Token" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea
              rows={3}
              placeholder="Опциональное описание для чего используется токен"
            />
          </Form.Item>

          <Form.Item
            name="scopes"
            label="Права доступа"
            rules={[{ required: true, message: 'Выберите хотя бы одно право доступа' }]}
          >
            <Select
              mode="multiple"
              placeholder="Выберите права доступа"
              options={[
                { value: 'READ', label: 'READ - Только чтение' },
                { value: 'WRITE', label: 'WRITE - Создание и изменение' },
                { value: 'DELETE', label: 'DELETE - Удаление' },
                { value: 'ADMIN', label: 'ADMIN - Полный доступ' },
              ]}
            />
          </Form.Item>

          <Form.Item name="expires_at" label="Дата истечения">
            <DatePicker
              showTime
              style={{ width: '100%' }}
              format="DD.MM.YYYY HH:mm"
              placeholder="Оставьте пустым для бессрочного токена"
            />
          </Form.Item>

          {!editingToken && (
            <Alert
              message="Важно!"
              description="Токен будет показан только один раз после создания. Сохраните его в безопасном месте."
              type="warning"
              showIcon
            />
          )}
        </Form>
      </Modal>

      {/* Модальное окно с новым токеном */}
      <Modal
        title="Токен успешно создан!"
        open={!!newTokenKey}
        onOk={() => setNewTokenKey(null)}
        onCancel={() => setNewTokenKey(null)}
        footer={[
          <Button key="close" type="primary" onClick={() => setNewTokenKey(null)}>
            Закрыть
          </Button>,
        ]}
        width={700}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="Сохраните токен!"
            description="Это единственный раз, когда вы видите полный токен. Скопируйте его и сохраните в безопасном месте."
            type="error"
            showIcon
          />

          <div>
            <Title level={5}>Ваш API токен:</Title>
            <Input.TextArea
              value={newTokenKey || ''}
              readOnly
              autoSize={{ minRows: 3, maxRows: 5 }}
              style={{ fontFamily: 'monospace', fontSize: '12px' }}
            />
            <Button
              type="primary"
              icon={<CopyOutlined />}
              onClick={() => handleCopyToken(newTokenKey!)}
              style={{ marginTop: 10 }}
            >
              Копировать токен
            </Button>
          </div>

          <div>
            <Title level={5}>Использование в 1С:</Title>
            <Paragraph>
              <Text code>
                Запрос.Заголовки.Вставить("Authorization", "Bearer " + APIТокен)
              </Text>
            </Paragraph>
          </div>

          <div>
            <Title level={5}>Использование в curl:</Title>
            <Paragraph>
              <Text code>curl -H "Authorization: Bearer {newTokenKey}" http://your-server/api/v1/external/...</Text>
            </Paragraph>
          </div>
        </Space>
      </Modal>
    </>
  )
}

export default ApiTokensDrawer
