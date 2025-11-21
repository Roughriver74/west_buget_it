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
  Statistic,
  Tooltip,
  Progress} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  CloseOutlined,
  CheckOutlined,
  SettingOutlined,
  InfoCircleOutlined} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as businessOperationMappingsApi from '@/api/businessOperationMappings'
import type { BusinessOperationMapping } from '@/types/businessOperationMapping'
import { useDepartment } from '@/contexts/DepartmentContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import BusinessOperationMappingFormModal from '@/components/businessOperationMappings/BusinessOperationMappingFormModal'
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery'
import {
  getResponsiveSpacing,
  getResponsiveGutter,
  getResponsiveButtonSize} from '@/utils/responsive'

const { Title, Paragraph, Text } = Typography
const { Option } = Select

const BusinessOperationMappingsPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedMapping, setSelectedMapping] = useState<BusinessOperationMapping | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [bulkLoading, setBulkLoading] = useState(false)
  const { selectedDepartment } = useDepartment()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()

  const queryClient = useQueryClient()

  const { data: mappings, isLoading } = useQuery({
    queryKey: ['business-operation-mappings', page, pageSize, search, activeFilter, selectedDepartment?.id],
    queryFn: () =>
      businessOperationMappingsApi.getMappings({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        business_operation: search || undefined,
        is_active: activeFilter,
        department_id: selectedDepartment?.id})})

  const deleteMutation = useMutation({
    mutationFn: businessOperationMappingsApi.deleteMapping,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-operation-mappings'] })
      message.success('Маппинг успешно удален')
    },
    onError: (error: any) => {
      message.error(`Ошибка при удалении: ${error.message}`)
    }})

  const handleCreate = () => {
    setModalMode('create')
    setSelectedMapping(null)
    setModalVisible(true)
  }

  const handleEdit = (mapping: BusinessOperationMapping) => {
    setModalMode('edit')
    setSelectedMapping(mapping)
    setModalVisible(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleBulkActivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите маппинги для активации')
      return
    }

    setBulkLoading(true)
    try {
      await businessOperationMappingsApi.bulkActivate(selectedRowKeys as number[])
      message.success(`Активировано: ${selectedRowKeys.length}`)
      queryClient.invalidateQueries({ queryKey: ['business-operation-mappings'] })
      setSelectedRowKeys([])
    } catch (error: any) {
      message.error(`Ошибка при активации: ${error.message}`)
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDeactivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите маппинги для деактивации')
      return
    }

    setBulkLoading(true)
    try {
      await businessOperationMappingsApi.bulkDeactivate(selectedRowKeys as number[])
      message.success(`Деактивировано: ${selectedRowKeys.length}`)
      queryClient.invalidateQueries({ queryKey: ['business-operation-mappings'] })
      setSelectedRowKeys([])
    } catch (error: any) {
      message.error(`Ошибка при деактивации: ${error.message}`)
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите маппинги для удаления')
      return
    }

    setBulkLoading(true)
    try {
      await businessOperationMappingsApi.bulkDelete(selectedRowKeys as number[])
      message.success(`Удалено: ${selectedRowKeys.length}`)
      queryClient.invalidateQueries({ queryKey: ['business-operation-mappings'] })
      setSelectedRowKeys([])
    } catch (error: any) {
      message.error(`Ошибка при удалении: ${error.message}`)
    } finally {
      setBulkLoading(false)
    }
  }

  const columns = [
    {
      title: 'Хозяйственная операция',
      dataIndex: 'business_operation',
      key: 'business_operation',
      width: 250,
      render: (text: string) => <Text strong>{text}</Text>},
    {
      title: 'Категория бюджета',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 200,
      render: (text: string, record: BusinessOperationMapping) => (
        <Space direction="vertical" size={0}>
          <Text>{text}</Text>
          {record.category_type && (
            <Tag color={record.category_type === 'OPEX' ? 'blue' : 'green'}>
              {record.category_type}
            </Tag>
          )}
        </Space>
      )},
    {
      title: (
        <Space>
          Приоритет
          <Tooltip title="Чем выше приоритет, тем раньше применяется маппинг">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'priority',
      key: 'priority',
      width: 120,
      sorter: (a: BusinessOperationMapping, b: BusinessOperationMapping) => a.priority - b.priority,
      render: (value: number) => <Tag color="purple">{value}</Tag>},
    {
      title: (
        <Space>
          Уверенность
          <Tooltip title="Уровень уверенности AI (0.0-1.0)">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'confidence',
      key: 'confidence',
      width: 150,
      sorter: (a: BusinessOperationMapping, b: BusinessOperationMapping) => a.confidence - b.confidence,
      render: (value: number) => {
        const percent = Math.round(value * 100)
        const color = percent >= 90 ? 'success' : percent >= 70 ? 'warning' : 'exception'
        return <Progress percent={percent} size="small" status={color as any} />
      }},
    {
      title: 'Отдел',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 150},
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || <Text type="secondary">—</Text>},
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      filters: [
        { text: 'Активный', value: true },
        { text: 'Неактивный', value: false },
      ],
      render: (isActive: boolean) =>
        isActive ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            Активный
          </Tag>
        ) : (
          <Tag color="default">Неактивный</Tag>
        )},
    {
      title: 'Действия',
      key: 'actions',
      fixed: 'right' as const,
      width: 120,
      render: (_: any, record: BusinessOperationMapping) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="Удалить маппинг?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Tooltip title="Удалить">
              <Button type="link" danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      )},
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys)
    }}

  const activeCount = mappings?.items?.filter((m) => m.is_active).length || 0
  const inactiveCount = mappings?.items?.filter((m) => !m.is_active).length || 0

  const spacing = getResponsiveSpacing(isMobile, isSmallScreen)
  const gutter = getResponsiveGutter(isMobile, isSmallScreen)
  const buttonSize = getResponsiveButtonSize(isMobile, isSmallScreen)

  return (
    <div style={{ padding: spacing.page }}>
      <Space direction="vertical" size={spacing.section} style={{ width: '100%' }}>
        {/* Header */}
        <div>
          <Title level={2}>
            <SettingOutlined /> Маппинг хозяйственных операций
          </Title>
          <Paragraph type="secondary">
            Настройка соответствий между хозяйственными операциями из 1С и категориями бюджета.
            Маппинг используется для автоматической классификации банковских транзакций.
          </Paragraph>
        </div>

        {/* Statistics */}
        <Row gutter={gutter}>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="Всего маппингов"
                value={mappings?.total || 0}
                prefix={<SettingOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="Активных"
                value={activeCount}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="Неактивных"
                value={inactiveCount}
                valueStyle={{ color: '#999' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={12} md={6} lg={6}>
            <Card>
              <Statistic
                title="Выбрано"
                value={selectedRowKeys.length}
                prefix={<CheckOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Filters and Actions */}
        <Card>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Row gutter={gutter}>
              <Col xs={24} sm={24} md={12} lg={12} xl={12}>
                <Input
                  placeholder="Поиск по названию операции..."
                  prefix={<SearchOutlined />}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  allowClear
                  size={buttonSize}
                />
              </Col>
              <Col xs={12} sm={12} md={6} lg={6} xl={6}>
                <Select
                  placeholder="Все статусы"
                  style={{ width: '100%' }}
                  value={activeFilter}
                  onChange={setActiveFilter}
                  allowClear
                  size={buttonSize}
                >
                  <Option value={true}>Активные</Option>
                  <Option value={false}>Неактивные</Option>
                </Select>
              </Col>
              <Col xs={12} sm={12} md={6} lg={6} xl={6}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreate}
                  size={buttonSize}
                  block={isMobile}
                >
                  {isMobile ? 'Создать' : 'Создать маппинг'}
                </Button>
              </Col>
            </Row>

            {selectedRowKeys.length > 0 && (
              <Space direction={isMobile ? 'vertical' : 'horizontal'} size="small" wrap style={{ width: isMobile ? '100%' : 'auto' }}>
                <Text strong>Выбрано: {selectedRowKeys.length}</Text>
                <Button
                  size={buttonSize}
                  icon={<CheckOutlined />}
                  onClick={handleBulkActivate}
                  loading={bulkLoading}
                  block={isMobile}
                >
                  Активировать
                </Button>
                <Button
                  size={buttonSize}
                  icon={<CloseOutlined />}
                  onClick={handleBulkDeactivate}
                  loading={bulkLoading}
                  block={isMobile}
                >
                  Деактивировать
                </Button>
                <Popconfirm
                  title="Удалить выбранные маппинги?"
                  description="Это действие нельзя отменить"
                  onConfirm={handleBulkDelete}
                  okText="Да"
                  cancelText="Нет"
                >
                  <Button
                    size={buttonSize}
                    danger
                    icon={<DeleteOutlined />}
                    loading={bulkLoading}
                    block={isMobile}
                  >
                    Удалить
                  </Button>
                </Popconfirm>
              </Space>
            )}
          </Space>
        </Card>

        {/* Table */}
        <Card>
          <ResponsiveTable
            rowKey="id"
            columns={columns}
            dataSource={mappings?.items || []}
            loading={isLoading}
            rowSelection={rowSelection}
            pagination={{
              current: page,
              pageSize: pageSize,
              total: mappings?.total || 0,
              showSizeChanger: true,
              showTotal: (total) => `Всего: ${total}`,
              onChange: (newPage, newPageSize) => {
                setPage(newPage)
                setPageSize(newPageSize)
              }}}
            scroll={{ x: 1400 }}
            mobileLayout="card"
          />
        </Card>
      </Space>

      {/* Form Modal */}
      <BusinessOperationMappingFormModal
        visible={modalVisible}
        mode={modalMode}
        mapping={selectedMapping}
        onClose={() => {
          setModalVisible(false)
          setSelectedMapping(null)
        }}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['business-operation-mappings'] })
          setModalVisible(false)
          setSelectedMapping(null)
        }}
      />
    </div>
  )
}

export default BusinessOperationMappingsPage
