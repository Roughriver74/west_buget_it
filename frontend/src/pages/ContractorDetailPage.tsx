import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Table, Tag, Spin, Statistic, Row, Col, Button, Space, Typography, Divider } from 'antd'
import { ArrowLeftOutlined, DollarOutlined, FileTextOutlined, EditOutlined, TeamOutlined, PhoneOutlined, MailOutlined } from '@ant-design/icons'
import { contractorsApi, expensesApi } from '@/api'
import { ExpenseStatus } from '@/types'
import type { Expense } from '@/types'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import ExpenseFormModal from '@/components/expenses/ExpenseFormModal'
import dayjs from 'dayjs'

const ContractorDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const contractorId = parseInt(id || '0')
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [isModalVisible, setIsModalVisible] = useState(false)

  // Fetch contractor details
  const { data: contractor, isLoading: contractorLoading } = useQuery({
    queryKey: ['contractor', contractorId],
    queryFn: () => contractorsApi.getOne(contractorId),
    enabled: !!contractorId,
  })

  // Fetch expenses for this contractor
  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', 'contractor', contractorId],
    queryFn: () => expensesApi.getAll({ contractor_id: contractorId, limit: 100 }),
    enabled: !!contractorId,
  })

  if (contractorLoading || expensesLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!contractor) {
    return <div>Контрагент не найден</div>
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
      title: 'Организация',
      dataIndex: ['organization', 'name'],
      key: 'organization',
      width: 150,
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
        <Link to="/contractors">
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
              <TeamOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  {contractor.name}
                  <Tag color={contractor.is_active ? 'success' : 'default'} style={{ marginLeft: 12 }}>
                    {contractor.is_active ? 'Активен' : 'Неактивен'}
                  </Tag>
                </Title>
                {contractor.short_name && (
                  <Text type="secondary">{contractor.short_name}</Text>
                )}
              </div>
            </Space>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          <Descriptions column={{ xs: 1, sm: 2, md: 3 }}>
            <Descriptions.Item label="ИНН">{contractor.inn || '—'}</Descriptions.Item>
            <Descriptions.Item label={<Space><PhoneOutlined />Телефон</Space>}>
              {contractor.phone || '—'}
            </Descriptions.Item>
            <Descriptions.Item label={<Space><MailOutlined />Email</Space>}>
              {contractor.email || '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Дата создания" span={2}>
              {dayjs(contractor.created_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="Обновлено">
              {dayjs(contractor.updated_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
            {contractor.contact_info && (
              <Descriptions.Item label="Контакты" span={3}>
                {contractor.contact_info}
              </Descriptions.Item>
            )}
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

export default ContractorDetailPage
