# Hardcoded Values in Backend - Comprehensive Report

## Summary
Found **50+ hardcoded values** that should be moved to configuration. These include:
- Magic numbers (timeouts, limits, rates, thresholds)
- Tax rates and financial thresholds
- API endpoints and URLs
- Database and cache configuration
- Pagination and batch sizes
- Confidence thresholds for AI
- File size limits and paths

---

## 1. CRITICAL CONFIGURATION (Should be in .env or config.py)

### 1.1 Rate Limiting (main.py, rate_limit.py)
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/main.py | 84 | `500` (requests_per_minute) | Magic number | `RATE_LIMIT_REQUESTS_PER_MINUTE` |
| backend/app/main.py | 84 | `5000` (requests_per_hour) | Magic number | `RATE_LIMIT_REQUESTS_PER_HOUR` |
| backend/app/middleware/rate_limit.py | 32 | `100` (default requests_per_minute) | Magic number | Default from config |
| backend/app/middleware/rate_limit.py | 32 | `1000` (default requests_per_hour) | Magic number | Default from config |
| backend/app/middleware/rate_limit.py | 49-50 | `5` (socket timeout seconds) | Magic number | `REDIS_SOCKET_TIMEOUT` |
| backend/app/middleware/rate_limit.py | 103 | `120` (2 minutes buffer) | Magic number | `REDIS_MINUTE_WINDOW_TTL` |
| backend/app/middleware/rate_limit.py | 105 | `7200` (2 hours buffer) | Magic number | `REDIS_HOUR_WINDOW_TTL` |
| backend/app/middleware/rate_limit.py | 64 | `300` (5 minutes cleanup interval) | Magic number | `RATE_LIMIT_CLEANUP_INTERVAL` |

### 1.2 JWT & Authentication (utils/auth.py, core/config.py)
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/utils/auth.py | 25 | `60 * 24 * 7` (7 days) | Magic number | **Uses `settings.ACCESS_TOKEN_EXPIRE_MINUTES` but hardcoded 7 days locally** |
| backend/app/core/config.py | 108 | `30` (minutes) | Config | ✓ Already configurable |

**Issue**: `utils/auth.py` line 25 overrides config with hardcoded 7 days instead of using `settings.ACCESS_TOKEN_EXPIRE_MINUTES`

### 1.3 Security Headers (middleware/security_headers.py)
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/middleware/security_headers.py | 79 | `31536000` (1 year for HSTS) | Magic number | `HSTS_MAX_AGE` |

---

## 2. TAX RATES & FINANCIAL THRESHOLDS (utils/)

### 2.1 НДФЛ Progressive Tax Brackets (ndfl_calculator.py)
| File | Line | Values | Type | Issue |
|------|------|--------|------|-------|
| backend/app/utils/ndfl_calculator.py | 14-20 | TAX_BRACKETS_2025 | Hardcoded | Should be in config or database |
| backend/app/utils/ndfl_calculator.py | 15 | `2400000` | Bracket threshold | Config: `TAX_BRACKET_2025_TIER1_THRESHOLD` |
| backend/app/utils/ndfl_calculator.py | 15 | `0.13` | Tax rate | Config: `TAX_BRACKET_2025_TIER1_RATE` |
| backend/app/utils/ndfl_calculator.py | 16 | `5000000` | Bracket threshold | Config: `TAX_BRACKET_2025_TIER2_THRESHOLD` |
| backend/app/utils/ndfl_calculator.py | 16 | `0.15` | Tax rate | Config: `TAX_BRACKET_2025_TIER2_RATE` |
| backend/app/utils/ndfl_calculator.py | 17 | `20000000` | Bracket threshold | Config: `TAX_BRACKET_2025_TIER3_THRESHOLD` |
| backend/app/utils/ndfl_calculator.py | 17 | `0.18` | Tax rate | Config: `TAX_BRACKET_2025_TIER3_RATE` |
| backend/app/utils/ndfl_calculator.py | 18 | `50000000` | Bracket threshold | Config: `TAX_BRACKET_2025_TIER4_THRESHOLD` |
| backend/app/utils/ndfl_calculator.py | 18 | `0.20` | Tax rate | Config: `TAX_BRACKET_2025_TIER4_RATE` |
| backend/app/utils/ndfl_calculator.py | 19 | `0.22` | Tax rate (top bracket) | Config: `TAX_BRACKET_2025_TIER5_RATE` |
| backend/app/utils/ndfl_calculator.py | 24 | `5000000` | 2024 threshold | Config: `TAX_BRACKET_2024_THRESHOLD` |
| backend/app/utils/ndfl_calculator.py | 25 | `0.15` | 2024 top rate | Config: `TAX_BRACKET_2024_TOP_RATE` |
| backend/app/utils/ndfl_calculator.py | 181 | `0.01` | Tolerance for binary search | Config: `TAX_CALCULATION_TOLERANCE` |
| backend/app/utils/ndfl_calculator.py | 182 | `50` | Max iterations for binary search | Config: `TAX_CALCULATION_MAX_ITERATIONS` |
| backend/app/utils/ndfl_calculator.py | 214 | `0.22` | Max rate for 2025+ | Derived from config |

