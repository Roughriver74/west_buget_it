import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Table, Tag, Spin, Statistic, Row, Col, Button, Space, Typography, Divider } from 'antd'
import { ArrowLeftOutlined, DollarOutlined, FileTextOutlined, EditOutlined, BankOutlined, IdcardOutlined } from '@ant-design/icons'
import { organizationsApi, expensesApi } from '@/api'
import { ExpenseStatus } from '@/types'
import type { Expense } from '@/types'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import ExpenseFormModal from '@/components/expenses/ExpenseFormModal'
import dayjs from 'dayjs'

const OrganizationDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const organizationId = parseInt(id || '0')
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [isModalVisible, setIsModalVisible] = useState(false)

  // Fetch organization details
  const { data: organization, isLoading: organizationLoading } = useQuery({
    queryKey: ['organization', organizationId],
    queryFn: () => organizationsApi.getOne(organizationId),
    enabled: !!organizationId,
  })

  // Fetch expenses for this organization
  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', 'organization', organizationId],
    queryFn: () => expensesApi.getAll({ organization_id: organizationId, limit: 100 }),
    enabled: !!organizationId,
  })

  if (organizationLoading || expensesLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!organization) {
    return <div>Организация не найдена</div>
  }

  // Calculate statistics
  const totalAmount = expenses?.items.reduce((sum, exp) => sum + Number(exp.amount), 0) || 0
  const totalCount = expenses?.items.length || 0
  const paidCount = expenses?.items.filter(exp => exp.status === ExpenseStatus.PAID).length || 0
  const paidAmount = expenses?.items
    .filter(exp => exp.status === ExpenseStatus.PAID)
    .reduce((sum, exp) => sum + Number(exp.amount), 0) || 0

  const columns = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 150,
      render: (number: string, record: any) => (
        <Link to={`/expenses`} style={{ color: '#1890ff' }}>
          {number}
        </Link>
      ),
    },
    {
      title: 'Дата',
      dataIndex: 'request_date',
      key: 'request_date',
      width: 120,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Категория',
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 200,
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 150,
      align: 'right' as const,
      render: (amount: number) =>
        new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB',
          minimumFractionDigits: 0,
        }).format(amount),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: ExpenseStatus) => (
        <Tag color={getExpenseStatusColor(status)}>
          {getExpenseStatusLabel(status)}
        </Tag>
      ),
    },
    {
      title: 'Контрагент',
      dataIndex: ['contractor', 'name'],
      key: 'contractor',
      width: 200,
      ellipsis: true,
      render: (_: string, record: any) =>
        record.contractor ? (
          <Link to={`/contractors/${record.contractor.id}`} style={{ color: '#1890ff' }}>
            {record.contractor.name}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Expense) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          onClick={() => {
            setEditingExpense(record)
            setIsModalVisible(true)
          }}
        >
          Изменить
        </Button>
      ),
    },
  ]

  const handleModalClose = () => {
    setIsModalVisible(false)
    setEditingExpense(null)
  }

  const { Title, Text } = Typography

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Link to="/organizations">
          <Button icon={<ArrowLeftOutlined />}>Назад к списку</Button>
        </Link>
      </Space>

      <Card
        style={{ marginBottom: 24 }}
        styles={{ body: { padding: 24 } }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Space align="center" size="middle">
              <BankOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  {organization.name}
                  <Tag color={organization.is_active ? 'success' : 'default'} style={{ marginLeft: 12 }}>
                    {organization.is_active ? 'Активна' : 'Неактивна'}
                  </Tag>
                </Title>
                {organization.legal_name && (
                  <Text type="secondary">{organization.legal_name}</Text>
                )}
              </div>
            </Space>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          <Descriptions column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label={<Space><IdcardOutlined />ИНН</Space>}>
              {organization.inn || '—'}
            </Descriptions.Item>
            <Descriptions.Item label="КПП">{organization.kpp || '—'}</Descriptions.Item>
            <Descriptions.Item label="Статус">
              <Tag color={organization.is_active ? 'success' : 'default'}>
                {organization.is_active ? 'Активна' : 'Неактивна'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Дата создания" span={2}>
              {dayjs(organization.created_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="Обновлено">
              {dayjs(organization.updated_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Всего заявок"
              value={totalCount}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Общая сумма"
              value={totalAmount}
              prefix={<DollarOutlined />}
              formatter={(value) =>
                new Intl.NumberFormat('ru-RU', {
                  style: 'currency',
                  currency: 'RUB',
                  minimumFractionDigits: 0,
                }).format(value as number)
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Оплачено заявок"
              value={paidCount}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Оплачено сумма"
              value={paidAmount}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
              formatter={(value) =>
                new Intl.NumberFormat('ru-RU', {
                  style: 'currency',
                  currency: 'RUB',
                  minimumFractionDigits: 0,
                }).format(value as number)
              }
            />
          </Card>
        </Col>
      </Row>

      <Card title="Заявки">
        <Table
          columns={columns}
          dataSource={expenses?.items}
          rowKey="id"
          pagination={{ pageSize: 20, showSizeChanger: true }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <ExpenseFormModal
        visible={isModalVisible}
        onCancel={handleModalClose}
        expense={editingExpense}
        mode="edit"
      />
    </div>
  )
}

export default OrganizationDetailPage
