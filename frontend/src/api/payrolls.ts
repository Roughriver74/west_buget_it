import { apiClient } from './client'

export interface Payroll {
  id: number
  employee_id: number
  employee?: {
    id: number
    full_name: string
    position: string
  }
  year: number
  month: number
  base_salary: number
  bonus: number
  other_payments: number
  gross_salary: number
  taxes: number
  net_salary: number
  employer_taxes: number
  total_cost: number
  worked_days?: number
  payment_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface PayrollCreate {
  employee_id: number
  year: number
  month: number
  base_salary: number
  bonus?: number
  other_payments?: number
  worked_days?: number
  payment_date?: string
  notes?: string
}

export interface PayrollUpdate {
  base_salary?: number
  bonus?: number
  other_payments?: number
  worked_days?: number
  payment_date?: string
  notes?: string
}

export interface PayrollSummary {
  year: number
  month?: number
  total_gross: number
  total_taxes: number
  total_net: number
  total_employer_taxes: number
  total_cost: number
  employees_count: number
  average_salary: number
}

export interface GeneratePayrollsRequest {
  year: number
}

export interface GeneratePayrollsResponse {
  created_count: number
  message: string
}

export const payrollsApi = {
  async getAll(params?: {
    employee_id?: number
    year?: number
    month?: number
    skip?: number
    limit?: number
  }): Promise<Payroll[]> {
    const response = await apiClient.get('/payrolls', { params })
    return response.data
  },

  async getSummary(params?: {
    year?: number
    month?: number
  }): Promise<PayrollSummary[]> {
    const response = await apiClient.get('/payrolls/summary', { params })
    return response.data
  },

  async getById(id: number): Promise<Payroll> {
    const response = await apiClient.get(`/payrolls/${id}`)
    return response.data
  },

  async create(data: PayrollCreate): Promise<Payroll> {
    const response = await apiClient.post('/payrolls', data)
    return response.data
  },

  async update(id: number, data: PayrollUpdate): Promise<Payroll> {
    const response = await apiClient.put(`/payrolls/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/payrolls/${id}`)
  },

  async generateForYear(year: number): Promise<GeneratePayrollsResponse> {
    const response = await apiClient.post(`/payrolls/generate/${year}`)
    return response.data
  },
}
