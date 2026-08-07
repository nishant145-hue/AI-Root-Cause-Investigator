from app.api.v1.routes import dashboard
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.report import router as report_router
from app.api.v1.routes.upload import router as upload_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(upload_router)
api_router.include_router(dashboard.router)
api_router.include_router(report_router)