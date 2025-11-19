# Frontend Hardcoded Values Report

## Summary
This report identifies hardcoded configuration values scattered across the frontend codebase that should be moved to configuration files.

## Categories of Hardcoded Values

### 1. API URLs (CRITICAL - 15 files)

**Pattern**: `import.meta.env.VITE_API_URL || 'http://localhost:8000'`

**Files with hardcoded URLs:**

| File | Line | Pattern | Issue |
|------|------|---------|-------|
| `/frontend/src/components/expenses/AttachmentManager.tsx` | 8 | `const API_BASE = import.meta.env.VITE_API_URL \|\| 'http://localhost:8000/api/v1'` | Should use `getApiBaseUrl()` |
| `/frontend/src/components/dashboard/widgets/TotalAmountWidget.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/components/dashboard/widgets/MonthlyTrendWidget.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/components/dashboard/widgets/RecentExpensesWidget.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/components/dashboard/widgets/CategoryChartWidget.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/components/budget/BudgetOverviewTable.tsx` | - | `import.meta.env.VITE_API_URL \|\| 'http://localhost:8000'` | Should use `getApiBaseUrl()` |
| `/frontend/src/components/budget/BudgetPlanTable.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/components/budget/BudgetPlanImportModal.tsx` | - | `const API_URL = import.meta.env.VITE_API_URL \|\| 'http://localhost:8000'` | Should use `getApiBaseUrl()` |
| `/frontend/src/components/kpi/ImportKPIModal.tsx` | - | Same pattern | Should use `getApiBaseUrl()` |
| `/frontend/src/pages/CustomDashboardPage.tsx` | - | `const API_BASE = import.meta.env.VITE_API_URL \|\| 'http://localhost:8000/api/v1'` | Should use `getApiBaseUrl()` |
| `/frontend/src/pages/ExpensesPage.tsx` | 138 | `const apiUrl = import.meta.env.VITE_API_URL \|\| 'http://localhost:8000'` | Should use `getApiBaseUrl()` |
| `/frontend/src/pages/PaymentCalendarPage.tsx` | - | Template literal with fallback | Should use `getApiBaseUrl()` |
| `/frontend/src/pages/ContractorsPage.tsx` | - | 2 instances with fallback | Should use `getApiBaseUrl()` |

**Recommendation**: Create utility function in `/frontend/src/config/api.ts` (already exists as `getApiBaseUrl()` and `buildApiUrl()`). Update all components to use these functions instead of fallback patterns.

---

### 2. Pagination & Page Sizes (24 files)

**Files with hardcoded page sizes:**

| File | Line | Value | Context |
|------|------|-------|---------|
| `/frontend/src/pages/ExpensesPage.tsx` | 20 | `20` | Default page size |
| `/frontend/src/pages/BankTransactionsPage.tsx` | 93 | `50` | Default page size |
| `/frontend/src/pages/UsersPage.tsx` | - | `20` | Default page size |
| `/frontend/src/pages/RevenueStreamsPage.tsx` | - | `20` | Default page size |
| `/frontend/src/components/bank/ProcessingEfficiencyChart.tsx` | - | `10` | Table pagination |
| `/frontend/src/components/bank/CounterpartyAnalysisChart.tsx` | - | `20` | Table pagination |
| `/frontend/src/components/bank/RegularPaymentsInsights.tsx` | - | `8` | Table pagination |
| `/frontend/src/components/expenses/InvoiceProcessingDrawer.tsx` | 508 | `20` | Default page size |
| `/frontend/src/components/references/categories/CategoryTable.tsx` | - | `20` + `['10', '20', '50', '100']` options | Table pagination |
| `/frontend/src/components/payroll/GeneratePayrollExpensesModal.tsx` | - | `5` | Modal table |
| `/frontend/src/components/payroll/CreatePayrollPlanForYearModal.tsx` | - | `10` | Modal table |
| `/frontend/src/components/payroll/RegisterPayrollPaymentModal.tsx` | - | `10` | Modal table |
| `/frontend/src/components/forecast/PaymentForecastChart.tsx` | - | `10` | Chart table |
| `/frontend/src/components/budget/BudgetVersionTable.tsx` | - | `10` | Version table |
| `/frontend/src/components/kpi/KpiAssignmentsTab.tsx` | - | `10` | Tab table |
| `/frontend/src/components/kpi/KpiSummaryTab.tsx` | - | `10` | Tab table |
| `/frontend/src/components/kpi/KpiGoalsTab.tsx` | - | `10` | Tab table |
| `/frontend/src/components/kpi/EmployeeKpiTab.tsx` | - | `10` | Tab table |
| `/frontend/src/components/admin/ApiTokensDrawer.tsx` | - | `10` | Drawer table |
| `/frontend/src/pages/OrganizationDetailPage.tsx` | - | `20` | Detail page table |
| `/frontend/src/pages/ApiTokensPage.tsx` | - | `10` | Page table |
| `/frontend/src/pages/KPIAnalyticsPage.tsx` | - | `10` (2 instances) | Analytics tables |

