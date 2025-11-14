import { useMemo } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface FilterState {
  organizations: string[]
  bankAccounts: string[]
  dateFrom: string
  dateTo: string
  contractNumber: string
  contracts: string[]
  setOrganizations: (orgs: string[]) => void
  setBankAccounts: (accounts: string[]) => void
  setDateFrom: (date: string) => void
  setDateTo: (date: string) => void
  setContractNumber: (contract: string) => void
  setContracts: (contracts: string[]) => void
  resetFilters: () => void
  setFilters: (filters: Partial<Omit<FilterState, keyof FilterActions>>) => void
}

type FilterActions = Pick<
  FilterState,
  | 'setOrganizations'
  | 'setBankAccounts'
  | 'setDateFrom'
  | 'setDateTo'
  | 'setContractNumber'
  | 'setContracts'
  | 'resetFilters'
  | 'setFilters'
>

type PersistedFilters = Pick<
  FilterState,
  'organizations' | 'bankAccounts' | 'dateFrom' | 'dateTo' | 'contractNumber' | 'contracts'
>

const sanitizeStringArray = (values?: string | string[]) => {
  if (typeof values === 'string') {
    if (values === 'all' || !values || values.trim().length === 0) {
      return []
    }
    return [values.trim()]
  }

  if (!values || !Array.isArray(values)) {
    return []
  }

  const normalized = values
    .map(value => value?.trim())
    .filter((value): value is string => Boolean(value) && value !== 'all')

  return Array.from(new Set(normalized))
}

export const DEFAULT_DATE_FROM = '2021-01-01'
export const DEFAULT_DATE_TO = '2028-12-31'

const initialState: PersistedFilters = {
  organizations: [],
  bankAccounts: [],
  dateFrom: DEFAULT_DATE_FROM,
  dateTo: DEFAULT_DATE_TO,
  contractNumber: '',
  contracts: [],
}

export const useFilterStore = create<FilterState>()(
  persist(
    set => ({
      ...initialState,
      setOrganizations: organizations => set({ organizations: sanitizeStringArray(organizations) }),
      setBankAccounts: bankAccounts => set({ bankAccounts: sanitizeStringArray(bankAccounts) }),
      setDateFrom: dateFrom => set({ dateFrom }),
      setDateTo: dateTo => set({ dateTo }),
      setContractNumber: contractNumber => set({ contractNumber }),
      setContracts: contracts => set({ contracts: sanitizeStringArray(contracts) }),
      resetFilters: () => set(() => ({ ...initialState })),
      setFilters: filters =>
        set(state => ({
          ...state,
          ...filters,
          ...(filters.organizations !== undefined
            ? { organizations: sanitizeStringArray(filters.organizations) }
            : {}),
          ...(filters.bankAccounts !== undefined
            ? { bankAccounts: sanitizeStringArray(filters.bankAccounts) }
            : {}),
          ...(filters.contracts !== undefined
            ? { contracts: sanitizeStringArray(filters.contracts) }
            : {}),
        })),
    }),
    {
      name: 'credit-legacy-filters',
      version: 1,
      partialize: (state): PersistedFilters => ({
        organizations: state.organizations,
        bankAccounts: state.bankAccounts,
        dateFrom: state.dateFrom,
        dateTo: state.dateTo,
        contractNumber: state.contractNumber,
        contracts: state.contracts,
      }),
    }
  )
)

export const useFilterValues = () => {
  const dateFrom = useFilterStore(state => state.dateFrom)
  const dateTo = useFilterStore(state => state.dateTo)
  const organizations = useFilterStore(state => state.organizations)
  const bankAccounts = useFilterStore(state => state.bankAccounts)
  const contractNumber = useFilterStore(state => state.contractNumber)
  const contracts = useFilterStore(state => state.contracts)

  return useMemo(
    () => ({
      dateFrom,
      dateTo,
      organizations,
      bankAccounts,
      contractNumber,
      contracts,
    }),
    [dateFrom, dateTo, organizations, bankAccounts, contractNumber, contracts]
  )
}

