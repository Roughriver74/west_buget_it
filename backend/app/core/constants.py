"""
Application Constants

This file contains all hardcoded values that are used across the application.
These values can be overridden via environment variables in config.py.
"""

# ============================================================================
# TAX RATES & FINANCIAL THRESHOLDS
# ============================================================================

# НДФЛ (Personal Income Tax) Brackets for 2025
TAX_BRACKETS_2025 = [
    {"threshold": 2_400_000, "rate": 0.13},
    {"threshold": 5_000_000, "rate": 0.15},
    {"threshold": 20_000_000, "rate": 0.18},
    {"threshold": 50_000_000, "rate": 0.20},
    {"threshold": float('inf'), "rate": 0.22},  # Top bracket
]

# НДФЛ for 2024 (legacy)
TAX_BRACKETS_2024 = [
    {"threshold": 5_000_000, "rate": 0.13},
    {"threshold": float('inf'), "rate": 0.15},
]

# Social Contributions Limits and Rates
PENSION_FUND_LIMIT = 1_917_000  # ПФР limit
PENSION_FUND_BASE_RATE = 0.22  # Base rate (up to limit)
PENSION_FUND_OVER_LIMIT_RATE = 0.10  # Rate above limit

MEDICAL_INSURANCE_LIMIT = 1_917_000  # ФОМС limit
MEDICAL_INSURANCE_RATE = 0.051

SOCIAL_INSURANCE_LIMIT = 1_032_000  # ФСС limit
SOCIAL_INSURANCE_RATE = 0.029

# Default НДФЛ rate (fallback)
DEFAULT_NDFL_RATE = 0.13

# Tax Calculation Precision
TAX_CALCULATION_TOLERANCE = 0.01  # Tolerance for binary search
TAX_CALCULATION_MAX_ITERATIONS = 50  # Max iterations for tax calculations

# Financial Multipliers
BONUS_MULTIPLIER_HEADCOUNT_CHANGE = 0.5  # Bonus multiplier for staff change scenarios
BONUS_MULTIPLIER_SALARY_CHANGE = 0.5  # Bonus multiplier for salary change scenarios


# ============================================================================
# AI & MACHINE LEARNING THRESHOLDS
# ============================================================================

# Transaction Classifier - Keyword Matching Scores
AI_KEYWORD_EXACT_SCORE = 10  # Exact match
AI_KEYWORD_START_SCORE = 8  # Starts with keyword
AI_KEYWORD_CONTAINS_SCORE = 5  # Contains keyword

# Transaction Classifier - Confidence Calculation
AI_MIN_SCORE_THRESHOLD = 5  # Minimum score to consider
AI_CONFIDENCE_MIN_BASE = 0.7  # Base confidence minimum
AI_SCORE_TO_CONFIDENCE_DIVISOR = 50  # Divisor for score-to-confidence conversion
AI_CONFIDENCE_MAX_CAP = 0.95  # Maximum confidence cap

# Transaction Classifier - Historical Data
AI_HISTORICAL_CONFIDENCE = 0.95  # Confidence from historical matches
AI_MIN_HISTORICAL_TRANSACTIONS = 2  # Minimum transactions for historical analysis

# Transaction Classifier - Name-based Matching
AI_NAME_BASED_CONFIDENCE_MULTIPLIER = 0.8  # Confidence multiplier for name matches

# Transaction Classifier - Default Confidences by Type
AI_DEFAULT_CREDIT_CONFIDENCE = 0.6  # Default for CREDIT transactions
AI_DEFAULT_DEBIT_CONFIDENCE = 0.5  # Default for DEBIT transactions

# Transaction Classifier - Boosts
AI_CREDIT_TYPE_BOOST = 0.1  # Boost for CREDIT transactions
AI_DEBIT_TYPE_BOOST = 0.05  # Boost for DEBIT transactions
AI_MATCH_COUNT_MULTIPLIER = 0.1  # Multiplier per matching keyword

# Bank Transaction Import - Auto-categorization Thresholds
AI_HIGH_CONFIDENCE_THRESHOLD = 0.9  # Auto-assign category if confidence > 90%
AI_MEDIUM_CONFIDENCE_THRESHOLD = 0.5  # Needs review if confidence < 50%

