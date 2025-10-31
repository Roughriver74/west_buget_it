/**
 * Revenue Module Types
 *
 * TypeScript interfaces for Revenue Budget module
 */

// ==================== Enums ====================

export enum RevenueStreamType {
  REGIONAL = 'REGIONAL',  // Региональные (СПБ, СЗФО, Регионы)
  CHANNEL = 'CHANNEL',    // Каналы продаж (Опт, Тендеры, Интернет-магазин)
  PRODUCT = 'PRODUCT',    // Продуктовые (Ортодонтия, Оборудование)
}

export enum RevenueCategoryType {
  PRODUCT = 'PRODUCT',       // Продукция
  SERVICE = 'SERVICE',       // Услуги
  EQUIPMENT = 'EQUIPMENT',   // Оборудование
  TENDER = 'TENDER',         // Тендеры
}

export enum RevenuePlanStatus {
  DRAFT = 'DRAFT',                       // Черновик
  PENDING_APPROVAL = 'PENDING_APPROVAL', // На согласовании
  APPROVED = 'APPROVED',                 // Утвержден
  ACTIVE = 'ACTIVE',                     // Активный
  ARCHIVED = 'ARCHIVED',                 // Архивный
}

export enum RevenueVersionStatus {
  DRAFT = 'DRAFT',                       // Черновик
  PENDING_APPROVAL = 'PENDING_APPROVAL', // На согласовании
  APPROVED = 'APPROVED',                 // Утвержден
  ACTIVE = 'ACTIVE',                     // Активный
}

export enum RevenueForecastMethod {
  LINEAR = 'LINEAR',           // Линейная регрессия
  ARIMA = 'ARIMA',             // ARIMA модель
  SEASONAL = 'SEASONAL',       // Сезонная декомпозиция
  ML_ENSEMBLE = 'ML_ENSEMBLE', // ML ансамбль
}

// ==================== Revenue Stream ====================

