from typing import List, Union, Annotated, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError, BeforeValidator, Field
import secrets
import json
import os


def parse_cors_origins(v: Any) -> List[str]:
    """
    Parse CORS origins from environment variable or list
    Supports both JSON string and Python list formats
    Handles escaped quotes from Coolify and other deployment platforms
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

            # Unescape escaped quotes from deployment platforms (Coolify, etc.)
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
    APP_NAME: str = "IT Budget Manager"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://budget_user:budget_pass@localhost:54329/it_budget_db"
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

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate DATABASE_URL to warn about weak passwords

        This is a warning, not an error, as it might be intentional in dev
        """
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