**Recommendation**: Create `/frontend/src/config/pagination.ts` with:
```typescript
export const PAGINATION_CONFIG = {
  EXPENSES_DEFAULT: 20,
  BANK_TRANSACTIONS_DEFAULT: 50,
  USERS_DEFAULT: 20,
  REVENUE_STREAMS_DEFAULT: 20,
  CHART_TABLE_DEFAULT: 10,
  MODAL_TABLE_DEFAULT: 10,
  MODAL_TABLE_SMALL: 5,
  OPTIONS: ['10', '20', '50', '100'],
  SMALL_OPTIONS: ['5', '10', '20'],
  LARGE_OPTIONS: ['20', '50', '100', '200']
}
```

---

### 3. File Size Limits (2 files)

**Files with hardcoded file sizes:**

| File | Line | Value | Context | Suggestion |
|------|------|-------|---------|-----------|
| `/frontend/src/components/expenses/QuickInvoiceUpload.tsx` | 92-95 | `10` MB | Invoice upload max size | Move to config |
| `/frontend/src/components/kpi/ImportKPIModal.tsx` | 139 | `10` MB | KPI import max size | Move to config |

**Recommendation**: Create `/frontend/src/config/uploadConfig.ts`:
```typescript
export const UPLOAD_CONFIG = {
  INVOICE_MAX_SIZE_MB: 10,
  KPI_IMPORT_MAX_SIZE_MB: 10,
  ATTACHMENT_MAX_SIZE_MB: 10,
  PROFILE_PHOTO_MAX_SIZE_MB: 5,
}
```

---

### 4. Timeouts & Delays (8 files)

**Files with hardcoded timeouts:**

| File | Line | Value | Purpose |
|------|------|-------|---------|
| `/frontend/src/components/bank/SyncProgressModal.tsx` | 26 | `120` polls | Max polling attempts (10 min) |
| `/frontend/src/components/bank/SyncProgressModal.tsx` | 39, 76 | `2000` ms | Initial delay |
| `/frontend/src/components/bank/SyncProgressModal.tsx` | 47 | `3000` ms | Completion delay |
| `/frontend/src/components/bank/SyncProgressModal.tsx` | 58, 70 | `5000` ms | Poll interval |
| `/frontend/src/components/expenses/QuickInvoiceUpload.tsx` | 183 | `3000` ms | Progress update delay |
| `/frontend/src/components/apiTokens/ShowTokenModal.tsx` | 34 | `2000` ms | Copy confirmation timeout |
| `/frontend/src/components/budget/BudgetPlanTable.tsx` | 133, 145, 194 | Unknown | Scroll timeouts |
| `/frontend/src/components/budget/BudgetPlanDetailsTable.tsx` | 522, 532, 594 | Unknown | Scroll timeouts |
| `/frontend/src/contexts/DepartmentContext.tsx` | 97 | Unknown | Department change delay |

