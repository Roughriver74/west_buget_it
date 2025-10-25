from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
from app.core.config import settings
from app.api.v1 import expenses, categories, contractors, organizations, budget, analytics, forecast, attachments, dashboards, auth, departments
from app.utils.logger import logger, log_error, log_info

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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
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
app.include_router(expenses.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix=f"{settings.API_PREFIX}/categories", tags=["Categories"])
app.include_router(contractors.router, prefix=f"{settings.API_PREFIX}/contractors", tags=["Contractors"])
app.include_router(organizations.router, prefix=f"{settings.API_PREFIX}/organizations", tags=["Organizations"])
app.include_router(budget.router, prefix=f"{settings.API_PREFIX}/budget", tags=["Budget"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(forecast.router, prefix=f"{settings.API_PREFIX}/forecast", tags=["Forecast"])
app.include_router(attachments.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Attachments"])
app.include_router(dashboards.router, prefix=f"{settings.API_PREFIX}/dashboards", tags=["Dashboards"])


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
