import { useState } from 'react'
import {
  Typography,
  Card,
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Input,
  Select,
  Row,
  Col,
  Statistic,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  StopOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  BankOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { departmentsApi } from '@/api'
import type { Department } from '@/contexts/DepartmentContext'
import DepartmentFormModal from '@/components/departments/DepartmentFormModal'
import { useAuth } from '@/contexts/AuthContext'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'

const { Title, Paragraph } = Typography
const { Option } = Select

const DepartmentsPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | null>(null)

  const queryClient = useQueryClient()
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  const { data: departments, isLoading } = useQuery({
    queryKey: ['departments', page, pageSize, search, activeFilter],
    queryFn: () =>
      departmentsApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        is_active: activeFilter,
      }),
  })

  const deactivateMutation = useMutation({
    mutationFn: departmentsApi.deactivate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      message.success('Отдел успешно деактивирован')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при деактивации: ${errorMessage}`)
    },
  })

  const activateMutation = useMutation({
    mutationFn: departmentsApi.activate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      message.success('Отдел успешно активирован')
    },
    onError: (error: any) => {
      message.error(`Ошибка при активации: ${error.message}`)
    },
  })

  const handleCreate = () => {
    setModalMode('create')
    setSelectedDepartmentId(null)
    setModalVisible(true)
  }

  const handleEdit = (department: Department) => {
    setModalMode('edit')
    setSelectedDepartmentId(department.id)
    setModalVisible(true)
  }

  const handleDeactivate = (id: number) => {
    deactivateMutation.mutate(id)
  }

  const handleActivate = (id: number) => {
    activateMutation.mutate(id)
  }

  // Filter departments by search
  const filteredDepartments = departments?.filter((dept) => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      dept.name.toLowerCase().includes(searchLower) ||
      dept.code.toLowerCase().includes(searchLower) ||
      dept.manager_name?.toLowerCase().includes(searchLower)
    )
  })

  // Calculate statistics
  const totalCount = filteredDepartments?.length || 0
  const activeCount = filteredDepartments?.filter((d) => d.is_active).length || 0
  const inactiveCount = filteredDepartments?.filter((d) => !d.is_active).length || 0

  // Get selected department from current data (always fresh)
  const selectedDepartment = selectedDepartmentId
    ? departments?.find((d) => d.id === selectedDepartmentId) || null
    : null

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (text: string) => (
        <Space>
          <BankOutlined />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Код',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Руководитель',
      dataIndex: 'manager_name',
      key: 'manager_name',
      width: 200,
      render: (text: string | null) => text || <span style={{ color: '#999' }}>—</span>,
    },
    {
      title: 'Email',
      dataIndex: 'contact_email',
      key: 'contact_email',
      width: 200,
      render: (text: string | null) => text || <span style={{ color: '#999' }}>—</span>,
    },
    {
      title: 'Телефон',
      dataIndex: 'contact_phone',
      key: 'contact_phone',
      width: 150,
      render: (text: string | null) => text || <span style={{ color: '#999' }}>—</span>,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      fixed: 'right' as const,
      render: (isActive: boolean) =>
        isActive ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            Активен
          </Tag>
        ) : (
          <Tag color="default" icon={<StopOutlined />}>
            Неактивен
          </Tag>
        ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Department) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled={!isAdmin}
          >
            Изменить
          </Button>
          {record.is_active ? (
            <Popconfirm
              title="Деактивировать отдел?"
              description="Отдел будет деактивирован, но данные сохранятся."
              onConfirm={() => handleDeactivate(record.id)}
              okText="Да"
              cancelText="Нет"
              disabled={!isAdmin}
            >
              <Button
                type="link"
                danger
                icon={<StopOutlined />}
                disabled={!isAdmin}
              >
                Деактивировать
              </Button>
            </Popconfirm>
          ) : (
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              onClick={() => handleActivate(record.id)}
              disabled={!isAdmin}
            >
              Активировать
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <BankOutlined /> Управление отделами
          </Title>
          <Paragraph type="secondary">
            Создание и управление отделами организации для multi-tenancy
          </Paragraph>
        </div>

        {/* Statistics */}
        <Row gutter={16}>
          <Col xs={24} sm={8} md={8}>
            <Card>
              <Statistic
                title="Всего отделов"
                value={totalCount}
                prefix={<BankOutlined />}
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
                prefix={<StopOutlined />}
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
                  placeholder="Поиск по названию, коду или руководителю"
                  prefix={<SearchOutlined />}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  allowClear
                />
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Select
                  placeholder="Фильтр по статусу"
                  value={activeFilter}
                  onChange={setActiveFilter}
                  style={{ width: '100%' }}
                  allowClear
                >
                  <Option value={true}>Активные</Option>
                  <Option value={false}>Неактивные</Option>
                </Select>
              </Col>
              <Col xs={24} sm={24} md={8} style={{ textAlign: 'right' }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleCreate}
                    disabled={!isAdmin}
                  >
                    Создать отдел
                  </Button>
                </Space>
              </Col>
            </Row>

            {/* Table */}
            <ResponsiveTable
              columns={columns}
              dataSource={filteredDepartments}
              rowKey="id"
              loading={isLoading}
              pagination={{
                current: page,
                pageSize: pageSize,
                total: filteredDepartments?.length || 0,
                onChange: (newPage, newPageSize) => {
                  setPage(newPage)
                  setPageSize(newPageSize)
                },
                showSizeChanger: true,
                showTotal: (total) => `Всего ${total} отделов`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
              scroll={{ x: 1200 }}
              mobileLayout="card"
            />
          </Space>
        </Card>
      </Space>

      <DepartmentFormModal
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setSelectedDepartmentId(null)
        }}
        department={selectedDepartment}
        mode={modalMode}
      />
    </div>
  )
}

export default DepartmentsPage