**Recommendation**: Create `/frontend/src/config/timingConfig.ts`:
```typescript
export const TIMING_CONFIG = {
  // Polling
  SYNC_POLL_INTERVAL_MS: 5000,      // 5 seconds
  SYNC_MAX_POLLS: 120,              // 10 minutes total
  SYNC_INITIAL_DELAY_MS: 2000,      // 2 seconds
  SYNC_COMPLETION_DELAY_MS: 3000,   // 3 seconds
  
  // UI Feedback
  COPY_CONFIRMATION_TIMEOUT_MS: 2000,
  PROGRESS_UPDATE_DELAY_MS: 3000,
  DEBOUNCE_DELAY_MS: 300,
  TABLE_SCROLL_DELAY_MS: 100,
}
```

---

### 5. Chart & Component Dimensions (30+ instances)

**Chart Heights:**

| Component | Values | Recommendation |
|-----------|--------|-----------------|
| ConfidenceScatterChart | `360` | Move to constants |
| ProcessingEfficiencyChart | `400` | Move to constants |
| DailyFlowChart | `360` | Move to constants |
| CategoryBreakdownChart | `400` | Move to constants |
| CounterpartyAnalysisChart | `400` | Move to constants |
| RegularPaymentsInsights | `300` | Move to constants |
| CashFlowChart | `400` | Move to constants |
| StatusTimelineChart | `360` | Move to constants |
| ActivityHeatmapChart | `300` | Move to constants |
| RegionalDistributionChart | `350` | Move to constants |
| ExhibitionSpendingInsights | `320` | Move to constants |

**Recommendation**: Create `/frontend/src/config/dimensionConfig.ts`:
```typescript
export const CHART_HEIGHTS = {
  SMALL: 300,
  MEDIUM: 320,
  STANDARD: 360,
  LARGE: 400,
  EXTRA_LARGE: 450,
}

export const COMPONENT_WIDTHS = {
  DRAWER_MODAL: 1200,
  LARGE_MODAL: 1000,
  MEDIUM_MODAL: 800,
  SMALL_MODAL: 500,
}

export const MIN_HEIGHTS = {
  EMPTY_STATE: 'calc(100vh - 200px)',
  CONTENT_AREA: '40vh',
  FULL_PAGE: '100vh',
}
```

---

### 6. String Field Lengths (maxLength) (10 files)

**Files with hardcoded field lengths:**

| File | Field | Value | Purpose |
|------|-------|-------|---------|
| All Form Modals | Description/Notes | `500-1000` | Text area max length |
| ContractorFormModal | INN | `12` | Russian tax ID |
| ContractorFormModal | KPP | `9` | Russian regional code |
| OrganizationFormModal | INN | `12` | Russian tax ID |
| OrganizationFormModal | KPP | `9` | Russian regional code |
| Various Forms | General text | `1000` | Description max |

**Recommendation**: Create `/frontend/src/config/validationConfig.ts`:
```typescript
export const FIELD_LENGTHS = {
  DESCRIPTION: 500,
  NOTES: 500,
  LONG_TEXT: 1000,
  SHORT_TEXT: 255,
  
  // Russian-specific
  INN: 12,          // Реквизиты
  KPP: 9,           // Территориальная ПФР
  OGRN: 13,         // Основной государственный реестровый номер
  BIK: 9,           // БИК банка
}
```

---

### 7. Query Limits (3 files)

**Files with hardcoded query limits:**

| File | Value | Purpose |
|------|-------|---------|
| `/frontend/src/components/bank/CreditPortfolioFilters.tsx` | `100, 100, 200` | API query limits |
| `/frontend/src/components/dashboard/widgets/BudgetDeviationHeatmap.tsx` | `1000` | Widget data limit |
| `/frontend/src/components/businessOperationMappings/BusinessOperationMappingFormModal.tsx` | `1000` | Category selection limit |

