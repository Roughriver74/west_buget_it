/**
 * TypeScript types for Budget Planning Module (Year-Agnostic)
 * Mirrors Pydantic schemas from backend
 */

// ============================================================================
// Enums
// ============================================================================

export enum BudgetVersionStatus {
  DRAFT = 'draft',
  IN_REVIEW = 'in_review',
  REVISION_REQUESTED = 'revision_requested',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  ARCHIVED = 'archived',
}

export enum BudgetScenarioType {
  BASE = 'base',
  OPTIMISTIC = 'optimistic',
  PESSIMISTIC = 'pessimistic',
}

export enum CalculationMethod {
  AVERAGE = 'average',
  GROWTH = 'growth',
  DRIVER_BASED = 'driver_based',
  SEASONAL = 'seasonal',
  MANUAL = 'manual',
}

export enum ApprovalAction {
  APPROVED = 'approved',
  REJECTED = 'rejected',
  REVISION_REQUESTED = 'revision_requested',
}

export enum ExpenseType {
  OPEX = 'OPEX',
  CAPEX = 'CAPEX',
}

// ============================================================================
// Budget Scenario Types
// ============================================================================

export interface BudgetScenario {
  id: number
  year: number
  scenario_name: string
  scenario_type: BudgetScenarioType
  department_id: number
  global_growth_rate: number
  inflation_rate: number
  fx_rate?: number
  assumptions?: Record<string, any>
  description?: string
  is_active: boolean
  created_at: string
  created_by?: string
}

export interface BudgetScenarioCreate {
  year: number
  scenario_name: string
  scenario_type: BudgetScenarioType
  global_growth_rate?: number
  inflation_rate?: number
  fx_rate?: number
  assumptions?: Record<string, any>
  description?: string
  is_active?: boolean
  // department_id is auto-assigned from current_user on backend
}

export interface BudgetScenarioUpdate {
  scenario_name?: string
  global_growth_rate?: number
  inflation_rate?: number
  fx_rate?: number
  assumptions?: Record<string, any>
  description?: string
  is_active?: boolean
}

// ============================================================================
// Budget Version Types
// ============================================================================

export interface BudgetVersion {
  id: number
  year: number
  version_number: number
  version_name?: string
  department_id: number
  scenario_id?: number
  status: BudgetVersionStatus
  created_by?: string
  created_at: string
  updated_at: string
  submitted_at?: string
  approved_at?: string
  approved_by?: string
  comments?: string
  change_log?: string
  total_amount: number
  total_capex: number
  total_opex: number
}

export interface BudgetVersionWithDetails extends BudgetVersion {
  plan_details: BudgetPlanDetail[]
  scenario?: BudgetScenario
  approval_logs: BudgetApprovalLog[]
}

export interface BudgetVersionCreate {
  year: number
  version_name?: string
  scenario_id?: number
  status?: BudgetVersionStatus
  comments?: string
  change_log?: string
  copy_from_version_id?: number
  auto_calculate?: boolean
  // department_id is auto-assigned from current_user on backend
  // version_number is auto-incremented on backend
}

export interface BudgetVersionUpdate {
  version_name?: string
  scenario_id?: number
  status?: BudgetVersionStatus
  comments?: string
  change_log?: string
  submitted_at?: string
  approved_at?: string
  approved_by?: string
}

// ============================================================================
// Budget Plan Detail Types
// ============================================================================

export interface BudgetPlanDetail {
  id: number
  version_id: number
  month: number
  category_id: number
  subcategory?: string
  planned_amount: number
  type: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: number
  based_on_total?: number
  growth_rate?: number
  created_at: string
  updated_at: string
}

export interface BudgetPlanDetailCreate {
  version_id: number
  month: number
  category_id: number
  subcategory?: string
  planned_amount: number
  type: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: number
  based_on_total?: number
  growth_rate?: number
}

export interface BudgetPlanDetailUpdate {
  month?: number
  category_id?: number
  subcategory?: string
  planned_amount?: number
  type?: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: number
  based_on_total?: number
  growth_rate?: number
}

// ============================================================================
// Budget Approval Log Types
// ============================================================================

export interface BudgetApprovalLog {
  id: number
  version_id: number
  iteration_number: number
  reviewer_name: string
  reviewer_role: string
  action: ApprovalAction
  decision_date: string
  comments?: string
  requested_changes?: Record<string, any>
  next_action?: string
  deadline?: string
  created_at: string
}

export interface BudgetApprovalLogCreate {
  version_id: number
  iteration_number: number
  reviewer_name: string
  reviewer_role: string
  action: ApprovalAction
  decision_date: string
  comments?: string
  requested_changes?: Record<string, any>
  next_action?: string
  deadline?: string
}

// ============================================================================
// Calculator Request/Response Types
// ============================================================================

export interface CalculateByAverageRequest {
  category_id: number
  base_year: number
  adjustment_percent?: number
  target_year: number
  // department_id is auto-assigned from current_user on backend
}

export interface CalculateByGrowthRequest {
  category_id: number
  base_year: number
  growth_rate: number
  inflation_rate?: number
  target_year: number
  // department_id is auto-assigned from current_user on backend
}

export interface CalculateByDriverRequest {
  category_id: number
  base_year: number
  driver_type: string
  base_driver_value: number
  planned_driver_value: number
  cost_per_unit?: number
  adjustment_percent?: number
  target_year: number
  // department_id is auto-assigned from current_user on backend
}

export interface MonthlyAmount {
  month: number
  amount: number
}

export interface CalculationResult {
  category_id: number
  annual_total: number
  monthly_avg: number
  growth_percent: number
  monthly_breakdown: MonthlyAmount[]
  calculation_method: CalculationMethod
  calculation_params: Record<string, any>
  based_on_total: number
  based_on_avg: number
}

export interface BaselineSummary {
  category_id: number
  category_name: string
  total_amount: number
  monthly_avg: number
  monthly_breakdown: MonthlyAmount[]
  capex_total: number
  opex_total: number
}

export interface VersionComparisonResult {
  category: string
  v1_amount: number
  v2_amount: number
  difference: number
  difference_percent: number
}

export interface VersionComparison {
  version1: BudgetVersion
  version2: BudgetVersion
  category_comparisons: VersionComparisonResult[]
  total_v1: number
  total_v2: number
  total_difference: number
  total_difference_percent: number
}

// ============================================================================
// Filter/Query Types
// ============================================================================

export interface BudgetScenarioFilters {
  year?: number
  scenario_type?: BudgetScenarioType
  is_active?: boolean
}

export interface BudgetVersionFilters {
  year?: number
  status?: BudgetVersionStatus
  scenario_id?: number
}
