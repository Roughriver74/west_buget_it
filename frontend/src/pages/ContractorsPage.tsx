import { useState } from 'react'
import { Typography, Card, Button, Space, Tag, Popconfirm, message, Input, Select, Row, Col, Statistic, Upload, Modal } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, TeamOutlined, CheckCircleOutlined, DownloadOutlined, UploadOutlined, CloseOutlined, CheckOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { contractorsApi } from '@/api'
import type { Contractor } from '@/types'
import type { UploadProps } from 'antd'
import axios from 'axios'
import ContractorFormModal from '@/components/contractors/ContractorFormModal'
import { useDepartment } from '@/contexts/DepartmentContext'
import { ResponsiveTable } from '@/components/common/ResponsiveTable'
import { getApiBaseUrl } from '@/config/api'

const { Title, Paragraph } = Typography
const { Option } = Select

const API_BASE = getApiBaseUrl()

const ContractorsPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedContractor, setSelectedContractor] = useState<Contractor | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [bulkLoading, setBulkLoading] = useState(false)
  const { selectedDepartment } = useDepartment()

  const queryClient = useQueryClient()

  const { data: contractors, isLoading } = useQuery({
    queryKey: ['contractors', page, pageSize, search, activeFilter, selectedDepartment?.id],
    queryFn: () =>
      contractorsApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        is_active: activeFilter,
        department_id: selectedDepartment?.id})})

  const deleteMutation = useMutation({
    mutationFn: contractorsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
      message.success('Контрагент успешно удален')
    },
    onError: (error: any) => {
      message.error(`Ошибка при удалении: ${error.message}`)
    }})

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

  const handleExport = () => {
    const url = `${API_BASE}/contractors/export`
    window.open(url, '_blank')
    message.success('Экспорт начат. Файл скоро будет загружен.')
  }

  const handleDownloadTemplate = async () => {
    try {
      const API_BASE = getApiBaseUrl()
      const url = `${API_BASE}/api/v1/templates/download/contractors`

      // Get token from localStorage
      const token = localStorage.getItem('token')

      // Fetch with authentication
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Не удалось скачать шаблон')
      }

      // Create blob and download
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = 'Шаблон_Контрагенты.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      message.success('Шаблон успешно скачан')
    } catch (error) {
      console.error('Template download error:', error)
      message.error('Ошибка при скачивании шаблона')
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    action: `${API_BASE}/contractors/import`,
    accept: '.xlsx,.xls',
    showUploadList: false,
    onChange(info) {
      if (info.file.status === 'done') {
        const response = info.file.response
        message.success(
          `Импорт завершен! Создано: ${response.created_count}, Обновлено: ${response.updated_count}`
        )
        if (response.errors && response.errors.length > 0) {
          Modal.warning({
            title: 'Предупреждения при импорте',
            content: (
              <div>
                {response.errors.map((error: string, index: number) => (
                  <div key={index}>{error}</div>
                ))}
              </div>
            ),
            width: 600})
        }
        queryClient.invalidateQueries({ queryKey: ['contractors'] })
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} загрузка не удалась`)
      }
    }}

  const handleBulkActivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите контрагентов для активации')
      return
    }

    setBulkLoading(true)
    try {
      await axios.post(`${API_BASE}/contractors/bulk/update`, {
        ids: selectedRowKeys,
        is_active: true})
      message.success(`Активировано ${selectedRowKeys.length} контрагентов`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
    } catch (error) {
      message.error('Ошибка при активации контрагентов')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDeactivate = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите контрагентов для деактивации')
      return
    }

    setBulkLoading(true)
    try {
      await axios.post(`${API_BASE}/contractors/bulk/update`, {
        ids: selectedRowKeys,
        is_active: false})
      message.success(`Деактивировано ${selectedRowKeys.length} контрагентов`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['contractors'] })
    } catch (error) {
      message.error('Ошибка при деактивации контрагентов')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите контрагентов для удаления')
      return
    }

    Modal.confirm({
      title: 'Удалить выбранных контрагентов?',
      content: `Будет удалено ${selectedRowKeys.length} контрагентов`,
      onOk: async () => {
        setBulkLoading(true)
        try {
          await axios.post(`${API_BASE}/contractors/bulk/delete`, {
            ids: selectedRowKeys})
          message.success(`Удалено ${selectedRowKeys.length} контрагентов`)
          setSelectedRowKeys([])
          queryClient.invalidateQueries({ queryKey: ['contractors'] })
        } catch (error) {
          message.error('Ошибка при удалении контрагентов')
        } finally {
          setBulkLoading(false)
        }
      }})
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
      )},
    {
      title: 'ИНН',
      dataIndex: 'inn',
      key: 'inn',
      width: 130,
      render: (text: string) => text || '—'},
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 180,
      ellipsis: true,
      render: (text: string) => text || '—'},
    {
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
      render: (text: string) => text || '—'},
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
      )},
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
      )},
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
        <Space style={{ marginBottom: 16 }} wrap>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            Экспорт в Excel
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate} type="dashed">
            Скачать шаблон
          </Button>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>Импорт из Excel</Button>
          </Upload>

          {selectedRowKeys.length > 0 && (
            <>
              <Button
                icon={<CheckOutlined />}
                onClick={handleBulkActivate}
                loading={bulkLoading}
              >
                Активировать ({selectedRowKeys.length})
              </Button>
              <Button
                icon={<CloseOutlined />}
                onClick={handleBulkDeactivate}
                loading={bulkLoading}
              >
                Деактивировать ({selectedRowKeys.length})
              </Button>
              <Button
                icon={<DeleteOutlined />}
                danger
                onClick={handleBulkDelete}
                loading={bulkLoading}
              >
                Удалить ({selectedRowKeys.length})
              </Button>
            </>
          )}
        </Space>

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

        <ResponsiveTable
          columns={columns}
          dataSource={contractors || []}
          loading={isLoading}
          rowKey="id"
          size="middle"
          scroll={{ x: 900 }}
          mobileLayout="card"
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
            pageSizeOptions: ['10', '20', '50', '100']}}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            preserveSelectedRowKeys: true}}
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
