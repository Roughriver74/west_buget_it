/**
 * API client for Payroll Scenarios and Insurance Rates
 */
import apiClient from './client';

export type TaxType = 'INCOME_TAX' | 'PENSION_FUND' | 'MEDICAL_INSURANCE' | 'SOCIAL_INSURANCE' | 'INJURY_INSURANCE';
export type ScenarioType = 'BASE' | 'OPTIMISTIC' | 'PESSIMISTIC' | 'CUSTOM';

export interface InsuranceRate {
  id: number;
  year: number;
  rate_type: TaxType;
  rate_percentage: number;
  threshold_amount?: number;
  rate_above_threshold?: number;
  description?: string;
  legal_basis?: string;
  total_employer_burden?: number;
  department_id: number;
  is_active: boolean;
  created_at: string;
}

export interface PayrollScenario {
  id: number;
  name: string;
  description?: string;
  scenario_type: ScenarioType;
  target_year: number;
  base_year: number;
  headcount_change_percent: number;
  salary_change_percent: number;
  total_headcount?: number;
  total_base_salary?: number;
  total_insurance_cost?: number;
  total_payroll_cost?: number;
  base_year_total_cost?: number;
  cost_difference?: number;
  cost_difference_percent?: number;
  department_id: number;
  is_active: boolean;
  created_at: string;
}

export interface YearlyComparison {
  id: number;
  base_year: number;
  target_year: number;
  base_year_headcount?: number;
  base_year_total_salary?: number;
  base_year_total_insurance?: number;
  base_year_total_cost?: number;
  target_year_headcount?: number;
  target_year_total_salary?: number;
  target_year_total_insurance?: number;
  target_year_total_cost?: number;
  insurance_rate_change?: Record<string, { from: number; to: number; change: number }>;
  total_cost_increase?: number;
  total_cost_increase_percent?: number;
  pension_increase?: number;
  medical_increase?: number;
  social_increase?: number;
  recommendations?: Array<{ type: string; description: string; impact: number }>;
  calculated_at: string;
}

export interface ImpactAnalysis {
  base_year: number;
  target_year: number;
  rate_changes: Record<string, { from: number; to: number; change: number }>;
  total_impact: number;
  impact_percent: number;
  recommendations: Array<{ type: string; description: string; impact: number; details?: any }>;
}

// ==================== Insurance Rates API ====================

export const insuranceRateAPI = {
  list: async (params?: { year?: number; department_id?: number }): Promise<InsuranceRate[]> => {
    const response = await apiClient.get('/payroll-scenarios/insurance-rates', { params });
    return response.data;
  },

  create: async (data: {
    year: number;
    rate_type: TaxType;
    rate_percentage: number;
    description?: string;
    legal_basis?: string;
    department_id?: number;
  }): Promise<InsuranceRate> => {
    const response = await apiClient.post('/payroll-scenarios/insurance-rates', data);
    return response.data;
  },

  update: async (id: number, data: Partial<InsuranceRate>): Promise<InsuranceRate> => {
    const response = await apiClient.put(`/payroll-scenarios/insurance-rates/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/payroll-scenarios/insurance-rates/${id}`);
  },
};

// ==================== Payroll Scenarios API ====================

export const payrollScenarioAPI = {
  list: async (params?: { target_year?: number; department_id?: number }): Promise<PayrollScenario[]> => {
    const response = await apiClient.get('/payroll-scenarios/scenarios', { params });
    return response.data;
  },

  get: async (id: number): Promise<PayrollScenario> => {
    const response = await apiClient.get(`/payroll-scenarios/scenarios/${id}`);
    return response.data;
  },

  create: async (data: {
    name: string;
    description?: string;
    scenario_type: ScenarioType;
    target_year: number;
    base_year: number;
    headcount_change_percent?: number;
    salary_change_percent?: number;
    department_id?: number;
  }): Promise<PayrollScenario> => {
    const response = await apiClient.post('/payroll-scenarios/scenarios', data);
    return response.data;
  },

  update: async (id: number, data: Partial<PayrollScenario>): Promise<PayrollScenario> => {
    const response = await apiClient.put(`/payroll-scenarios/scenarios/${id}`, data);
    return response.data;
  },

  calculate: async (id: number): Promise<PayrollScenario> => {
    const response = await apiClient.post(`/payroll-scenarios/scenarios/${id}/calculate`);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/payroll-scenarios/scenarios/${id}`);
  },
};

// ==================== Analysis API ====================

export const payrollAnalysisAPI = {
  compareYears: async (params: {
    base_year: number;
    target_year: number;
    department_id?: number;
  }): Promise<YearlyComparison> => {
    const response = await apiClient.post('/payroll-scenarios/compare-years', params);
    return response.data;
  },

  getImpactAnalysis: async (params: {
    base_year: number;
    target_year: number;
    department_id?: number;
  }): Promise<ImpactAnalysis> => {
    const response = await apiClient.get('/payroll-scenarios/impact-analysis', { params });
    return response.data;
  },

  getYearlyComparisons: async (department_id?: number): Promise<YearlyComparison[]> => {
    const response = await apiClient.get('/payroll-scenarios/yearly-comparisons', {
      params: { department_id },
    });
    return response.data;
  },
};
