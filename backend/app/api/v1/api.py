from app.api.v1.investigation import (
    router as investigation_router,
)
from app.api.v1.routes import dashboard
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.notification_preferences import (
    router as notification_preferences_router,
)
from app.api.v1.routes.notifications import (
    router as notifications_router,
)
from app.api.v1.routes.observability import (
    router as observability_router,
)
from app.api.v1.routes.report import router as report_router
from app.api.v1.routes.upload import router as upload_router
from fastapi import APIRouter

api_router = APIRouter()

# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------
api_router.include_router(
    auth_router,
)
# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------
api_router.include_router(
    upload_router,
)
# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
api_router.include_router(
    dashboard.router,
)
# ---------------------------------------------------------
# Reports
# ---------------------------------------------------------
api_router.include_router(
    report_router,
)
# ---------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------
api_router.include_router(
    notification_preferences_router,
)
# ---------------------------------------------------------
# Notifications
# ---------------------------------------------------------
api_router.include_router(
    notifications_router,
)
# ---------------------------------------------------------
# Investigations
# ---------------------------------------------------------
api_router.include_router(
    investigation_router,
)
# ---------------------------------------------------------
# Observability
# ---------------------------------------------------------
api_router.include_router(
    observability_router,
)
