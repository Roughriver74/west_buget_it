import { useState } from 'react'
import { Typography, Card, Table, Button, Space, Tag, Popconfirm, message, Input, Select, Row, Col, Statistic } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, TeamOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { contractorsApi } from '@/api'
import type { Contractor } from '@/types'
import ContractorFormModal from '@/components/contractors/ContractorFormModal'

const { Title, Paragraph } = Typography
const { Option } = Select

const ContractorsPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedContractor, setSelectedContractor] = useState<Contractor | null>(null)

  const queryClient = useQueryClient()

  const { data: contractors, isLoading } = useQuery({
    queryKey: ['contractors', page, pageSize, search, activeFilter],
    queryFn: () =>
      contractorsApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        is_active: activeFilter,
      }),
  })

  const deleteMutation = useMutation({
    mutationFn: contractorsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
      message.success('Контрагент успешно удален')
    },
    onError: (error: any) => {
      message.error(`Ошибка при удалении: ${error.message}`)
    },
  })

  const handleCreate = () => {
    setModalMode('create')
    setSelectedContractor(null)
    setModalVisible(true)
  }

  const handleEdit = (contractor: Contractor) => {
    setModalMode('edit')
    setSelectedContractor(contractor)
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
      render: (name: string, record: Contractor) => (
        <Link to={`/contractors/${record.id}`} style={{ color: '#1890ff', fontWeight: 500 }}>
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
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 180,
      ellipsis: true,
      render: (text: string) => text || '—',
    },
    {
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
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
      render: (_: any, record: Contractor) => (
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
            title="Удалить контрагента?"
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
  const totalContractors = contractors?.length || 0
  const activeContractors = contractors?.filter(c => c.is_active).length || 0

  return (
    <div>
      <Title level={2}>Справочник контрагентов</Title>
      <Paragraph>
        Управление контрагентами (поставщиками, подрядчиками) для учета расходов и оплат.
      </Paragraph>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Всего контрагентов"
              value={totalContractors}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Активных"
              value={activeContractors}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Неактивных"
              value={totalContractors - activeContractors}
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
            Добавить контрагента
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={contractors || []}
          loading={isLoading}
          rowKey="id"
          size="middle"
          scroll={{ x: 900 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: contractors?.length || 0,
            onChange: (newPage, newPageSize) => {
              setPage(newPage)
              setPageSize(newPageSize)
            },
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total} контрагентов`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />

        <ContractorFormModal
          visible={modalVisible}
          onCancel={() => {
            setModalVisible(false)
            setSelectedContractor(null)
          }}
          contractor={selectedContractor}
          mode={modalMode}
        />
      </Card>
    </div>
  )
}

export default ContractorsPage