**Recommendation**: Move to API config or add to pagination config.

---

### 8. Number Formatting Constants (4 files)

**Files with formatting magic numbers:**

| File | Value | Purpose |
|------|-------|---------|
| `/frontend/src/components/dashboard/widgets/BudgetPlanVsActualWidget.tsx` | `1000` | Format K suffix |
| `/frontend/src/components/budget/BudgetScenarioComparisonChart.tsx` | `1000, 1000000` | Format K, M suffixes |
| `/frontend/src/components/forecast/PaymentForecastChart.tsx` | `1000` | Format K suffix |
| `/frontend/src/components/budget/EditableCell.tsx` | `1000` | Input step value |

**Recommendation**: Create `/frontend/src/config/formatConfig.ts`:
```typescript
export const FORMAT_CONFIG = {
  THOUSAND: 1000,
  MILLION: 1000000,
  BILLION: 1000000000,
  
  // Number formatting thresholds
  FORMAT_THRESHOLD_K: 1000,
  FORMAT_THRESHOLD_M: 1000000,
}

export const INPUT_STEPS = {
  CURRENCY: 1000,      // Smallest unit for currency
  PERCENTAGE: 0.01,
  QUANTITY: 1,
}
```

---

### 9. Colors & Theme (50+ hardcoded hex values)

**Files with hardcoded colors:**

Multiple chart and component files contain hardcoded colors like:
- `#1890ff`, `#52c41a`, `#faad14`, `#ff4d4f`, `#722ed1`, etc.

**Examples:**
- `/frontend/src/components/bank/ProcessingEfficiencyChart.tsx` - 10+ color definitions
- `/frontend/src/components/bank/CategoryBreakdownChart.tsx` - Multiple colors
- `/frontend/src/components/bank/TransactionInsightsPanel.tsx` - Status colors
- Various chart components with fill colors

**Recommendation**: Ensure all colors are centralized in theme configuration. Check if Ant Design theme is being fully utilized.

---

## Recommended File Structure

Create the following configuration files:

```
frontend/src/config/
├── api.ts                    ✓ (Already exists - needs updates)
├── axiosConfig.ts           ✓ (Already exists)
├── pagination.ts            (NEW)
├── uploadConfig.ts          (NEW)
├── timingConfig.ts          (NEW)
├── dimensionConfig.ts       (NEW)
├── validationConfig.ts      (NEW)
├── formatConfig.ts          (NEW)
└── themeConfig.ts           (NEW or enhance existing)
```

---

## Implementation Priority

### Priority 1 (Critical) - API URLs
- Affects 15 files
- Risk: Hardcoded localhost URLs in production
- Effort: Medium (find & replace with utility functions)
- Impact: High (production safety)

### Priority 2 (High) - Pagination
- Affects 24 files
- Risk: Inconsistent UX, hard to change globally
- Effort: Medium
- Impact: Medium (maintainability)

### Priority 3 (High) - Timeouts & Delays
- Affects 8 files  
- Risk: Race conditions, poor UX consistency
- Effort: Low
- Impact: Medium

### Priority 4 (Medium) - File Sizes
- Affects 2 files
- Risk: Easy to update wrong values
- Effort: Very Low
- Impact: Low (maintainability)

### Priority 5 (Medium) - Dimensions
- Affects 30+ files
- Risk: Inconsistent layouts
- Effort: Medium
- Impact: Low (maintainability)

### Priority 6 (Low) - Field Lengths
- Affects 10 files
- Risk: Inconsistency
- Effort: Low
- Impact: Very Low

---

## Validation Notes

- All `maxLength` values should match backend validation constraints
- Chart heights should be responsive-compatible
- File size limits should match backend constraints (`INVOICE_MAX_FILE_SIZE=10485760` = 10MB)
- Timeout values should be tested with real API latency
- Page size defaults should balance UX and API performance

