/**
 * API client for Budget Planning Module (Year-Agnostic)
 */
import apiClient from './client'
import type {
  BudgetScenario,
  BudgetScenarioCreate,
  BudgetScenarioUpdate,
  BudgetScenarioFilters,
  BudgetVersion,
  BudgetVersionWithDetails,
  BudgetVersionCreate,
  BudgetVersionUpdate,
  BudgetVersionFilters,
  BudgetPlanDetail,
  BudgetPlanDetailCreate,
  BudgetPlanDetailUpdate,
  BudgetApprovalLog,
  BudgetApprovalLogCreate,
  CalculateByAverageRequest,
  CalculateByGrowthRequest,
  CalculateByDriverRequest,
  CalculationResult,
  BaselineSummary,
  VersionComparison,
} from '@/types/budgetPlanning'

const BASE_PATH = '/budget/planning'

// ============================================================================
// Budget Scenarios API
// ============================================================================

export const scenariosApi = {
  /**
   * Get all scenarios with optional filters
   */
  getAll: async (filters?: BudgetScenarioFilters): Promise<BudgetScenario[]> => {
    const params = new URLSearchParams()
    if (filters?.year) params.append('year', filters.year.toString())
    if (filters?.scenario_type) params.append('scenario_type', filters.scenario_type)
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString())

    const response = await apiClient.get<BudgetScenario[]>(
      `${BASE_PATH}/scenarios?${params.toString()}`
    )
    return response.data
  },

  /**
   * Get scenario by ID
   */
  getById: async (id: number): Promise<BudgetScenario> => {
    const response = await apiClient.get<BudgetScenario>(`${BASE_PATH}/scenarios/${id}`)
    return response.data
  },

  /**
   * Create new scenario
   */
  create: async (data: BudgetScenarioCreate): Promise<BudgetScenario> => {
    const response = await apiClient.post<BudgetScenario>(`${BASE_PATH}/scenarios`, data)
    return response.data
  },

  /**
   * Update scenario
   */
  update: async (id: number, data: BudgetScenarioUpdate): Promise<BudgetScenario> => {
    const response = await apiClient.put<BudgetScenario>(`${BASE_PATH}/scenarios/${id}`, data)
    return response.data
  },

  /**
   * Delete scenario
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/scenarios/${id}`)
  },
}

// ============================================================================
// Budget Versions API
// ============================================================================

export const versionsApi = {
  /**
   * Get all versions with optional filters
   */
  getAll: async (filters?: BudgetVersionFilters): Promise<BudgetVersion[]> => {
    const params = new URLSearchParams()
    if (filters?.year) params.append('year', filters.year.toString())
    if (filters?.status) params.append('status', filters.status)
    if (filters?.scenario_id) params.append('scenario_id', filters.scenario_id.toString())

    const response = await apiClient.get<BudgetVersion[]>(
      `${BASE_PATH}/versions?${params.toString()}`
    )
    return response.data
  },

  /**
   * Get version by ID with optional details
   */
  getById: async (
    id: number,
    includeDetails = true,
    includeApprovalLogs = true
  ): Promise<BudgetVersionWithDetails> => {
    const params = new URLSearchParams()
    params.append('include_details', includeDetails.toString())
    params.append('include_approval_logs', includeApprovalLogs.toString())

    const response = await apiClient.get<BudgetVersionWithDetails>(
      `${BASE_PATH}/versions/${id}?${params.toString()}`
    )
    return response.data
  },

  /**
   * Create new version
   */
  create: async (data: BudgetVersionCreate): Promise<BudgetVersion> => {
    const response = await apiClient.post<BudgetVersion>(`${BASE_PATH}/versions`, data)
    return response.data
  },

  /**
   * Update version
   */
  update: async (id: number, data: BudgetVersionUpdate): Promise<BudgetVersion> => {
    const response = await apiClient.put<BudgetVersion>(`${BASE_PATH}/versions/${id}`, data)
    return response.data
  },

  /**
   * Delete version
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/versions/${id}`)
  },

  /**
   * Copy version to create a new one
   */
  copy: async (sourceVersionId: number, data: Partial<BudgetVersionCreate>): Promise<BudgetVersion> => {
    const createData: BudgetVersionCreate = {
      ...data,
      copy_from_version_id: sourceVersionId,
    } as BudgetVersionCreate

    return versionsApi.create(createData)
  },
}

