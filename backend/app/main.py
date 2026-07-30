from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@app.on_event("startup")
async def startup():
    logger.info("AI Root Cause Investigator Backend Started")


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "message": "AI Root Cause Investigator API is running 🚀"
    }


@app.get("/health")
async def health():
    logger.info("Health endpoint called")
    return {
        "status": "healthy"
    }