from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from typing_extensions import Final

from app.api.v1.api import api_router
from app.auth.security import require_admin
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.metrics import metrics
from app.core.rate_limit import limiter
from app.database.session import engine
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security.exceptions import (
    global_exception_handler,
)
from app.middleware.security.request_size import (
    RequestSizeLimitMiddleware,
)
from app.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI Root Cause Investigator",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_exception_handler(
    Exception,
    global_exception_handler,
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Return a safe validation response without exposing
    internal implementation details or sensitive input values.
    """

    safe_errors = []

    for error in exc.errors():
        safe_errors.append(
            {
                "loc": error.get("loc", []),
                "type": error.get("type", "validation_error"),
                "msg": "Invalid request data.",
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "detail": safe_errors,
        },
    )

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

# -----------------------------
# Request Body Size Protection
# -----------------------------
app.add_middleware(
    RequestIDMiddleware,
)

app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_size=settings.MAX_REQUEST_BODY_SIZE,
)

# -----------------------------
# Security Headers
# -----------------------------
app.add_middleware(
    SecurityHeadersMiddleware,
)
# -----------------------------
# CORS Configuration
# -----------------------------
origins = [
    "http://localhost:3000",  # React (CRA)
    "http://localhost:5173",  # React (Vite)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
    ],
)

@app.on_event("startup")
async def startup():
    logger.info("AI Root Cause Investigator Backend Started")


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "message": "AI Root Cause Investigator API is running 🚀",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    logger.info("Health endpoint called")
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/ready")
async def readiness():
    """
    Readiness check.

    Verifies that the application is running and the
    database connection is available.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Readiness check passed")

        return {
            "status": "ready",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "dependencies": {
                "database": "healthy",
            },
        }

    except Exception:
        logger.exception("Readiness check failed")

        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "dependencies": {
                    "database": "unavailable",
                },
            },
        )

@app.get("/metrics")
def metrics_endpoint(
    _admin=Depends(require_admin),
):
    """Return application metrics for administrators only."""

    return metrics.snapshot()
