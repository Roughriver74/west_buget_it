import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import { useTheme } from '@/contexts/ThemeContext'
import {
  receiptsAPI,
  expensesAPI,
  expenseDetailsAPI,
} from '@/legacy/services/api'
import type {
  Expense,
  ExpenseDetail,
  Receipt,
  ReceiptQueryParams,
  ExpenseQueryParams,
} from '@/legacy/types/api'
import { useFilterValues } from '@/legacy/stores/filterStore'
import { useDebounce } from '@/legacy/hooks/usePerformance'
import { buildFilterPayload } from '@/legacy/utils/filterParams'
import ExportButton from '@/legacy/components/ExportButton'
import { SkeletonDashboard } from '@/legacy/components/SkeletonLoader'
import VirtualTable, { type VirtualTableColumn } from '@/legacy/components/VirtualTable'
import { formatAmount, formatAxisAmount, formatTooltipAmount } from '@/legacy/utils/formatters'
import {
  ResponsiveContainer,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Legend,
  Bar,
  Line,
  Tooltip as RechartsTooltip,
  BarChart,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { Info, ChevronDown, ChevronUp } from 'lucide-react'

interface CreditDashboardProps {
  departmentId?: number
}

interface ContractKpi {
  name: string
  organization: string
  bankAccount: string
  principal: number
  interest: number
  total: number
  operations: number
}

interface BankData {
  name: string
  amount: number
  count: number
}

interface MonthlyData {
  month: string
  received: number
  principal: number
  interest: number
}

interface OrgData {
  name: string
  principal: number
  interest: number
  total: number
}

interface ActiveCredit {
  contractNumber: string
  organization: string
  bankAccount: string
  received: number
  principalPaid: number
  interestPaid: number
  balance: number
  lastPaymentDate: string | null
  receiptDate: string | null
}

const CreditDashboard = ({ departmentId }: CreditDashboardProps) => {
  const filters = useFilterValues()
  const debouncedFilters = useDebounce(filters, 500)
  const [currentPage, setCurrentPage] = useState<'overview' | 'details'>('overview')
  const [helpExpanded, setHelpExpanded] = useState(false)
  const queryClient = useQueryClient()
  const { mode } = useTheme()
  
  // Colors for charts based on theme
  const isDark = mode === 'dark'
  const gridColor = isDark ? '#334155' : '#E5E7EB'
  const textColor = isDark ? '#94a3b8' : '#6B7280'
  const textColorDark = isDark ? '#cbd5e1' : '#374151'

  const filterPayload = useMemo(
    () => buildFilterPayload(debouncedFilters, { includeDefaultDateTo: true }),
    [debouncedFilters]
  )

  // Backend API limits set to 50000 for comprehensive financial data
  const limitBase = 50000

  const receiptParams = useMemo<ReceiptQueryParams>(() => {
    const params: ReceiptQueryParams = { limit: limitBase, department_id: departmentId }
    if (filterPayload.date_from) params.date_from = filterPayload.date_from
    if (filterPayload.date_to) params.date_to = filterPayload.date_to
    if (filterPayload.organizations) params.organization = filterPayload.organizations
    if (filterPayload.bank_accounts) params.bank_account = filterPayload.bank_accounts
    return params
  }, [filterPayload, limitBase, departmentId])

  const expenseParams = useMemo<ExpenseQueryParams>(() => {
    const params: ExpenseQueryParams = { limit: limitBase, department_id: departmentId }
    if (filterPayload.date_from) params.date_from = filterPayload.date_from
    if (filterPayload.date_to) params.date_to = filterPayload.date_to
    if (filterPayload.organizations) params.organization = filterPayload.organizations
    if (filterPayload.bank_accounts) params.bank_account = filterPayload.bank_accounts
    return params
  }, [filterPayload, limitBase, departmentId])

  const receiptsQuery = useQuery({
    queryKey: ['legacy-dashboard', 'receipts', receiptParams],
    queryFn: () => receiptsAPI.getAll(receiptParams),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(departmentId),
  })

  const expensesQuery = useQuery({
    queryKey: ['legacy-dashboard', 'expenses', expenseParams],
    queryFn: () => expensesAPI.getAll(expenseParams),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(departmentId),
  })

  const expenseDetailsQuery = useQuery({
    queryKey: ['legacy-dashboard', 'expense-details', departmentId],
    queryFn: () => expenseDetailsAPI.getAll({ limit: limitBase, department_id: departmentId }),
    placeholderData: keepPreviousData,
    staleTime: 10 * 60 * 1000,
    enabled: Boolean(departmentId),
  })

  const receipts = (receiptsQuery.data?.items ?? []) as Receipt[]
  const expenses = (expensesQuery.data?.items ?? []) as Expense[]
  const expenseDetails = (expenseDetailsQuery.data?.items ?? []) as ExpenseDetail[]

  const isInitialLoading =
    !departmentId ||
    (receiptsQuery.isLoading && !receiptsQuery.data) ||
    (expensesQuery.isLoading && !expensesQuery.data) ||
    (expenseDetailsQuery.isLoading && !expenseDetailsQuery.data)

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['legacy-dashboard', 'receipts'] })
    queryClient.invalidateQueries({ queryKey: ['legacy-dashboard', 'expenses'] })
    queryClient.invalidateQueries({ queryKey: ['legacy-dashboard', 'expense-details'] })
  }

  const normalizeContractNumber = (value?: string | null) => value?.trim().toLowerCase() || ''
  const normalizedContractFilter = useMemo(
    () => normalizeContractNumber(filters.contractNumber),
    [filters.contractNumber]
  )
  const hasContractFilter = Boolean(normalizedContractFilter)

  const includedContractsSet = useMemo(() => {
    return new Set(
      (filters.contracts || [])
        .map(value => normalizeContractNumber(value))
        .filter(Boolean)
    )
  }, [filters.contracts])
  const hasIncludedContracts = includedContractsSet.size > 0

  const filteredReceipts = useMemo(() => {
    return receipts.filter(r => {
      if (filters.organizations.length > 0 && !filters.organizations.includes(r.organization)) {
        return false
      }
      if (
        filters.bankAccounts.length > 0 &&
        r.bank_account &&
        !filters.bankAccounts.includes(r.bank_account)
      ) {
        return false
      }
      const normalized = normalizeContractNumber(r.contract_number)
      if (hasContractFilter) {
        return normalized && normalized === normalizedContractFilter
      }
      if (hasIncludedContracts) {
        return normalized ? includedContractsSet.has(normalized) : false
      }
      return true
    })
  }, [
    receipts,
    filters.organizations,
    filters.bankAccounts,
    hasContractFilter,
    normalizedContractFilter,
    hasIncludedContracts,
    includedContractsSet,
  ])

  const filteredExpenses = useMemo(() => {
    return expenses.filter(e => {
      if (filters.organizations.length > 0 && !filters.organizations.includes(e.organization)) {
        return false
      }
      if (
        filters.bankAccounts.length > 0 &&
        e.bank_account &&
        !filters.bankAccounts.includes(e.bank_account)
      ) {
        return false
      }
      const normalized = normalizeContractNumber(e.contract_number)
      if (hasContractFilter) {
        return normalized && normalized === normalizedContractFilter
      }
      if (hasIncludedContracts) {
        return normalized ? includedContractsSet.has(normalized) : false
      }
      return true
    })
  }, [
    expenses,
    filters.organizations,
    filters.bankAccounts,
    hasContractFilter,
    normalizedContractFilter,
    hasIncludedContracts,
    includedContractsSet,
  ])

  const filteredExpensesMap = useMemo(() => {
    const map = new Map<string, Expense>()
    filteredExpenses.forEach(expense => {
      map.set(expense.operation_id, expense)
    })
    return map
  }, [filteredExpenses])

  const filteredDetails = useMemo(() => {
    return expenseDetails.filter(detail => filteredExpensesMap.has(detail.expense_operation_id))
  }, [expenseDetails, filteredExpensesMap])

  const kpis = useMemo(() => {
    const totalReceived = filteredReceipts.reduce((sum, r) => sum + Number(r.amount || 0), 0)
    const totalExpenses = filteredExpenses.reduce((sum, e) => sum + Number(e.amount || 0), 0)
    const principalPaid = filteredDetails
      .filter(d => d.payment_type === 'Погашение долга')
      .reduce((sum, d) => sum + Number(d.payment_amount || 0), 0)
    const interestPaid = filteredDetails
      .filter(d => d.payment_type === 'Уплата процентов')
      .reduce((sum, d) => sum + Number(d.payment_amount || 0), 0)
    const debtBalance = totalReceived - principalPaid

    return {
      totalReceived,
      principalPaid,
      interestPaid,
      debtBalance,
      totalExpenses,
    }
  }, [filteredReceipts, filteredExpenses, filteredDetails])

  const contractData = useMemo<ContractKpi[]>(() => {
    const contracts: Record<string, ContractKpi> = {}

    filteredExpenses.forEach(e => {
      const contract = e.contract_number || 'Без договора'
      if (!contracts[contract]) {
        contracts[contract] = {
          name: contract,
          organization: e.organization || '',
          bankAccount: e.bank_account || '',
          principal: 0,
          interest: 0,
          total: 0,
          operations: 0,
        }
      }
      contracts[contract].total += Number(e.amount || 0)
      contracts[contract].operations += 1
    })

    filteredDetails.forEach(d => {
      const expense = filteredExpensesMap.get(d.expense_operation_id)
      if (!expense) return
      const contract = expense.contract_number || 'Без договора'
      if (!contracts[contract]) return
      if (d.payment_type === 'Погашение долга') {
        contracts[contract].principal += Number(d.payment_amount || 0)
      } else if (d.payment_type === 'Уплата процентов') {
        contracts[contract].interest += Number(d.payment_amount || 0)
      }
    })

    return Object.values(contracts)
      .sort((a, b) => b.total - a.total)
      .slice(0, 15)
  }, [filteredExpenses, filteredDetails, filteredExpensesMap])

  const bankData = useMemo<BankData[]>(() => {
    const banks: Record<string, BankData> = {}

    filteredExpenses.forEach(e => {
      const bank = e.bank_account || 'Не указано'
      if (!banks[bank]) {
        banks[bank] = { name: bank, amount: 0, count: 0 }
      }
      banks[bank].amount += Number(e.amount || 0)
      banks[bank].count += 1
    })

    return Object.values(banks)
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10)
      .map(item => ({
        name: item.name.length > 30 ? `${item.name.substring(0, 27)}...` : item.name,
        amount: item.amount,
        count: item.count,
      }))
  }, [filteredExpenses])

  const monthlyData = useMemo<MonthlyData[]>(() => {
    const map = new Map<string, MonthlyData>()

    const ensureMonth = (monthKey: string) => {
      if (!map.has(monthKey)) {
        map.set(monthKey, {
          month: monthKey,
          received: 0,
          principal: 0,
          interest: 0,
        })
      }
      return map.get(monthKey)!
    }

    filteredReceipts.forEach(receipt => {
      if (!receipt.document_date) return
      const monthKey = receipt.document_date.slice(0, 7)
      const record = ensureMonth(monthKey)
      record.received += Number(receipt.amount || 0)
    })

    filteredDetails.forEach(detail => {
      const expense = filteredExpensesMap.get(detail.expense_operation_id)
      const dateStr = expense?.document_date
      if (!dateStr) return
      const monthKey = dateStr.slice(0, 7)
      const record = ensureMonth(monthKey)
      if (detail.payment_type === 'Погашение долга') {
        record.principal += Number(detail.payment_amount || 0)
      } else if (detail.payment_type === 'Уплата процентов') {
        record.interest += Number(detail.payment_amount || 0)
      }
    })

    return Array.from(map.values()).sort((a, b) => a.month.localeCompare(b.month))
  }, [filteredReceipts, filteredDetails, filteredExpensesMap])

  const orgData = useMemo<OrgData[]>(() => {
    const orgs: Record<string, OrgData> = {}

    filteredExpenses.forEach(e => {
      const org = e.organization || 'Не указано'
      if (!orgs[org]) {
        orgs[org] = { name: org, principal: 0, interest: 0, total: 0 }
      }
      orgs[org].total += Number(e.amount || 0)
    })

    filteredDetails.forEach(d => {
      const expense = filteredExpensesMap.get(d.expense_operation_id)
      if (!expense) return
      const org = expense.organization || 'Не указано'
      if (!orgs[org]) return
      if (d.payment_type === 'Погашение долга') {
        orgs[org].principal += Number(d.payment_amount || 0)
      } else if (d.payment_type === 'Уплата процентов') {
        orgs[org].interest += Number(d.payment_amount || 0)
      }
    })

    return Object.values(orgs).sort((a, b) => b.total - a.total)
  }, [filteredExpenses, filteredDetails, filteredExpensesMap])

  const activeCredits = useMemo<ActiveCredit[]>(() => {
    const contracts: Record<string, ActiveCredit> = {}

    filteredReceipts.forEach(r => {
      const contract = r.contract_number || 'Без договора'
      if (!contracts[contract]) {
        contracts[contract] = {
          contractNumber: contract,
          organization: r.organization,
          bankAccount: r.bank_account || '',
          received: 0,
          principalPaid: 0,
          interestPaid: 0,
          balance: 0,
          lastPaymentDate: null,
          receiptDate: r.document_date || null,
        }
      }
      contracts[contract].received += Number(r.amount || 0)
      if (
        r.document_date &&
        (!contracts[contract].receiptDate || r.document_date < contracts[contract].receiptDate!)
      ) {
        contracts[contract].receiptDate = r.document_date
      }
    })

    filteredDetails.forEach(d => {
      const expense = filteredExpensesMap.get(d.expense_operation_id)
      if (!expense) return
      const contract = expense.contract_number || 'Без договора'
      if (!contracts[contract]) return

      if (d.payment_type === 'Погашение долга') {
        contracts[contract].principalPaid += Number(d.payment_amount || 0)
      } else if (d.payment_type === 'Уплата процентов') {
        contracts[contract].interestPaid += Number(d.payment_amount || 0)
      }

      if (
        expense.document_date &&
        (!contracts[contract].lastPaymentDate || expense.document_date > contracts[contract].lastPaymentDate!)
      ) {
        contracts[contract].lastPaymentDate = expense.document_date
      }
    })

    return Object.values(contracts)
      .map(c => ({
        ...c,
        balance: c.received - c.principalPaid,
      }))
      .filter(c => c.balance > 100)
      .sort((a, b) => b.balance - a.balance)
  }, [filteredReceipts, filteredDetails, filteredExpensesMap])

  const activeCreditColumns = useMemo<VirtualTableColumn<ActiveCredit>[]>(() => [
    {
      key: 'contractNumber',
      label: '№ Договора',
      flex: 2,
      render: (value: string) => <strong>{value}</strong>,
    },
    {
      key: 'organization',
      label: 'Организация',
      flex: 2,
    },
    {
      key: 'bankAccount',
      label: 'Банк',
      flex: 2,
      render: (value: string) => (
        <span className="text-xs text-muted-foreground">
          {value?.length > 30 ? `${value.substring(0, 27)}...` : value || '-'}
        </span>
      ),
    },
    {
      key: 'received',
      label: 'Получено',
      align: 'right',
      render: (value: number) => <span className="font-mono">{formatAmount(value)}</span>,
    },
    {
      key: 'principalPaid',
      label: 'Погашено тела',
      align: 'right',
      render: (value: number) => <span className="font-mono text-green-600 dark:text-green-400">{formatAmount(value)}</span>,
    },
    {
      key: 'balance',
      label: 'Остаток',
      align: 'right',
      render: (value: number) => <span className="font-mono text-red-600 dark:text-red-400">{formatAmount(value)}</span>,
    },
    {
      key: 'interestPaid',
      label: 'Уплачено %',
      align: 'right',
      render: (value: number) => <span className="font-mono">{formatAmount(value)}</span>,
    },
    {
      key: 'receiptDate',
      label: 'Дата получения',
      render: (value: string | null) => (value ? format(parseISO(value), 'dd.MM.yyyy') : '-'),
    },
    {
      key: 'lastPaymentDate',
      label: 'Последний платеж',
      render: (value: string | null) => (value ? format(parseISO(value), 'dd.MM.yyyy') : '-'),
    },
  ], [])

  const detailColumns = useMemo<VirtualTableColumn<ContractKpi>[]>(() => [
    {
      key: 'name',
      label: 'Договор',
      flex: 2,
      render: (value: string) => (value.length > 45 ? `${value.substring(0, 42)}...` : value),
    },
    {
      key: 'organization',
      label: 'Организация',
      flex: 2,
    },
    {
      key: 'bankAccount',
      label: 'Банк',
      flex: 2,
      render: (value: string) => <span className="text-xs text-muted-foreground">{value?.substring(0, 25)}...</span>,
    },
    {
      key: 'operations',
      label: 'Операций',
      align: 'center',
    },
    {
      key: 'principal',
      label: 'Погашено тела',
      align: 'right',
      render: (value: number) => formatAmount(value),
    },
    {
      key: 'interest',
      label: 'Уплачено %',
      align: 'right',
      render: (value: number) => formatAmount(value),
    },
    {
      key: 'total',
      label: 'Всего',
      align: 'right',
      render: (value: number) => <strong>{formatAmount(value)}</strong>,
    },
  ], [])

  const activeCreditsHeight = useMemo(
    () => Math.min(600, Math.max(320, activeCredits.length * 60)),
    [activeCredits.length]
  )

  const contractDetailsHeight = useMemo(
    () => Math.min(500, Math.max(280, contractData.length * 55)),
    [contractData.length]
  )

  const hasError = receiptsQuery.isError || expensesQuery.isError || expenseDetailsQuery.isError

  const dateTickFormatter = (value: string) => {
    if (!value) return ''
    const [year, month] = value.split('-')
    const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    return `${months[parseInt(month) - 1]} '${year.slice(-2)}`
  }

  if (!departmentId) {
    return (
      <div className="p-6 bg-card rounded-2xl shadow-sm text-foreground/70">
        Пожалуйста, выберите отдел, чтобы просмотреть аналитику кредитного портфеля.
      </div>
    )
  }

  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4 text-center bg-card rounded-2xl shadow-sm">
        <p className="text-foreground/70">Не удалось загрузить данные дашборда. Попробуйте еще раз.</p>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
        >
          Обновить
        </button>
      </div>
    )
  }

  if (isInitialLoading) {
    return <SkeletonDashboard />
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-6 bg-card p-5 md:p-6 rounded-2xl shadow-sm"
      id="dashboard-content"
    >
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground m-0">Аналитика кредитов и платежей</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Период:{' '}
            {filters.dateFrom ? format(parseISO(filters.dateFrom), 'dd.MM.yyyy') : 'Не указано'} -{' '}
            {filters.dateTo ? format(parseISO(filters.dateTo), 'dd.MM.yyyy') : 'Не указано'}
          </p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => setCurrentPage('overview')}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              currentPage === 'overview'
                ? 'bg-blue-500 text-white border border-blue-500'
                : 'bg-card text-muted-foreground border border-border hover:bg-muted'
            }`}
          >
            Обзор
          </button>
          <button
            onClick={() => setCurrentPage('details')}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              currentPage === 'details'
                ? 'bg-blue-500 text-white border border-blue-500'
                : 'bg-card text-muted-foreground border border-border hover:bg-muted'
            }`}
          >
            Детали
          </button>
          <button
            onClick={handleRefresh}
            className="px-5 py-2.5 bg-green-500 text-white border-0 rounded-lg cursor-pointer text-sm font-medium hover:bg-green-600"
          >
            ⟳ Обновить
          </button>
          <ExportButton targetId="dashboard-content" fileName="credit-dashboard" data={contractData} />
        </div>
      </header>

      <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-2xl overflow-hidden">
        <button
          onClick={() => setHelpExpanded(prev => !prev)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Info size={20} className="text-blue-600 dark:text-blue-400" />
            <span className="font-semibold text-blue-900 dark:text-blue-300">
              Как рассчитываются показатели?
            </span>
          </div>
          {helpExpanded ? (
            <ChevronUp size={20} className="text-blue-600 dark:text-blue-400" />
          ) : (
            <ChevronDown size={20} className="text-blue-600 dark:text-blue-400" />
          )}
        </button>
        {helpExpanded && (
          <div className="px-6 pb-5 pt-2 space-y-4 text-sm text-foreground/80 border-t border-border bg-card">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/30">
                <h4 className="font-semibold text-blue-900 dark:text-blue-300 text-sm mb-2">
                  💰 Получено кредитов
                </h4>
                <p className="text-xs text-foreground/70">
                  Сумма всех поступлений из таблицы «Поступления» с учётом выбранных фильтров.
                </p>
              </div>
              <div className="p-4 rounded-xl border border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/30">
                <h4 className="font-semibold text-green-900 dark:text-green-300 text-sm mb-2">
                  ✓ Погашено тела
                </h4>
                <p className="text-xs text-foreground/70">
                  Сумма всех деталей списаний с типом «тело», источник — «Детализация списаний».
                </p>
              </div>
              <div className="p-4 rounded-xl border border-orange-200 dark:border-orange-800 bg-orange-50/50 dark:bg-orange-950/30">
                <h4 className="font-semibold text-orange-900 dark:text-orange-300 text-sm mb-2">
                  % Уплачено процентов
                </h4>
                <p className="text-xs text-foreground/70">
                  Сумма деталей списаний с типом «проценты».
                </p>
              </div>
              <div className="p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/30">
                <h4 className="font-semibold text-red-900 dark:text-red-300 text-sm mb-2">
                  📊 Остаток задолженности
                </h4>
                <p className="text-xs text-foreground/70">
                  Получено минус погашено тело. Показывает текущий баланс основного долга.
                </p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Все показатели автоматически пересчитываются в зависимости от выбранных дат, организаций, банков и договоров.
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5">
        <div className="p-6 rounded-2xl shadow-lg text-white bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 dark:shadow-blue-500/20">
          <div className="text-sm opacity-90 dark:opacity-80">Получено кредитов</div>
          <div className="text-3xl font-bold my-2">{formatAmount(kpis.totalReceived)}</div>
          <div className="text-xs opacity-90 dark:opacity-75">
            {filteredReceipts.length} операций поступления
          </div>
        </div>
        <div className="p-6 rounded-2xl shadow-lg text-white bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 dark:shadow-green-500/20">
          <div className="text-sm opacity-90 dark:opacity-80">Погашено тела</div>
          <div className="text-3xl font-bold my-2">{formatAmount(kpis.principalPaid)}</div>
          <div className="text-xs opacity-90 dark:opacity-75">
            {filteredDetails.filter(d => d.payment_type === 'Погашение долга').length} платежей
          </div>
        </div>
        <div className="p-6 rounded-2xl shadow-lg text-white bg-gradient-to-br from-orange-500 to-orange-600 dark:from-orange-600 dark:to-orange-700 dark:shadow-orange-500/20">
          <div className="text-sm opacity-90 dark:opacity-80">Уплачено процентов</div>
          <div className="text-3xl font-bold my-2">{formatAmount(kpis.interestPaid)}</div>
          <div className="text-xs opacity-90 dark:opacity-75">
            {filteredDetails.filter(d => d.payment_type === 'Уплата процентов').length} платежей
          </div>
        </div>
        <div className="p-6 rounded-2xl shadow-lg text-white bg-gradient-to-br from-red-500 to-red-600 dark:from-red-600 dark:to-red-700 dark:shadow-red-500/20">
          <div className="text-sm opacity-90 dark:opacity-80">Остаток задолженности</div>
          <div className="text-3xl font-bold my-2">{formatAmount(kpis.debtBalance)}</div>
          <div className="text-xs opacity-90 dark:opacity-75">
            {(kpis.totalReceived > 0
              ? ((kpis.debtBalance / kpis.totalReceived) * 100).toFixed(1)
              : '0')}{' '}
            % от полученного
          </div>
        </div>
      </div>

      <div className="p-6 bg-card dark:bg-slate-800/50 rounded-2xl shadow-sm border border-red-100 dark:border-red-900/30">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            🔴 Активные кредиты
          </h2>
          <div className="px-4 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full text-sm font-medium">
            {activeCredits.length} {activeCredits.length === 1 ? 'договор' : 'договоров'}
          </div>
        </div>
        {activeCredits.length > 0 ? (
          <VirtualTable
            data={activeCredits}
            columns={activeCreditColumns}
            height={activeCreditsHeight}
            rowHeight={64}
            emptyMessage="Все кредиты погашены!"
          />
        ) : (
          <div className="py-12 text-center text-muted-foreground text-sm">
            Все кредиты погашены!
          </div>
        )}
      </div>

      {currentPage === 'overview' && (
        <div className="grid gap-5">
          <div className="p-6 bg-card rounded-2xl shadow-sm">
            <h2 className="text-lg font-semibold mb-2 text-foreground">
              Динамика получения и погашения кредитов
            </h2>
            <p className="text-xs text-muted-foreground mb-4">
              Помесячная динамика поступлений (синий), погашения тела (зелёный) и процентов (оранжевый).
            </p>
            <ResponsiveContainer width="100%" height={360}>
              <ComposedChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis
                  dataKey="month"
                  tickFormatter={dateTickFormatter}
                  tick={{ fontSize: 11, fill: textColor }}
                  angle={-45}
                  textAnchor="end"
                  height={70}
                />
                <YAxis tickFormatter={formatAxisAmount} tick={{ fontSize: 11, fill: textColor }} />
                <RechartsTooltip
                  formatter={formatTooltipAmount as any}
                  labelFormatter={dateTickFormatter}
                  contentStyle={{ 
                    fontSize: 12,
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    border: `1px solid ${gridColor}`,
                    borderRadius: '8px',
                    color: isDark ? '#f8fafc' : '#1f2937'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: textColor }} />
                <Bar dataKey="received" name="Получено" fill="#3B82F6" />
                <Bar dataKey="principal" name="Погашено тела" fill="#10B981" />
                <Bar dataKey="interest" name="Уплачено %" fill="#F59E0B" />
                <Line dataKey="received" name="Линия получено" stroke={isDark ? '#60a5fa' : '#1E3A8A'} strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="p-6 bg-card rounded-2xl shadow-sm">
            <h2 className="text-lg font-semibold mb-2 text-foreground">
              Топ-15 кредитных договоров
            </h2>
            <p className="text-xs text-muted-foreground mb-4">
              Сумма выплат по договорам: тело (зелёный) и проценты (оранжевый).
            </p>
            <ResponsiveContainer width="100%" height={480}>
              <BarChart data={contractData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis type="number" tickFormatter={formatAxisAmount} tick={{ fontSize: 11, fill: textColor }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={240}
                  tick={{ fontSize: 11, fill: textColorDark }}
                  tickFormatter={value =>
                    value.length > 38 ? `${value.substring(0, 35)}...` : value
                  }
                />
                <RechartsTooltip 
                  formatter={formatTooltipAmount as any} 
                  contentStyle={{ 
                    fontSize: 12,
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    border: `1px solid ${gridColor}`,
                    borderRadius: '8px',
                    color: isDark ? '#f8fafc' : '#1f2937'
                  }} 
                />
                <Legend wrapperStyle={{ fontSize: 12, color: textColor }} />
                <Bar dataKey="principal" name="Тело" fill="#10B981" stackId="a" />
                <Bar dataKey="interest" name="Проценты" fill="#F59E0B" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="p-6 bg-card rounded-2xl shadow-sm">
              <h2 className="text-lg font-semibold mb-2 text-foreground">Топ-10 банковских счетов</h2>
              <p className="text-xs text-muted-foreground mb-4">
                Счета с наибольшим объёмом списаний.
              </p>
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={bankData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis type="number" tickFormatter={formatAxisAmount} tick={{ fontSize: 11, fill: textColor }} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={200}
                    tick={{ fontSize: 11, fill: textColorDark }}
                  />
                  <RechartsTooltip 
                    formatter={formatTooltipAmount as any} 
                    contentStyle={{ 
                      fontSize: 12,
                      backgroundColor: isDark ? '#1e293b' : '#ffffff',
                      border: `1px solid ${gridColor}`,
                      borderRadius: '8px',
                      color: isDark ? '#f8fafc' : '#1f2937'
                    }} 
                  />
                  <Bar dataKey="amount" name="Сумма" fill="#8B5CF6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="p-6 bg-card rounded-2xl shadow-sm">
              <h2 className="text-lg font-semibold mb-2 text-foreground">Распределение по организациям</h2>
              <p className="text-xs text-muted-foreground mb-4">
                Погашение тела (зелёный) и уплата процентов (оранжевый) по каждому юрлицу.
              </p>
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={orgData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: '#6B7280' }}
                    height={80}
                    angle={-40}
                    textAnchor="end"
                  />
                  <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} />
                  <RechartsTooltip formatter={formatTooltipAmount as any} contentStyle={{ fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="principal" name="Тело" fill="#10B981" />
                  <Bar dataKey="interest" name="Проценты" fill="#F59E0B" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {currentPage === 'details' && (
        <div className="grid gap-5">
          <div className="p-6 bg-card rounded-2xl shadow-sm">
            <h2 className="text-lg font-semibold mb-3 text-foreground">Детализация по договорам</h2>
            <VirtualTable
              data={contractData}
              columns={detailColumns}
              height={contractDetailsHeight}
              rowHeight={60}
              emptyMessage="Нет данных по договорам"
            />
          </div>
          <div className="p-6 bg-card rounded-2xl shadow-sm">
            <h2 className="text-lg font-semibold mb-3 text-foreground">Расшифровка активных кредитов</h2>
            <VirtualTable
              data={activeCredits}
              columns={activeCreditColumns}
              height={activeCreditsHeight}
              rowHeight={60}
              emptyMessage="Нет активных кредитов"
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default CreditDashboard
