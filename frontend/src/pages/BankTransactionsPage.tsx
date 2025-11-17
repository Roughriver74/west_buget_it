import { useCallback, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  App,
  Button,
  Card,
  Col,
  DatePicker,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Upload,
  Typography,
} from 'antd'
import {
  BankOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  FilterOutlined,
  PlusOutlined,
  ReloadOutlined,
  TagOutlined,
  UploadOutlined,
  WalletOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { bankTransactionsApi, categoriesApi, organizationsApi } from '@/api'
import CategoryCreateModal from '@/components/references/categories/CategoryCreateModal'
import type { BudgetCategory } from '@/types'
import { BankTransactionStatus, BankTransactionType } from '@/types/bankTransaction'
import type { BankTransaction, BankTransactionList } from '@/types/bankTransaction'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import ColumnMappingModal from '@/components/bank/ColumnMappingModal'

const { RangePicker } = DatePicker
const { Search } = Input
const { Paragraph, Text } = Typography

type CategoryCreationContext =
  | { type: 'inline'; record: BankTransaction }
  | { type: 'drawer' }

type AccountBreakdownEntry = {
  key: string
  account?: string | null
  organization?: string | null
  department?: string | null
  credit: number
  debit: number
  net: number
  count: number
  pending: number
}

const BankTransactionsPage = () => {
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const { modal } = App.useApp()
  const { message } = App.useApp()

  // Filters
  const [transactionType, setTransactionType] = useState<BankTransactionType | undefined>()
  const [paymentSource, setPaymentSource] = useState<'BANK' | 'CASH' | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [search, setSearch] = useState('')
  const [onlyUnprocessed, setOnlyUnprocessed] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [accountFilter, setAccountFilter] = useState<{ value: string | null; label: string } | null>(
    null
  )
  const [organizationFilter, setOrganizationFilter] = useState<number | undefined>(undefined)
  const [accountBreakdownCollapsed, setAccountBreakdownCollapsed] = useState(true)
  const [collapsedAccounts, setCollapsedAccounts] = useState<Record<string, boolean>>({})

  // Modals
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [mappingModalOpen, setMappingModalOpen] = useState(false)
  const [odataSyncModalOpen, setOdataSyncModalOpen] = useState(false)
  const [categorizeDrawerOpen, setCategorizeDrawerOpen] = useState(false)
  const [matchingDrawerOpen, setMatchingDrawerOpen] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)
  const [categoryModalInitialName, setCategoryModalInitialName] = useState<string>()
  const [categorySearchValue, setCategorySearchValue] = useState('')

  // Import state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)

  // Selection state
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  // Editable state
  const [editingKey, setEditingKey] = useState<number | null>(null)
  const [editForm] = Form.useForm()

  // Forms
  const [categorizeForm] = Form.useForm()
  const [odataSyncForm] = Form.useForm()
  const [categoryCreationContext, setCategoryCreationContext] =
    useState<CategoryCreationContext | null>(null)

  // Fetch transactions - filter params (MUST be before fetchAllTransactionIds)
  const baseFilterParams = useMemo(
    () => ({
      transaction_type: transactionType,
      payment_source: paymentSource,
      date_from: dateRange?.[0]?.format('YYYY-MM-DD'),
      date_to: dateRange?.[1]?.format('YYYY-MM-DD'),
      search: search || undefined,
      only_unprocessed: onlyUnprocessed,
      department_id: selectedDepartment?.id,
      organization_id: organizationFilter,
    }),
    [
      transactionType,
      paymentSource,
      dateRange,
      search,
      onlyUnprocessed,
      selectedDepartment?.id,
      organizationFilter,
    ]
  )

  const transactionFilterParams = useMemo(() => {
    const params: Record<string, any> = { ...baseFilterParams }
    if (accountFilter) {
      if (accountFilter.value) {
        params.account_number = accountFilter.value
      } else {
        params.account_is_null = true
      }
    }
    return params
  }, [accountFilter, baseFilterParams])

  const fetchAllTransactionIds = useCallback(async () => {
    const limit = 500
    let skip = 0
    let processed = 0
    const ids: number[] = []
    let hasMore = true

    while (hasMore) {
      const response = await bankTransactionsApi.getTransactions({
        skip,
        limit,
        ...transactionFilterParams,
      })

      if (!response.items || response.items.length === 0) break

      ids.push(...response.items.map((item) => item.id))
      processed += response.items.length

      if (processed >= response.total) {
        hasMore = false
      } else {
        skip += limit
      }
    }

    return ids
  }, [transactionFilterParams])

  const openCategoryModal = (initialName?: string, context?: CategoryCreationContext) => {
    setCategoryCreationContext(context ?? null)
    setCategoryModalInitialName(initialName)
    setCategoryModalOpen(true)
  }

  const closeCategoryModal = () => {
    setCategoryModalOpen(false)
    setCategoryCreationContext(null)
    setCategoryModalInitialName(undefined)
    setCategorySearchValue('')
  }

  const bankTransactionsQueryKey = useMemo(
    () => [
      'bankTransactions',
      page,
      pageSize,
      transactionFilterParams,
    ],
    [page, pageSize, transactionFilterParams]
  )

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: bankTransactionsQueryKey,
    queryFn: () =>
      bankTransactionsApi.getTransactions({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...transactionFilterParams,
      }),
  })

  const updateTransactionInCache = useCallback(
    (id: number, patch: Partial<BankTransaction>) => {
      queryClient.setQueryData(bankTransactionsQueryKey, (oldData?: BankTransactionList) => {
        if (!oldData) return oldData
        return {
          ...oldData,
          items: oldData.items.map((item) => (item.id === id ? { ...item, ...patch } : item)),
        }
      })
    },
    [queryClient, bankTransactionsQueryKey]
  )

  const renderCategoryNotFoundContent = (onCreate?: () => void) => (
    <div style={{ padding: 12, textAlign: 'center' }}>
      <Empty description="Категория не найдена" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      {categorySearchValue && (
        <Button
          type="link"
          icon={<PlusOutlined />}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => onCreate?.()}
        >
          Создать "{categorySearchValue}"
        </Button>
      )}
    </div>
  )

  const handleCategoryCreated = (category: BudgetCategory) => {
    if (categoryCreationContext?.type === 'inline') {
      handleInlineCategorySelect(categoryCreationContext.record, category.id)
    } else if (categoryCreationContext?.type === 'drawer') {
      categorizeForm.setFieldsValue({ category_id: category.id })
    }
    closeCategoryModal()
  }

  const promptApplyCategoryToSimilar = useCallback(
    (record: BankTransaction, categoryId: number | null, categoryName?: string) => {
      if (!categoryId || !data?.items) return

      const normalizedInn = record.counterparty_inn?.trim()
      const normalizedName = record.counterparty_name?.toLowerCase().trim()

      const similar = data.items.filter((item) => {
        if (item.id === record.id) return false
        if (item.category_id) return false
        if (normalizedInn && item.counterparty_inn) {
          return item.counterparty_inn.trim() === normalizedInn
        }
        if (normalizedName && item.counterparty_name) {
          return item.counterparty_name.toLowerCase().trim() === normalizedName
        }
        return false
      })

      if (similar.length === 0) return

      modal.confirm({
        title: `Применить категорию "${categoryName || 'выбранную'}"?`,
        content: (
          <div>
            <p>Найдено {similar.length} похожих операций с тем же контрагентом без категории.</p>
            <ul style={{ paddingLeft: 20 }}>
              {similar.slice(0, 3).map((item) => (
                <li key={item.id}>
                  {dayjs(item.transaction_date).format('DD.MM.YYYY')} — {formatCurrency(item.amount)}
                </li>
              ))}
              {similar.length > 3 && <li>и ещё {similar.length - 3}...</li>}
            </ul>
          </div>
        ),
        okText: 'Применить',
        cancelText: 'Не применять',
        onOk: async () => {
          try {
            await bankTransactionsApi.bulkCategorize({
              transaction_ids: similar.map((item) => item.id),
              category_id: categoryId,
            })
            message.success(`Категория применена к ${similar.length} транзакциям`)
            queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
            queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
          } catch (error: any) {
            message.error(error.response?.data?.detail || error.message)
            throw error
          }
        },
      })
    },
    [data?.items, modal, message, queryClient]
  )

  // Fetch stats (with all filters applied)
  const { data: stats } = useQuery({
    queryKey: [
      'bankTransactionsStats',
      transactionFilterParams,
    ],
    queryFn: () =>
      bankTransactionsApi.getStats({
        ...transactionFilterParams,
      }),
  })

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories', selectedDepartment?.id],
    queryFn: () => categoriesApi.getAll({ department_id: selectedDepartment?.id, is_active: true }),
  })

  // Fetch organizations for filters
  const { data: organizations, isLoading: organizationsLoading } = useQuery({
    queryKey: ['organizations', selectedDepartment?.id],
    queryFn: () => organizationsApi.getAll({ is_active: true }),
  })

  // Fetch matching expenses
  const { data: matchingSuggestions, isLoading: matchingLoading } = useQuery({
    queryKey: ['matchingExpenses', selectedTransaction?.id],
    queryFn: () =>
      selectedTransaction
        ? bankTransactionsApi.getMatchingExpenses(selectedTransaction.id, 10)
        : Promise.resolve([]),
    enabled: !!selectedTransaction && matchingDrawerOpen,
  })

  // Fetch AI category suggestions
  const { data: categorySuggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ['categorySuggestions', selectedTransaction?.id],
    queryFn: () =>
      selectedTransaction
        ? bankTransactionsApi.getCategorySuggestions(selectedTransaction.id, 3)
        : Promise.resolve([]),
    enabled: !!selectedTransaction && categorizeDrawerOpen,
  })

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: (file: File) => bankTransactionsApi.previewImport(file),
    onSuccess: (result) => {
      setPreviewData(result)
      setImportModalOpen(false)
      setMappingModalOpen(true)
    },
    onError: (error: any) => {
      message.error(`Ошибка чтения файла: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Import mutation
  const importMutation = useMutation({
    mutationFn: ({ file, mapping }: { file: File; mapping: Record<string, string> }) =>
      bankTransactionsApi.importFromExcel(file, selectedDepartment?.id, mapping),
    onSuccess: (result) => {
      message.success(
        `Импортировано: ${result.imported}, пропущено: ${result.skipped} транзакций`
      )
      if (result.errors.length > 0) {
        message.warning(`Ошибок при импорте: ${result.errors.length}`)
      }
      setMappingModalOpen(false)
      setUploadFile(null)
      setPreviewData(null)
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка импорта: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Categorize mutation
  const categorizeMutation = useMutation({
    mutationFn: ({ id, categoryId, notes }: { id: number; categoryId: number; notes?: string }) =>
      bankTransactionsApi.categorize(id, { category_id: categoryId, notes }),
    onSuccess: () => {
      message.success('Категория установлена')
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
      setCategorizeDrawerOpen(false)
      setSelectedTransaction(null)
      categorizeForm.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Link mutation
  const linkMutation = useMutation({
    mutationFn: ({ id, expenseId }: { id: number; expenseId: number }) =>
      bankTransactionsApi.linkToExpense(id, { expense_id: expenseId }),
    onSuccess: () => {
      message.success('Транзакция связана с заявкой')
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
      setMatchingDrawerOpen(false)
      setSelectedTransaction(null)
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Bulk delete mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: (transactionIds: number[]) => bankTransactionsApi.bulkDelete(transactionIds),
    onSuccess: (result) => {
      message.success(`Удалено транзакций: ${result.deleted}`)
      setSelectedRowKeys([])
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Quick update mutation for inline editing
  type QuickUpdatePayload = {
    id: number
    updates: Record<string, any>
    localPatch?: Partial<BankTransaction>
  }

  const quickUpdateMutation = useMutation({
    mutationFn: ({ id, updates }: QuickUpdatePayload) =>
      bankTransactionsApi.updateTransaction(id, updates),
    onSuccess: (_, variables) => {
      message.success('Транзакция обновлена')
      setEditingKey(null)
      editForm.resetFields()
      if (variables?.localPatch) {
        updateTransactionInCache(variables.id, variables.localPatch)
      }
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления: ${error.response?.data?.detail || error.message}`)
    },
  })

  // OData sync mutation (Background Task)
  const odataSyncMutation = useMutation({
    mutationFn: (params: {
      odata_url: string
      username: string
      password: string
      entity_name?: string
      department_id: number
      organization_id?: number
      date_from?: string
      date_to?: string
    }) => bankTransactionsApi.syncFromOData(params),
    onSuccess: (result) => {
      // Закрываем модалку сразу - синхронизация идет в фоне
      message.success(result.message || 'Синхронизация запущена в фоновом режиме')
      setOdataSyncModalOpen(false)
      odataSyncForm.resetFields()

      // Запускаем polling для проверки статуса
      const taskId = result.task_id
      let pollCount = 0
      const maxPolls = 60 // Максимум 5 минут (60 * 5 сек)

      const pollStatus = async () => {
        try {
          const status = await bankTransactionsApi.getSyncStatus(taskId)

          if (status.status === 'COMPLETED') {
            // Успешно завершено
            const result = status.result!
            message.success(
              `✅ Синхронизация завершена: создано ${result.created}, обновлено ${result.updated}, пропущено ${result.skipped}`
            )
            queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
            queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
          } else if (status.status === 'FAILED') {
            // Ошибка
            message.error(`❌ Синхронизация не удалась: ${status.error || 'Неизвестная ошибка'}`)
          } else if (status.status === 'STARTED') {
            // Еще выполняется - продолжить polling
            pollCount++
            if (pollCount < maxPolls) {
              setTimeout(pollStatus, 5000) // Проверять каждые 5 секунд
            } else {
              message.warning('⏱️ Синхронизация все еще выполняется. Проверьте статус позже.')
            }
          }
        } catch (error: any) {
          console.error('Failed to poll sync status:', error)
          // Не показываем ошибку пользователю - возможно, задача еще выполняется
        }
      }

      // Начать polling через 3 секунды
      setTimeout(pollStatus, 3000)
    },
    onError: (error: any) => {
      message.error(`Ошибка запуска синхронизации: ${error.response?.data?.detail || error.message}`)
    },
  })

  const formatCurrency = (value: number) => {
    const numericValue = Number.isFinite(value) ? value : Number(value) || 0
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(numericValue)
  }
  const formatAccountNumber = useCallback((account?: string | null) => {
    if (!account) return ''
    const sanitized = account.replace(/\s+/g, '')
    if (sanitized.length <= 8) return sanitized
    return `${sanitized.slice(0, 4)}****${sanitized.slice(-4)}`
  }, [])

  const clearAccountFilter = useCallback(() => {
    setAccountFilter(null)
    setPage(1)
  }, [])

  const handleAccountCardClick = useCallback(
    (entry: AccountBreakdownEntry) => {
      setAccountFilter((current) => {
        const entryValue = entry.account ?? null
        const isSame =
          !!current && current.value === entryValue && !!entry.account === !!current.value
        if (isSame) {
          return null
        }
        return {
          value: entryValue,
          label: entry.account ? formatAccountNumber(entry.account) : 'Счёт не указан',
        }
      })
      setPage(1)
    },
    [formatAccountNumber]
  )

  const toggleAccountBreakdownVisibility = useCallback(() => {
    setAccountBreakdownCollapsed((prev) => !prev)
  }, [])

  const toggleAccountCardCollapse = useCallback((key: string) => {
    setCollapsedAccounts((prev) => {
      const current = prev[key] ?? true
      return {
        ...prev,
        [key]: !current,
      }
    })
  }, [])

  const paymentSourceMeta: Record<'BANK' | 'CASH', { label: string; color: string; icon: ReactNode }> = {
    BANK: {
      label: 'Безнал',
      color: 'geekblue',
      icon: <BankOutlined />,
    },
    CASH: {
      label: 'Наличные',
      color: 'gold',
      icon: <WalletOutlined />,
    },
  }

  const pageSnapshot = useMemo(() => {
    const items = data?.items ?? []

    const summary = items.reduce(
      (acc, item) => {
        const amount =
          typeof item.amount === 'number' ? Number(item.amount) : Number(item.amount ?? 0)
        if (item.transaction_type === BankTransactionType.CREDIT) {
          acc.credit += amount
        } else {
          acc.debit += amount
        }
        if (item.status === BankTransactionStatus.NEW || item.status === BankTransactionStatus.NEEDS_REVIEW) {
          acc.pending += 1
        }

        const accountKey = item.account_number || '—'
        if (!acc.banks[accountKey]) {
          acc.banks[accountKey] = {
            key: accountKey,
            account: item.account_number,
            organization: item.organization_name,
            department: item.department_name,
            credit: 0,
            debit: 0,
            count: 0,
          }
        }
        const bucket = acc.banks[accountKey]
        bucket.count += 1
        if (item.transaction_type === BankTransactionType.CREDIT) {
          bucket.credit += amount
        } else {
          bucket.debit += amount
        }

        return acc
      },
      { credit: 0, debit: 0, pending: 0, banks: {} as Record<string, {
        key: string
        account?: string | null
        organization?: string | null
        department?: string | null
        credit: number
        debit: number
        count: number
      }> }
    )

    const bankBreakdown = Object.values(summary.banks)
      .map((bank) => ({
        ...bank,
        total: bank.credit + bank.debit,
      }))
      .sort((a, b) => b.total - a.total)

    return {
      credit: summary.credit,
      debit: summary.debit,
      pending: summary.pending,
      net: summary.credit - summary.debit,
      count: items.length,
      bankBreakdown,
    }
  }, [data?.items])

  const hasTransactions = pageSnapshot.count > 0
  const selectedCount = selectedRowKeys.length

  const filterTotals = useMemo(() => {
    if (!stats) {
      return {
        count: 0,
        pending: 0,
        credit: 0,
        debit: 0,
        net: 0,
      }
    }
    const credit = Number(stats.total_credit_amount ?? 0)
    const debit = Number(stats.total_debit_amount ?? 0)
    return {
      count: stats.total_transactions ?? 0,
      pending: (stats.new_count ?? 0) + (stats.needs_review_count ?? 0),
      credit,
      debit,
      net: credit - debit,
    }
  }, [stats])

  const processedCount = useMemo(() => {
    if (!stats) return 0
    const directTotal =
      (stats.categorized_count ?? 0) +
      (stats.matched_count ?? 0) +
      (stats.approved_count ?? 0)
    if (directTotal > 0) return directTotal
    return Math.max(
      0,
      (stats.total_transactions ?? 0) -
        (stats.new_count ?? 0) -
        (stats.needs_review_count ?? 0)
    )
  }, [stats])

  const bankBreakdownKey = useMemo(() => ['bankBreakdown', baseFilterParams], [baseFilterParams])

  const { data: bankAccountBreakdown, isLoading: bankBreakdownLoading } = useQuery<
    AccountBreakdownEntry[]
  >({
    queryKey: bankBreakdownKey,
    queryFn: async (): Promise<AccountBreakdownEntry[]> => {
      const limit = 500
      let skip = 0
      let processed = 0
      let total = 0
      let hasMore = true
      const summary: Record<
        string,
        AccountBreakdownEntry
      > = {}

      while (hasMore) {
        const response = await bankTransactionsApi.getTransactions({
          skip,
          limit,
          ...baseFilterParams,
        })
        total = response.total
        response.items.forEach((item) => {
          const accountKey = item.account_number || '—'
          if (!summary[accountKey]) {
            summary[accountKey] = {
              key: accountKey,
              account: item.account_number,
              organization: item.organization_name,
              department: item.department_name,
              credit: 0,
              debit: 0,
              count: 0,
              net: 0,
              pending: 0,
            }
          }
          const bucket = summary[accountKey]
          bucket.count += 1
          const amount =
            typeof item.amount === 'number' ? Number(item.amount) : Number(item.amount ?? 0)
          if (item.transaction_type === BankTransactionType.CREDIT) {
            bucket.credit += amount
          } else {
            bucket.debit += amount
          }
          if (
            item.status === BankTransactionStatus.NEW ||
            item.status === BankTransactionStatus.NEEDS_REVIEW
          ) {
            bucket.pending += 1
          }
        })
        processed += response.items.length
        if (processed >= total || response.items.length === 0) {
          hasMore = false
        } else {
          skip += limit
        }
      }

      return Object.values(summary)
        .map((entry) => ({
          ...entry,
          net: entry.credit - entry.debit,
        }))
        .sort((a, b) => (b.credit + b.debit) - (a.credit + a.debit))
    },
    enabled: !isNaN(data?.total ?? 0) && (data?.total ?? 0) > 0,
  })

  const shouldShowAccountBreakdown =
    bankBreakdownLoading || (bankAccountBreakdown && bankAccountBreakdown.length > 0)

  const columns: ColumnsType<BankTransaction> = [
    {
      title: 'Дата',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 170,
      sorter: (a, b) => dayjs(a.transaction_date).unix() - dayjs(b.transaction_date).unix(),
      render: (date: string, record) => (
        <div className="transaction-date-cell">
          <Text strong className="transaction-date-main">
            {dayjs(date).format('DD MMM YYYY')}
          </Text>
          <div className="transaction-date-sub">
            <Text type="secondary">{dayjs(date).format('ddd')}</Text>
            {record.document_number && (
              <Tooltip
                title={`Документ №${record.document_number}${record.document_date ? ` от ${dayjs(record.document_date).format('DD.MM.YYYY')}` : ''}`}
              >
                <Tag color="purple" icon={<FileTextOutlined />} className="transaction-chip">
                  № {record.document_number}
                </Tag>
              </Tooltip>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 150,
      align: 'right',
      sorter: (a, b) => a.amount - b.amount,
      render: (amount: number, record) => {
        const isCredit = record.transaction_type === BankTransactionType.CREDIT
        return (
            <div className="transaction-amount-cell">
              <div className={`transaction-amount ${isCredit ? 'credit' : 'debit'}`}>
                {isCredit ? '+' : '-'}
                {formatCurrency(amount)}
              </div>
            <div className="transaction-amount-meta">
              {typeof record.matching_score === 'number' && (
                <Tooltip title="Точность сопоставления с расходом">
                  <Tag color="blue" className="transaction-chip">
                    Совпадение {Math.round(record.matching_score * 100)}%
                  </Tag>
                </Tooltip>
              )}
            </div>
          </div>
        )
      },
    },
    {
      title: 'Форма оплаты',
      key: 'payment_source',
      width: 260,
      render: (_, record) => {
        const sourceMeta = record.payment_source ? paymentSourceMeta[record.payment_source] : undefined
        return (
          <div className="payment-form-cell">
            <div className="payment-form-row">
              {sourceMeta ? (
                <Tag color={sourceMeta.color} icon={sourceMeta.icon} className="transaction-chip mini-chip">
                  {sourceMeta.label}
                </Tag>
              ) : (
                <Text type="secondary">Форма не указана</Text>
              )}
              {record.import_source && (
                <Tooltip title={`Источник данных: ${record.import_source}`}>
                  <CloudUploadOutlined className="payment-form-icon" />
                </Tooltip>
              )}
            </div>
            <div className="payment-form-row payment-org-row">
              <Text strong>{record.organization_name || 'Организация не указана'}</Text>
              {record.department_name && (
                <Tag className="transaction-chip mini-chip" icon={<TagOutlined />}>
                  {record.department_name}
                </Tag>
              )}
            </div>
            <div className="payment-form-row">
              {record.account_number && (
                <Tooltip title={`Расчетный счет ${record.account_number}`}>
                  <div className="bank-account-chip">
                    {formatAccountNumber(record.account_number)}
                  </div>
                </Tooltip>
              )}
              {record.import_file_name && (
                <Tooltip title={`Файл импорта: ${record.import_file_name}`}>
                  <FileTextOutlined className="payment-form-icon" />
                </Tooltip>
              )}
            </div>
            {record.counterparty_bank && (
              <div className="payment-form-row">
                <Text type="secondary">{record.counterparty_bank}</Text>
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: 'Контрагент',
      dataIndex: 'counterparty_name',
      key: 'counterparty_name',
      width: 280,
      render: (name: string, record) => (
        <div className="counterparty-cell">
          <Text strong>{name || 'Не указан'}</Text>
          {(record.counterparty_inn || record.counterparty_kpp || record.counterparty_bank) && (
            <Space size={4} wrap>
              {record.counterparty_inn && (
                <Tag className="transaction-chip">ИНН {record.counterparty_inn}</Tag>
              )}
              {record.counterparty_kpp && (
                <Tag className="transaction-chip" color="default">
                  КПП {record.counterparty_kpp}
                </Tag>
              )}
              {record.counterparty_bank && (
                <Tag className="transaction-chip" icon={<BankOutlined />}>
                  {record.counterparty_bank}
                </Tag>
              )}
            </Space>
          )}
        </div>
      ),
    },
    {
      title: 'Назначение',
      dataIndex: 'payment_purpose',
      key: 'payment_purpose',
      width: 320,
      render: (purpose: string) => (
        <div className="transaction-purpose-cell">
          <Paragraph
            className="transaction-purpose-text"
            ellipsis={{ rows: 2, expandable: true, symbol: 'ещё' }}
          >
            {purpose || 'Назначение не заполнено'}
          </Paragraph>
        </div>
      ),
    },
    {
      title: 'Обработка',
      key: 'processing',
      width: 360,
      fixed: 'right',
      render: (_, record) => {
        const editable = isEditing(record)
        if (editable) {
          return (
            <div className="processing-editor">
              <Form.Item
                name="category_id"
                style={{ marginBottom: 0 }}
                rules={[{ required: false }]}
              >
                <Select
                  placeholder="Категория"
                  allowClear
                  loading={!categories}
                  options={(categories || []).map((cat: BudgetCategory) => ({
                    value: cat.id,
                    label: cat.name,
                  }))}
                  showSearch
                  filterOption={(input, option) =>
                    String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  onSearch={(value) => setCategorySearchValue(value)}
                  notFoundContent={renderCategoryNotFoundContent(() =>
                    openCategoryModal(categorySearchValue, { type: 'inline', record })
                  )}
                  autoFocus
                  onChange={(value) => {
                    editForm.setFieldsValue({ category_id: value })
                    handleInlineCategorySelect(record, value as number | null)
                  }}
                  onBlur={handleCancel}
                />
              </Form.Item>
            </div>
          )
        }

        const renderCategoryChip = () => {
          if (record.category_name) {
            const isAutoCategory = record.category_confidence && record.category_confidence >= 0.9
            return (
              <Space size={4} wrap>
                <Tag color="blue" className="transaction-chip">
                  {record.category_name}
                  {record.category_confidence && (
                    <span style={{ marginLeft: 4, fontSize: 11 }}>
                      ({Math.round(record.category_confidence * 100)}%)
                    </span>
                  )}
                </Tag>
                {isAutoCategory && (
                  <Tag color="green" className="transaction-chip mini-chip">
                    Авто
                  </Tag>
                )}
              </Space>
            )
          }
          if (record.suggested_category_name) {
            return (
              <Tag color="orange" icon={<ExclamationCircleOutlined />} className="transaction-chip">
                {record.suggested_category_name}
              </Tag>
            )
          }
          return <Tag className="transaction-chip mini-chip">Категория?</Tag>
        }

        return (
          <div className="processing-cell">
            <div
              className="processing-row processing-category-row"
              onClick={() => handleCategoryChipClick(record)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  handleCategoryChipClick(record)
                }
              }}
            >
              {renderCategoryChip()}
            </div>
          </div>
        )
      },
    },
  ]

  const handleImport = () => {
    if (!uploadFile) {
      message.warning('Выберите файл для импорта')
      return
    }

    // Для MANAGER и ADMIN требуется выбрать отдел
    if (user && ['MANAGER', 'ADMIN'].includes(user.role)) {
      if (!selectedDepartment) {
        message.error('Выберите отдел для импорта данных')
        return
      }
    }

    // Start with preview
    previewMutation.mutate(uploadFile)
  }

  const handleConfirmMapping = (mapping: Record<string, string>) => {
    if (!uploadFile) return
    importMutation.mutate({ file: uploadFile, mapping })
  }

  const handleCategorize = (values: any) => {
    if (!selectedTransaction) return
    categorizeMutation.mutate({
      id: selectedTransaction.id,
      categoryId: values.category_id,
      notes: values.notes,
    })
  }

  const handleLinkToExpense = (expenseId: number) => {
    if (!selectedTransaction) return
    linkMutation.mutate({
      id: selectedTransaction.id,
      expenseId,
    })
  }

  const handleBulkDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите транзакции для удаления')
      return
    }

    modal.confirm({
      title: 'Подтверждение удаления',
      content: `Вы уверены, что хотите удалить ${selectedRowKeys.length} транзакций? Это действие нельзя отменить.`,
      okText: 'Удалить',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: () => {
        bulkDeleteMutation.mutate(selectedRowKeys)
      },
    })
  }

  const handleDeleteAll = () => {
    modal.confirm({
      title: 'Удалить все транзакции?',
      content: `Вы уверены, что хотите удалить ВСЕ транзакции, подходящие под текущие фильтры? Это действие нельзя отменить.`,
      okText: 'Удалить всё',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: async () => {
        const allIds = await fetchAllTransactionIds()
        if (allIds.length === 0) {
          message.warning('Нет транзакций для удаления')
          return Promise.reject()
        }
        return bulkDeleteMutation.mutateAsync(allIds)
      },
    })
  }

  const isEditing = (record: BankTransaction) => record.id === editingKey

  const handleEdit = (record: BankTransaction) => {
    editForm.setFieldsValue({
      category_id: record.category_id,
      status: record.status,
      notes: record.notes,
    })
    setEditingKey(record.id)
  }

  const handleCancel = () => {
    setEditingKey(null)
    editForm.resetFields()
    setCategorySearchValue('')
  }

  const handleCategoryChipClick = (record: BankTransaction) => {
    if (editingKey && editingKey !== record.id) {
      message.warning('Завершите редактирование другой строки')
      return
    }
    setCategorySearchValue('')
    handleEdit(record)
  }

  const handleInlineCategorySelect = (record: BankTransaction, value: number | null) => {
    const updates: Record<string, any> = {
      category_id: value ?? undefined,
    }

    const selectedCategory = value
      ? (categories || []).find((cat: BudgetCategory) => cat.id === value)
      : null

    const localPatch: Partial<BankTransaction> = {
      category_id: value ?? undefined,
      category_name: selectedCategory?.name,
      suggested_category_name: value ? undefined : record.suggested_category_name,
    }

    if (
      value &&
      (record.status === BankTransactionStatus.NEW ||
        record.status === BankTransactionStatus.NEEDS_REVIEW ||
        record.status === undefined)
    ) {
      updates.status = BankTransactionStatus.CATEGORIZED
      localPatch.status = BankTransactionStatus.CATEGORIZED
    }

    quickUpdateMutation.mutate(
      { id: record.id, updates, localPatch },
      {
        onSuccess: () => {
          if (value) {
            promptApplyCategoryToSimilar(record, value, selectedCategory?.name)
          }
        },
      }
    )
  }

  const handleODataSync = async () => {
    if (!selectedDepartment) {
      message.error('Выберите отдел для синхронизации')
      return
    }

    try {
      const values = await odataSyncForm.validateFields()

      // Параметры подключения по умолчанию
      const defaultODataUrl = 'http://10.10.100.77/trade/odata/standard.odata'
      const defaultUsername = 'odata.user'
      const defaultPassword = 'ak228Hu2hbs28'

      odataSyncMutation.mutate({
        odata_url: defaultODataUrl,
        username: defaultUsername,
        password: defaultPassword,
        department_id: selectedDepartment.id,
        date_from: values.date_range?.[0]?.format('YYYY-MM-DD'),
        date_to: values.date_range?.[1]?.format('YYYY-MM-DD'),
      })
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  return (
    <div>
      {/* Stats */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card>
              <Statistic
                title="Всего транзакций"
                value={stats.total_transactions}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={5}>
            <Card>
              <Statistic
                title="💰 Приход (CREDIT)"
                value={stats.total_credit_amount}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ color: '#52c41a', fontWeight: 600 }}
                prefix="+"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8} lg={5}>
            <Card>
              <Statistic
                title="💸 Расход (DEBIT)"
                value={stats.total_debit_amount}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ color: '#ff4d4f', fontWeight: 600 }}
                prefix="-"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={12} lg={5}>
            <Card>
              <Statistic
                title="Требует обработки"
                value={filterTotals.pending}
                valueStyle={{ color: '#faad14' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={12} lg={5}>
            <Card>
              <Statistic
                title="Обработано"
                value={processedCount}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Account breakdown cards */}
      {shouldShowAccountBreakdown &&
        (accountBreakdownCollapsed ? (
          <div
            style={{
              marginBottom: 8,
              display: 'flex',
              justifyContent: 'flex-start',
            }}
          >
            <Button
              type="dashed"
              icon={<DownOutlined />}
              onClick={toggleAccountBreakdownVisibility}
            >
              Показать блок счетов
            </Button>
          </div>
        ) : (
          <Card
            style={{ marginBottom: 16 }}
            title={
              <Space align="center">
                <BankOutlined />
                <span>Приход / расход по счетам</span>
              </Space>
            }
            extra={
              <Button
                type="link"
                icon={<UpOutlined />}
                onClick={toggleAccountBreakdownVisibility}
              >
                Свернуть блок
              </Button>
            }
          >
            {bankBreakdownLoading ? (
              <div className="account-breakdown-loading">Загрузка разбивки по счетам...</div>
            ) : bankAccountBreakdown && bankAccountBreakdown.length > 0 ? (
              <div className="account-breakdown-grid">
                {bankAccountBreakdown.map((bank) => {
                  const accountValue = bank.account ?? null
                  const isActive = !!accountFilter && accountFilter.value === accountValue
                  const cardKey = String(bank.key)
                  const isCollapsed = collapsedAccounts[cardKey] ?? true
                  return (
                    <div
                      key={`${bank.key}-${bank.organization || 'unknown'}`}
                      className={`account-breakdown-card${isActive ? ' account-breakdown-card--active' : ''}${isCollapsed ? ' account-breakdown-card--collapsed' : ''}`}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleAccountCardClick(bank)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleAccountCardClick(bank)
                        }
                      }}
                    >
                      <div className="account-breakdown-card__header">
                        <span className="account-breakdown-card__account">
                          {bank.account ? formatAccountNumber(bank.account) : 'Счёт не указан'}
                        </span>
                        <Space size={8} align="center">
                          <span className="account-breakdown-card__count">{bank.count} шт.</span>
                          <Button
                            size="small"
                            type="text"
                            icon={isCollapsed ? <DownOutlined /> : <UpOutlined />}
                            onClick={(e) => {
                              e.stopPropagation()
                              toggleAccountCardCollapse(cardKey)
                            }}
                            aria-label={isCollapsed ? 'Развернуть карточку счёта' : 'Свернуть карточку счёта'}
                          />
                        </Space>
                      </div>
                      {!isCollapsed && (
                        <>
                          <div className="account-breakdown-card__org">
                            <Text strong>{bank.organization || 'Организация не указана'}</Text>
                            {bank.department && (
                              <Tag className="account-breakdown-card__dept" icon={<TagOutlined />}>
                                {bank.department}
                              </Tag>
                            )}
                          </div>
                          <div className="account-breakdown-card__metrics">
                            <div className="account-breakdown-card__metric">
                              <span>Приход</span>
                              <strong className="credit">+{formatCurrency(bank.credit)}</strong>
                            </div>
                            <div className="account-breakdown-card__metric">
                              <span>Расход</span>
                              <strong className="debit">-{formatCurrency(bank.debit)}</strong>
                            </div>
                            <div
                              className={`account-breakdown-card__metric ${
                                bank.net >= 0 ? 'net-positive' : 'net-negative'
                              }`}
                            >
                              <span>Сальдо</span>
                              <strong>
                                {bank.net >= 0 ? '+' : '-'}
                                {formatCurrency(Math.abs(bank.net))}
                              </strong>
                            </div>
                          </div>
                          {bank.pending > 0 && (
                            <div className="account-breakdown-card__pending">
                              Требует обработки: {bank.pending}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <Empty description="Нет данных по счетам" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        ))}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* Action Buttons Row */}
          <Space wrap>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setImportModalOpen(true)}
            >
              Импорт из Excel
            </Button>
            {user && ['MANAGER', 'ADMIN'].includes(user.role) && (
              <Button
                type="primary"
                onClick={() => setOdataSyncModalOpen(true)}
                style={{ background: '#52c41a', borderColor: '#52c41a' }}
              >
                Синхронизация с 1С
              </Button>
            )}
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Обновить
            </Button>
            {user && ['MANAGER', 'ADMIN'].includes(user.role) && (data?.total || 0) > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleDeleteAll}
                loading={bulkDeleteMutation.isPending}
              >
                Удалить все ({data?.total})
              </Button>
            )}
          </Space>

          {/* Quick Filters Row - Transaction Type */}
          <div>
            <span style={{ marginRight: 12, fontWeight: 500 }}>Тип операции:</span>
            <Space wrap>
              <Button
                size="small"
                type={transactionType === BankTransactionType.CREDIT ? 'primary' : 'default'}
                onClick={() => setTransactionType(transactionType === BankTransactionType.CREDIT ? undefined : BankTransactionType.CREDIT)}
                style={{ backgroundColor: transactionType === BankTransactionType.CREDIT ? '#52c41a' : undefined }}
              >
                ✅ Приход
              </Button>
              <Button
                size="small"
                type={transactionType === BankTransactionType.DEBIT ? 'primary' : 'default'}
                onClick={() => setTransactionType(transactionType === BankTransactionType.DEBIT ? undefined : BankTransactionType.DEBIT)}
                style={{ backgroundColor: transactionType === BankTransactionType.DEBIT ? '#ff4d4f' : undefined }}
              >
                ❌ Расход
              </Button>
              <Button
                size="small"
                danger
                type={!transactionType ? 'primary' : 'default'}
                onClick={() => setTransactionType(undefined)}
              >
                Сбросить тип
              </Button>
            </Space>
          </div>

          {/* Quick Filters Row - Payment Source */}
          <div>
            <span style={{ marginRight: 12, fontWeight: 500 }}>Форма оплаты:</span>
            <Space wrap>
              <Button
                size="small"
                type={paymentSource === 'BANK' ? 'primary' : 'default'}
                onClick={() => setPaymentSource(paymentSource === 'BANK' ? undefined : 'BANK')}
              >
                💳 Безнал
              </Button>
              <Button
                size="small"
                type={paymentSource === 'CASH' ? 'primary' : 'default'}
                onClick={() => setPaymentSource(paymentSource === 'CASH' ? undefined : 'CASH')}
              >
                💵 Наличные
              </Button>
              <Button
                size="small"
                danger
                type={!paymentSource ? 'primary' : 'default'}
                onClick={() => setPaymentSource(undefined)}
              >
                Сбросить форму
              </Button>
            </Space>
          </div>

          {/* Quick Date Filters Row */}
          <div>
            <span style={{ marginRight: 12, fontWeight: 500 }}>Период:</span>
            <Space wrap>
              <Button
                size="small"
                type={dateRange && dayjs().isSame(dateRange[0], 'day') && dayjs().isSame(dateRange[1], 'day') ? 'primary' : 'default'}
                onClick={() => setDateRange([dayjs().startOf('day'), dayjs().endOf('day')])}
              >
                Сегодня
              </Button>
              <Button
                size="small"
                type={dateRange && dayjs().subtract(1, 'day').isSame(dateRange[0], 'day') && dayjs().subtract(1, 'day').isSame(dateRange[1], 'day') ? 'primary' : 'default'}
                onClick={() => setDateRange([dayjs().subtract(1, 'day').startOf('day'), dayjs().subtract(1, 'day').endOf('day')])}
              >
                Вчера
              </Button>
              <Button
                size="small"
                type={dateRange && dayjs().startOf('month').isSame(dateRange[0], 'day') && dayjs().endOf('month').isSame(dateRange[1], 'day') ? 'primary' : 'default'}
                onClick={() => setDateRange([dayjs().startOf('month'), dayjs().endOf('month')])}
              >
                Этот месяц
              </Button>
              <Button
                size="small"
                onClick={() => setDateRange([dayjs().subtract(1, 'month').startOf('month'), dayjs().subtract(1, 'month').endOf('month')])}
              >
                Прошлый месяц
              </Button>
              <Button
                size="small"
                onClick={() => setDateRange([dayjs().startOf('year'), dayjs().endOf('year')])}
              >
                Этот год
              </Button>
              <Button
                size="small"
                onClick={() => setDateRange([dayjs().subtract(1, 'year').startOf('year'), dayjs().subtract(1, 'year').endOf('year')])}
              >
                Прошлый год
              </Button>
              <Button
                size="small"
                danger
                type={!dateRange ? 'primary' : 'default'}
                onClick={() => setDateRange(null)}
              >
                Сбросить даты
              </Button>
            </Space>
          </div>

          <Space wrap>
            <Select
              placeholder="Организация"
              allowClear
              showSearch
              optionFilterProp="label"
              style={{ minWidth: 220 }}
              loading={organizationsLoading}
              value={organizationFilter}
              onChange={(value) => setOrganizationFilter(value ?? undefined)}
              options={(organizations || []).map((org) => ({
                value: org.id,
                label: org.name,
              }))}
            />
            <Search
              placeholder="Поиск по контрагенту, ИНН, назначению..."
              style={{ width: 350 }}
              onSearch={setSearch}
              allowClear
            />
            <Button
              type={onlyUnprocessed ? 'primary' : 'default'}
              icon={<FilterOutlined />}
              onClick={() => setOnlyUnprocessed(!onlyUnprocessed)}
            >
              Только необработанные
            </Button>
            {accountFilter && (
              <Tag
                color="geekblue"
                closable
                onClose={(e) => {
                  e.preventDefault()
                  clearAccountFilter()
                }}
                style={{ marginLeft: 4 }}
              >
                Счёт: {accountFilter.label}
              </Tag>
            )}
          </Space>
        </Space>
      </Card>

      {/* Table */}
      <Card>
        {/* Bulk actions */}
        {selectedRowKeys.length > 0 && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Space>
              <span>Выбрано: {selectedRowKeys.length}</span>
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBulkDelete}
                loading={bulkDeleteMutation.isPending}
                disabled={!user || !['MANAGER', 'ADMIN'].includes(user.role)}
              >
                Удалить выбранные
              </Button>
              <Button size="small" onClick={() => setSelectedRowKeys([])}>
                Отменить выбор
              </Button>
            </Space>
          </div>
        )}

        <Form form={editForm} component={false}>
          <Table
            className="bank-transactions-table"
            columns={columns}
            dataSource={data?.items || []}
            rowKey="id"
            size="middle"
            scroll={{ x: 1700 }}
            sticky={{ offsetHeader: 64 }}
            title={() => (
              <div className="bank-transactions-table__title">
                <Space size="large" wrap>
                  <div className="table-metric">
                    <span>На странице</span>
                    <strong>{pageSnapshot.count}</strong>
                  </div>
                  <div className="table-metric">
                    <span>Выбрано</span>
                    <strong>{selectedCount}</strong>
                  </div>
                  <div className="table-metric table-metric--pending">
                    <span>Нуждаются в обработке</span>
                    <strong>{filterTotals.pending}</strong>
                  </div>
                </Space>
              </div>
            )}
                footer={
                  hasTransactions
                    ? () => (
                        <div className="bank-transactions-table__footer">
                          <Space size="middle" wrap>
                            <div className="footer-pill footer-pill--credit">
                              Приход (фильтр) <strong>{formatCurrency(filterTotals.credit)}</strong>
                            </div>
                            <div className="footer-pill footer-pill--debit">
                              Расход (фильтр) <strong>{formatCurrency(filterTotals.debit)}</strong>
                            </div>
                            <div className="footer-pill footer-pill--net">
                              Сальдо {filterTotals.net >= 0 ? '+' : '-'}
                              <strong>{formatCurrency(Math.abs(filterTotals.net))}</strong>
                            </div>
                          </Space>
                        </div>
                      )
                : undefined
            }
            rowClassName={(record) => {
              // Цветовое выделение согласно ТЗ:
              // Расход (DEBIT) — красный
              // Приход (CREDIT) — зелёный
              if (record.transaction_type === BankTransactionType.DEBIT) {
                return 'bank-transaction-debit'
              } else if (record.transaction_type === BankTransactionType.CREDIT) {
                return 'bank-transaction-credit'
              }
              return ''
            }}
            rowSelection={{
              selectedRowKeys,
              onChange: (keys) => setSelectedRowKeys(keys as number[]),
              getCheckboxProps: () => ({
                disabled: !user || !['MANAGER', 'ADMIN'].includes(user.role),
              }),
            }}
            pagination={{
              current: page,
              pageSize,
              total: data?.total || 0,
              showSizeChanger: true,
              showTotal: (total) => `Всего ${total} транзакций`,
              onChange: (newPage, newPageSize) => {
                setPage(newPage)
                setPageSize(newPageSize)
              },
            }}
          />
        </Form>
      </Card>

      {/* Import Modal */}
      <Modal
        title="Импорт банковских операций"
        open={importModalOpen}
        onOk={handleImport}
        onCancel={() => {
          setImportModalOpen(false)
          setUploadFile(null)
        }}
        confirmLoading={previewMutation.isPending}
        okText="Далее"
      >
        {/* Department info for MANAGER/ADMIN */}
        {user && ['MANAGER', 'ADMIN'].includes(user.role) && (
          <div style={{
            marginBottom: 16,
            padding: 12,
            background: selectedDepartment ? '#f6ffed' : '#fff7e6',
            border: `1px solid ${selectedDepartment ? '#b7eb8f' : '#ffd591'}`,
            borderRadius: 4,
          }}>
            {selectedDepartment ? (
              <div>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <strong>Отдел:</strong> {selectedDepartment.name}
              </div>
            ) : (
              <div>
                <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
                <strong>Внимание:</strong> Выберите отдел в фильтрах для импорта данных
              </div>
            )}
          </div>
        )}

        <p>
          Загрузите файл Excel с банковской выпиской. Система автоматически определит колонки.
        </p>
        <Upload
          beforeUpload={(file) => {
            setUploadFile(file)
            return false
          }}
          maxCount={1}
          accept=".xlsx,.xls"
        >
          <Button icon={<UploadOutlined />}>Выбрать файл</Button>
        </Upload>
        {uploadFile && <div style={{ marginTop: 8 }}>Выбран файл: {uploadFile.name}</div>}
      </Modal>

      {/* Categorize Drawer */}
      <Drawer
        title="Установить категорию"
        open={categorizeDrawerOpen}
        onClose={() => {
          setCategorizeDrawerOpen(false)
          setSelectedTransaction(null)
          categorizeForm.resetFields()
          setCategorySearchValue('')
        }}
        width={500}
      >
        {selectedTransaction && (
          <div>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <div><strong>Контрагент:</strong> {selectedTransaction.counterparty_name}</div>
              <div><strong>Сумма:</strong> {formatCurrency(selectedTransaction.amount)}</div>
              <div><strong>Дата:</strong> {dayjs(selectedTransaction.transaction_date).format('DD.MM.YYYY')}</div>
              {selectedTransaction.payment_purpose && (
                <div><strong>Назначение:</strong> {selectedTransaction.payment_purpose}</div>
              )}
            </div>

            {/* AI Suggestions */}
            {suggestionsLoading ? (
              <div style={{ textAlign: 'center', padding: 16 }}>
                <span>Поиск подходящих категорий...</span>
              </div>
            ) : categorySuggestions && categorySuggestions.length > 0 ? (
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>
                  🤖 AI рекомендует:
                </div>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {categorySuggestions.map((suggestion) => (
                    <Card
                      key={suggestion.category_id}
                      size="small"
                      hoverable
                      style={{
                        borderColor: suggestion.confidence >= 0.9 ? '#52c41a' : suggestion.confidence >= 0.7 ? '#1890ff' : '#faad14',
                        cursor: 'pointer',
                      }}
                      onClick={() => {
                        categorizeForm.setFieldsValue({ category_id: suggestion.category_id })
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 500 }}>{suggestion.category_name}</div>
                          <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                            {suggestion.reasoning.join(', ')}
                          </div>
                        </div>
                        <Tag color={suggestion.confidence >= 0.9 ? 'green' : suggestion.confidence >= 0.7 ? 'blue' : 'orange'}>
                          {Math.round(suggestion.confidence * 100)}%
                        </Tag>
                      </div>
                    </Card>
                  ))}
                </Space>
              </div>
            ) : null}

            <Form form={categorizeForm} layout="vertical" onFinish={handleCategorize}>
              <Form.Item
                name="category_id"
                label="Категория"
                rules={[{ required: true, message: 'Выберите категорию' }]}
              >
                <Select
                  showSearch
                  placeholder="Выберите категорию"
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  onSearch={(value) => setCategorySearchValue(value)}
                  notFoundContent={renderCategoryNotFoundContent(() =>
                    openCategoryModal(categorySearchValue, { type: 'drawer' })
                  )}
                  options={categories?.map((cat: BudgetCategory) => ({
                    value: cat.id,
                    label: cat.name,
                  }))}
                />
              </Form.Item>

              <Form.Item name="notes" label="Примечания">
                <Input.TextArea rows={3} placeholder="Дополнительные комментарии..." />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={categorizeMutation.isPending}
                  block
                >
                  Сохранить
                </Button>
              </Form.Item>
            </Form>
          </div>
        )}
      </Drawer>

      <CategoryCreateModal
        open={categoryModalOpen}
        onClose={closeCategoryModal}
        initialName={categoryModalInitialName}
        onCreated={handleCategoryCreated}
      />

      {/* Matching Drawer */}
      <Drawer
        title="Связать с заявкой"
        open={matchingDrawerOpen}
        onClose={() => {
          setMatchingDrawerOpen(false)
          setSelectedTransaction(null)
        }}
        width={600}
      >
        {selectedTransaction && (
          <div>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <div><strong>Контрагент:</strong> {selectedTransaction.counterparty_name}</div>
              <div><strong>Сумма:</strong> {formatCurrency(selectedTransaction.amount)}</div>
              <div><strong>Дата:</strong> {dayjs(selectedTransaction.transaction_date).format('DD.MM.YYYY')}</div>
            </div>

            {matchingLoading ? (
              <LoadingState />
            ) : matchingSuggestions && matchingSuggestions.length > 0 ? (
              <div>
                <h4>Найденные заявки:</h4>
                {matchingSuggestions.map((suggestion) => (
                  <Card
                    key={suggestion.expense_id}
                    size="small"
                    style={{ marginBottom: 12 }}
                    actions={[
                      <Button
                        key="link"
                        type="link"
                        onClick={() => handleLinkToExpense(suggestion.expense_id)}
                        loading={linkMutation.isPending}
                      >
                        Связать
                      </Button>,
                    ]}
                  >
                    <div>
                      <strong>Заявка #{suggestion.expense_number}</strong>
                      <Tag color="blue" style={{ marginLeft: 8 }}>
                        {Math.round(suggestion.matching_score)}%
                      </Tag>
                    </div>
                    <div>Сумма: {formatCurrency(suggestion.expense_amount)}</div>
                    <div>Дата: {dayjs(suggestion.expense_date).format('DD.MM.YYYY')}</div>
                    {suggestion.expense_contractor_name && (
                      <div>Контрагент: {suggestion.expense_contractor_name}</div>
                    )}
                    <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                      {suggestion.match_reasons.join(', ')}
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 24, color: '#8c8c8c' }}>
                Подходящие заявки не найдены
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* Column Mapping Modal */}
      <ColumnMappingModal
        open={mappingModalOpen}
        onCancel={() => {
          setMappingModalOpen(false)
          setPreviewData(null)
          setUploadFile(null)
        }}
        onConfirm={handleConfirmMapping}
        previewData={previewData}
        loading={importMutation.isPending}
      />

      {/* OData Sync Modal */}
      <Modal
        title="Синхронизация с 1С через OData"
        open={odataSyncModalOpen}
        onOk={handleODataSync}
        onCancel={() => {
          setOdataSyncModalOpen(false)
          odataSyncForm.resetFields()
        }}
        width={700}
        confirmLoading={odataSyncMutation.isPending}
        okText="Синхронизировать"
        cancelText="Отмена"
      >
        <div style={{ marginBottom: 16 }}>
          <p>
            Синхронизация банковских операций из 1С через протокол OData.
            Система автоматически создаст новые транзакции и обновит существующие.
          </p>
          {selectedDepartment && (
            <div style={{
              padding: 12,
              background: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: 4,
              marginBottom: 16,
            }}>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              <strong>Отдел:</strong> {selectedDepartment.name}
            </div>
          )}
        </div>

        <Form form={odataSyncForm} layout="vertical">
          <Form.Item
            name="date_range"
            label="Период синхронизации"
            rules={[{ required: true, message: 'Выберите период' }]}
          >
            <RangePicker
              style={{ width: '100%' }}
              format="DD.MM.YYYY"
              placeholder={['Дата начала', 'Дата окончания']}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default BankTransactionsPage
