/**
 * Pagination Configuration
 *
 * Centralized pagination settings for consistent UX across the application
 */

export const PAGINATION_CONFIG = {
  // Default page sizes for different entity types
  EXPENSES_DEFAULT: 20,
  BANK_TRANSACTIONS_DEFAULT: 50,
  USERS_DEFAULT: 20,
  REVENUE_STREAMS_DEFAULT: 20,
  CONTRACTORS_DEFAULT: 20,
  ORGANIZATIONS_DEFAULT: 20,

  // Table sizes by context
  CHART_TABLE_DEFAULT: 10,
  MODAL_TABLE_DEFAULT: 10,
  MODAL_TABLE_SMALL: 5,
  MODAL_TABLE_LARGE: 20,

  // Page size options (dropdown selections)
  OPTIONS: [10, 20, 50, 100],
  OPTIONS_STRINGS: ['10', '20', '50', '100'], // For Ant Design Select
  SMALL_OPTIONS: [5, 10, 20],
  SMALL_OPTIONS_STRINGS: ['5', '10', '20'],
  LARGE_OPTIONS: [20, 50, 100, 200],
  LARGE_OPTIONS_STRINGS: ['20', '50', '100', '200'],
} as const;

// Export individual constants for convenience
export const DEFAULT_PAGE_SIZE = PAGINATION_CONFIG.EXPENSES_DEFAULT;
export const PAGE_SIZE_OPTIONS = PAGINATION_CONFIG.OPTIONS_STRINGS;