### 2.2 Social Contributions (social_contributions_calculator.py)
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/utils/social_contributions_calculator.py | 14-15 | `1917000` (ПФР limit) | Threshold | `PENSION_FUND_LIMIT` |
| backend/app/utils/social_contributions_calculator.py | 17-18 | `1917000` (ФОМС limit) | Threshold | `MEDICAL_INSURANCE_LIMIT` |
| backend/app/utils/social_contributions_calculator.py | 20-21 | `1032000` (ФСС limit) | Threshold | `SOCIAL_INSURANCE_LIMIT` |
| backend/app/utils/social_contributions_calculator.py | 24 | `0.22` | ПФР base rate | `PENSION_FUND_BASE_RATE` |
| backend/app/utils/social_contributions_calculator.py | 25 | `0.10` | ПФР over-limit rate | `PENSION_FUND_OVER_LIMIT_RATE` |
| backend/app/utils/social_contributions_calculator.py | 27 | `0.051` | ФОМС rate | `MEDICAL_INSURANCE_RATE` |
| backend/app/utils/social_contributions_calculator.py | 28 | `0.029` | ФСС rate | `SOCIAL_INSURANCE_RATE` |

---

## 3. AI & CONFIDENCE THRESHOLDS (services/transaction_classifier.py, bank_transaction_import.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/services/transaction_classifier.py | 238 | `5` | Min score threshold | `AI_MIN_SCORE_THRESHOLD` |
| backend/app/services/transaction_classifier.py | 241 | `0.7` | Min confidence base | `AI_CONFIDENCE_MIN_BASE` |
| backend/app/services/transaction_classifier.py | 241 | `50` | Score to confidence divisor | `AI_SCORE_TO_CONFIDENCE_DIVISOR` |
| backend/app/services/transaction_classifier.py | 241 | `0.95` | Max confidence cap | `AI_CONFIDENCE_MAX_CAP` |
| backend/app/services/transaction_classifier.py | 287 | `0.95` | Historical confidence | `AI_HISTORICAL_CONFIDENCE` |
| backend/app/services/transaction_classifier.py | 300 | `0.8` | Name-based confidence multiplier | `AI_NAME_BASED_CONFIDENCE_MULTIPLIER` |
| backend/app/services/transaction_classifier.py | 308 | `0.6` | Default CREDIT confidence | `AI_DEFAULT_CREDIT_CONFIDENCE` |
| backend/app/services/transaction_classifier.py | 310 | `0.5` | Default DEBIT confidence | `AI_DEFAULT_DEBIT_CONFIDENCE` |
| backend/app/services/transaction_classifier.py | 346 | `2` | Min historical transactions | `AI_MIN_HISTORICAL_TRANSACTIONS` |
| backend/app/services/transaction_classifier.py | 222-230 | `10`, `8`, `5` | Keyword match scores | `AI_KEYWORD_EXACT_SCORE`, `AI_KEYWORD_START_SCORE`, `AI_KEYWORD_CONTAINS_SCORE` |
| backend/app/services/transaction_classifier.py | 430 | `0.7` | Base confidence calculation | Part of formula |
| backend/app/services/transaction_classifier.py | 430 | `0.1` | Match count multiplier | `AI_MATCH_COUNT_MULTIPLIER` |
| backend/app/services/transaction_classifier.py | 430 | `0.95` | Max confidence cap | `AI_CONFIDENCE_MAX_CAP` |
| backend/app/services/transaction_classifier.py | 434 | `0.1` | CREDIT boost | `AI_TRANSACTION_TYPE_BOOST` |
| backend/app/services/transaction_classifier.py | 436 | `0.05` | DEBIT boost | `AI_DEBIT_BOOST` |
| backend/app/services/transaction_classifier.py | 669 | `0.3` | Pattern variation threshold (30%) | `REGULAR_PAYMENT_PATTERN_THRESHOLD` |
| backend/app/services/bank_transaction_import.py | 307 | `0.9` | High confidence threshold | `AI_HIGH_CONFIDENCE_THRESHOLD` |
| backend/app/services/bank_transaction_import.py | 311 | `0.5` | Medium confidence threshold | `AI_MEDIUM_CONFIDENCE_THRESHOLD` |
| backend/app/services/invoice_ai_parser.py | 56 | `0.1` | Temperature (randomness) | `AI_PARSER_TEMPERATURE` |
| backend/app/services/invoice_ai_parser.py | 57 | `4000` | Max tokens | `AI_PARSER_MAX_TOKENS` |

