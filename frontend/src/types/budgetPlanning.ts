/**
 * TypeScript types for Budget Planning Module (Year-Agnostic)
 * Mirrors Pydantic schemas from backend
 */

// ============================================================================
// Enums
// ============================================================================

export enum BudgetVersionStatus {
  DRAFT = 'DRAFT',
  IN_REVIEW = 'IN_REVIEW',
  REVISION_REQUESTED = 'REVISION_REQUESTED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  ARCHIVED = 'ARCHIVED',
}

export enum BudgetScenarioType {
  BASE = 'BASE',
  OPTIMISTIC = 'OPTIMISTIC',
  PESSIMISTIC = 'PESSIMISTIC',
}

export enum CalculationMethod {
  AVERAGE = 'AVERAGE',
  GROWTH = 'GROWTH',
  DRIVER_BASED = 'DRIVER_BASED',
  SEASONAL = 'SEASONAL',
  MANUAL = 'MANUAL',
}

export enum ApprovalAction {
  SUBMITTED = 'SUBMITTED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  REVISION_REQUESTED = 'REVISION_REQUESTED',
}

export enum ExpenseType {
  OPEX = 'OPEX',
  CAPEX = 'CAPEX',
}

// ============================================================================
// Common value types
// ============================================================================

export type NumericValue = number | string

// ============================================================================
// Budget Scenario Types
// ============================================================================

export interface BudgetScenario {
  id: number
  year: number
  scenario_name: string
  scenario_type: BudgetScenarioType
  department_id: number
  global_growth_rate: NumericValue
  inflation_rate: NumericValue
  fx_rate?: NumericValue
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
  global_growth_rate?: NumericValue
  inflation_rate?: NumericValue
  fx_rate?: NumericValue
  assumptions?: Record<string, any>
  description?: string
  is_active?: boolean
  // department_id is auto-assigned from current_user on backend
}

export interface BudgetScenarioUpdate {
  scenario_name?: string
  global_growth_rate?: NumericValue
  inflation_rate?: NumericValue
  fx_rate?: NumericValue
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
  total_amount: NumericValue
  total_capex: NumericValue
  total_opex: NumericValue

  // Custom approval checkboxes for presentation
  manager_approved: boolean
  manager_approved_at?: string
  cfo_approved: boolean
  cfo_approved_at?: string
  founder1_approved: boolean
  founder1_approved_at?: string
  founder2_approved: boolean
  founder2_approved_at?: string
  founder3_approved: boolean
  founder3_approved_at?: string
}

// Payroll Summary Types for Budget Integration
export interface PayrollMonthlySummary {
  month: number // 1-12
  employee_count: number
  total_base_salary: NumericValue
  total_bonuses: NumericValue
  total_other: NumericValue
  total_planned: NumericValue
}

export interface PayrollYearlySummary {
  year: number
  total_employees: number
  total_planned_annual: NumericValue
  total_base_salary_annual: NumericValue
  total_bonuses_annual: NumericValue
  monthly_breakdown: PayrollMonthlySummary[]
}

export interface BudgetVersionWithDetails extends BudgetVersion {
  plan_details: BudgetPlanDetail[]
  scenario?: BudgetScenario
  approval_logs: BudgetApprovalLog[]
  payroll_summary?: PayrollYearlySummary
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

export interface SetApprovalsRequest {
  manager_approved?: boolean
  cfo_approved?: boolean
  founder1_approved?: boolean
  founder2_approved?: boolean
  founder3_approved?: boolean
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
  planned_amount: NumericValue
  type: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: NumericValue
  based_on_total?: NumericValue
  growth_rate?: NumericValue
  created_at: string
  updated_at: string
}

export interface BudgetPlanDetailCreate {
  version_id: number
  month: number
  category_id: number
  subcategory?: string
  planned_amount: NumericValue
  type: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: NumericValue
  based_on_total?: NumericValue
  growth_rate?: NumericValue
}

export interface BudgetPlanDetailUpdate {
  month?: number
  category_id?: number
  subcategory?: string
  planned_amount?: NumericValue
  type?: ExpenseType
  calculation_method?: CalculationMethod
  calculation_params?: Record<string, any>
  business_driver?: string
  justification?: string
  based_on_year?: number
  based_on_avg?: NumericValue
  based_on_total?: NumericValue
  growth_rate?: NumericValue
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
  amount: NumericValue
}

export interface CalculationResult {
  category_id: number
  annual_total: NumericValue
  monthly_avg: NumericValue
  growth_percent: NumericValue
  monthly_breakdown: MonthlyAmount[]
  calculation_method: CalculationMethod
  calculation_params: Record<string, any>
  based_on_total: NumericValue
  based_on_avg: NumericValue
}

export interface BaselineSummary {
  category_id: number
  category_name: string
  total_amount: NumericValue
  monthly_avg: NumericValue
  monthly_breakdown: MonthlyAmount[]
  capex_total: NumericValue
  opex_total: NumericValue
}

export interface VersionComparisonVersion {
  id: number
  version_name?: string
  version_number: number
  status: BudgetVersionStatus
  total_amount: NumericValue
}

export interface VersionComparisonCategory {
  category_id: number
  category_name: string
  version1_amount: NumericValue
  version2_amount: NumericValue
  difference_amount: NumericValue
  difference_percent: NumericValue
}

export interface VersionComparison {
  version1: VersionComparisonVersion
  version2: VersionComparisonVersion
  category_comparisons: VersionComparisonCategory[]
  total_difference_amount: NumericValue
  total_difference_percent: NumericValue
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
