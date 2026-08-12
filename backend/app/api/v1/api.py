from fastapi import APIRouter

from app.api.v1.routes import dashboard
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.notification_preferences import (
    router as notification_preferences_router,
)
from app.api.v1.routes.notifications import (
    router as notifications_router,
)
from app.api.v1.routes.report import router as report_router
from app.api.v1.routes.upload import router as upload_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(upload_router)
api_router.include_router(dashboard.router)
api_router.include_router(report_router)
api_router.include_router(notification_preferences_router)
api_router.include_router(notifications_router)