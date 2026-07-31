from typing_extensions import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for AI Root Cause Investigator",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
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
    allow_methods=["*"],
    allow_headers=["*"],
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