---

## 4. PAGINATION & BATCH SIZES (api/v1/, services/)

### 4.1 API Endpoints - Pagination
| File | Line | Current Default | Max | Suggested Config |
|------|------|---|---|---|
| backend/app/api/v1/organizations.py | 35 | `100` | `1000` | `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE` |
| backend/app/api/v1/expenses.py | 159 | `50` | `100` | `DEFAULT_EXPENSES_PAGE_SIZE`, `MAX_EXPENSES_PAGE_SIZE` |
| backend/app/api/v1/bank_transactions.py | 84 | `50` | `500` | `DEFAULT_BANK_TX_PAGE_SIZE`, `MAX_BANK_TX_PAGE_SIZE` |
| backend/app/api/v1/business_operation_mappings.py | 45-46 | `0`, `100` | - | `DEFAULT_PAGE_SIZE` |
| backend/app/api/v1/revenue_streams.py | 62 | `100` | `1000` | `DEFAULT_PAGE_SIZE` |
| backend/app/api/v1/payroll.py | 68 | `100` | `1000` | `DEFAULT_PAGE_SIZE` |
| backend/app/api/v1/budget_planning.py | 599 | - | `1-12` | Month validation (OK) |
| backend/app/api/v1/credit_portfolio.py | 75 | `100` | `50000` | ⚠️ Very high max! Should be `1000` |
| backend/app/api/v1/credit_portfolio.py | 325 | `20` | `100` | `CREDIT_PORTFOLIO_PAGE_SIZE` |
| backend/app/api/v1/credit_portfolio.py | 719 | `1000` | `50000` | ⚠️ Very high! Should be `1000` max |
| backend/app/api/v1/revenue_plan_details.py | 103 | `1000` | `10000` | ⚠️ Too high! Should be `500` max |
| backend/app/api/v1/revenue_analytics.py | 368 | `5` | `20` | `TOP_ITEMS_DEFAULT_LIMIT` |
| backend/app/api/v1/customer_metrics.py | 65 | `100` | `1000` | `DEFAULT_PAGE_SIZE` |

### 4.2 Batch Processing
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/api/v1/organizations.py | 382 | `100` | Batch size | `SYNC_BATCH_SIZE` |
| backend/app/api/v1/expenses.py | 979 | `100` | Batch size | `SYNC_BATCH_SIZE` |
| backend/app/services/dynamic_import_service.py | 204 | `[1]` | Skip rows for header | `EXCEL_SKIP_ROWS` |
| backend/app/services/bank_transaction_import.py | 56 | `5` | Sample preview rows | `PREVIEW_SAMPLE_ROWS` |

