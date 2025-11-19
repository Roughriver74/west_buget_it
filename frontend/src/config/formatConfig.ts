/**
 * Number Formatting Configuration
 *
 * Constants for number formatting and display
 */

export const FORMAT_CONFIG = {
  // Number magnitude thresholds
  THOUSAND: 1000,
  MILLION: 1_000_000,
  BILLION: 1_000_000_000,

  // Formatting thresholds (when to apply K, M suffixes)
  FORMAT_THRESHOLD_K: 1000,
  FORMAT_THRESHOLD_M: 1_000_000,
  FORMAT_THRESHOLD_B: 1_000_000_000,

  // Decimal places
  CURRENCY_DECIMALS: 2,
  PERCENTAGE_DECIMALS: 1,
  RATE_DECIMALS: 2,
  LARGE_NUMBER_DECIMALS: 1, // For K, M, B formatting
} as const;

export const INPUT_STEPS = {
  CURRENCY: 1000, // Step for currency inputs (1,000 rubles)
  CURRENCY_SMALL: 100, // Small step for precise currency
  PERCENTAGE: 0.01, // 0.01% step
  PERCENTAGE_WHOLE: 1, // 1% step
  QUANTITY: 1, // Integer quantity
  RATE: 0.01, // 0.01 rate step
} as const;

/**
 * Format number with K, M, B suffixes
 */
export const formatLargeNumber = (value: number, decimals: number = FORMAT_CONFIG.LARGE_NUMBER_DECIMALS): string => {
  if (Math.abs(value) >= FORMAT_CONFIG.BILLION) {
    return (value / FORMAT_CONFIG.BILLION).toFixed(decimals) + 'B';
  }
  if (Math.abs(value) >= FORMAT_CONFIG.MILLION) {
    return (value / FORMAT_CONFIG.MILLION).toFixed(decimals) + 'M';
  }
  if (Math.abs(value) >= FORMAT_CONFIG.THOUSAND) {
    return (value / FORMAT_CONFIG.THOUSAND).toFixed(decimals) + 'K';
  }
  return value.toString();
};

/**
 * Format currency (Russian Rubles)
 */
export const formatCurrency = (value: number, decimals: number = FORMAT_CONFIG.CURRENCY_DECIMALS): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format percentage
 */
export const formatPercentage = (value: number, decimals: number = FORMAT_CONFIG.PERCENTAGE_DECIMALS): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format number with thousand separators
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};
