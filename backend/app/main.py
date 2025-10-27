from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
from app.core.config import settings
from app.api.v1 import expenses, categories, contractors, organizations, budget, analytics, forecast, attachments, dashboards, auth, departments, audit, reports, employees, payroll, budget_planning
from app.utils.logger import logger, log_error, log_info
from app.middleware import (
    create_rate_limiter,
    create_security_headers_middleware,
    create_https_redirect_middleware,
)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API для управления бюджетом IT-отдела",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure HTTPS redirect (disabled by default)
# To enable HTTPS redirect in production:
# 1. Ensure SSL/TLS certificates are properly configured
# 2. Set up reverse proxy (nginx/load balancer) with X-Forwarded-Proto header
# 3. Uncomment the middleware below and set enabled=not settings.DEBUG
# 4. Also set enable_hsts=True in security headers middleware
#
# app.add_middleware(
#     create_https_redirect_middleware(
#         enabled=not settings.DEBUG  # Enable in production only
#     )
# )

# Configure security headers
# Enable HSTS only if HTTPS is enabled (check settings.DEBUG for production)
app.add_middleware(
    create_security_headers_middleware(
        is_production=not settings.DEBUG,
        enable_hsts=False  # Set to True when HTTPS is enabled in production
    )
)
log_info(f"Security headers enabled (production mode: {not settings.DEBUG})", "Startup")

# Configure rate limiting
# 100 requests per minute, 1000 requests per hour per IP
app.add_middleware(create_rate_limiter(requests_per_minute=100, requests_per_hour=1000))
log_info("Rate limiting enabled: 100 req/min, 1000 req/hour per IP", "Startup")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()

    # Get user info if available
    user = "anonymous"
    if hasattr(request.state, "user") and request.state.user:
        user = getattr(request.state.user, "username", "unknown")

    # Log request
    logger.info(f"Request: {request.method} {request.url.path} - User: {user}")

    # Process request
    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.2f}s"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_error(e, f"Request failed: {request.method} {request.url.path} - Time: {process_time:.2f}s")
        raise


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        f"Validation Error: {request.url.path} - Errors: {exc.errors()}"
    )
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = dict(error)
        # Convert bytes to string if present
        if 'input' in error_dict and isinstance(error_dict['input'], bytes):
            error_dict['input'] = error_dict['input'].decode('utf-8', errors='replace')
        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    log_error(exc, f"Unhandled exception in {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(departments.router, prefix=f"{settings.API_PREFIX}/departments", tags=["Departments"])
app.include_router(audit.router, prefix=f"{settings.API_PREFIX}/audit", tags=["Audit Logs"])
app.include_router(expenses.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix=f"{settings.API_PREFIX}/categories", tags=["Categories"])
app.include_router(contractors.router, prefix=f"{settings.API_PREFIX}/contractors", tags=["Contractors"])
app.include_router(organizations.router, prefix=f"{settings.API_PREFIX}/organizations", tags=["Organizations"])
app.include_router(budget.router, prefix=f"{settings.API_PREFIX}/budget", tags=["Budget"])
app.include_router(budget_planning.router, prefix=f"{settings.API_PREFIX}/budget/planning", tags=["Budget Planning"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(forecast.router, prefix=f"{settings.API_PREFIX}/forecast", tags=["Forecast"])
app.include_router(attachments.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Attachments"])
app.include_router(dashboards.router, prefix=f"{settings.API_PREFIX}/dashboards", tags=["Dashboards"])
app.include_router(reports.router, prefix=f"{settings.API_PREFIX}/reports", tags=["Reports"])
app.include_router(employees.router, prefix=f"{settings.API_PREFIX}/employees", tags=["Employees"])
app.include_router(payroll.router, prefix=f"{settings.API_PREFIX}/payroll", tags=["Payroll"])


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    log_info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}", "Startup")
    log_info(f"API Documentation: /docs", "Startup")
    log_info(f"API Prefix: {settings.API_PREFIX}", "Startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    log_info(f"Shutting down {settings.APP_NAME}", "Shutdown")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IT Budget Manager API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
