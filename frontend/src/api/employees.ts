import { apiClient } from './client'

export interface Employee {
  id: number
  full_name: string
  position: string
  position_level?: 'JUNIOR' | 'MIDDLE' | 'SENIOR' | 'LEAD' | 'MANAGER'
  hire_date: string
  termination_date?: string
  status: 'ACTIVE' | 'VACATION' | 'SICK_LEAVE' | 'DISMISSED'
  base_salary: number
  tax_rate: number
  organization_id?: number
  organization?: {
    id: number
    name: string
  }
  email?: string
  phone?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface EmployeeCreate {
  full_name: string
  position: string
  position_level?: 'JUNIOR' | 'MIDDLE' | 'SENIOR' | 'LEAD' | 'MANAGER'
  hire_date: string
  base_salary: number
  tax_rate?: number
  organization_id?: number
  email?: string
  phone?: string
  notes?: string
}

export interface EmployeeUpdate {
  full_name?: string
  position?: string
  position_level?: 'JUNIOR' | 'MIDDLE' | 'SENIOR' | 'LEAD' | 'MANAGER'
  hire_date?: string
  termination_date?: string
  status?: 'ACTIVE' | 'VACATION' | 'SICK_LEAVE' | 'DISMISSED'
  base_salary?: number
  tax_rate?: number
  organization_id?: number
  email?: string
  phone?: string
  notes?: string
}

export interface EmployeeStats {
  total_employees: number
  active_employees: number
  dismissed_employees: number
  on_vacation: number
  on_sick_leave: number
  average_salary: number
  total_annual_payroll: number
}

export interface EmployeeWithPayrolls extends Employee {
  recent_payrolls: any[]
  ytd_total_cost: number
}

export const employeesApi = {
  async getAll(params?: {
    status?: string
    position?: string
    organization_id?: number
    search?: string
    skip?: number
    limit?: number
  }): Promise<Employee[]> {
    const response = await apiClient.get('/employees', { params })
    return response.data
  },

  async getStats(): Promise<EmployeeStats> {
    const response = await apiClient.get('/employees/stats')
    return response.data
  },

  async getById(id: number): Promise<EmployeeWithPayrolls> {
    const response = await apiClient.get(`/employees/${id}`)
    return response.data
  },

  async create(data: EmployeeCreate): Promise<Employee> {
    const response = await apiClient.post('/employees', data)
    return response.data
  },

  async update(id: number, data: EmployeeUpdate): Promise<Employee> {
    const response = await apiClient.put(`/employees/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/employees/${id}`)
  },

  async restore(id: number): Promise<Employee> {
    const response = await apiClient.post(`/employees/${id}/restore`)
    return response.data
  },
}
