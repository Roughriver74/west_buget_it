import type { FilterState } from '@/legacy/stores/filterStore'
import { DEFAULT_DATE_TO } from '@/legacy/stores/filterStore'

export interface FilterParamOptions {
  includeContract?: boolean
  includeDefaultDateTo?: boolean
}

type FilterPayload = Record<string, string>

const normalizeValue = (value?: string | null) => (value && value.trim().length > 0 ? value : undefined)

const normalizeArrayToString = (values?: string[]) => {
  if (!values || values.length === 0) {
    return undefined
  }
  return values.filter(v => v && v.trim().length > 0).join(',')
}

export const buildFilterPayload = (
  filters: Partial<FilterState>,
  options: FilterParamOptions = {}
): FilterPayload => {
  const payload: FilterPayload = {}

  if (filters.dateFrom) {
    payload.date_from = filters.dateFrom
  }

  if (filters.dateTo && (options.includeDefaultDateTo || filters.dateTo !== DEFAULT_DATE_TO)) {
    payload.date_to = filters.dateTo
  }

  const organizations = normalizeArrayToString(filters.organizations)
  if (organizations) {
    payload.organizations = organizations
  }

  const bankAccounts = normalizeArrayToString(filters.bankAccounts)
  if (bankAccounts) {
    payload.bank_accounts = bankAccounts
  }

  const contracts = normalizeArrayToString(filters.contracts)
  if (contracts) {
    payload.contracts = contracts
  }

  if (options.includeContract) {
    const contract = normalizeValue(filters.contractNumber)
    if (contract) {
      payload.contract_number = contract
    }
  }

  return payload
}

export const buildFilterQueryString = (filters: Partial<FilterState>, options?: FilterParamOptions): string => {
  const payload = buildFilterPayload(filters, options)
  const params = new URLSearchParams(payload)
  return params.toString()
}

export const filtersToCacheKey = (filters: Partial<FilterState>, options?: FilterParamOptions): string => {
  const payload = buildFilterPayload(filters, {
    ...options,
    includeDefaultDateTo: true,
  })
  return JSON.stringify(payload)
}

export const buildFilterParamsObject = (filters: Partial<FilterState>, options?: FilterParamOptions) => {
  return buildFilterPayload(filters, options)
}

