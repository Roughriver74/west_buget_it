import { useState } from 'react'
import { Typography, Card, Table, Button, Space, Tag, Popconfirm, message, Input, Select, Row, Col, Statistic } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, BankOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { organizationsApi } from '@/api'
import type { Organization } from '@/types'
import OrganizationFormModal from '@/components/organizations/OrganizationFormModal'

const { Title, Paragraph } = Typography
const { Option } = Select

const OrganizationsPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedOrganization, setSelectedOrganization] = useState<Organization | null>(null)

  const queryClient = useQueryClient()

  const { data: organizations, isLoading } = useQuery({
    queryKey: ['organizations', page, pageSize, search, activeFilter],
    queryFn: () =>
      organizationsApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        is_active: activeFilter,
      }),
  })

  const deleteMutation = useMutation({
    mutationFn: organizationsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      message.success('Организация успешно удалена')
    },
    onError: (error: any) => {
      message.error(`Ошибка при удалении: ${error.message}`)
    },
  })

  const handleCreate = () => {
    setModalMode('create')
    setSelectedOrganization(null)
    setModalVisible(true)
  }

  const handleEdit = (organization: Organization) => {
    setModalMode('edit')
    setSelectedOrganization(organization)
    setModalVisible(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      ellipsis: true,
      render: (name: string, record: Organization) => (
        <Link to={`/organizations/${record.id}`} style={{ color: '#1890ff', fontWeight: 500 }}>
          {name}
        </Link>
      ),
    },
    {
      title: 'ИНН',
      dataIndex: 'inn',
      key: 'inn',
      width: 130,
      render: (text: string) => text || '—',
    },
    {
      title: 'КПП',
      dataIndex: 'kpp',
      key: 'kpp',
      width: 110,
      render: (text: string) => text || '—',
    },
    {
      title: 'Адрес',
      dataIndex: 'address',
      key: 'address',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '—',
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      align: 'center' as const,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Да' : 'Нет'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Organization) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить организацию?"
            description="Это действие нельзя отменить."
            onConfirm={() => handleDelete(record.id)}
            okText="Удалить"
            cancelText="Отмена"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Calculate statistics
  const totalOrganizations = organizations?.length || 0
  const activeOrganizations = organizations?.filter(o => o.is_active).length || 0

  return (
    <div>
      <Title level={2}>Справочник организаций</Title>
      <Paragraph>
        Управление организациями компании для учета расходов по различным юридическим лицам.
      </Paragraph>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Всего организаций"
              value={totalOrganizations}
              prefix={<BankOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Активных"
              value={activeOrganizations}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Неактивных"
              value={totalOrganizations - activeOrganizations}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <Space>
            <Input
              placeholder="Поиск по названию, ИНН"
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 300 }}
              allowClear
            />

            <Select
              value={activeFilter}
              onChange={setActiveFilter}
              style={{ width: 150 }}
              placeholder="Статус"
            >
              <Option value={undefined}>Все</Option>
              <Option value={true}>Активные</Option>
              <Option value={false}>Неактивные</Option>
            </Select>
          </Space>

          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Добавить организацию
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={organizations || []}
          loading={isLoading}
          rowKey="id"
          size="middle"
          scroll={{ x: 800 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: organizations?.length || 0,
            onChange: (newPage, newPageSize) => {
              setPage(newPage)
              setPageSize(newPageSize)
            },
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total} организаций`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />

        <OrganizationFormModal
          visible={modalVisible}
          onCancel={() => {
            setModalVisible(false)
            setSelectedOrganization(null)
          }}
          organization={selectedOrganization}
          mode={modalMode}
        />
      </Card>
    </div>
  )
}

export default OrganizationsPage
