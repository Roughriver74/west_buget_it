from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import expenses, categories, contractors, organizations, budget, analytics, forecast, attachments, dashboards, auth

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

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix=f"{settings.API_PREFIX}/categories", tags=["Categories"])
app.include_router(contractors.router, prefix=f"{settings.API_PREFIX}/contractors", tags=["Contractors"])
app.include_router(organizations.router, prefix=f"{settings.API_PREFIX}/organizations", tags=["Organizations"])
app.include_router(budget.router, prefix=f"{settings.API_PREFIX}/budget", tags=["Budget"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(forecast.router, prefix=f"{settings.API_PREFIX}/forecast", tags=["Forecast"])
app.include_router(attachments.router, prefix=f"{settings.API_PREFIX}/expenses", tags=["Attachments"])
app.include_router(dashboards.router, prefix=f"{settings.API_PREFIX}/dashboards", tags=["Dashboards"])


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
