import { apiClient } from './client';

// ==================== Types ====================

export interface Employee {
  id: number;
  full_name: string;
  position: string;
  employee_number?: string;
  hire_date?: string;
  fire_date?: string;
  status: 'ACTIVE' | 'ON_VACATION' | 'ON_LEAVE' | 'FIRED';
  base_salary: number;
  monthly_bonus_base: number;
  quarterly_bonus_base: number;
  annual_bonus_base: number;
  department_id: number;
  email?: string;
  phone?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface EmployeeWithSalaryHistory extends Employee {
  salary_history: SalaryHistory[];
}

export interface SalaryHistory {
  id: number;
  employee_id: number;
  old_salary?: number;
  new_salary: number;
  effective_date: string;
  reason?: string;
  notes?: string;
  created_at: string;
}

export interface PayrollPlan {
  id: number;
  year: number;
  month: number;
  employee_id: number;
  department_id: number;
  base_salary: number;
  monthly_bonus: number;
  quarterly_bonus: number;
  annual_bonus: number;
  other_payments: number;
  total_planned: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PayrollPlanWithEmployee extends PayrollPlan {
  employee: Employee;
}

export interface PayrollActual {
  id: number;
  year: number;
  month: number;
  employee_id: number;
  department_id: number;
  base_salary_paid: number;
  monthly_bonus_paid: number;
  quarterly_bonus_paid: number;
  annual_bonus_paid: number;
  other_payments_paid: number;
  total_paid: number;  // Gross amount (до вычета налогов)
  // Tax calculations
  income_tax_rate: number;  // Ставка НДФЛ (default 13%)
  income_tax_amount: number;  // Сумма НДФЛ
  social_tax_amount: number;  // Социальные отчисления
  payment_date?: string;
  expense_id?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PayrollActualWithEmployee extends PayrollActual {
  employee: Employee;
}

export interface PayrollSummary {
  year: number;
  month: number;
  total_employees: number;
  total_planned: number;
  total_paid: number;
  variance: number;
  variance_percent: number;
}

export interface SalaryStatistics {
  total_employees: number;
  active_employees?: number;
  avg_salary?: number;
  min_salary: number;
  max_salary: number;
  average_salary?: number;
  median_salary: number;
  percentile_25: number;
  percentile_75: number;
  percentile_90: number;
  std_deviation?: number;
  total_payroll?: number;
}

export interface PayrollStructureMonth {
  year: number;
  month: number;
  total_base_salary: number;
  total_monthly_bonus: number;
  total_quarterly_bonus: number;
  total_annual_bonus: number;
  total_other_payments: number;
  total_amount: number;
  employee_count: number;
}

export interface PayrollDynamics {
  year: number;
  month: number;
  planned_base_salary: number;
  planned_monthly_bonus: number;
  planned_quarterly_bonus: number;
  planned_annual_bonus: number;
  planned_other: number;
  planned_total: number;
  actual_base_salary: number;
  actual_monthly_bonus: number;
  actual_quarterly_bonus: number;
  actual_annual_bonus: number;
  actual_other: number;
  actual_total: number;
  employee_count: number;
}

export interface PayrollForecast {
  year: number;
  month: number;
  forecasted_total: number;
  forecasted_base_salary: number;
  forecasted_monthly_bonus: number;
  forecasted_quarterly_bonus: number;
  forecasted_annual_bonus: number;
  forecasted_other: number;
  employee_count: number;
  confidence: string;
  based_on_months: number;
}

export interface SalaryDistributionBucket {
  range_min: number;
  range_max: number;
  range_label: string;
  employee_count: number;
  percentage: number;
  avg_salary: number;
}

export interface SalaryDistribution {
  total_employees: number;
  buckets: SalaryDistributionBucket[];
  statistics: SalaryStatistics;
}

export interface EmployeePayrollStats {
  employee_id: number;
  employee_name: string;
  position: string;
  department_id: number;
  total_planned: number;
  total_paid: number;
  months_worked: number;
  average_monthly_pay: number;
}

export interface DepartmentPayrollStats {
  department_id: number;
  department_name: string;
  total_employees: number;
  total_planned: number;
  total_paid: number;
  variance: number;
  average_salary: number;
}

// Create types
export interface EmployeeCreate {
  full_name: string;
  position: string;
  employee_number?: string;
  hire_date?: string;
  fire_date?: string;
  status: 'ACTIVE' | 'ON_VACATION' | 'ON_LEAVE' | 'FIRED';
  base_salary: number;
  monthly_bonus_base?: number;
  quarterly_bonus_base?: number;
  annual_bonus_base?: number;
  // department_id is auto-assigned from current_user on backend
  email?: string;
  phone?: string;
  notes?: string;
}

export interface EmployeeUpdate {
  full_name?: string;
  position?: string;
  employee_number?: string;
  hire_date?: string;
  fire_date?: string;
  status?: 'ACTIVE' | 'ON_VACATION' | 'ON_LEAVE' | 'FIRED';
  base_salary?: number;
  monthly_bonus_base?: number;
  quarterly_bonus_base?: number;
  annual_bonus_base?: number;
  // department_id cannot be changed via update
  email?: string;
  phone?: string;
  notes?: string;
}

export interface PayrollPlanCreate {
  year: number;
  month: number;
  employee_id: number;
  base_salary: number;
  monthly_bonus?: number;
  quarterly_bonus?: number;
  annual_bonus?: number;
  other_payments?: number;
  notes?: string;
}

export interface PayrollPlanUpdate {
  base_salary?: number;
  monthly_bonus?: number;
  quarterly_bonus?: number;
  annual_bonus?: number;
  other_payments?: number;
  notes?: string;
}

export interface PayrollActualCreate {
  year: number;
  month: number;
  employee_id: number;
  base_salary_paid: number;
  monthly_bonus_paid?: number;
  quarterly_bonus_paid?: number;
  annual_bonus_paid?: number;
  other_payments_paid?: number;
  // Tax calculations (optional, defaults will be applied)
  income_tax_rate?: number;
  income_tax_amount?: number;
  social_tax_amount?: number;
  payment_date?: string;
  expense_id?: number;
  notes?: string;
}

export interface PayrollActualUpdate {
  base_salary_paid?: number;
  monthly_bonus_paid?: number;
  quarterly_bonus_paid?: number;
  annual_bonus_paid?: number;
  other_payments_paid?: number;
  // Tax calculations (optional for update)
  income_tax_rate?: number;
  income_tax_amount?: number;
  social_tax_amount?: number;
  payment_date?: string;
  expense_id?: number;
  notes?: string;
}

export interface SalaryHistoryCreate {
  employee_id: number;
  old_salary?: number;
  new_salary: number;
  effective_date: string;
  reason?: string;
  notes?: string;
}

// ==================== Employee API ====================

export const employeeAPI = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    department_id?: number;
    status?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<Employee[]>('employees/', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await apiClient.get<EmployeeWithSalaryHistory>(`employees/${id}`);
    return response.data;
  },

