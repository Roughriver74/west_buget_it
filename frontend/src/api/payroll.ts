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
  bonus: number;
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
  bonus_paid: number;
  other_payments_paid: number;
  total_paid: number;
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
  department_id: number;
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
  department_id?: number;
  email?: string;
  phone?: string;
  notes?: string;
}

export interface PayrollPlanCreate {
  year: number;
  month: number;
  employee_id: number;
  base_salary: number;
  bonus?: number;
  other_payments?: number;
  notes?: string;
}

export interface PayrollPlanUpdate {
  base_salary?: number;
  bonus?: number;
  other_payments?: number;
  notes?: string;
}

export interface PayrollActualCreate {
  year: number;
  month: number;
  employee_id: number;
  base_salary_paid: number;
  bonus_paid?: number;
  other_payments_paid?: number;
  payment_date?: string;
  expense_id?: number;
  notes?: string;
}

export interface PayrollActualUpdate {
  base_salary_paid?: number;
  bonus_paid?: number;
  other_payments_paid?: number;
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
    const response = await apiClient.get<Employee[]>('/employees', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await apiClient.get<EmployeeWithSalaryHistory>(`/employees/${id}`);
    return response.data;
  },

  create: async (data: EmployeeCreate) => {
    const response = await apiClient.post<Employee>('/employees', data);
    return response.data;
  },

  update: async (id: number, data: EmployeeUpdate) => {
    const response = await apiClient.put<Employee>(`/employees/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`/employees/${id}`);
  },

  getSalaryHistory: async (id: number) => {
    const response = await apiClient.get<SalaryHistory[]>(`/employees/${id}/salary-history`);
    return response.data;
  },

  addSalaryHistory: async (id: number, data: SalaryHistoryCreate) => {
    const response = await apiClient.post<SalaryHistory>(`/employees/${id}/salary-history`, data);
    return response.data;
  },

  exportToExcel: async (params?: { department_id?: number; status?: string }) => {
    const response = await apiClient.get('/employees/export', {
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
    const response = await apiClient.get<PayrollPlanWithEmployee[]>('/payroll/plans', { params });
    return response.data;
  },

  get: async (id: number) => {
    const response = await apiClient.get<PayrollPlanWithEmployee>(`/payroll/plans/${id}`);
    return response.data;
  },

  create: async (data: PayrollPlanCreate) => {
    const response = await apiClient.post<PayrollPlan>('/payroll/plans', data);
    return response.data;
  },

  update: async (id: number, data: PayrollPlanUpdate) => {
    const response = await apiClient.put<PayrollPlan>(`/payroll/plans/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`/payroll/plans/${id}`);
  },

  exportToExcel: async (params?: { year?: number; month?: number; department_id?: number }) => {
    const response = await apiClient.get('/payroll/plans/export', {
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
    const response = await apiClient.get<PayrollActualWithEmployee[]>('/payroll/actuals', { params });
    return response.data;
  },

  create: async (data: PayrollActualCreate) => {
    const response = await apiClient.post<PayrollActual>('/payroll/actuals', data);
    return response.data;
  },

  update: async (id: number, data: PayrollActualUpdate) => {
    const response = await apiClient.put<PayrollActual>(`/payroll/actuals/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`/payroll/actuals/${id}`);
  },

  exportToExcel: async (params?: { year?: number; month?: number; department_id?: number }) => {
    const response = await apiClient.get('/payroll/actuals/export', {
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
    const response = await apiClient.get<PayrollSummary[]>('/payroll/analytics/summary', {
      params: { year, department_id },
    });
    return response.data;
  },
};