---

## 5. DATABASE & CONNECTION (core/config.py)

| File | Line | Current Value | Type | Status |
|------|------|---------------|------|--------|
| backend/app/core/config.py | 58 | `54329` | Port | ✓ Configurable via `DB_PORT` |
| backend/app/core/config.py | 62 | `10` | Pool size | ✓ Configurable via `DB_POOL_SIZE` |
| backend/app/core/config.py | 63 | `20` | Max overflow | ✓ Configurable via `DB_MAX_OVERFLOW` |
| backend/app/core/config.py | 64 | `30` | Pool timeout | ✓ Configurable via `DB_POOL_TIMEOUT` |
| backend/app/core/config.py | 65 | `1800` | Pool recycle | ✓ Configurable via `DB_POOL_RECYCLE` |

---

## 6. REDIS & CACHE (core/config.py, middleware/, services/)

| File | Line | Current Value | Type | Status |
|------|------|---------------|------|--------|
| backend/app/core/config.py | 111-117 | Redis config | - | ✓ All configurable |
| backend/app/core/config.py | 116 | `300` (seconds) | Cache TTL | ✓ Configurable `BASELINE_CACHE_TTL_SECONDS` |
| backend/app/core/config.py | 117 | `300` (seconds) | Cache TTL | ✓ Configurable `CACHE_TTL_SECONDS` |
| backend/app/middleware/rate_limit.py | 64 | `300` | Cleanup interval | Hardcoded locally |

---

## 7. OCR & AI PROCESSING (invoice_processor.py, invoice_ocr.py, invoice_ai_parser.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/core/config.py | 125 | `"rus+eng"` | OCR language | ✓ `OCR_LANGUAGE` |
| backend/app/core/config.py | 126 | `300` | OCR DPI | ✓ `OCR_DPI` |
| backend/app/services/invoice_ocr.py | 46 | `0.1` | Cyrillic ratio threshold | `CYRILLIC_RATIO_THRESHOLD` |
| backend/app/services/invoice_ai_parser.py | 56 | `0.1` | Temperature | `AI_PARSER_TEMPERATURE` |
| backend/app/services/invoice_ai_parser.py | 57 | `4000` | Max tokens | `AI_PARSER_MAX_TOKENS` |

---

## 8. 1C OData Integration (services/odata_1c_client.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/services/odata_1c_client.py | 60 | `30` | HTTP timeout (seconds) | `ODATA_REQUEST_TIMEOUT` |
| backend/app/services/odata_1c_client.py | 95 | `30` | Connection timeout | `ODATA_CONNECTION_TIMEOUT` |
| backend/app/services/odata_1c_client.py | 969 | `10` | Get request timeout | `ODATA_GET_REQUEST_TIMEOUT` |
| backend/app/services/odata_1c_client.py | 1028 | `http://10.10.100.77/trade/odata/standard.odata` | Default URL | **Uses `ODATA_1C_URL` from config ✓** |
| backend/app/schemas/bank_transaction.py | 195 | `http://10.10.100.77/trade/odata/standard.odata` | Default URL | Duplicate - should reference config |

---

## 9. EXCEL EXPORT (utils/excel_export.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/utils/excel_export.py | 109, 114, etc. | Various | Column numbers (2, 7, 14) | Should use named constants |
| backend/app/utils/excel_export.py | 697 | `"xls/Planning_Template_10.2025-3.xlsx"` | Template path | `EXCEL_TEMPLATE_PATH` |
| backend/app/utils/excel_export.py | 413 | `0.2` (20% threshold) | Budget warning threshold | `BUDGET_WARNING_THRESHOLD` |

---