  create: async (data: EmployeeCreate) => {
    const response = await apiClient.post<Employee>('employees/', data);
    return response.data;
  },

  update: async (id: number, data: EmployeeUpdate) => {
    const response = await apiClient.put<Employee>(`employees/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`employees/${id}`);
  },

  getSalaryHistory: async (id: number) => {
    const response = await apiClient.get<SalaryHistory[]>(`employees/${id}/salary-history`);
    return response.data;
  },

  addSalaryHistory: async (id: number, data: SalaryHistoryCreate) => {
    const response = await apiClient.post<SalaryHistory>(`employees/${id}/salary-history`, data);
    return response.data;
  },

  exportToExcel: async (params?: { department_id?: number; status?: string }) => {
    const response = await apiClient.get('employees/export', {
      params,
      responseType: 'blob',
    });
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'employees_export.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

// ==================== Payroll Plan API ====================

export const payrollPlanAPI = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    department_id?: number;
    employee_id?: number;
    year?: number;
    month?: number;
  }) => {
    const response = await apiClient.get<PayrollPlanWithEmployee[]>('payroll/plans', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await apiClient.get<PayrollPlanWithEmployee>(`payroll/plans/${id}`);
    return response.data;
  },

  create: async (data: PayrollPlanCreate) => {
    const response = await apiClient.post<PayrollPlan>('payroll/plans', data);
    return response.data;
  },

  update: async (id: number, data: PayrollPlanUpdate) => {
    const response = await apiClient.put<PayrollPlan>(`payroll/plans/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`payroll/plans/${id}`);
  },

