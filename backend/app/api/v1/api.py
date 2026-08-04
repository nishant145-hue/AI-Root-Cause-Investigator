from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.upload import router as upload_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(upload_router)