// ============================================================================
// Budget Plan Details API
// ============================================================================

export const planDetailsApi = {
  /**
   * Get plan details for a version
   */
  getByVersion: async (versionId: number): Promise<BudgetPlanDetail[]> => {
    const version = await versionsApi.getById(versionId, true, false)
    return version.plan_details
  },

  /**
   * Create plan detail
   */
  create: async (data: BudgetPlanDetailCreate): Promise<BudgetPlanDetail> => {
    const response = await apiClient.post<BudgetPlanDetail>(`${BASE_PATH}/plan-details`, data)
    return response.data
  },

  /**
   * Update plan detail
   */
  update: async (id: number, data: BudgetPlanDetailUpdate): Promise<BudgetPlanDetail> => {
    const response = await apiClient.put<BudgetPlanDetail>(`${BASE_PATH}/plan-details/${id}`, data)
    return response.data
  },

  /**
   * Delete plan detail
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/plan-details/${id}`)
  },
}

// ============================================================================
// Budget Approval Log API
// ============================================================================

export const approvalLogApi = {
  /**
   * Get approval logs for a version
   */
  getByVersion: async (versionId: number): Promise<BudgetApprovalLog[]> => {
    const version = await versionsApi.getById(versionId, false, true)
    return version.approval_logs
  },

  /**
   * Create approval log entry
   */
  create: async (data: BudgetApprovalLogCreate): Promise<BudgetApprovalLog> => {
    const response = await apiClient.post<BudgetApprovalLog>(`${BASE_PATH}/approval-log`, data)
    return response.data
  },
}

// ============================================================================
// Calculator API
// ============================================================================

export const calculatorApi = {
  /**
   * Get baseline data for a category
   */
  getBaseline: async (categoryId: number, year: number): Promise<BaselineSummary> => {
    const response = await apiClient.get<BaselineSummary>(
      `${BASE_PATH}/baseline/${categoryId}?year=${year}`
    )
    return response.data
  },

  /**
   * Calculate budget using average method
   */
  calculateByAverage: async (request: CalculateByAverageRequest): Promise<CalculationResult> => {
    const response = await apiClient.post<CalculationResult>(
      `${BASE_PATH}/calculate/average`,
      request
    )
    return response.data
  },

  /**
   * Calculate budget using growth method
   */
  calculateByGrowth: async (request: CalculateByGrowthRequest): Promise<CalculationResult> => {
    const response = await apiClient.post<CalculationResult>(
      `${BASE_PATH}/calculate/growth`,
      request
    )
    return response.data
  },

  /**
   * Calculate budget using driver-based method
   */
  calculateByDriver: async (request: CalculateByDriverRequest): Promise<CalculationResult> => {
    const response = await apiClient.post<CalculationResult>(
      `${BASE_PATH}/calculate/driver`,
      request
    )
    return response.data
  },
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Get all scenarios for a specific year
 */
export const getScenariosByYear = async (year: number): Promise<BudgetScenario[]> => {
  return scenariosApi.getAll({ year, is_active: true })
}

/**
 * Get all versions for a specific year
 */
export const getVersionsByYear = async (year: number): Promise<BudgetVersion[]> => {
  return versionsApi.getAll({ year })
}

/**
 * Get latest version for a scenario
 */
export const getLatestVersionByScenario = async (
  year: number,
  scenarioId: number
): Promise<BudgetVersion | null> => {
  const versions = await versionsApi.getAll({ year, scenario_id: scenarioId })
  if (versions.length === 0) return null

  // Versions are ordered by version_number desc from backend
  return versions[0]
}

/**
 * Get version comparison
 */
export const compareVersions = async (
  version1Id: number,
  version2Id: number
): Promise<VersionComparison> => {
  const response = await apiClient.get<VersionComparison>(
    `${BASE_PATH}/versions/compare?v1=${version1Id}&v2=${version2Id}`
  )
  return response.data
}

// Export all APIs as default
export default {
  scenarios: scenariosApi,
  versions: versionsApi,
  planDetails: planDetailsApi,
  approvalLog: approvalLogApi,
  calculator: calculatorApi,
  getScenariosByYear,
  getVersionsByYear,
  getLatestVersionByScenario,
  compareVersions,
}
