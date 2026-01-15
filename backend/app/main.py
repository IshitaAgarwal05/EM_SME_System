"""
FastAPI application initialization and configuration.
Main entry point for the Event Management SaaS backend.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.exceptions import AppException
from app.db.session import close_db, init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_startup", environment=settings.environment)

    # Initialize database (in production, use Alembic migrations instead)
    if settings.is_development:
        await init_db()
        logger.info("database_initialized")

    # Initialize Sentry for error tracking
    if settings.sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration()],
        )
        logger.info("sentry_initialized")

    yield

    # Shutdown
    logger.info("application_shutdown")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Event Management SaaS API",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Add Rate Limiter to App State
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# MIDDLEWARE ORDER MATTERS

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts
)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEBUG: Allow all origins to fix CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug: Print all routes on startup
@app.on_event("startup")
async def startup_event():
    routes = []
    for route in app.routes:
        routes.append(route.path)
    logger.info("registered_routes", routes=routes)

# 3. SlowAPI (Rate Limiting)
app.add_middleware(SlowAPIMiddleware)


# Custom Middleware for Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    # HSTS (Strict-Transport-Security) - only relevant if HTTPS, but good practice to have logic
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    
    # Preventing Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Preventing MIME Sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS Protection (Legacy but still useful for some browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Content Security Policy (Basic)
    # Note: Requires careful tuning for allowing scripts/styles
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-specific exceptions."""
    logger.error(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )


# Generic exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": {} if settings.is_production else {"message": str(exc)},
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs" if settings.debug else "disabled",
    }


# Include API routers
from app.api.v1.router import api_router

app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
