import { useState, useEffect, useMemo } from 'react'
import { RotateCcw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import {
  useFilterStore,
  useFilterValues,
  DEFAULT_DATE_FROM,
  DEFAULT_DATE_TO,
} from '@/legacy/stores/filterStore'
import { Button } from '@/legacy/components/ui/button'
import { Input } from '@/legacy/components/ui/input'
import { MultiSelect } from '@/legacy/components/ui/multi-select'
import { useDepartment } from '@/contexts/DepartmentContext'

export default function Filters() {
  const setFilters = useFilterStore(state => state.setFilters)
  const resetFilters = useFilterStore(state => state.resetFilters)
  const { dateFrom, dateTo, organizations, bankAccounts, contracts } = useFilterValues()
  const [localDateFrom, setLocalDateFrom] = useState(dateFrom)
  const [localDateTo, setLocalDateTo] = useState(dateTo)
  const [localOrganizations, setLocalOrganizations] = useState<string[]>(organizations)
  const [localBankAccounts, setLocalBankAccounts] = useState<string[]>(bankAccounts)
  const [localContracts, setLocalContracts] = useState<string[]>(contracts)
  const { selectedDepartment } = useDepartment()
  const departmentId = selectedDepartment?.id

  useEffect(() => setLocalDateFrom(dateFrom), [dateFrom])
  useEffect(() => setLocalDateTo(dateTo), [dateTo])
  useEffect(() => setLocalOrganizations(organizations), [organizations])
  useEffect(() => setLocalBankAccounts(bankAccounts), [bankAccounts])
  useEffect(() => setLocalContracts(contracts), [contracts])

  const {
    data: organizationsData,
    isLoading: organizationsLoading,
  } = useQuery({
    queryKey: ['credit-legacy-organizations', departmentId],
    queryFn: () =>
      creditPortfolioApi.getOrganizations({
        department_id: departmentId,
        limit: 1000,
      }),
    enabled: true,
  })

  const {
    data: bankAccountsData,
    isLoading: bankAccountsLoading,
  } = useQuery({
    queryKey: ['credit-legacy-bank-accounts', departmentId],
    queryFn: () =>
      creditPortfolioApi.getBankAccounts({
        department_id: departmentId,
        limit: 1000,
      }),
    enabled: true,
  })

  const {
    data: contractsData,
    isLoading: contractsLoading,
  } = useQuery({
    queryKey: ['credit-legacy-contracts', departmentId],
    queryFn: () =>
      creditPortfolioApi.getContracts({
        department_id: departmentId,
        limit: 2000,
      }),
    enabled: true,
  })

  const organizationOptions = useMemo(
    () =>
      (organizationsData || []).map(org => ({
        value: org.name,
        label: org.name,
      })),
    [organizationsData]
  )

  const bankAccountOptions = useMemo(
    () =>
      (bankAccountsData || []).map(bank => ({
        value: bank.account_number,
        label: bank.bank_name ? `${bank.account_number} • ${bank.bank_name}` : bank.account_number,
      })),
    [bankAccountsData]
  )

  const contractOptions = useMemo(
    () =>
      (contractsData || [])
        .filter(contract => Boolean(contract.contract_number))
        .map(contract => ({
          value: contract.contract_number,
          label: contract.contract_number,
        })),
    [contractsData]
  )

  const arraysEqual = (a: string[], b: string[]) => {
    if (a.length !== b.length) return false
    const sortedA = [...a].sort()
    const sortedB = [...b].sort()
    return sortedA.every((value, index) => value === sortedB[index])
  }

  const hasChanges =
    localDateFrom !== dateFrom ||
    localDateTo !== dateTo ||
    !arraysEqual(localOrganizations, organizations) ||
    !arraysEqual(localBankAccounts, bankAccounts) ||
    !arraysEqual(localContracts, contracts)

  const handleApply = () => {
    setFilters({
      dateFrom: localDateFrom,
      dateTo: localDateTo,
      organizations: localOrganizations,
      bankAccounts: localBankAccounts,
      contracts: localContracts,
    })
  }

  const handleReset = () => {
    resetFilters()
    setLocalDateFrom(DEFAULT_DATE_FROM)
    setLocalDateTo(DEFAULT_DATE_TO)
    setLocalOrganizations([])
    setLocalBankAccounts([])
    setLocalContracts([])
  }

  const isLoading = organizationsLoading || bankAccountsLoading || contractsLoading

  return (
    <div className="flex flex-wrap gap-4 items-end bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-600">Период с:</label>
        <Input type="date" value={localDateFrom} onChange={e => setLocalDateFrom(e.target.value)} />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-600">по:</label>
        <Input type="date" value={localDateTo} onChange={e => setLocalDateTo(e.target.value)} />
      </div>

      <MultiSelect
        label="Организация:"
        options={organizationOptions}
        selected={localOrganizations}
        onChange={setLocalOrganizations}
        placeholder="Все организации"
        searchPlaceholder="Поиск организации..."
        className="min-w-[260px]"
        isLoading={organizationsLoading}
      />

      <MultiSelect
        label="Банк:"
        options={bankAccountOptions}
        selected={localBankAccounts}
        onChange={setLocalBankAccounts}
        placeholder="Все банки"
        searchPlaceholder="Поиск банка..."
        className="min-w-[260px]"
        isLoading={bankAccountsLoading}
      />

      <MultiSelect
        label="Договоры:"
        options={contractOptions}
        selected={localContracts}
        onChange={setLocalContracts}
        placeholder="Все договоры"
        searchPlaceholder="Поиск по номеру договора..."
        hint="Договоры фильтруются на клиенте."
        isLoading={contractsLoading}
        className="min-w-[300px]"
      />

      <Button onClick={handleApply} disabled={!hasChanges || isLoading}>
        {isLoading ? 'Обновляем...' : 'Применить'}
      </Button>

      <Button variant="secondary" onClick={handleReset}>
        <RotateCcw size={16} />
      </Button>
    </div>
  )
}

