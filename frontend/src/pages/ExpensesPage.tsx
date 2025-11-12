import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { Table, Button, Space, Tag, Input, Select, DatePicker, message, Tooltip, Badge, Popconfirm, Modal } from 'antd'
import { PlusOutlined, SearchOutlined, DownloadOutlined, EditOutlined, CloudUploadOutlined, CloudDownloadOutlined, DeleteOutlined, DollarOutlined, FileTextOutlined, SwapOutlined } from '@ant-design/icons'
import { expensesApi, categoriesApi, departmentsApi } from '@/api'
import { ExpenseStatus, type Expense } from '@/types'
import { getExpenseStatusLabel, getExpenseStatusColor } from '@/utils/formatters'
import ExpenseFormModal from '@/components/expenses/ExpenseFormModal'
import FTPImportModal from '@/components/expenses/FTPImportModal'
import RegisterPayrollPaymentModal from '@/components/payroll/RegisterPayrollPaymentModal'
import InvoiceProcessingDrawer from '@/components/expenses/InvoiceProcessingDrawer'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const ExpensesPage = () => {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ExpenseStatus | undefined>()
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [registerPaymentModalVisible, setRegisterPaymentModalVisible] = useState(false)
  const [invoiceProcessingDrawerVisible, setInvoiceProcessingDrawerVisible] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [transferModalVisible, setTransferModalVisible] = useState(false)
  const [targetDepartmentId, setTargetDepartmentId] = useState<number | undefined>()

  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()

  // Reset page when department changes
  useEffect(() => {
    setPage(1)
  }, [selectedDepartment?.id])

  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses', page, pageSize, search, status, categoryId, dateRange, selectedDepartment?.id],
    queryFn: () =>
      expensesApi.getAll({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        status,
        category_id: categoryId,
        department_id: selectedDepartment?.id,
        date_from: dateRange?.[0]?.toISOString(),
        date_to: dateRange?.[1]?.toISOString(),
      }),
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll({ is_active: true }),
  })

  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: () => departmentsApi.getAll({ is_active: true }),
  })

  // Bulk delete mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => expensesApi.bulkDelete(ids),
    onSuccess: (data) => {
      message.success(`Удалено заявок: ${data.deleted_count}`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при удалении: ${errorMessage}`)
    },
  })

  // Bulk transfer department mutation
  const bulkTransferMutation = useMutation({
    mutationFn: ({ expenseIds, targetDepartmentId }: { expenseIds: number[]; targetDepartmentId: number }) =>
      expensesApi.bulkTransferDepartment(expenseIds, targetDepartmentId),
    onSuccess: (data) => {
      message.success(data.message || `Переведено заявок: ${data.transferred_count}`)
      setSelectedRowKeys([])
      setTransferModalVisible(false)
      setTargetDepartmentId(undefined)
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message
      message.error(`Ошибка при переносе: ${errorMessage}`)
    },
  })

  const handleBulkDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите заявки для удаления')
      return
    }
    bulkDeleteMutation.mutate(selectedRowKeys)
  }

  const handleBulkTransfer = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите заявки для переноса')
      return
    }
    setTransferModalVisible(true)
  }

  const handleTransferConfirm = () => {
    if (!targetDepartmentId) {
      message.warning('Выберите целевой отдел')
      return
    }
    bulkTransferMutation.mutate({
      expenseIds: selectedRowKeys,
      targetDepartmentId,
    })
  }

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()

      if (status) params.append('status', status)
      if (categoryId) params.append('category_id', categoryId.toString())
      if (selectedDepartment?.id) params.append('department_id', selectedDepartment.id.toString())
      if (search) params.append('search', search)
      if (dateRange?.[0]) params.append('date_from', dateRange[0].toISOString())
      if (dateRange?.[1]) params.append('date_to', dateRange[1].toISOString())

      const token = localStorage.getItem('token')
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const url = `${apiUrl}/api/v1/expenses/export?${params.toString()}`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error(`Ошибка экспорта: ${response.status}`)
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `expenses_export_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      message.success('Файл успешно экспортирован')
    } catch (error: any) {
      console.error('Export error:', error)
      message.error(error.message || 'Ошибка при экспорте данных')
    }
  }

  const handleCreate = () => {
    setModalMode('create')
    setSelectedExpense(null)
    setModalVisible(true)
  }

  const handleEdit = (expense: Expense) => {
    setModalMode('edit')
    setSelectedExpense(expense)
    setModalVisible(true)
  }

  const handleModalCancel = () => {
    setModalVisible(false)
    setSelectedExpense(null)
  }

  const columns = [
    {
      title: 'Номер',
      dataIndex: 'number',
      key: 'number',
      width: 180,
      render: (number: string, record: Expense) => (
        <Space>
          {record.imported_from_ftp && (
            <Tooltip title="Загружена из FTP">
              <CloudDownloadOutlined style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
          {record.needs_review && (
            <Tooltip title="Требует проверки категории">
              <Badge status="warning" />
            </Tooltip>
          )}
          <span>{number}</span>
        </Space>
      ),
    },
    {
      title: 'Дата заявки',
      dataIndex: 'request_date',
      key: 'request_date',
      width: 120,
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: 'Категория',
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 150,
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
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
      render: (_: string, record: Expense) =>
        record.contractor ? (
          <Link
            to={`/contractors/${record.contractor.id}`}
            style={{ color: '#1890ff' }}
          >
            {record.contractor.name}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      title: 'Организация',
      dataIndex: ['organization', 'name'],
      key: 'organization',
      width: 150,
      render: (_: string, record: Expense) =>
        record.organization ? (
          <Link
            to={`/organizations/${record.organization.id}`}
            style={{ color: '#1890ff' }}
          >
            {record.organization.name}
          </Link>
        ) : (
          '-'
        ),
    },
    {
      title: 'Заявитель',
      dataIndex: 'requester',
      key: 'requester',
      width: 150,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Expense) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Изменить
          </Button>
          {record.needs_review && (
            <Tooltip title="Отметить категорию как проверенную">
              <Button
                type="link"
                size="small"
                onClick={async () => {
                  try {
                    await expensesApi.markReviewed(record.id)
                    message.success('Заявка отмечена как проверенная')
                    queryClient.invalidateQueries({ queryKey: ['expenses'] })
                  } catch (error) {
                    message.error('Ошибка при обновлении')
                  }
                }}
                style={{ color: '#52c41a' }}
              >
                ✓ Проверено
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Input
          placeholder="Поиск по номеру, комментарию, заявителю"
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
        <Select
          placeholder="Статус"
          style={{ width: 150 }}
          value={status}
          onChange={setStatus}
          allowClear
          options={[
            { value: ExpenseStatus.DRAFT, label: getExpenseStatusLabel(ExpenseStatus.DRAFT) },
            { value: ExpenseStatus.PENDING, label: getExpenseStatusLabel(ExpenseStatus.PENDING) },
            { value: ExpenseStatus.PAID, label: getExpenseStatusLabel(ExpenseStatus.PAID) },
            { value: ExpenseStatus.REJECTED, label: getExpenseStatusLabel(ExpenseStatus.REJECTED) },
            { value: ExpenseStatus.CLOSED, label: getExpenseStatusLabel(ExpenseStatus.CLOSED) },
          ]}
        />
        <Select
          placeholder="Категория"
          style={{ width: 200 }}
          value={categoryId}
          onChange={setCategoryId}
          allowClear
          options={categories?.map((cat) => ({ value: cat.id, label: cat.name }))}
        />
        <RangePicker
          format="DD.MM.YYYY"
          value={dateRange}
          onChange={setDateRange as any}
        />
        <Button icon={<CloudUploadOutlined />} onClick={() => setImportModalVisible(true)}>
          Импорт из FTP
        </Button>
        <Button
          icon={<FileTextOutlined />}
          onClick={() => setInvoiceProcessingDrawerVisible(true)}
        >
          Обработка счетов AI
        </Button>
        <Button
          icon={<DollarOutlined />}
          onClick={() => setRegisterPaymentModalVisible(true)}
          type="primary"
        >
          Зарегистрировать выплату ЗП
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          Экспорт в Excel
        </Button>
        <Button
          icon={<SwapOutlined />}
          onClick={handleBulkTransfer}
          disabled={selectedRowKeys.length === 0}
        >
          Перенести в отдел ({selectedRowKeys.length})
        </Button>
        <Popconfirm
          title="Удалить выбранные заявки?"
          description={`Вы действительно хотите удалить ${selectedRowKeys.length} заявок?`}
          onConfirm={handleBulkDelete}
          okText="Да"
          cancelText="Отмена"
          disabled={selectedRowKeys.length === 0}
        >
          <Button
            danger
            icon={<DeleteOutlined />}
            disabled={selectedRowKeys.length === 0}
            loading={bulkDeleteMutation.isPending}
          >
            Удалить выбранные ({selectedRowKeys.length})
          </Button>
        </Popconfirm>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Создать заявку
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={expenses?.items}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        rowSelection={{
          selectedRowKeys,
          onChange: (selectedKeys) => setSelectedRowKeys(selectedKeys as number[]),
        }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: expenses?.total,
          showSizeChanger: true,
          showTotal: (total) => `Всего: ${total}`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage)
            setPageSize(newPageSize)
          },
        }}
      />

      <ExpenseFormModal
        visible={modalVisible}
        onCancel={handleModalCancel}
        expense={selectedExpense}
        mode={modalMode}
      />

      <FTPImportModal
        visible={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
      />

      <RegisterPayrollPaymentModal
        open={registerPaymentModalVisible}
        onClose={() => setRegisterPaymentModalVisible(false)}
      />

      <InvoiceProcessingDrawer
        visible={invoiceProcessingDrawerVisible}
        onClose={() => setInvoiceProcessingDrawerVisible(false)}
      />

      <Modal
        title="Перенос заявок в другой отдел"
        open={transferModalVisible}
        onOk={handleTransferConfirm}
        onCancel={() => {
          setTransferModalVisible(false)
          setTargetDepartmentId(undefined)
        }}
        okText="Перенести"
        cancelText="Отмена"
        confirmLoading={bulkTransferMutation.isPending}
      >
        <p>
          Вы собираетесь перенести <strong>{selectedRowKeys.length}</strong> заявок в другой отдел.
        </p>
        <p>Выберите целевой отдел:</p>
        <Select
          style={{ width: '100%' }}
          placeholder="Выберите отдел"
          value={targetDepartmentId}
          onChange={setTargetDepartmentId}
          options={departments?.map((dept) => ({
            label: dept.name,
            value: dept.id,
          }))}
        />
      </Modal>
    </div>
  )
}

export default ExpensesPage
