// Bonus type enums matching backend
export type BonusType = 'FIXED' | 'PERFORMANCE_BASED' | 'MIXED'

// Employee status
export type EmployeeStatus = 'ACTIVE' | 'INACTIVE' | 'ON_LEAVE'

// Payroll interfaces
export interface Employee {
  id: number
  full_name: string
  position: string
  base_salary: number
  monthly_bonus_base?: number
  department_id: number
  status: EmployeeStatus
  hire_date?: string
  created_at: string
  updated_at: string
}

export interface PayrollPlan {
  id: number
  employee_id: number
  year: number
  month: number
  base_salary_planned: number
  monthly_bonus_planned: number
  quarterly_bonus_planned: number
  annual_bonus_planned: number
  monthly_bonus_type: BonusType
  quarterly_bonus_type: BonusType
  annual_bonus_type: BonusType
  department_id: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface PayrollActual {
  id: number
  employee_id: number
  year: number
  month: number
  base_salary_paid: number
  monthly_bonus_paid: number
  quarterly_bonus_paid: number
  annual_bonus_paid: number
  other_payments_paid: number
  total_paid: number
  income_tax_rate: number
  income_tax_amount: number
  social_tax_amount: number
  department_id: number
  notes?: string
  created_at: string
  updated_at: string
}
