# Исправленная версия backend/app/main.py (строки 1-110)
# ИСПОЛЬЗУЙТЕ ЭТУ ВЕРСИЮ ПОСЛЕ ОТКАТА

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.api.v1 import expenses, categories, contractors, organizations, budget, analytics, analytics_advanced, forecast, attachments, dashboards, auth, departments, audit, reports, employees, payroll, budget_planning, kpi, templates, comprehensive_report
from app.utils.logger import logger, log_error, log_info
from app.middleware import (
    create_rate_limiter,
    create_security_headers_middleware,
    create_https_redirect_middleware,
)

# Initialize Sentry (optional)
if settings.SENTRY_DSN:
    sentry_init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        environment="production" if not settings.DEBUG else "development",
    )
    log_info("Sentry initialized", "Startup")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API для управления бюджетом IT-отдела",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Prometheus metrics (optional)
if settings.ENABLE_PROMETHEUS:
    Instrumentator().instrument(app).expose(app)
    log_info("Prometheus metrics exposed at /metrics", "Startup")


# ============================================
# CRITICAL: Preflight OPTIONS Handler
# ============================================
# ИСПРАВЛЕННАЯ ВЕРСИЯ: использует PlainTextResponse вместо Response
# и более надёжную проверку origin
class OptionsMiddleware(BaseHTTPMiddleware):
    """
    Handle OPTIONS requests (CORS preflight) immediately.

    This prevents OPTIONS from being blocked by rate limiting or other middleware
    that might cause 503 errors when Traefik tries to forward preflight requests.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS request immediately
        if request.method == "OPTIONS":
            # Get origin from request
            origin = request.headers.get("origin", "")

            # Check if origin is allowed
            allowed = False
            cors_origins = settings.CORS_ORIGINS

            # Check against all CORS origins
            for allowed_origin in cors_origins:
                if allowed_origin == "*":
                    allowed = True
                    origin = "*"
                    break
                elif origin == allowed_origin:
                    allowed = True
                    break
                # Support wildcards like https://*.example.com
                elif allowed_origin.startswith("https://") and "*" in allowed_origin:
                    pattern = allowed_origin.replace("*", ".*")
                    import re
                    if re.match(pattern, origin):
                        allowed = True
                        break

            # Build response headers
            headers = {
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "3600",
                "Content-Type": "text/plain",
                "Content-Length": "0",
            }

            if allowed:
                headers["Access-Control-Allow-Origin"] = origin
                headers["Access-Control-Allow-Credentials"] = "true"

            # Return PlainTextResponse instead of Response for better compatibility
            return PlainTextResponse(
                status_code=200,
                headers=headers,
                content=""
            )

        # For non-OPTIONS requests, proceed normally
        return await call_next(request)


# Add OPTIONS middleware FIRST (before any other middleware)
app.add_middleware(OptionsMiddleware)
log_info("OPTIONS preflight middleware enabled (handles CORS preflight immediately)", "Startup")

# Configure CORS (this will handle actual requests, not preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... rest of the file stays the same