# Regular Payment Detection
REGULAR_PAYMENT_PATTERN_THRESHOLD = 0.3  # 30% variation threshold for pattern detection

# Invoice AI Parser
AI_PARSER_TEMPERATURE = 0.1  # Low temperature for consistent parsing
AI_PARSER_MAX_TOKENS = 4000  # Maximum tokens for AI response

# OCR
CYRILLIC_RATIO_THRESHOLD = 0.1  # Threshold for Cyrillic text detection


# ============================================================================
# PAGINATION & BATCH SIZES
# ============================================================================

# Default Pagination
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000

# Specific Entity Pagination
DEFAULT_EXPENSES_PAGE_SIZE = 50
MAX_EXPENSES_PAGE_SIZE = 500  # Reduced from 100

DEFAULT_BANK_TX_PAGE_SIZE = 50
MAX_BANK_TX_PAGE_SIZE = 500

CREDIT_PORTFOLIO_PAGE_SIZE = 20
MAX_CREDIT_PORTFOLIO_PAGE_SIZE = 1000  # Reduced from 50,000 (excessive!)

REVENUE_PLAN_DETAILS_PAGE_SIZE = 100
MAX_REVENUE_PLAN_DETAILS_PAGE_SIZE = 1000  # Reduced from 10,000 (excessive!)

# Top Items Limits (for analytics)
TOP_ITEMS_DEFAULT_LIMIT = 5
TOP_ITEMS_MAX_LIMIT = 20

# Batch Processing
SYNC_BATCH_SIZE = 100  # Batch size for 1C sync operations
EXCEL_SKIP_ROWS = [1]  # Skip first row (header) when reading Excel
PREVIEW_SAMPLE_ROWS = 5  # Number of rows to show in import preview
IMPORT_PREVIEW_ROWS = 10  # Maximum preview rows for unified import


# ============================================================================
# RATE LIMITING
# ============================================================================

# Rate Limits (requests per time window)
RATE_LIMIT_REQUESTS_PER_MINUTE = 500
RATE_LIMIT_REQUESTS_PER_HOUR = 5000

# Default Rate Limits (if not specified in endpoint)
RATE_LIMIT_DEFAULT_REQUESTS_PER_MINUTE = 100
RATE_LIMIT_DEFAULT_REQUESTS_PER_HOUR = 1000

# Redis Configuration for Rate Limiting
REDIS_SOCKET_TIMEOUT = 5  # Socket timeout in seconds
REDIS_MINUTE_WINDOW_TTL = 120  # 2 minutes buffer for minute window
REDIS_HOUR_WINDOW_TTL = 7200  # 2 hours buffer for hour window
RATE_LIMIT_CLEANUP_INTERVAL = 300  # 5 minutes cleanup interval


# ============================================================================
# API TIMEOUTS
# ============================================================================

# OData 1C Integration
ODATA_REQUEST_TIMEOUT = 30  # Default HTTP request timeout (seconds)
ODATA_CONNECTION_TIMEOUT = 30  # Connection timeout
ODATA_GET_REQUEST_TIMEOUT = 10  # GET request timeout


# ============================================================================
# SECURITY
# ============================================================================

# HSTS (HTTP Strict Transport Security)
HSTS_MAX_AGE = 31_536_000  # 1 year in seconds


# ============================================================================
# FILE HANDLING & VALIDATION
# ============================================================================

# Excel Export
EXCEL_TEMPLATE_PATH = "xls/Planning_Template_10.2025-3.xlsx"
BUDGET_WARNING_THRESHOLD = 0.2  # 20% threshold for budget warnings

# Number Precision
FLOAT_TOLERANCE = 0.01  # Floating point comparison tolerance


# ============================================================================
# BUSINESS LOGIC
# ============================================================================

# Business Operation Mapping
DEFAULT_MAPPING_CONFIDENCE = 0.98  # Default confidence for operation mappings

# Month Validation
MIN_MONTH = 1
MAX_MONTH = 12

# Column Numbers (for Excel export - consider refactoring to use names)
EXCEL_COLUMN_NAMES = {
    'MONTH': 2,
    'CATEGORY': 7,
    'AMOUNT': 14,
}