  exportToExcel: async (params?: { year?: number; month?: number; department_id?: number }) => {
    const response = await apiClient.get('payroll/plans/export', {
      params,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'payroll_plans_export.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

// ==================== Payroll Actual API ====================

export const payrollActualAPI = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    department_id?: number;
    employee_id?: number;
    year?: number;
    month?: number;
  }) => {
    const response = await apiClient.get<PayrollActualWithEmployee[]>('payroll/actuals', { params });
    return response.data;
  },

  create: async (data: PayrollActualCreate) => {
    const response = await apiClient.post<PayrollActual>('payroll/actuals', data);
    return response.data;
  },

  update: async (id: number, data: PayrollActualUpdate) => {
    const response = await apiClient.put<PayrollActual>(`payroll/actuals/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`payroll/actuals/${id}`);
  },

  exportToExcel: async (params?: { year?: number; month?: number; department_id?: number }) => {
    const response = await apiClient.get('payroll/actuals/export', {
      params,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'payroll_actuals_export.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

// ==================== Analytics API ====================

export const payrollAnalyticsAPI = {
  getSummary: async (year: number, department_id?: number) => {
    const response = await apiClient.get<PayrollSummary[]>('payroll/analytics/summary', {
      params: { year, department_id },
    });
    return response.data;
  },

  getSalaryStats: async (department_id?: number) => {
    const response = await apiClient.get<SalaryStatistics>('payroll/analytics/salary-stats', {
      params: { department_id },
    });
    return response.data;
  },

  getStructure: async (year: number, department_id?: number) => {
    const response = await apiClient.get<PayrollStructureMonth[]>('payroll/analytics/structure', {
      params: { year, department_id },
    });
    return response.data;
  },

  getDynamics: async (year: number, department_id?: number) => {
    const response = await apiClient.get<PayrollDynamics[]>('payroll/analytics/dynamics', {
      params: { year, department_id },
    });
    return response.data;
  },

  getForecast: async (params?: { months_ahead?: number; historical_months?: number; department_id?: number }) => {
    const response = await apiClient.get<PayrollForecast[]>('payroll/analytics/forecast', {
      params,
    });
    return response.data;
  },

  // Integration with Expenses: Generate payroll expense requests
  generatePayrollExpenses: async (params: {
    year: number;
    month: number;
    department_id?: number;
    dry_run?: boolean;
  }) => {
    const response = await apiClient.post<{
      success: boolean;
      dry_run: boolean;
      year: number;
      month: number;
      department_id?: number;
      salary_category_id: number;
      salary_category_name: string;
      statistics: {
        employee_count: number;
        total_amount: number;
        expenses_created: number;
      };
      preview: Array<{
        employee_id: number;
        employee_name: string;
        position: string;
        base_salary: number;
        kpi_percentage: number | null;
        kpi_bonuses: number;
        total_amount: number;
        department_id: number;
      }>;
      message: string;
    }>('payroll/generate-payroll-expenses', null, { params });
    return response.data;
  },

  // Register actual payroll payments from PayrollPlan
  registerPayrollPayment: async (params: {
    year: number;
    month: number;
    payment_type: 'advance' | 'final';
    payment_date?: string;
    department_id?: number;
    dry_run?: boolean;
  }) => {
    const response = await apiClient.post<{
      success: boolean;
      dry_run: boolean;
      payment_type: string;
      payment_date: string;
      year: number;
      month: number;
      department_id?: number;
      statistics: {
        employee_count: number;
        total_amount: number;
        records_created: number;
        skipped_existing: number;
      };
      preview: Array<{
        employee_id: number;
        employee_name: string;
        position: string;
        base_salary_paid: number;
        monthly_bonus_paid: number;
        quarterly_bonus_paid: number;
        annual_bonus_paid: number;
        total_paid: number;
        payment_type: string;
        payment_date: string;
        department_id: number;
      }>;
      message: string;
    }>('payroll/analytics/register-payroll-payment', null, { params });
    return response.data;
  },

  // Get salary distribution (histogram)
  getSalaryDistribution: async (params: {
    year?: number;
    department_id?: number;
    bucket_size?: number;
  }) => {
    const response = await apiClient.get<SalaryDistribution>('payroll/analytics/salary-distribution', {
      params,
    });
    return response.data;
  },

  // Bulk register payroll payments with custom amounts (for edited data)
  registerPayrollPaymentBulk: async (payments: PayrollActualCreate[]) => {
    const response = await apiClient.post<{
      success: boolean;
      created_count: number;
      skipped_count: number;
      total_amount: number;
      errors: string[];
    }>('payroll/analytics/register-payroll-payment-bulk', payments);
    return response.data;
  },
};