## 10. FINANCIAL CALCULATIONS (services/payroll_scenario_calculator.py, api/v1/payroll.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/api/v1/payroll.py | 1685 | `0.5` | Bonus multiplier for staff change | `BONUS_MULTIPLIER_HEADCOUNT_CHANGE` |
| backend/app/api/v1/payroll.py | 1691 | `0.5` | Bonus multiplier for salary change | `BONUS_MULTIPLIER_SALARY_CHANGE` |
| backend/app/services/payroll_scenario_calculator.py | 87 | `0.13` | Fallback NDFL rate | Should use `TAX_BRACKET_*_RATE` from config |
| backend/app/db/models.py | 798 | `0.13` | Default NDFL rate | `DEFAULT_NDFL_RATE` |
| backend/app/db/models.py | 2142 | `0.98` | Default confidence for mapping | `DEFAULT_MAPPING_CONFIDENCE` |

---

## 11. FTP & FILE HANDLING (core/config.py, ftp_import_service.py)

| File | Line | Current Value | Type | Status |
|------|------|---------------|------|--------|
| backend/app/core/config.py | 135-139 | FTP credentials & paths | - | ✓ All configurable |

---

## 12. UNIFIED IMPORT SERVICE (services/unified_import_service.py)

| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/services/unified_import_service.py | 328 | `10` | Preview row limit | `IMPORT_PREVIEW_ROWS` |
| backend/app/services/unified_import_service.py | 499 | `0.01` | Floating point tolerance | `FLOAT_TOLERANCE` |

---

## 13. SECURITY HEADERS (middleware/security_headers.py)

| File | Line | Current Value | Type | Should Be Config |
|------|------|---------------|------|------------------|
| backend/app/middleware/security_headers.py | 79 | `31536000` (1 year) | HSTS max-age | `HSTS_MAX_AGE` |

---

## 14. SCHEDULER CONFIGURATION (services/scheduler.py)

Need to check: What are the hardcoded schedule times?
| File | Line | Current Value | Type | Suggested Config Variable |
|------|------|---------------|------|--------------------------|
| backend/app/core/config.py | 142-145 | Scheduler settings | - | ✓ Already configurable |

---

## RECOMMENDATIONS BY PRIORITY

### HIGH PRIORITY (Security & Performance)
1. **Move JWT token expiry from hardcoded 7 days to use `settings.ACCESS_TOKEN_EXPIRE_MINUTES`** 
   - File: `backend/app/utils/auth.py:25`
   - Current: `60 * 24 * 7`
   - Fix: Use `ACCESS_TOKEN_EXPIRE_MINUTES` from config

2. **Create constants file for tax rates & thresholds**
   - File: `backend/app/utils/constants.py` (new)
   - Move all tax brackets, rates, limits from `ndfl_calculator.py` and `social_contributions_calculator.py`
   - Make configurable in `.env` or database

3. **Create constants file for AI thresholds**
   - File: `backend/app/services/constants.py` (new)
   - Move confidence thresholds, min scores, etc.
   - Allow override via environment variables

4. **Fix rate limiting misconfiguration**
   - Add `RATE_LIMIT_REQUESTS_PER_MINUTE` and `RATE_LIMIT_REQUESTS_PER_HOUR` to config
   - Default values in main.py should come from settings

5. **Fix excessive pagination limits**
   - `backend/app/api/v1/credit_portfolio.py:75` - max `50000` should be `1000`
   - `backend/app/api/v1/revenue_plan_details.py:103` - max `10000` should be `1000`

### MEDIUM PRIORITY (Maintainability)
6. **Extract numeric constants to named variables**
   - HSTS max-age (`31536000`)
   - Redis TTLs (`120`, `7200`)
   - Cleanup intervals
   - Timeout values

7. **Standardize pagination defaults**
   - Different endpoints use different defaults (50, 100, 1000)
   - Create `PaginationConfig` class with sensible defaults

8. **Create TaxRatesConfig class**
   - Centralize all tax rate management
   - Support multiple years
   - Allow database-driven configuration

### LOW PRIORITY (Nice-to-have)
9. Document all hardcoded values in ADR (Architecture Decision Record)
10. Add configuration validation to ensure tax rates sum correctly
11. Add feature flags for AI thresholds

---