export interface RevenueStream {
  id: number
  code: string
  name: string
  stream_type: RevenueStreamType
  parent_id?: number | null
  department_id: number
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface RevenueStreamTree extends RevenueStream {
  children: RevenueStreamTree[]
}

export interface RevenueStreamCreate {
  code: string
  name: string
  stream_type: RevenueStreamType
  parent_id?: number | null
  department_id?: number
  description?: string
}

export interface RevenueStreamUpdate {
  code?: string
  name?: string
  stream_type?: RevenueStreamType
  parent_id?: number | null
  description?: string
  is_active?: boolean
}

// ==================== Revenue Category ====================

export interface RevenueCategory {
  id: number
  code: string
  name: string
  category_type: RevenueCategoryType
  parent_id?: number | null
  department_id: number
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface RevenueCategoryTree extends RevenueCategory {
  subcategories: RevenueCategoryTree[]
}

export interface RevenueCategoryCreate {
  code: string
  name: string
  category_type: RevenueCategoryType
  parent_id?: number | null
  department_id?: number
  description?: string
}

export interface RevenueCategoryUpdate {
  code?: string
  name?: string
  category_type?: RevenueCategoryType
  parent_id?: number | null
  description?: string
  is_active?: boolean
}

// ==================== Revenue Plan ====================

export interface RevenuePlan {
  id: number
  name: string
  year: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id: number
  status: RevenuePlanStatus
  total_planned_revenue?: number
  description?: string
  created_by: number
  created_at: string
  approved_by?: number | null
  approved_at?: string | null
  updated_at?: string
}

export interface RevenuePlanCreate {
  name: string
  year: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id?: number
  description?: string
}

export interface RevenuePlanUpdate {
  name?: string
  status?: RevenuePlanStatus
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  description?: string
}

// ==================== Revenue Plan Version ====================

export interface RevenuePlanVersion {
  id: number
  plan_id: number
  version_number: number
  version_name?: string
  status: RevenueVersionStatus
  description?: string
  created_by: number
  created_at: string
  updated_at?: string
}

export interface RevenuePlanVersionCreate {
  plan_id: number
  version_number: number
  version_name?: string
  description?: string
}

export interface RevenuePlanVersionUpdate {
  version_name?: string
  status?: RevenueVersionStatus
  description?: string
}

// ==================== Revenue Plan Detail ====================

export interface RevenuePlanDetail {
  id: number
  version_id: number
  department_id: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  month_01: number
  month_02: number
  month_03: number
  month_04: number
  month_05: number
  month_06: number
  month_07: number
  month_08: number
  month_09: number
  month_10: number
  month_11: number
  month_12: number
  total?: number
  created_at: string
  updated_at?: string
}

export interface RevenuePlanDetailCreate {
  version_id: number
  department_id?: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  month_01?: number
  month_02?: number
  month_03?: number
  month_04?: number
  month_05?: number
  month_06?: number
  month_07?: number
  month_08?: number
  month_09?: number
  month_10?: number
  month_11?: number
  month_12?: number
}

export interface RevenuePlanDetailUpdate {
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  month_01?: number
  month_02?: number
  month_03?: number
  month_04?: number
  month_05?: number
  month_06?: number
  month_07?: number
  month_08?: number
  month_09?: number
  month_10?: number
  month_11?: number
  month_12?: number
}

// ==================== Revenue Actual ====================

export interface RevenueActual {
  id: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id: number
  year: number
  month: number
  actual_amount: number
  planned_amount?: number
  variance?: number
  variance_percent?: number
  comment?: string
  created_by: number
  created_at: string
  updated_at?: string
}

export interface RevenueActualCreate {
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id?: number
  year: number
  month: number
  actual_amount: number
  planned_amount?: number
  comment?: string
}

export interface RevenueActualUpdate {
  actual_amount?: number
  planned_amount?: number
  comment?: string
}

// ==================== Customer Metrics ====================

export interface CustomerMetrics {
  id: number
  revenue_stream_id: number
  department_id: number
  year: number
  month: number
  total_customer_base: number      // ОКБ (Общая клиентская база)
  active_customer_base: number     // АКБ (Активная клиентская база)
  coverage_percent?: number        // Покрытие (АКБ/ОКБ)
  avg_check_regular?: number       // Средний чек (обычные клиники)
  avg_check_chain?: number         // Средний чек (сетевые клиники)
  avg_check_new?: number           // Средний чек (новые клиники)
  comment?: string
  created_at: string
  updated_at?: string
}

export interface CustomerMetricsCreate {
  revenue_stream_id: number
  department_id?: number
  year: number
  month: number
  total_customer_base: number
  active_customer_base: number
  avg_check_regular?: number
  avg_check_chain?: number
  avg_check_new?: number
  comment?: string
}

export interface CustomerMetricsUpdate {
  total_customer_base?: number
  active_customer_base?: number
  avg_check_regular?: number
  avg_check_chain?: number
  avg_check_new?: number
  comment?: string
}

// ==================== Seasonality Coefficient ====================

export interface SeasonalityCoefficient {
  id: number
  revenue_stream_id: number
  department_id: number
  year: number
  month_01_coeff: number
  month_02_coeff: number
  month_03_coeff: number
  month_04_coeff: number
  month_05_coeff: number
  month_06_coeff: number
  month_07_coeff: number
  month_08_coeff: number
  month_09_coeff: number
  month_10_coeff: number
  month_11_coeff: number
  month_12_coeff: number
  comment?: string
  created_at: string
  updated_at?: string
}

export interface SeasonalityCoefficientCreate {
  revenue_stream_id: number
  department_id?: number
  year: number
  month_01_coeff?: number
  month_02_coeff?: number
  month_03_coeff?: number
  month_04_coeff?: number
  month_05_coeff?: number
  month_06_coeff?: number
  month_07_coeff?: number
  month_08_coeff?: number
  month_09_coeff?: number
  month_10_coeff?: number
  month_11_coeff?: number
  month_12_coeff?: number
  comment?: string
}

// ==================== Revenue Forecast ====================

export interface RevenueForecast {
  id: number
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id: number
  forecast_year: number
  forecast_month: number
  forecast_amount: number
  confidence_level?: number
  forecast_method: RevenueForecastMethod
  based_on_period_start?: string
  based_on_period_end?: string
  comment?: string
  created_by: number
  created_at: string
  updated_at?: string
}

export interface RevenueForecastCreate {
  revenue_stream_id?: number | null
  revenue_category_id?: number | null
  department_id?: number
  forecast_year: number
  forecast_month: number
  forecast_amount: number
  confidence_level?: number
  forecast_method: RevenueForecastMethod
  based_on_period_start?: string
  based_on_period_end?: string
  comment?: string
}

// ==================== Dashboard & Analytics ====================

export interface RevenueDashboardData {
  total_revenue_current_month: number
  total_revenue_previous_month: number
  total_revenue_ytd: number
  plan_vs_actual_current_month: {
    plan: number
    actual: number
    variance: number
    variance_percent: number
  }
  plan_vs_actual_ytd: {
    plan: number
    actual: number
    variance: number
    variance_percent: number
  }
  revenue_by_stream: Array<{
    stream_id: number
    stream_name: string
    amount: number
    percent: number
  }>
  revenue_by_category: Array<{
    category_id: number
    category_name: string
    amount: number
    percent: number
  }>
  monthly_trend: Array<{
    month: number
    month_name: string
    plan: number
    actual: number
  }>
}

export interface RevenueAnalytics {
  year: number
  total_planned: number
  total_actual: number
  variance: number
  variance_percent: number
  by_stream: Array<{
    stream_id: number
    stream_name: string
    stream_type: RevenueStreamType
    planned: number
    actual: number
    variance: number
  }>
  by_category: Array<{
    category_id: number
    category_name: string
    category_type: RevenueCategoryType
    planned: number
    actual: number
    variance: number
  }>
  by_month: Array<{
    month: number
    month_name: string
    planned: number
    actual: number
    variance: number
  }>
}

// ==================== Filters ====================

export interface RevenueStreamFilters {
  is_active?: boolean
  stream_type?: RevenueStreamType
  parent_id?: number | null
  department_id?: number
  skip?: number
  limit?: number
}

export interface RevenueCategoryFilters {
  is_active?: boolean
  category_type?: RevenueCategoryType
  parent_id?: number | null
  department_id?: number
  skip?: number
  limit?: number
}

export interface RevenuePlanFilters {
  year?: number
  status?: RevenuePlanStatus
  revenue_stream_id?: number
  revenue_category_id?: number
  department_id?: number
  skip?: number
  limit?: number
}

export interface RevenueActualFilters {
  year?: number
  month?: number
  revenue_stream_id?: number
  revenue_category_id?: number
  department_id?: number
  skip?: number
  limit?: number
}
