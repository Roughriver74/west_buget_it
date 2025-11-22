import { useState } from 'react'
import {
  Typography,
  Card,
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Input,
  Select,
  Row,
  Col,
  Statistic} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UserOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api'
import type { UserListItem } from '@/api/users'
import UserFormModal from '@/components/users/UserFormModal'
import { useAuth } from '@/contexts/AuthContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { PAGINATION_CONFIG } from '@/config/pagination'

const { Title, Paragraph } = Typography
const { Option } = Select

const getRoleLabel = (role: string) => {
  const roleLabels: Record<string, { label: string; color: string }> = {
    ADMIN: { label: 'Администратор', color: 'red' },
    MANAGER: { label: 'Руководитель', color: 'purple' },
    ACCOUNTANT: { label: 'Бухгалтер', color: 'blue' },
    REQUESTER: { label: 'Заявитель', color: 'green' },
    USER: { label: 'Пользователь', color: 'default' }}
  return roleLabels[role] || { label: role, color: 'default' }
}

const UsersPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined)
  const [statusFilter, setStatusFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedUser, setSelectedUser] = useState<any | null>(null)

  const queryClient = useQueryClient()
  const { user: currentUser } = useAuth()
  const isAdmin = currentUser?.role === 'ADMIN'

  const { data: users, isLoading } = useQuery({
    queryKey: ['users', page, pageSize],
    queryFn: () =>
      usersApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize})})

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      message.success('Пользователь успешно удален')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при удалении: ${errorMessage}`)
    }})

  const handleCreate = () => {
    setModalMode('create')
    setSelectedUser(null)
    setModalVisible(true)
  }

  const handleEdit = async (user: UserListItem) => {
    // Load full user data
    try {
      const fullUser = await usersApi.getById(user.id)
      setModalMode('edit')
      setSelectedUser(fullUser)
      setModalVisible(true)
    } catch (error) {
      message.error('Не удалось загрузить данные пользователя')
    }
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  // Filter users by search and filters
  const filteredUsers = users?.filter((user) => {
    if (search) {
      const searchLower = search.toLowerCase()
      if (
        !user.username.toLowerCase().includes(searchLower) &&
        !user.email.toLowerCase().includes(searchLower) &&
        !user.full_name?.toLowerCase().includes(searchLower)
      ) {
        return false
      }
    }
    if (roleFilter && user.role !== roleFilter) {
      return false
    }
    if (statusFilter !== undefined && user.is_active !== statusFilter) {
      return false
    }
    return true
  })

  // Calculate statistics
  const totalCount = filteredUsers?.length || 0
  const activeCount = filteredUsers?.filter((u) => u.is_active).length || 0
  const inactiveCount = filteredUsers?.filter((u) => !u.is_active).length || 0

  const columns = [
    {
      title: 'Логин',
      dataIndex: 'username',
      key: 'username',
      width: 150,
      render: (text: string) => (
        <Space>
          <UserOutlined />
          <strong>{text}</strong>
        </Space>
      )},
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 200},
    {
      title: 'Полное имя',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 200,
      render: (text: string | null) => text || <span style={{ color: '#999' }}>—</span>},
    {
      title: 'Роль',
      dataIndex: 'role',
      key: 'role',
      width: 150,
      render: (role: string) => {
        const { label, color } = getRoleLabel(role)
        return <Tag color={color}>{label}</Tag>
      }},
    {
      title: 'Отдел',
      dataIndex: 'department_id',
      key: 'department_id',
      width: 100,
      render: (dept: number | null) =>
        dept ? `Отдел #${dept}` : <span style={{ color: '#999' }}>—</span>},
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 120,
      fixed: 'right' as const,
      render: (isActive: boolean) =>
        isActive ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            Активен
          </Tag>
        ) : (
          <Tag color="default" icon={<CloseCircleOutlined />}>
            Неактивен
          </Tag>
        )},
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: UserListItem) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled={!isAdmin}
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить пользователя?"
            description="Это действие нельзя отменить!"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
            disabled={!isAdmin || record.id === currentUser?.id}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={!isAdmin || record.id === currentUser?.id}
            >
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      )},
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <UserOutlined /> Управление пользователями
          </Title>
          <Paragraph type="secondary">
            Создание и управление пользователями системы
          </Paragraph>
        </div>

        {/* Statistics */}
        <Row gutter={16}>
          <Col xs={24} sm={8} md={8}>
            <Card>
              <Statistic
                title="Всего пользователей"
                value={totalCount}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8} md={8}>
            <Card>
              <Statistic
                title="Активных"
                value={activeCount}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8} md={8}>
            <Card>
              <Statistic
                title="Неактивных"
                value={inactiveCount}
                valueStyle={{ color: '#999' }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Card>
          <Space
            direction="vertical"
            size="middle"
            style={{ width: '100%' }}
          >
            {/* Filters and Actions */}
            <Row gutter={[16, 16]} justify="space-between">
              <Col xs={24} sm={12} md={8}>
                <Input
                  placeholder="Поиск по логину, email или имени"
                  prefix={<SearchOutlined />}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  allowClear
                />
              </Col>
              <Col xs={24} sm={6} md={4}>
                <Select
                  placeholder="Роль"
                  value={roleFilter}
                  onChange={setRoleFilter}
                  style={{ width: '100%' }}
                  allowClear
                >
                  <Option value="ADMIN">Администратор</Option>
                  <Option value="MANAGER">Руководитель</Option>
                  <Option value="ACCOUNTANT">Бухгалтер</Option>
                  <Option value="REQUESTER">Заявитель</Option>
                  <Option value="USER">Пользователь</Option>
                </Select>
              </Col>
              <Col xs={24} sm={6} md={4}>
                <Select
                  placeholder="Статус"
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: '100%' }}
                  allowClear
                >
                  <Option value={true}>Активные</Option>
                  <Option value={false}>Неактивные</Option>
                </Select>
              </Col>
              <Col xs={24} sm={24} md={8} style={{ textAlign: 'right' }}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreate}
                  disabled={!isAdmin}
                >
                  Создать пользователя
                </Button>
              </Col>
            </Row>

            {/* Table */}
            <ResponsiveTable
              columns={columns}
              dataSource={filteredUsers}
              rowKey="id"
              loading={isLoading}
              pagination={{
                current: page,
                pageSize: pageSize,
                total: filteredUsers?.length || 0,
                onChange: (newPage, newPageSize) => {
                  setPage(newPage)
                  setPageSize(newPageSize)
                },
                showSizeChanger: true,
                showTotal: (total) => `Всего ${total} пользователей`,
                pageSizeOptions: [...PAGINATION_CONFIG.OPTIONS_STRINGS]}}
              scroll={{ x: 1200 }}
              mobileLayout="card"
            />
          </Space>
        </Card>
      </Space>

      <UserFormModal
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        user={selectedUser}
        mode={modalMode}
      />
    </div>
  )
}

export default UsersPage
