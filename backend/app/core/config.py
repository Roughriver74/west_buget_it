from typing import List, Union, Annotated, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError, BeforeValidator, Field
import secrets
import json
import os

# Import constants for defaults
from app.core import constants


def parse_cors_origins(v: Any) -> List[str]:
    """
    Parse CORS origins from environment variable or list
    Supports both JSON string and Python list formats
    Handles escaped quotes from deployment platforms
    """
    # If it's already a list, use it directly
    if isinstance(v, list):
        return v

    # If it's a string, try to parse it as JSON
    if isinstance(v, str):
        try:
            # Remove outer quotes if present
            v = v.strip()
            if v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]

            # Unescape escaped quotes from deployment platforms
            # Example: [\"http://...\"] -> ["http://..."]
            v = v.replace('\\"', '"')

            origins = json.loads(v)
            if not isinstance(origins, list):
                raise ValueError("CORS_ORIGINS must be a list")
            return origins
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse CORS_ORIGINS as JSON: {e}\n"
                f"Expected format: '[\"http://example.com\",\"http://example.org\"]'\n"
                f"Received: {v}"
            )

    raise ValueError(f"CORS_ORIGINS must be a list or JSON string, got {type(v)}")


class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    APP_NAME: str = "Budget Manager"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Database - individual connection parameters
    DB_HOST: str = "localhost"
    DB_PORT: int = 54329
    DB_NAME: str = "it_budget_db"
    DB_USER: str = "budget_user"
    DB_PASSWORD: str = "budget_pass"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    # DATABASE_URL - can be provided directly or built from individual params
    database_url_override: str | None = Field(default=None, validation_alias='DATABASE_URL')

    @property
    def DATABASE_URL(self) -> str:
        """Build DATABASE_URL from individual components or use provided value"""
        if self.database_url_override:
            return self.database_url_override
        # Build from individual components
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # CORS - stored as string to avoid Pydantic auto-parsing, then converted to list
    cors_origins_raw: Union[str, List[str]] = Field(
        default='["http://localhost:5173","http://localhost:3000"]',
        validation_alias='CORS_ORIGINS'
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS from string or list"""
        return parse_cors_origins(self.cors_origins_raw)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # Sentry
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0

    # Observability
    ENABLE_PROMETHEUS: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis (optional - for distributed rate limiting and caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    USE_REDIS: bool = False  # Set to True to enable Redis
    BASELINE_CACHE_TTL_SECONDS: int = 300
    CACHE_TTL_SECONDS: int = 300

    # AI для обработки счетов (VseGPT)
    VSEGPT_API_KEY: str | None = None
    VSEGPT_BASE_URL: str = "https://api.vsegpt.ru/v1"
    VSEGPT_MODEL: str = "google/gemini-2.5-flash-lite-pre-0925-thinking"

    # OCR настройки
    OCR_LANGUAGE: str = "rus+eng"
    OCR_DPI: int = 300

    # 1С интеграция (опционально)
    C1_ENABLED: bool = False
    C1_BASE_URL: str = "http://localhost:8080"
    C1_USERNAME: str = "api_user"
    C1_PASSWORD: str = "api_password"

    # 1C OData Integration
    ODATA_1C_URL: str = "http://10.10.100.77/trade/odata/standard.odata"
    ODATA_1C_USERNAME: str = "odata.user"
    ODATA_1C_PASSWORD: str = "ak228Hu2hbs28"
    ODATA_1C_CUSTOM_AUTH_TOKEN: str = "Basic 0KjQuNC60YPQvdC+0LLQlTohUUFaMndzeA=="

    # 1C OData File Upload Configuration
    ODATA_1C_ATTACHMENT_ENDPOINT: str = "Catalog_Файлы"
    ODATA_1C_MAX_FILE_SIZE_MB: int = 6  # Максимальный размер файла в МБ

    @property
    def ODATA_1C_MAX_FILE_SIZE(self) -> int:
        """Максимальный размер файла в байтах"""
        return self.ODATA_1C_MAX_FILE_SIZE_MB * 1024 * 1024

    # Credit Portfolio FTP (для автоматического импорта из 1С)
    CREDIT_PORTFOLIO_FTP_HOST: str = "floppisw.beget.tech"
    CREDIT_PORTFOLIO_FTP_USER: str = "floppisw_fin"
    CREDIT_PORTFOLIO_FTP_PASSWORD: str = "G!5zb1FiL8!d"
    CREDIT_PORTFOLIO_FTP_REMOTE_DIR: str = "/"
    CREDIT_PORTFOLIO_FTP_LOCAL_DIR: str = "data/credit_portfolio"

    # Background Scheduler
    SCHEDULER_ENABLED: bool = True
    CREDIT_PORTFOLIO_IMPORT_ENABLED: bool = True
    CREDIT_PORTFOLIO_IMPORT_HOUR: int = 6  # 0-23
    CREDIT_PORTFOLIO_IMPORT_MINUTE: int = 0  # 0-59

    # Employee KPI Auto-Creation
    EMPLOYEE_KPI_AUTO_CREATE_ENABLED: bool = True  # Auto-create EmployeeKPI records monthly

    # Module Expiry Check
    MODULE_EXPIRY_CHECK_ENABLED: bool = True  # Check and deactivate expired modules
    MODULE_EXPIRY_CHECK_HOUR: int = 1  # Hour to run expiry check (0-23)
    MODULE_EXPIRY_CHECK_MINUTE: int = 0  # Minute to run expiry check (0-59)

    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = constants.RATE_LIMIT_REQUESTS_PER_MINUTE
    RATE_LIMIT_REQUESTS_PER_HOUR: int = constants.RATE_LIMIT_REQUESTS_PER_HOUR
    RATE_LIMIT_DEFAULT_REQUESTS_PER_MINUTE: int = constants.RATE_LIMIT_DEFAULT_REQUESTS_PER_MINUTE
    RATE_LIMIT_DEFAULT_REQUESTS_PER_HOUR: int = constants.RATE_LIMIT_DEFAULT_REQUESTS_PER_HOUR
    RATE_LIMIT_CLEANUP_INTERVAL: int = constants.RATE_LIMIT_CLEANUP_INTERVAL

    # Redis Rate Limiting
    REDIS_SOCKET_TIMEOUT: int = constants.REDIS_SOCKET_TIMEOUT
    REDIS_MINUTE_WINDOW_TTL: int = constants.REDIS_MINUTE_WINDOW_TTL
    REDIS_HOUR_WINDOW_TTL: int = constants.REDIS_HOUR_WINDOW_TTL

    # ============================================================================
    # PAGINATION & LIMITS
    # ============================================================================
    DEFAULT_PAGE_SIZE: int = constants.DEFAULT_PAGE_SIZE
    MAX_PAGE_SIZE: int = constants.MAX_PAGE_SIZE
    DEFAULT_EXPENSES_PAGE_SIZE: int = constants.DEFAULT_EXPENSES_PAGE_SIZE
    MAX_EXPENSES_PAGE_SIZE: int = constants.MAX_EXPENSES_PAGE_SIZE
    DEFAULT_BANK_TX_PAGE_SIZE: int = constants.DEFAULT_BANK_TX_PAGE_SIZE
    MAX_BANK_TX_PAGE_SIZE: int = constants.MAX_BANK_TX_PAGE_SIZE
    CREDIT_PORTFOLIO_PAGE_SIZE: int = constants.CREDIT_PORTFOLIO_PAGE_SIZE
    MAX_CREDIT_PORTFOLIO_PAGE_SIZE: int = constants.MAX_CREDIT_PORTFOLIO_PAGE_SIZE
    REVENUE_PLAN_DETAILS_PAGE_SIZE: int = constants.REVENUE_PLAN_DETAILS_PAGE_SIZE
    MAX_REVENUE_PLAN_DETAILS_PAGE_SIZE: int = constants.MAX_REVENUE_PLAN_DETAILS_PAGE_SIZE
    TOP_ITEMS_DEFAULT_LIMIT: int = constants.TOP_ITEMS_DEFAULT_LIMIT
    TOP_ITEMS_MAX_LIMIT: int = constants.TOP_ITEMS_MAX_LIMIT

    # ============================================================================
    # AI & MACHINE LEARNING
    # ============================================================================
    AI_MIN_SCORE_THRESHOLD: int = constants.AI_MIN_SCORE_THRESHOLD
    AI_CONFIDENCE_MIN_BASE: float = constants.AI_CONFIDENCE_MIN_BASE
    AI_CONFIDENCE_MAX_CAP: float = constants.AI_CONFIDENCE_MAX_CAP
    AI_HISTORICAL_CONFIDENCE: float = constants.AI_HISTORICAL_CONFIDENCE
    AI_HIGH_CONFIDENCE_THRESHOLD: float = constants.AI_HIGH_CONFIDENCE_THRESHOLD
    AI_MEDIUM_CONFIDENCE_THRESHOLD: float = constants.AI_MEDIUM_CONFIDENCE_THRESHOLD
    AI_PARSER_TEMPERATURE: float = constants.AI_PARSER_TEMPERATURE
    AI_PARSER_MAX_TOKENS: int = constants.AI_PARSER_MAX_TOKENS

    # ============================================================================
    # API TIMEOUTS
    # ============================================================================
    ODATA_REQUEST_TIMEOUT: int = constants.ODATA_REQUEST_TIMEOUT
    ODATA_CONNECTION_TIMEOUT: int = constants.ODATA_CONNECTION_TIMEOUT
    ODATA_GET_REQUEST_TIMEOUT: int = constants.ODATA_GET_REQUEST_TIMEOUT

    # ============================================================================
    # SECURITY HEADERS
    # ============================================================================
    HSTS_MAX_AGE: int = constants.HSTS_MAX_AGE

    # ============================================================================
    # BATCH PROCESSING
    # ============================================================================
    SYNC_BATCH_SIZE: int = constants.SYNC_BATCH_SIZE
    IMPORT_PREVIEW_ROWS: int = constants.IMPORT_PREVIEW_ROWS

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Validate SECRET_KEY to ensure it's secure

        - Must not be the default value in production
        - Must be at least 32 characters for security
        """
        # Get DEBUG from environment (can't access self here)
        import os
        debug = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

        if not debug and v == "your-secret-key-here-change-in-production":
            raise ValueError(
                "❌ SECURITY ERROR: SECRET_KEY must be changed from default value in production!\n"
                f"Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        if len(v) < 32:
            raise ValueError(
                f"❌ SECURITY ERROR: SECRET_KEY must be at least 32 characters (current: {len(v)})\n"
                f"Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        return v

    @field_validator('database_url_override')
    @classmethod
    def validate_database_url(cls, v: str | None) -> str | None:
        """
        Validate DATABASE_URL to warn about weak passwords

        This is a warning, not an error, as it might be intentional in dev
        """
        if v is None:
            return v

        import os
        debug = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

        weak_passwords = ['password', 'admin', '123456', 'budget_pass', 'postgres']

        if not debug:
            for weak_pass in weak_passwords:
                if weak_pass in v:
                    print(f"⚠️  WARNING: Database URL contains common password '{weak_pass}' - change in production!")
                    break

        return v


    @field_validator('DB_POOL_SIZE', 'DB_MAX_OVERFLOW', 'DB_POOL_TIMEOUT', 'DB_POOL_RECYCLE')
    @classmethod
    def validate_pool_numbers(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return v

    @field_validator('SENTRY_TRACES_SAMPLE_RATE', 'SENTRY_PROFILES_SAMPLE_RATE')
    @classmethod
    def validate_sample_rate(cls, v: float, info) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"{info.field_name} must be between 0.0 and 1.0")
        return v


def get_settings() -> Settings:
    """
    Get validated settings instance

    This function can be used as a dependency in FastAPI routes
    """
    try:
        return Settings()
    except ValidationError as e:
        print("\n" + "=" * 80)
        print("❌ CONFIGURATION ERROR: Invalid settings detected!")
        print("=" * 80)
        for error in e.errors():
            field = error['loc'][0]
            message = error['msg']
            print(f"\nField: {field}")
            print(f"Error: {message}")
        print("\n" + "=" * 80)
        print("Please fix the configuration in your .env file and restart the application.")
        print("=" * 80 + "\n")
        raise


# Create and validate settings on module import
settings = get_settings()