## CONFIGURATION TEMPLATE

Add to `.env`:

```bash
# ===== RATE LIMITING =====
RATE_LIMIT_REQUESTS_PER_MINUTE=500
RATE_LIMIT_REQUESTS_PER_HOUR=5000
RATE_LIMIT_CLEANUP_INTERVAL=300
REDIS_MINUTE_WINDOW_TTL=120
REDIS_HOUR_WINDOW_TTL=7200
REDIS_SOCKET_TIMEOUT=5

# ===== TAX RATES (2025) =====
TAX_BRACKET_2025_TIER1_THRESHOLD=2400000
TAX_BRACKET_2025_TIER1_RATE=0.13
TAX_BRACKET_2025_TIER2_THRESHOLD=5000000
TAX_BRACKET_2025_TIER2_RATE=0.15
TAX_BRACKET_2025_TIER3_THRESHOLD=20000000
TAX_BRACKET_2025_TIER3_RATE=0.18
TAX_BRACKET_2025_TIER4_THRESHOLD=50000000
TAX_BRACKET_2025_TIER4_RATE=0.20
TAX_BRACKET_2025_TIER5_RATE=0.22

# ===== SOCIAL CONTRIBUTIONS =====
PENSION_FUND_LIMIT=1917000
PENSION_FUND_BASE_RATE=0.22
PENSION_FUND_OVER_LIMIT_RATE=0.10
MEDICAL_INSURANCE_LIMIT=1917000
MEDICAL_INSURANCE_RATE=0.051
SOCIAL_INSURANCE_LIMIT=1032000
SOCIAL_INSURANCE_RATE=0.029

# ===== AI THRESHOLDS =====
AI_MIN_SCORE_THRESHOLD=5
AI_CONFIDENCE_MIN_BASE=0.7
AI_CONFIDENCE_MAX_CAP=0.95
AI_HISTORICAL_CONFIDENCE=0.95
AI_HIGH_CONFIDENCE_THRESHOLD=0.9
AI_MEDIUM_CONFIDENCE_THRESHOLD=0.5
AI_PARSER_TEMPERATURE=0.1
AI_PARSER_MAX_TOKENS=4000

# ===== PAGINATION =====
DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=1000
DEFAULT_EXPENSES_PAGE_SIZE=50
MAX_EXPENSES_PAGE_SIZE=100
DEFAULT_BANK_TX_PAGE_SIZE=50
MAX_BANK_TX_PAGE_SIZE=500

# ===== API TIMEOUTS =====
ODATA_REQUEST_TIMEOUT=30
ODATA_CONNECTION_TIMEOUT=30
ODATA_GET_REQUEST_TIMEOUT=10

# ===== SECURITY =====
HSTS_MAX_AGE=31536000

# ===== TAX CALCULATION =====
TAX_CALCULATION_TOLERANCE=0.01
TAX_CALCULATION_MAX_ITERATIONS=50
```

---

## FILES TO CREATE/MODIFY

1. **NEW: `backend/app/core/constants.py`**
   - Tax brackets (move from ndfl_calculator.py)
   - Tax rates (move from social_contributions_calculator.py)
   - AI thresholds (move from transaction_classifier.py)
   - Financial multipliers

2. **MODIFY: `backend/app/core/config.py`**
   - Add all hardcoded values as configurable fields
   - Import from `constants.py` for defaults

3. **MODIFY: `backend/app/main.py`**
   - Use `settings.RATE_LIMIT_REQUESTS_PER_MINUTE` and `settings.RATE_LIMIT_REQUESTS_PER_HOUR`

4. **MODIFY: `backend/app/utils/auth.py`**
   - Use `settings.ACCESS_TOKEN_EXPIRE_MINUTES` instead of hardcoded 7 days

5. **MODIFY: `backend/app/middleware/rate_limit.py`**
   - Get cleanup interval from settings
   - Get TTL values from settings

6. **MODIFY: `backend/app/api/v1/credit_portfolio.py` and `revenue_plan_details.py`**
   - Fix excessive `max` values in pagination

