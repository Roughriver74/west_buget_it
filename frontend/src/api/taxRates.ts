import { apiClient } from './client';

export type TaxType =
  | 'INCOME_TAX'
  | 'PENSION_FUND'
  | 'MEDICAL_INSURANCE'
  | 'SOCIAL_INSURANCE'
  | 'INJURY_INSURANCE';

export interface TaxRateListItem {
  id: number;
  tax_type: TaxType;
  name: string;
  description?: string | null;
  rate: number;
  threshold_amount?: number | null;
  rate_above_threshold?: number | null;
  effective_from: string;
  effective_to?: string | null;
  department_id?: number | null;
  is_active: boolean;
  notes?: string | null;
}

export interface TaxRatePayload {
  tax_type: TaxType;
  name: string;
  description?: string;
  rate: number;
  threshold_amount?: number | null;
  rate_above_threshold?: number | null;
  effective_from: string;
  effective_to?: string | null;
  department_id?: number | null;
  is_active?: boolean;
  notes?: string;
}

export interface TaxRateFilters {
  tax_type?: TaxType;
  is_active?: boolean;
  effective_date?: string;
  department_id?: number;
  skip?: number;
  limit?: number;
}

export const taxRateAPI = {
  async list(params: TaxRateFilters) {
    const response = await apiClient.get<TaxRateListItem[]>('tax-rates/', {
      params,
    });
    return response.data;
  },

  async get(id: number) {
    const response = await apiClient.get<TaxRateListItem>(`tax-rates/${id}`);
    return response.data;
  },

  async create(payload: TaxRatePayload) {
    const response = await apiClient.post<TaxRateListItem>('tax-rates/', payload);
    return response.data;
  },

  async update(id: number, payload: Partial<TaxRatePayload>) {
    const response = await apiClient.put<TaxRateListItem>(`tax-rates/${id}`, payload);
    return response.data;
  },

  async remove(id: number) {
    await apiClient.delete(`tax-rates/${id}`);
  },

  async initializeDefault() {
    const response = await apiClient.post<{ message: string; count: number }>(
      'tax-rates/initialize-default',
      null
    );
    return response.data;
  },
};

