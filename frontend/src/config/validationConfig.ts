/**
 * Validation Configuration
 *
 * Form field validation rules and constraints
 * These should match backend validation rules
 */

export const FIELD_LENGTHS = {
  // General text fields
  SHORT_TEXT: 255,
  DESCRIPTION: 500,
  NOTES: 500,
  LONG_TEXT: 1000,
  COMMENT: 1000,

  // Russian tax/legal identifiers
  INN: 12, // ИНН (Идентификационный номер налогоплательщика)
  KPP: 9, // КПП (Код причины постановки на учет)
  OGRN: 13, // ОГРН (Основной государственный регистрационный номер)
  BIK: 9, // БИК (Банковский идентификационный код)
  BANK_ACCOUNT: 20, // Номер банковского счета

  // Other identifiers
  PHONE: 20,
  EMAIL: 255,
  USERNAME: 50,
  NAME: 255,
} as const;

export const VALIDATION_RULES = {
  // INN validation (10 or 12 digits)
  INN: {
    pattern: /^\d{10}$|^\d{12}$/,
    message: 'ИНН должен содержать 10 или 12 цифр',
  },

  // KPP validation (9 digits)
  KPP: {
    pattern: /^\d{9}$/,
    message: 'КПП должен содержать 9 цифр',
  },

  // BIK validation (9 digits)
  BIK: {
    pattern: /^\d{9}$/,
    message: 'БИК должен содержать 9 цифр',
  },

  // Bank account validation (20 digits)
  BANK_ACCOUNT: {
    pattern: /^\d{20}$/,
    message: 'Номер счета должен содержать 20 цифр',
  },

  // Email validation
  EMAIL: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Введите корректный email адрес',
  },

  // Phone validation (flexible for Russian formats)
  PHONE: {
    pattern: /^[\d\s+()-]+$/,
    message: 'Введите корректный номер телефона',
  },
} as const;

export const NUMBER_CONSTRAINTS = {
  // Amount constraints
  MIN_AMOUNT: 0,
  MAX_AMOUNT: 999_999_999_999, // ~1 trillion

  // Percentage constraints
  MIN_PERCENTAGE: 0,
  MAX_PERCENTAGE: 100,

  // Rate constraints
  MIN_RATE: 0,
  MAX_RATE: 100,

  // Tax rate constraints
  MIN_TAX_RATE: 0,
  MAX_TAX_RATE: 1, // 0-100% as 0-1
} as const;
